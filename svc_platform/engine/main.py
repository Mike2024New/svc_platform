import uuid, asyncio
from time import perf_counter
from typing import Any, Awaitable, Callable, TypeVar, Generic
from svc_platform import slots
from svc_platform.engine.exc import EngineExc
from svc_platform.schemas import BaseSettings, EngineIOSchemas

__all__ = ['Engine']

"""
На потом:
Промануалить api, сейчас они не совсем удобны.
Добавить статусы (для execute/process), чтобы по api можно было их запрашивать
Добавить очистку памяти (процесс) по таймауту, иначе утечка ресурсов.
"""

# =============== ДЖЕНЕРИКИ ТИПОВ ===============
# TypeVar с bound задает "верхнюю границу" — тип-ограничение.
# В дочерних проектах нужно переопределить эти TypeVar,
# подставив свои модели-наследники из EngineIOSchemas и также переопределив BaseSettings.
#
# Это позволяет:
# 1. IDE видеть точные типы (автокомплит полей voice, speed и т.д.)
# 2. Pydantic валидировать данные по расширенным схемам
# 3. Сохранить типобезопасность на всех уровнях
#
# Механизм: TypeVar → Generic → наследование с типами
# Чтобы не забыть это всё и не мучиться с этим каждый раз, лучше сделать репозиторий копируемый шаблон где это всё сделано
# ====================================================
BaseSettingsType = TypeVar('BaseSettingsType', bound=BaseSettings)
ExecuteInputDataType = TypeVar('ExecuteInputDataType', bound=EngineIOSchemas.execute_input_data)
ProcessInputDataType = TypeVar('ProcessInputDataType', bound=EngineIOSchemas.process_input_data)
ProcessOutputDataType = TypeVar('ProcessOutputDataType', bound=EngineIOSchemas.process_output_data)
StreamingInputDataType = TypeVar('StreamingInputDataType', bound=EngineIOSchemas.streaming_input_data)
StreamingOutputDataType = TypeVar('StreamingOutputDataType', bound=EngineIOSchemas.streaming_output_data)

from dataclasses import dataclass


@dataclass
class ProcessTask:
    event: asyncio.Event
    result: Any | None = None
    completed_at: float | None = None


@dataclass
class ExecuteTask:
    event: asyncio.Event


@dataclass
class StreamingTask:
    event: asyncio.Event
    task: asyncio.Task | None


