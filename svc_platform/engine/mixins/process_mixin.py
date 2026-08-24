import asyncio
from time import perf_counter
from typing import Generic
from svc_platform.slots_manager import slots
from svc_platform.engine.exc import EngineExc
from svc_platform.schemas import EngineIOSchemas
from svc_platform.engine.functions import stop_all_async_tasks
from svc_platform.engine.types import ProcessTask
from svc_platform.schemas import engine_types as e_types


class ProcessMixin(
    Generic[
        e_types.ProcessInputDataType,
        e_types.ProcessOutputDataType,
    ]
):
    def __init__(self, settings: e_types.SettingsType):
        self._settings = settings
        self._process_tasks_registry: dict[str, ProcessTask] = {}
        self._process_semaphore = asyncio.Semaphore(self._settings.process_limit)
        self._process_stop_all = False  # во внешнем движке нужно установить эту переменную в false в методе start

    @property
    def process_result_storage_size(self):
        return len(self._process_tasks_registry.keys())

    async def process(self, data: e_types.ProcessInputDataType, request_id: str, *args, **kwargs) -> None:
        """
        (Не переопределять этот метод, бизнес логику реализовывать в _on_process)
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
        (Не переопределять этот метод, бизнес логику реализовывать в _on_process)
        """
        _ = self, args, kwargs  # игнорировать variable unused

        async with self._process_semaphore:  # защита от конфликта корутин (превышения лимита)

            if self._process_stop_all:
                return

            if request_id in self._process_tasks_registry:
                raise EngineExc.ProcessRequestIdAlreadyExists(f'Задача с `{request_id}` уже выполняется.')

            start_time = perf_counter()
            slots.slot16(name=self._settings.name, request_id=request_id)
            try:
                # создание и запуск задачи
                event = asyncio.Event()
                self._process_tasks_registry[request_id] = ProcessTask(
                    event=event,
                    task=asyncio.create_task(
                        self._on_process(
                            data=data,
                            event=event,
                            request_id=request_id,
                        )
                    )
                )
                result = await self._process_tasks_registry[request_id].task
                self._process_tasks_registry[request_id].completed_at = perf_counter()
                end_time = round(perf_counter() - start_time, 2)
                # вилка, задача завершена или задача была отменена?
                if result is not None:
                    self._process_tasks_registry[request_id].result = result
                    slots.slot17(name=self._settings.name, request_id=request_id, end_time=end_time)
                else:
                    slots.slot29(name=self._settings.name, request_id=request_id, end_time=end_time)
            except asyncio.CancelledError:
                end_time = round(perf_counter() - start_time, 2)
                slots.slot20(name=self._settings.name, request_id=request_id, end_time=end_time)
                self._process_tasks_registry.pop(request_id, None)
            except Exception as err:
                slots.slot5(name=self._settings.name, request_id=request_id, err=err)
                self._process_tasks_registry.pop(request_id, None)
                raise
            finally:
                if self._process_tasks_registry.get(request_id) is not None:
                    self._process_tasks_registry[request_id].event.set()

    async def _on_process(
            self, data: e_types.ProcessInputDataType, event: asyncio.Event, request_id: str, *args, **kwargs
    ) -> bytes | None:
        """
        (Заглушка! В наследниках полностью переопределить метод, (без super) )
        Реализация логики process
        ------------------------------------------------------------------------------
        ⚠ Требования к реализации:
            ✔ Метод должен завершаться при сигнале event ( проверка is_set() )
            ✔ Event должен находиться в контексте цикла событий текущего метода
            ✔ Метод использовать для сложных вычислений, не возращающих результат мгновенно
            ✔ Метод должен возвращать результат (полезная нагрузка) если не было сигнала event
            ✔ Результат должен быть байтовым представлением экземпляра схемы ProcessOutputData
            ✔ Метод должен возвращать None если event сигнал произошел ( выход по is_set() )
            ✔ Переопределяется в наследниках без super (чтобы убрать заглушку)
        ------------------------------------------------------------------------------

        :param data: Входные данные (схема ProcessInputDataType)
        :param process: event для прерывания выполнения извне (stop_process - бизнес логика должна отслеживать сигнал is_set())
        :return: Результат вычислений (ProcessOutputDataType) или None при прерывании

        Описание примера заглушки:
        Принимает входные данные, имитирует длительную обработку (time_step * iterations) с возможностью прерывания,
        возвращает те же входные данные что и получил
        (Заглушка! В наследниках полностью переопределить метод, (без super) )
        """
        _ = self, args, kwargs, data, request_id
        # функция заглушка с демонстрацией работы _on_process
        iterations = 10
        time_step = 0.2
        # print(f'process {request_id} stub: sleep {time_step * iterations} sec')
        for i in range(iterations):
            # во всех наследниках класса переопределяющих этот метод, ключевое прерывание по event
            if event.is_set():
                return None
            await asyncio.sleep(time_step)
        result = EngineIOSchemas.process_output_data(result=data).model_dump_json()
        result_bytes = result.encode('utf-8')  # результат в байтах

        return result_bytes

    def stop_process(self, request_id: str):
        """
        (Не переопределять этот метод, бизнес логику реализовывать в _on_process)
        Остановка запущенного процесса вычислений (batch режима) по request_id, если такая задача была запущена
        :param request_id: id процесса
        :return: None
        (Не переопределять этот метод, бизнес логику реализовывать в _on_process)
        """
        if request_id not in self._process_tasks_registry:
            raise EngineExc.ProcessNoFindReqestId(f'Не запущен process для request_id: {request_id}')

        # мягкая остановка задачи через испускание сигнала
        self._process_tasks_registry[request_id].event.set()

        # жесткая остановка задачи, если она не была завершена
        task = self._process_tasks_registry[request_id].task
        if not task.done():
            task.cancel()

    def get_process_result(self, request_id) -> e_types.ProcessOutputDataType:
        """
        (Не переопределять этот метод, бизнес логику реализовывать в _on_process)
        Получение результата вычисления процесса по request_id, если не готово или отменено, возбуждаются исключения
        :param request_id: id процесса
        :return: результат вычисления процесса если готов
        (Не переопределять этот метод, бизнес логику реализовывать в _on_process)
        """
        if request_id not in self._process_tasks_registry:
            raise EngineExc.ProcessNoFindReqestId(f'Не запущен процесс для request_id: {request_id}')

        if self._process_tasks_registry[request_id].result is None:
            raise EngineExc.ProcessResultNotCompleted('результат ещё не готов')

        result = self._process_tasks_registry[request_id].result
        self._process_tasks_registry.pop(request_id)  # задача потреблена, удалить её
        slots.slot26(name=self._settings.name, request_id=request_id)
        return result

    async def _process_stop_all_tasks(self):
        """
        (Не переопределять этот метод, бизнес логику реализовывать в _on_process)
        Досрочная остановка всех текущих процессов, например при закрытии экземпляра приложения
        :return:None
        (Не переопределять этот метод, бизнес логику реализовывать в _on_process)
        """
        self._process_stop_all = True
        await stop_all_async_tasks(
            tasks_registry=self._process_tasks_registry,
            timeout=self._settings.process_cancel_all_timeout,
        )

    async def _cleanup_old_processes_loop(self):
        """
        (Не переопределять этот метод, бизнес логику реализовывать в _on_execute)
        Удаление старых процессов (процессы результат по которым готов, но они лежат уже долго дольше ttl)
        Запускать через asyncio.create_task(...) <-> чтобы цикл был самоостановлен по завершении
        :return: None
        (Не переопределять этот метод, бизнес логику реализовывать в _on_execute)
        """
        while True:
            await asyncio.sleep(self._settings.process_cleanup_interval)

            # если экземпляр уничтожен (дополнительная гарантия выхода, чтобы цикл не завис в памяти)
            if not hasattr(self, '_process_tasks_registry'):
                break

            # если registry пуст
            if not self._process_tasks_registry:
                continue

            now = perf_counter()
            expired_ids = []
            for req_id, data in self._process_tasks_registry.items():
                if data.completed_at is not None:
                    if (now - data.completed_at) > self._settings.process_cleanup_result_ttl:
                        expired_ids.append(req_id)

            # удаление устаревших задач
            for req_id in expired_ids:
                slots.slot22(self._settings.name, request_id=req_id)
                self._process_tasks_registry.pop(req_id, None)


# пример использования
async def main():
    from svc_platform.schemas import Settings
    from svc_platform.slots_manager import slots_init, handler_print_message_factory
    slots_init(handlers_list=[handler_print_message_factory()], enable=False)
    request_id = '#001'
    mixin = ProcessMixin(settings=Settings())
    await mixin.process(data=EngineIOSchemas.process_input_data(), request_id=request_id)
    print(mixin.get_process_result(request_id=request_id))


if __name__ == '__main__':
    asyncio.run(main())
