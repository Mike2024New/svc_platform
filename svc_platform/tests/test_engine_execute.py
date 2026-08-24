import asyncio, pytest
from svc_platform.tests.conftest import EngineTestSuite
from svc_platform.engine import EngineExc
from dataclasses import dataclass, field


@dataclass
class TaskParameters:
    """Модель для запускаемых execute"""
    tasks_list: list[asyncio.Task] = field(default_factory=list)
    requests_id_list: list[str] = field(default_factory=list)


class EngineTestExecute(EngineTestSuite):

    async def __run_tasks(
            self, engine, engine_io_schemas, request_id_map: list[str] = None, count: int = 1,
            wait_for_tasks_runned: bool = True,
    ) -> TaskParameters:
        """
        Запускает процесс, и возвращает объект с списком задач, request_id, и очередями.
        """
        parameters = TaskParameters()

        for i in range(count):
            request_id = request_id_map[i] if request_id_map is not None else f'#00{i}'
            task = asyncio.create_task(
                engine.execute(
                    data=engine_io_schemas.execute_input_data,
                    request_id=request_id,
                )
            )
            parameters.tasks_list.append(task)
            parameters.requests_id_list.append(request_id)

        if wait_for_tasks_runned:
            # ожидание что процессы были запущены
            for i in range(len(parameters.tasks_list)):
                assert await self.wait_for_task_state(
                    request_id=parameters.requests_id_list[i],
                    registry=engine._execute_tasks_registry,  # noqa
                    target_state=True,
                ), 'процессы запущены не были'

        return parameters

    async def test_execute(self, test_engine_factory, engine_io_schemas):
        """Проверка, что execute появляется в реестре и удаляется после завершения."""
        _ = self
        engine = test_engine_factory()
        await engine.start(engine_io_schemas.engine_parameters)
        # запуск задачи
        execute_parameters = await self.__run_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=1,
        )
        task = execute_parameters.tasks_list[0]
        request_id = execute_parameters.requests_id_list[0]

        await task  # ожидание завершения задачи
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._execute_tasks_registry, target_state=False,
        ), 'реестр задач не был очищен'

    async def test_execute_double_request_id(self, test_engine_factory, engine_io_schemas, settings):
        """Проверка, что запуск двух execute с одинаковым request_id вызывает исключение ExecuteRequestIdAlreadyExists."""
        _ = self
        if settings.execute_limit <= 1:
            return  # нет смысла в тесте, так как одновременно разрешено не более одного процесса

        settings.execute_limit = 2  # запуск двух задач параллельно
        engine = test_engine_factory(settings_override=settings)
        await engine.start(engine_io_schemas.engine_parameters)
        # запуск задачи
        execute_parameters = await self.__run_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=2,  # две задачи одновременно
            request_id_map=['#001', '#001'],  # два одинаковых id
            wait_for_tasks_runned=True,
        )

        # должно отработать исключение ExecuteRequestIdAlreadyExists
        with pytest.raises(EngineExc.ExecuteRequestIdAlreadyExists):
            await asyncio.gather(*execute_parameters.tasks_list)

    async def test_execute_stop(self, test_engine_factory, engine_io_schemas):
        """Проверка, что execute останавливается по request_id и удаляется из реестра."""
        _ = self
        engine = test_engine_factory()
        await engine.start(engine_io_schemas.engine_parameters)
        # запуск задачи
        execute_parameters = await self.__run_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=1,
        )
        request_id = execute_parameters.requests_id_list[0]
        # остановка execute
        engine.stop_execute(request_id=request_id)
        # ожидание отмены задачи
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._execute_tasks_registry, target_state=False,
        ), 'задача не была остановлена в timeout'

    async def test_execute_stop_no_request_id(self, test_engine_factory, engine_io_schemas):
        """Проверка, что остановка execute по несуществующему request_id вызывает исключение ExecuteNoFindReqestId."""
        _ = self
        engine = test_engine_factory()
        await engine.start(engine_io_schemas.engine_parameters)
        # запуск задачи
        await self.__run_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=1,
        )
        # остановка execute
        with pytest.raises(EngineExc.ExecuteNoFindReqestId):
            engine.stop_execute(request_id='_unknow_id_test_')

    async def test_execute_limit(self, test_engine_factory, engine_io_schemas, settings):
        """Проверка, что execute не запускает больше задач, чем установлено в execute_limit."""
        _ = self
        if settings.execute_limit <= 1:
            return  # нет смысла в тесте, так как одновременно разрешено не более одного процесса
        tasks_count = 2  # всего 2 задачи
        settings.execute_limit = 1  # ограничение семафора в 1 задачу
        engine = test_engine_factory()
        await engine.start(engine_io_schemas.engine_parameters)
        execute_parameters = await self.__run_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=tasks_count,
            wait_for_tasks_runned=False,
        )

        first_task_request_id = execute_parameters.requests_id_list[0]
        first_task = execute_parameters.tasks_list[0]
        second_task_request_id = execute_parameters.requests_id_list[1]
        # ожидание завершения 1 задачи
        await first_task
        # первая задача должна быть удалена из реестра так как выполнена
        assert first_task_request_id not in engine._execute_tasks_registry
        # вторая задача должна быть unset (не выполнена, т.к. она запускается следом за first_task)
        assert not engine._execute_tasks_registry[
            second_task_request_id].event.is_set(), 'вторая задача выполнилась раньше времени'

    async def test_execute_stop_all_tasks(self, test_engine_factory, engine_io_schemas, settings):
        """Проверка, что execute_stop_all останавливает все задачи и устанавливает флаг остановки."""
        _ = self
        engine = test_engine_factory()
        await engine.start(engine_io_schemas.engine_parameters)
        await self.__run_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=settings.execute_limit,
            wait_for_tasks_runned=True,
        )
        await engine.stop()
        assert engine._execute_tasks_registry == {}, 'задачи не были удалены из реестра'
        assert engine._execute_stop_all is True, 'Флаг остановки всех задач не был установлен'
