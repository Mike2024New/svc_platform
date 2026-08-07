import uuid
import asyncio
import threading, atexit
from time import perf_counter
from typing import Any, Awaitable, Callable, TypeVar, Generic
from svc_platform import slots
from svc_platform.schemas import BaseSettings
from svc_platform.engine.exc import EngineExc
from svc_platform.schemas import EngineIOSchemas

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
StreamingInputData = TypeVar('StreamingInputData', bound=EngineIOSchemas.streaming_input_data)


class Engine(
    Generic[  # привязка дженериков, это важно чтобы в дочерних проектах IDE видел определенные в них схемы
        BaseSettingsType,
        ExecuteInputDataType,
        ProcessInputDataType,
        ProcessOutputDataType,
        StreamingInputData,
    ]
):
    def __init__(
            self,
            settings: BaseSettingsType,
            process_limit: int = 1,
            execute_limit: int = 1,
    ):
        """
        :param settings: системные настройки приложения (settings.json)
        """
        atexit.register(self.stop)
        self._settings = settings
        self._running = False
        self.parameters: dict[str, Any] = {'running': self._running}
        self._on_set_parameters()
        # стоп сигналы
        self._stop_component = threading.Event()
        self._stop_streaming = asyncio.Event()
        self._stop_process = threading.Event()
        # регистраторы задач
        self._process_registry: dict[str, Any] = {}
        self._execute_registry: dict[str, Any] = {}
        # лимиты задач
        self._process_limit = process_limit
        self._execute_limit = execute_limit
        self._process_semaphore = asyncio.Semaphore(process_limit)
        self._execute_semaphore = asyncio.Semaphore(execute_limit)
        self._streaming_running = False

    def _on_set_parameters(self):
        """логика записи параметров (например информация об используемом устройстве)"""
        pass

    # =============== START =================

    def start(self, *args, **kwargs) -> None:
        """Запуск движка, выполняет тяжелую логику запуска (например whisper или llm), метод идемпотентен."""
        _ = self, args, kwargs  # игнорировать variable unused
        if self._running:
            return
        self._stop_component.clear()
        self._running = True
        self.parameters['running'] = True
        try:
            self._on_start(*args, **kwargs)
            slots.slot1(self._settings.name, parameters=self.parameters)
        except Exception as err:
            slots.slot3(name=self._settings.name, err=err)
            raise err

    def _on_start(self, *args, **kwargs) -> None:
        pass

    # =============== STOP =================

    def stop(self, *args, **kwargs) -> None:
        """Остановка движка, метод идемпотентный."""
        _ = self, args, kwargs  # игнорировать variable unused
        if not self._running:
            return
        self._stop_component.set()
        self._running = False
        self.parameters['running'] = False
        try:
            self.stop_stream()  # остановить стриминг если он продолжается
            self._on_stop(*args, **kwargs)
            slots.slot2(self._settings.name, parameters=self.parameters)
            self._process_registry = {}
            self._execute_registry = {}
        except Exception as err:
            slots.slot3(name=self._settings.name, err=err)
            raise err
        # базовая логика, наследники должны вызывать super (либо без super для переопределения метода полностью)

    def _on_stop(self, *args, **kwargs) -> None:
        pass

    # =============== PROCESS =================

    async def process(
            self, data: ProcessInputDataType, request_id: str = str(uuid.uuid4())[:8], *args, **kwargs
    ) -> None:
        """
        (логику метода определять в _on_execute)
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
        (логику метода определять в _on_execute)
        """
        _ = self, data, args, kwargs  # игнорировать variable unused
        async with self._process_semaphore:  # защита от конфликта корутин (превышения лимита)
            # входные проверки
            if not self._running:
                return None

            if request_id in self._process_registry:
                raise EngineExc.ProcessRequestIdAlreadyExists(f'Задача с `{request_id}` уже выполняется.')

            start_time = perf_counter()
            slots.slot16(name=self._settings.name, request_id=request_id)
            # создание задачи (процесса)
            process = asyncio.Event()
            self._process_registry[request_id] = {'event': process, 'result': None, 'cancelled': False}
            try:
                # добавление ячейки результата (со своим процессом)
                result = await self._on_process(data, process=process, *args, **kwargs)
                end_time = round(perf_counter() - start_time, 2)
                slots.slot17(name=self._settings.name, request_id=request_id, end_time=end_time)
                # добавление результата в ячейку
                if self._process_registry.get(request_id) is not None:
                    self._process_registry[request_id]['result'] = result
            except asyncio.CancelledError:
                slots.slot20(name=self._settings.name, request_id=request_id)
                self._process_registry.pop(request_id, None)  # если задача упала с ошибкой, то убрать её из списка
                raise
            except Exception as err:
                slots.slot5(name=self._settings.name, err=err)
                raise
            finally:
                if self._process_registry.get(request_id):
                    self._process_registry[request_id]['event'].set()

    async def _on_process(
            self, data: ProcessInputDataType, process: asyncio.Event, *args, **kwargs
    ) -> ProcessOutputDataType | None:
        """Процесс вычислений, например transcribate у whisper (перевод аудио в текст). Может быть прерван через stop_process"""
        _ = self, data, args, kwargs
        for _ in range(5):  # 5 итераций по 0.5 сек -> 2.5 сек
            if process.is_set():  # досрочная остановка
                return None
            await asyncio.sleep(0.5)  # иммитация длительной нагрузки вычислений
        # возвращается заглушка с текстом прописанным в модели по умолчанию
        return EngineIOSchemas.process_output_data()

    def stop_process(self, request_id: str) -> None:
        if self._process_registry.get(request_id) is not None:
            self._process_registry[request_id]['event'].set()
            self._process_registry[request_id]['cancelled'] = True  # сообщить что задача отменена
        else:
            raise EngineExc.ProcessResultNoFindReqestId(f'Не запущен процесс для request_id: {request_id}')

    def get_process_result(self, request_id) -> ProcessOutputDataType:
        if request_id not in self._process_registry:
            raise EngineExc.ProcessResultNoFindReqestId(f'Не запущен процесс для request_id: {request_id}')

        if self._process_registry[request_id]['cancelled']:
            self._process_registry.pop(request_id)  # утилизация задачи
            raise EngineExc.ProcessCancelled(f'Задача `{request_id}` была отменена.')

        if self._process_registry[request_id]['result'] is None:
            raise EngineExc.ProcessResultNotCompleted('результат ещё не готов')

        result = self._process_registry[request_id]['result']
        self._process_registry.pop(request_id)  # утилизация задачи
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
            process = asyncio.Event()
            self._execute_registry[request_id] = {'event': process, 'cancelled': False}
            try:
                await self._on_execute(data, process, *args, **kwargs)
                end_time = round(perf_counter() - start_time, 2)
                slots.slot19(name=self._settings.name, request_id=request_id, end_time=end_time)
            except asyncio.CancelledError:
                print(f'Остановка приложения')
                raise
            except Exception as err:
                slots.slot6(name=self._settings.name, err=err)
                raise
            finally:
                # сообщить о завершении
                if self._execute_registry.get(request_id) is not None:
                    self._execute_registry[request_id]['event'].set()
                self._execute_registry.pop(request_id, None)  # удалить задачу

    async def _on_execute(self, data: ExecuteInputDataType, process: asyncio.Event, *args, **kwargs) -> None:
        """Метод исполнительный, например tts. Следит за состоянием переменной self._stop_execute.is_set()"""
        _ = self, data, args, kwargs
        for i in 'This is a #stub. Example TTS Voice synthesis in progress. Long text for example.'.split():
            await asyncio.sleep(0.1)

            # Остановка задачи (в классах наследниках этот же механизм)
            if process.is_set():
                return

            print(i)

    def stop_execute(self, request_id: str) -> None:
        if request_id not in self._execute_registry:
            raise EngineExc.ExecuteNoFindReqestId(f'Не запущен execute для request_id: {request_id}')

        self._execute_registry[request_id]['event'].set()
        self._execute_registry[request_id]['cancelled'] = True

    # =============== STREAM =================

    async def stream(self, callback: Callable[[Any], Awaitable[None]], data: StreamingInputData, *args,
                     **kwargs) -> None:
        """
        Стриминговая обработка (real-time режим). Метод асинхронный
        -------------------------------------------------------
        Паттерн: Один запрос → Много ответов (по частям)
        Примеры:
            - LLM: промпт → токены (через callback)
            - Real-time STT: аудио → фрагменты текста
            - TTS: текст → аудио фрагменты
        -------------------------------------------------------
        :param callback: Функция для каждого фрагмента результата
        :param data: Входные данные (опционально)
        :return: None
        """
        start_time = perf_counter()
        _ = self, data, args, kwargs  # игнорировать variable unused
        if not self._running or self._streaming_running:
            return

        self._streaming_running = True
        self._stop_streaming.clear()
        task = asyncio.create_task(self._on_stream(data, callback, *args, **kwargs))

        request_id = str(uuid.uuid4())[:8]
        try:
            slots.slot8(name=self._settings.name, request_id=request_id)
            while not self._stop_streaming.is_set():
                if task.done():
                    exc = task.exception()
                    if exc:  # если в стриме происходит неучтенная ошибка, то пробросить её вверх (она критическая)
                        raise exc
                    break
                await asyncio.sleep(0.1)
            end_time = round(perf_counter() - start_time, 2)
            slots.slot9(name=self._settings.name, request_id=request_id, end_time=end_time)
        except Exception as err:
            slots.slot7(name=self._settings.name, request_id=request_id, err=err)
            raise
        finally:
            if task.done():
                task.cancel()
            self._streaming_running = False
            self._stop_streaming.clear()

    async def _on_stream(self, data, callback, *args, **kwargs) -> None:
        _ = self, data, args, kwargs  # игнорировать variable unused
        # временная заглушка, имитирующая полезную нагрузку
        i = 0
        while True:
            i += 1
            await callback(f'stream chunk:{i} #stub')
            await asyncio.sleep(0.2)

    def stop_stream(self) -> None:
        """Явная остановка стриминга (например через http)"""
        self._stop_streaming.set()


if __name__ == '__main__':
    # пример расширения класса и применения модели в наследниках
    class SettingsExtend(BaseSettings):
        samplerate: int = 16000


    async def main():
        from svc_platform.factories import settings_manager_factory, engine_factory
        from svc_platform.slots import slots_init

        slots_init(callback=None, enable=False)
        current_settings, _ = settings_manager_factory(settings_model=SettingsExtend())
        engine = engine_factory(engine_class=Engine, settings=current_settings)
        engine.start()
        task1 = asyncio.create_task(
            engine.execute(data=EngineIOSchemas.execute_input_data(text='123'), request_id='#000'))
        await asyncio.sleep(0.4)
        engine.stop_execute(request_id='#000')
        await task1


    asyncio.run(main())
