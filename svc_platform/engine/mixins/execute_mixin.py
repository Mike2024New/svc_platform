import asyncio
from time import perf_counter
from typing import Generic
from svc_platform.engine.exc import EngineExc
from svc_platform.schemas import SettingsSchemaType, EngineIOSchemas
from svc_platform.engine.functions import stop_all_async_tasks
from svc_platform.engine.types import ExecuteTask
from svc_platform.schemas import engine_types as e_types
from svc_platform.slots_manager import slots


class ExecuteMixin(Generic[e_types.ExecuteInputDataType]):
    def __init__(self, settings: SettingsSchemaType):
        self._settings = settings
        self._execute_tasks_registry: dict[str, ExecuteTask] = {}
        self._execute_semaphore = asyncio.Semaphore(self._settings.execute_limit)
        self._execute_stop_all = False  # во внешнем движке нужно установить эту переменную в false в методе start

    async def execute(self, data: e_types.ExecuteInputDataType, request_id: str, *args, **kwargs) -> None:
        """
        (логику метода определять в _on_execute)
        Исполнительный метод (action режим).
        Команда - исполняемая без ответа.
        ----------------------------------------------------
        Паттерн: Один запрос → Действие без ответа
        Примеры:
            - Audio Output: PCM аудио → воспроизведение
            - Управление устройством: команда → выполнение
            - Сохранение данных: информация → запись
        ----------------------------------------------------
        :param request_id: идентификатор цепочки задач
        :param data: Входные данные (опционально)
        :return: None
        (логику метода определять в _on_execute)
        """
        _ = self, args, kwargs  # игнорировать variable unused

        async with self._execute_semaphore:  # защита от конфликта корутин (превышения лимита)

            if self._execute_stop_all:
                return

            if request_id in self._execute_tasks_registry:
                raise EngineExc.ExecuteRequestIdAlreadyExists(f'Задача с `{request_id}` уже выполняется.')

            start_time = perf_counter()

            try:
                # создание и запуск задачи
                event = asyncio.Event()
                self._execute_tasks_registry[request_id] = ExecuteTask(
                    event=event,
                    task=asyncio.create_task(
                        self._on_execute(
                            event=event,
                            request_id=request_id,
                            data=data,
                        )
                    )
                )
                slots.slot18(name=self._settings.name, request_id=request_id)
                # ожидание завершения
                result = await self._execute_tasks_registry[request_id].task
                end_time = round(perf_counter() - start_time, 2)
                # вилка, задача завершена или задача была отменена?
                if result:
                    slots.slot19(name=self._settings.name, request_id=request_id, end_time=end_time)
                else:
                    slots.slot21(name=self._settings.name, request_id=request_id, end_time=end_time)
            except asyncio.CancelledError:
                end_time = round(perf_counter() - start_time, 2)
                slots.slot27(name=self._settings.name, request_id=request_id, end_time=end_time)
            except Exception as err:
                slots.slot6(name=self._settings.name, request_id=request_id, err=err)
                raise
            finally:
                if self._execute_tasks_registry.get(request_id) is not None:
                    self._execute_tasks_registry[request_id].event.set()
                self._execute_tasks_registry.pop(request_id, None)

    async def _on_execute(
            self, data: e_types.ExecuteInputDataType, event: asyncio.Event, request_id: str, *args,
            **kwargs) -> bool:
        """
        (Заглушка! В наследниках полностью переопределить метод, (без super) )
        Реализация логики execute.

        ------------------------------------------------------------------------------
        ⚠ Требования к реализации:
            ✔ Метод должен завершаться при сигнале event ( проверка is_set() )
            ✔ Метод должен возвращать True если не было сигнала event
            ✔ Метод должен возвращать False если event сигнал произошел ( выход по is_set() )
            ✔ Переопределяется в наследниках без super (чтобы убрать заглушку)
        ------------------------------------------------------------------------------

        :param data: данные полезная нагрузка
        :param event: отслеживаемый объект, если он испустил сигнал, то необходимо срочно остановить метод
        :param request_id: идентификатор цепочки задач
        :return: завершилась ли корутина или была отменена (важно для логирования)

        Описание заглушки:
        Принимает входные данные, имитирует длительную обработку (time_step * iterations) с возможностью прерывания

        (Заглушка! В наследниках полностью переопределить метод, (без super) )
        """
        _ = self, args, kwargs, data
        # функция заглушка с демонстрацией работы _on_execute
        iterations = 10
        time_step = 0.2
        print(f'execute {request_id} stub: sleep {time_step * iterations} sec')
        for i in range(iterations):
            # во всех наследниках класса переопределяющих этот метод, ключевое прерывание по event
            if event.is_set():
                return False
            await asyncio.sleep(time_step)
        return True

    def stop_execute(self, request_id: str):
        """
        Остановка запущенной команды по request_id (если такая команда выполняется)
        :param request_id: идентификатор цепочки задач
        """
        if request_id not in self._execute_tasks_registry:
            raise EngineExc.ExecuteNoFindReqestId(f'Не запущен execute для request_id: {request_id}')

        # мягкая остановка задачи через испускание сигнала
        self._execute_tasks_registry[request_id].event.set()

        # жесткая остановка задачи, если она не была завершена
        task = self._execute_tasks_registry[request_id].task
        if not task.done():
            task.cancel()

    async def execute_stop_all_tasks(self):
        self._execute_stop_all = True
        await stop_all_async_tasks(
            tasks_registry=self._execute_tasks_registry,
            timeout=self._settings.execute_cancel_all_timeout,
        )


# пример использования
async def main():
    from svc_platform.schemas import BaseSettings
    from svc_platform.slots_manager import slots_init
    from svc_platform.slots_manager.handlers import handler_print_message_factory
    from svc_platform.factories import settings_manager_factory

    request_id = '#001'
    request_id2 = '#002'
    settings, settings_manager = settings_manager_factory(settings_model=BaseSettings(execute_limit=1), reset_json=True)
    ex = ExecuteMixin(settings=settings)

    slots_init(enable=True, handlers_list=[handler_print_message_factory()])
    task = asyncio.create_task(ex.execute(request_id=request_id, data=EngineIOSchemas.execute_input_data()))
    task2 = asyncio.create_task(ex.execute(request_id=request_id2, data=EngineIOSchemas.execute_input_data()))
    await asyncio.sleep(0.2)
    await ex.execute_stop_all_tasks()
    # ex.stop_execute(request_id=request_id)
    await task
    await task2
    print(task.done())


if __name__ == '__main__':
    asyncio.run(main())
