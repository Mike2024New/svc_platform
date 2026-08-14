import asyncio
import pytest
from svc_platform.engine import EngineExc
from svc_platform.tests.conftest import EngineTestSuite
from dataclasses import dataclass, field


@dataclass
class TaskParameters:
    """Модель для запускаемых process"""
    tasks_list: list[asyncio.Task] = field(default_factory=list)
    requests_id_list: list[str] = field(default_factory=list)


class EngineTestProcess(EngineTestSuite):

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
                engine.process(
                    data=engine_io_schemas.process_input_data,
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
                    registry=engine._process_tasks_registry,  # noqa
                    target_state=True,
                ), 'процессы запущены не были'

        return parameters

    async def test_process(self, test_engine_factory, engine_io_schemas):
        """Проверка, что process появляется в реестре и удаляется после потребления результата."""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        process_parameters = await self.__run_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=1,
        )
        task = process_parameters.tasks_list[0]
        request_id = process_parameters.requests_id_list[0]
        await task  # ожидание завершения задачи
        engine.get_process_result(request_id=request_id)  # потребление результата
        # проверка что процесс был удален из реестра
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._process_tasks_registry, target_state=False,
        ), 'реестр задач не был очищен'

    async def test_process_double_request_id(self, test_engine_factory, engine_io_schemas, settings):
        """Проверка, что запуск двух process с одинаковым request_id вызывает исключение ProcessRequestIdAlreadyExists."""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        process_parameters = await self.__run_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=2,  # запуск двух задач
            request_id_map=['#001', '#001'],  # одинаковые request_id
        )
        # должно отработать исключение ProcessRequestIdAlreadyExists
        with pytest.raises(EngineExc.ProcessRequestIdAlreadyExists):
            await asyncio.gather(*process_parameters.tasks_list)
        # задача при этом должна остаться в реестре
        assert '#001' in engine._process_tasks_registry, 'Первая задача была удалена'

    async def test_process_stop(self, test_engine_factory, engine_io_schemas):
        """
        Проверка, что process останавливается по request_id и удаляется из реестра.
        """
        _ = self
        engine = test_engine_factory()
        await engine.start()
        process_parameters = await self.__run_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=1,
            wait_for_tasks_runned=True,
        )
        tasks = process_parameters.tasks_list
        request_id = process_parameters.requests_id_list[0]
        # остановка process
        engine.stop_process(request_id=request_id)
        # ожидание отмены задачи
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._process_tasks_registry, target_state=False,
        ), 'задача не была остановлена в timeout'
        # оставшаяся задача сверху должна выполниться
        await asyncio.gather(*tasks)

    async def test_process_stop_no_request_id(self, test_engine_factory, engine_io_schemas):
        """Проверка, что остановка process по несуществующему request_id вызывает исключение ProcessNoFindReqestId."""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        await self.__run_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=1,
            wait_for_tasks_runned=True,
        )
        # остановка process
        with pytest.raises(EngineExc.ProcessNoFindReqestId):
            engine.stop_process(request_id='_unkonw_id_test_')

    #
    async def test_process_get_result_by_id(self, test_engine_factory, engine_io_schemas):
        """Проверка, что результат process соответствует схеме process_output_data."""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        process_parameters = await self.__run_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=1,
            wait_for_tasks_runned=True,
        )
        task = process_parameters.tasks_list[0]
        request_id = process_parameters.requests_id_list[0]
        await task
        # получение и проверка результата
        result = engine.get_process_result(request_id=request_id)
        assert result is not None
        try:
            # сперва нужно результат распаковать в словарь, за тем уже валидировать через модель
            engine_io_schemas.process_output_data.model_validate(result.model_dump())
        except Exception:
            raise ValueError(
                f'process, метод _on_process возвращает результат не согласованный со схемой {engine_io_schemas.process_output_data.__class__.__name__}'
            )

    async def test_process_get_result_no_completed(self, test_engine_factory, engine_io_schemas):
        """Проверка, что запрос результата process до завершения вызывает исключение ProcessResultNotCompleted."""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        process_parameters = await self.__run_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=1,
            wait_for_tasks_runned=True,
        )
        request_id = process_parameters.requests_id_list[0]
        # не дожидаясь завершения задачи, мгновенно запросить результат
        with pytest.raises(EngineExc.ProcessResultNotCompleted):
            engine.get_process_result(request_id=request_id)

    async def test_process_cleanup(self, test_engine_factory, engine_io_schemas, settings):
        """Проверка, что устаревший результат process удаляется по истечении TTL."""
        _ = self
        settings.process_cleanup_enable = True
        settings.process_cleanup_result_ttl = 0.2
        engine = test_engine_factory()
        await engine.start()
        process_parameters = await self.__run_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=1,
            wait_for_tasks_runned=True,
        )
        request_id = process_parameters.requests_id_list[0]
        task = process_parameters.tasks_list[0]
        await task
        # после вычисления ожидать n времени (чтобы задача была признана устаревшей)
        await asyncio.sleep(settings.process_cleanup_result_ttl)
        # проверка что объект процесса с результатом был удален
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._process_tasks_registry, target_state=False,
        ), 'устаревший результат не был удален'

    async def test_process_limit(self, test_engine_factory, engine_io_schemas, settings):
        """Проверка, что process не запускает в одном семафоре, больше задач, чем установлено в process_limit."""
        _ = self
        tasks_count = 2  # всего 2 задачи
        settings.process_limit = 1  # ограничение семафора в 1 задачу
        engine = test_engine_factory()
        await engine.start()
        process_parameters = await self.__run_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=tasks_count,
            wait_for_tasks_runned=False,
        )

        first_task_request_id = process_parameters.requests_id_list[0]
        first_task = process_parameters.tasks_list[0]
        second_task_request_id = process_parameters.requests_id_list[1]
        # ожидание завершения 1 задачи
        await first_task
        # проверка что первая задача готова (есть результат)
        assert engine._process_tasks_registry[first_task_request_id].event.is_set(), 'задача не была завершена'
        # вторая задача должна быть ещё unset
        assert not engine._process_tasks_registry[
            second_task_request_id].event.is_set(), 'вторая задача посчиталась раньше времени'

    async def test_process_stop_all_tasks(self, test_engine_factory, engine_io_schemas, settings):
        """Проверка, что process_stop_all останавливает все задачи и устанавливает флаг остановки."""
        _ = self
        settings.process_limit = 3  # 3 задачи одновременно
        engine = test_engine_factory()
        await engine.start()
        await self.__run_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=3,
            wait_for_tasks_runned=True,
        )
        await engine.stop()
        assert engine._process_tasks_registry == {}, 'задачи не были удалены из реестра'
        assert engine._process_stop_all is True, 'Флаг остановки всех задач не был установлен'