class Engine(
    Generic[  # привязка дженериков, это важно чтобы в дочерних проектах IDE видел определенные в них схемы
        BaseSettingsType,
        ExecuteInputDataType,
        ProcessInputDataType,
        ProcessOutputDataType,
        StreamingInputDataType,
        StreamingOutputDataType,
    ]
):
    def __init__(self, settings: BaseSettingsType, ):
        """
        :param settings: системные настройки приложения (settings.json)
        """
        self._settings = settings
        self._running = False
        self.parameters: dict[str, Any] = {'running': self._running}
        self._on_set_parameters()
        # состояние Engine
        # стоп сигналы
        self._stop_component = asyncio.Event()

        # настройка цепочки stream
        self._streaming_registry: dict[str, StreamingTask] = {}
        self._streaming_semaphore = asyncio.Semaphore(self._settings.streaming_limit)

        # настройка цепочки execute
        self._execute_registry: dict[str, ExecuteTask] = {}
        self._execute_semaphore = asyncio.Semaphore(self._settings.execute_limit)

        # настройка цепочки process
        self._process_registry: dict[str, ProcessTask] = {}
        self._process_semaphore = asyncio.Semaphore(self._settings.process_limit)
        self._process_cleanup_task: asyncio.Task | None = None

    def _on_set_parameters(self):
        """логика записи параметров (например информация об используемом устройстве)"""
        self.parameters['execute_limit'] = self._settings.execute_limit
        self.parameters['process_limit'] = self._settings.process_limit
        self.parameters['process_result_ttl'] = self._settings.process_result_ttl
        self.parameters['streaming_limit'] = self._settings.streaming_limit
        self.parameters['streaming_all_tasks_timeout'] = self._settings.streaming_all_tasks_timeout

    # =============== START =================

    async def start(self, *args, **kwargs) -> None:
        """Запуск движка, выполняет тяжелую логику запуска (например whisper или llm), метод идемпотентен."""
        _ = self, args, kwargs  # игнорировать variable unused
        if self._running:
            return
        self._stop_component.clear()
        self._running = True
        self.parameters['running'] = True
        try:
            # запуск Engine
            await self._on_start(*args, **kwargs)
            slots.slot1(self._settings.name, parameters=self.parameters)
            # запуск наблюдателя за результатами процессов (чтобы удалять старые процессы)
            if self._process_cleanup_task is None:
                self._process_cleanup_task = asyncio.create_task(self._cleanup_old_processes())
        except Exception as err:
            slots.slot3(name=self._settings.name, err=err)
            raise EngineExc.StartError(err)

    async def _on_start(self, *args, **kwargs) -> None:
        pass

    # =============== STOP =================

    async def stop(self, *args, **kwargs) -> None:
        """Остановка движка, метод идемпотентный."""
        _ = self, args, kwargs  # игнорировать variable unused
        if not self._running:
            return
        self._stop_component.set()
        self._running = False
        self.parameters['running'] = False
        try:
            await self._on_stop(*args, **kwargs)
            # сбросить все процессы.
            self._process_registry = {}
            self._execute_registry = {}
            await self.stop_all_stream_tasks()
            # остановка наблюдателя за результатами процессов (который удаляет старые процессы)
            if self._process_cleanup_task is not None:
                self._process_cleanup_task.cancel()
                self._process_cleanup_task = None
            slots.slot2(self._settings.name, parameters=self.parameters)
        except Exception as err:
            slots.slot3(name=self._settings.name, err=err)
            raise EngineExc.StopError(err)
        # базовая логика, наследники должны вызывать super (либо без super для переопределения метода полностью)

    async def _on_stop(self, *args, **kwargs) -> None:
        pass

    # =============== PROCESS =================

    async def _cleanup_old_processes(self):
        """Удаление старых процессов (процессы результат по которым готов, но они лежат уже долго дольше ttl)"""
        while self._running:
            await asyncio.sleep(2)
            now = perf_counter()

            expired_ids = []
            for req_id, data in self._process_registry.items():
                if data.completed_at is not None:
                    if (now - data.completed_at) > self._settings.process_result_ttl:
                        expired_ids.append(req_id)

            # удаление устаревших задач
            for req_id in expired_ids:
                slots.slot22(self._settings.name, request_id=req_id)
                self._process_registry.pop(req_id, None)

    async def process(
            self, data: ProcessInputDataType, request_id: str = str(uuid.uuid4())[:8], *args, **kwargs
    ) -> None:
        """
        (Не переопределять этот метод, бизнес логику реализовывать в _on_execute)
        Блокирующая обработка (batch режим).
        -------------------------------------------------------
        Паттерн: Один запрос → Один ответ
        Примеры:
            - STT: аудио → текст
            - TTS: текст → аудио
            - Классификация: данные → категория
        -------------------------------------------------------
        :param request_id: id запроса (например для цепочки http запросов)
        :param data: Входные данные
        :return: Результат обработки или None если сервис не запущен
        (Не переопределять этот метод, бизнес логику реализовывать в _on_execute)
        """
        _ = self, data, args, kwargs  # игнорировать variable unused

        if not self._running:
            return None

        if request_id in self._process_registry:
            raise EngineExc.ProcessRequestIdAlreadyExists(f'Задача с `{request_id}` уже выполняется.')

        async with self._process_semaphore:  # защита от конфликта корутин (превышения лимита)
            start_time = perf_counter()
            slots.slot16(name=self._settings.name, request_id=request_id)
            # создание задачи (процесса)
            self._process_registry[request_id] = ProcessTask(event=asyncio.Event())
            try:
                # добавление ячейки результата (со своим процессом)
                process_task = asyncio.create_task(self._on_process(
                    data, event=self._process_registry[request_id].event, *args, **kwargs)
                )
                result = await process_task
                # если задача была отменена
                if result is None:
                    slots.slot23(name=self._settings.name, request_id=request_id)
                    self._process_registry.pop(request_id, None)
                    return None
                end_time = round(perf_counter() - start_time, 2)
                slots.slot17(name=self._settings.name, request_id=request_id, end_time=end_time)
                # добавление результата в ячейку
                if self._process_registry.get(request_id) is not None:
                    self._process_registry[request_id].result = result
                    self._process_registry[request_id].completed_at = perf_counter()
            except asyncio.CancelledError:  # на случай отмены через task.cancel()
                slots.slot20(name=self._settings.name, request_id=request_id)
                self._process_registry.pop(request_id, None)  # если задача упала с ошибкой, то убрать её из списка
                raise
            except Exception as err:  # отлов любых ошибок
                slots.slot5(name=self._settings.name, request_id=request_id, err=err)
                raise
            finally:
                # в любом случае испустить сигнал о завершении процесса
                if request_id in self._process_registry:
                    self._process_registry[request_id].event.set()

    async def _on_process(
            self, data: ProcessInputDataType, event: asyncio.Event, *args, **kwargs
    ) -> ProcessOutputDataType | None:
        """
        Вычислитель в режиме "запрос-ответ" (batch).
        В наследниках переопределяется под конкретную бизнес-логику (STT, TTS, LLM и т.д.).
        Сейчас пример заглушка:
        Принимает входные данные, имитирует длительную обработку (data.iterations * data.step_time) с возможностью прерывания,
        возвращает результат в виде выходной схемы (с результатом который был передан в текст).

        :param data: Входные данные (схема ProcessInputDataType)
        :param process: event для прерывания выполнения извне (stop_process - бизнес логика должна отслеживать сигнал is_set())
        :return: Результат вычислений (ProcessOutputDataType) или None при прерывании
        """
        _ = self, data, args, kwargs
        for _ in range(data.iterations):
            if event.is_set():  # досрочная остановка
                return None
            await asyncio.sleep(0.1)  # иммитация длительной нагрузки вычислений (чем больше итераций тем дольше)
        # возвращается заглушка с текстом прописанным в модели по умолчанию
        return EngineIOSchemas.process_output_data(result=data)

    def stop_process(self, request_id: str) -> None:
        """
        Остановка запущенного процесса вычислений (batch режима) по request_id, если такая задача была запущена
        :param request_id: id процесса
        :return: None
        """
        if request_id not in self._process_registry:
            raise EngineExc.ProcessResultNoFindReqestId(f'Не запущен процесс для request_id: {request_id}')

        self._process_registry[request_id].event.set()

    def get_process_result(self, request_id) -> ProcessOutputDataType:
        """
        Получение результата вычисления процесса по request_id, если не готово или отменено, возбуждаются исключения
        :param request_id: id процесса
        :return: результат вычисления процесса если готов
        """
        if request_id not in self._process_registry:
            raise EngineExc.ProcessResultNoFindReqestId(f'Не запущен процесс для request_id: {request_id}')

        if self._process_registry[request_id].result is None:
            raise EngineExc.ProcessResultNotCompleted('результат ещё не готов')

        result = self._process_registry[request_id].result
        self._process_registry.pop(request_id)
        slots.slot26(name=self._settings.name, request_id=request_id)
        return result

    # =============== EXECUTE =================

    async def execute(self, data: ExecuteInputDataType, request_id: str = str(uuid.uuid4())[:8], *args,
                      **kwargs) -> None:
        """
        (логику метода определять в _on_execute)
        Исполнительный метод (action режим).
        ----------------------------------------------------
        Паттерн: Один запрос → Действие без ответа
        Примеры:
            - Audio Output: PCM аудио → воспроизведение
            - Управление устройством: команда → выполнение
            - Сохранение данных: информация → запись
        ----------------------------------------------------
        :param request_id:
        :param data: Входные данные (опционально)
        :return: None
        (логику метода определять в _on_execute)
        """
        _ = self, data, args, kwargs  # игнорировать variable unused
        async with self._execute_semaphore:  # защита от конфликта корутин (превышения лимита)
            # входные проверки
            if not self._running:
                return

            if request_id in self._execute_registry:
                raise EngineExc.ExecuteRequestIdAlreadyExists(f'Задача с `{request_id}` уже выполняется.')

            start_time = perf_counter()
            slots.slot18(name=self._settings.name, request_id=request_id)
            # создание event для управления текущей задачей (процессом)
            self._execute_registry[request_id] = ExecuteTask(event=asyncio.Event())
            try:
                await self._on_execute(data, event=self._execute_registry[request_id].event, *args, **kwargs)
                end_time = round(perf_counter() - start_time, 2)
                slots.slot19(name=self._settings.name, request_id=request_id, end_time=end_time)
            except asyncio.CancelledError:
                raise
            except Exception as err:
                slots.slot6(name=self._settings.name, request_id=request_id, err=err)
                raise
            finally:
                # сообщить о завершении
                if self._execute_registry.get(request_id) is not None:
                    self._execute_registry[request_id].event.set()
                self._execute_registry.pop(request_id, None)  # удалить задачу

    async def _on_execute(self, data: ExecuteInputDataType, event: asyncio.Event, *args, **kwargs) -> None:
        """Метод исполнительный, например tts. Следит за состоянием переменной self._stop_execute.is_set()"""
        _ = self, data, args, kwargs
        for i in data.text.split():
            await asyncio.sleep(data.step_time)

            # Остановка задачи (в классах наследниках этот же механизм)
            if event.is_set():
                return

            print(i)

    def stop_execute(self, request_id: str) -> None:
        if request_id not in self._execute_registry:
            raise EngineExc.ExecuteNoFindReqestId(f'Не запущен execute для request_id: {request_id}')

        self._execute_registry[request_id].event.set()
        slots.slot21(name=self._settings.name, request_id=request_id)

    # =============== STREAM =================

    async def stream(
            self,
            callback: Callable[[StreamingOutputDataType],
            Awaitable[None]],
            data: StreamingInputDataType,
            request_id: str = str(uuid.uuid4())[:8],
            *args,
            **kwargs
    ) -> None:
        """
        Стриминговая обработка (real-time режим). Метод асинхронный
        -------------------------------------------------------
        Паттерн: Один запрос → Много ответов (по частям)
        Примеры:
            - LLM: промпт → токены (через callback)
            - Real-time STT: аудио → фрагменты текста
            - TTS: текст → аудио фрагменты
        -------------------------------------------------------
        :param request_id:
        :param callback: Функция для каждого фрагмента результата
        :param data: Входные данные (опционально)
        :return: None
        """
        if request_id in self._streaming_registry:
            raise EngineExc.StreamRequestIdAlreadyExists(f'Задача с `{request_id}` уже выполняется.')

        async with self._streaming_semaphore:

            if not self._running:
                return

            start_time = perf_counter()
            _ = self, data, args, kwargs  # игнорировать variable unused

            try:
                self._streaming_registry[request_id] = StreamingTask(event=asyncio.Event(), task=None)
                # запуск стриминга
                task = asyncio.create_task(
                    self._on_stream(
                        data=data,
                        callback=callback,
                        event=self._streaming_registry[request_id].event,
                        *args, **kwargs
                    )
                )
                self._streaming_registry[request_id].task = task  # собрать задачи для отмены (в stop)
                slots.slot8(name=self._settings.name, request_id=request_id)
                await task
                end_time = round(perf_counter() - start_time, 2)
                slots.slot9(name=self._settings.name, request_id=request_id, end_time=end_time)
            except asyncio.CancelledError:
                end_time = round(perf_counter() - start_time, 2)
                slots.slot24(name=self._settings.name, request_id=request_id, end_time=end_time)
            except Exception as err:
                slots.slot7(name=self._settings.name, request_id=request_id, err=err)
                raise
            finally:
                self._streaming_registry.pop(request_id, None)  # удалить задачу

    async def _on_stream(self, data: StreamingInputDataType, callback, event: asyncio.Event, *args, **kwargs) -> None:
        _ = self, data, args, kwargs  # игнорировать variable unused
        # временная заглушка, имитирующая полезную нагрузку
        for i in range(data.iterations):
            if event.is_set():
                return
            await callback(f'stream chunk:{i} {data.text}')
            await asyncio.sleep(0.2)

    def stop_stream(self, request_id: str) -> None:
        """Явная остановка стриминга (например через http)"""
        if request_id not in self._streaming_registry:
            raise EngineExc.StreamNoFindReqestId(f'Не запущен stream для request_id: {request_id}')
        self._streaming_registry[request_id].event.set()

    async def stop_all_stream_tasks(self):
        """Прерывание всех запущенных стриминговых процессов"""
        # собрать все неотмененные задачи
        active_tasks = [data.task for data in self._streaming_registry.values() if not data.task.done()]

        for task in active_tasks:
            task.cancel()

        if active_tasks:
            try:
                # ожидание отмены текущих стримов
                await asyncio.wait_for(
                    asyncio.gather(
                        *active_tasks,
                        return_exceptions=True  # подав исключ (например если гонка и какая то задача отменилась раньше)
                    ),
                    timeout=self._settings.streaming_all_tasks_timeout,
                )
            except asyncio.TimeoutError:
                slots.slot25(name=self._settings.name, timeout=self._settings.streaming_all_tasks_timeout)


if __name__ == '__main__':
    async def main():
        from svc_platform.schemas import BaseSettings
        from svc_platform.factories import settings_manager_factory, engine_factory
        from svc_platform.slots import slots_init
        from svc_platform.schemas import EngineIOSchemas

        slots_init(callback=None, enable=True)
        current_settings, _ = settings_manager_factory(reset_json=True, settings_model=BaseSettings(streaming_limit=3))
        engine = engine_factory(engine_class=Engine, settings=current_settings)
        print(engine.parameters)
        await engine.start()

        async def callback(chunk: EngineIOSchemas.streaming_output_data):
            print(chunk)

        request_id = '#000'
        task = asyncio.create_task(
            engine.stream(
                callback=callback,
                data=EngineIOSchemas.streaming_input_data(),
                request_id=request_id,
            )
        )
        # важно при стопе, нужно отменить в ручную все запущенные стриминги иначе процесс зависнет и не выйдет
        await asyncio.sleep(1)
        engine.stop_stream(request_id=request_id)
        await task
        # engine.stop_stream(request_id=request_id)
        # await task
        # print(engine._streaming_registry)


    asyncio.run(main())
