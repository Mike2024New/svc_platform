import asyncio, pytest
from svc_platform.tests.conftest import EngineTestSuite
from svc_platform.engine import EngineExc


class EngineTestExecute(EngineTestSuite):
    async def test_execute(self, test_engine_factory, eingine_io_schemas):
        """Проверка запуска execute, что он появляется в реестре, и удаляется из него по завершении"""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        request_id = '#001'
        task = asyncio.create_task(
            engine.execute(
                data=eingine_io_schemas.execute_input_data,
                request_id=request_id
            )
        )
        await task  # ожидание завершения задачи
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._execute_tasks_registry, target_state=False,
        ), 'реестр задач не был очищен'

    async def test_execute_double_request_id(self, test_engine_factory, eingine_io_schemas, settings):
        """Проверка запуска дублирования request_id - попытка запустить две команды с одинаковым id"""
        _ = self
        settings.execute_limit = 2  # разрешить запуск 2 задач одновременно
        engine = test_engine_factory(settings_override=settings)
        await engine.start()
        tasks = []
        for _ in range(2):
            task = asyncio.create_task(
                engine.execute(
                    data=eingine_io_schemas.execute_input_data,
                    request_id='#001',  # одинаковый id
                )
            )
            tasks.append(task)

        # должно отработать исключение ExecuteRequestIdAlreadyExists
        with pytest.raises(EngineExc.ExecuteRequestIdAlreadyExists):
            await asyncio.gather(*tasks)

    async def test_execute_stop(self, test_engine_factory, eingine_io_schemas):
        """Проверка что execute stop работает"""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        request_id = '#001'
        # запуск задачи
        asyncio.create_task(
            engine.execute(
                data=eingine_io_schemas.execute_input_data,
                request_id=request_id
            )
        )
        # ожидание запуска задачи
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._execute_tasks_registry, target_state=True,
        ), 'задача не была запущена в timeout'
        # остановка execute
        engine.stop_execute(request_id=request_id)
        # ожидание отмены задачи
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._execute_tasks_registry, target_state=False,
        ), 'задача не была остановлена в timeout'

    async def test_execute_stop_no_request_id(self, test_engine_factory, eingine_io_schemas):
        """Попытка остановить execute по неправильному id, должно выброситься исключение ExecuteNoFindReqestId"""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        request_id = '#001'
        asyncio.create_task(
            engine.execute(
                data=eingine_io_schemas.execute_input_data,
                request_id=request_id
            )
        )
        # ожидание запуска задачи
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._execute_tasks_registry, target_state=True,
        ), 'задача не была запущена в timeout'
        # остановка execute
        with pytest.raises(EngineExc.ExecuteNoFindReqestId):
            engine.stop_execute(request_id='#002')

    async def test_execute_limit(self, test_engine_factory, eingine_io_schemas, settings):
        """Лимиты на одновременный запуск команд, проверить что в один момент времени выполняется limit команд"""
        _ = self
        tasks_count = 3
        settings.execute_limit = 2  # Установка лимита на выполнение задач
        engine = test_engine_factory(settings_override=settings)
        await engine.start()
        tasks = []
        for i in range(tasks_count):  # запуск большего количества задач
            task = asyncio.create_task(
                engine.execute(
                    data=eingine_io_schemas.execute_input_data,
                    request_id=f'#00{i}',  # одинаковый id
                )
            )

            tasks.append(task)

        # ожидание запуска задач
        for i in range(settings.execute_limit):
            assert await self.wait_for_task_state(
                request_id=f'#00{i}', registry=engine._execute_tasks_registry, target_state=True,
            ), 'задача не была запущена в timeout'

        # проверка что количество запущенных в один момент времени задач не больше чем limit
        assert settings.execute_limit == len(engine._execute_tasks_registry), 'Запущенных задач больше лимита'
        # дождаться завершения задачи
        await asyncio.gather(*tasks)
        # проверка что все задачи выполнились (и те которые выходили за лимит одновременного запуска)
        assert len([True for task in tasks if task.done()]) == len(tasks), 'Не все задачи выполнились'

    #
    async def test_execute_stop_all_tasks(self, test_engine_factory, eingine_io_schemas, settings):
        """Проверка что все задачи отменяются по execute_stop_all,
        включая те которые не попали в семафор на момент остановки всех задач"""
        _ = self
        tasks_count = 3
        settings.execute_limit = 2  # Установка лимита на выполнение задач
        engine = test_engine_factory(settings_override=settings)
        await engine.start()
        tasks = []
        for i in range(tasks_count):  # запуск большего количества задач
            task = asyncio.create_task(
                engine.execute(
                    data=eingine_io_schemas.execute_input_data,
                    request_id=f'#00{i}',  # одинаковый id
                )
            )

            tasks.append(task)
        # ожидание запуска задач
        for i in range(settings.execute_limit):
            assert await self.wait_for_task_state(
                request_id=f'#00{i}', registry=engine._execute_tasks_registry, target_state=True,
            ), 'задача не была запущена в timeout'
        await engine.stop()
        assert engine._execute_tasks_registry == {}, 'задачи не были удалены из реестра'
        assert engine._execute_stop_all is True, 'Флаг остановки всех задач не был установлен'
