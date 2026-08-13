import asyncio
import pytest
from svc_platform.engine import EngineExc
from svc_platform.tests.conftest import EngineTestSuite


class EngineTestProcess(EngineTestSuite):
    async def test_process(self, test_engine_factory, eingine_io_schemas):
        """Проверка запуска process, что он появляется в реестре, и удаляется из него после потребления результата"""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        request_id = '#001'
        task = asyncio.create_task(
            engine.process(
                data=eingine_io_schemas.process_input_data,
                request_id=request_id
            )
        )
        await task  # ожидание завершения задачи
        engine.get_process_result(request_id=request_id)  # потребление результата
        # проверка что процесс был удален из реестра
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._process_tasks_registry, target_state=False,
        ), 'реестр задач не был очищен'

    async def test_process_double_request_id(self, test_engine_factory, eingine_io_schemas, settings):
        """Проверка запуска дублирования request_id - попытка запустить две команды с одинаковым id"""
        _ = self
        settings.execute_limit = 2  # разрешить запуск 2 задач одновременно
        engine = test_engine_factory(settings_override=settings)
        await engine.start()
        tasks = []
        for _ in range(2):
            task = asyncio.create_task(
                engine.process(
                    data=eingine_io_schemas.process_input_data,
                    request_id='#001',  # одинаковый id
                )
            )
            tasks.append(task)

        # должно отработать исключение ProcessRequestIdAlreadyExists
        with pytest.raises(EngineExc.ProcessRequestIdAlreadyExists):
            await asyncio.gather(*tasks)

    async def test_process_stop(self, test_engine_factory, eingine_io_schemas):
        """Проверка что execute stop работает"""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        request_id = '#001'
        # запуск задачи
        asyncio.create_task(
            engine.process(
                data=eingine_io_schemas.process_input_data,
                request_id=request_id
            )
        )
        # ожидание запуска задачи
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._process_tasks_registry, target_state=True,
        ), 'задача не была запущена в timeout'
        # остановка process
        engine.stop_process(request_id=request_id)
        # ожидание отмены задачи
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._process_tasks_registry, target_state=False,
        ), 'задача не была остановлена в timeout'

    async def test_process_stop_no_request_id(self, test_engine_factory, eingine_io_schemas):
        """Попытка остановить process по неправильному id, должно выброситься исключение processNoFindReqestId"""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        request_id = '#001'
        asyncio.create_task(
            engine.process(
                data=eingine_io_schemas.process_input_data,
                request_id=request_id
            )
        )
        # ожидание запуска задачи
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._process_tasks_registry, target_state=True,
        ), 'задача не была запущена в timeout'
        # остановка process
        with pytest.raises(EngineExc.ProcessNoFindReqestId):
            engine.stop_process(request_id='#002')

    async def test_process_get_result_by_id(self, test_engine_factory, eingine_io_schemas):
        """Получение результата по process id, проверка что результат соответствует схеме process_output_data"""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        request_id = '#001'
        task = asyncio.create_task(
            engine.process(
                data=eingine_io_schemas.process_input_data,
                request_id=request_id
            )
        )
        await task
        # получение и проверка результата
        result = engine.get_process_result(request_id=request_id)
        assert result is not None
        try:
            eingine_io_schemas.process_output_data.model_validate(result)
        except Exception:
            raise

    async def test_process_get_result_no_completed(self, test_engine_factory, eingine_io_schemas):
        """Попытка получить результат раньше времени (не дождавшись выполнения корутины) ProcessResultNotCompleted"""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        request_id = '#001'
        asyncio.create_task(
            engine.process(
                data=eingine_io_schemas.process_input_data,
                request_id=request_id
            )
        )
        # ожидание запуска задачи
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._process_tasks_registry, target_state=True,
        ), 'задача не была запущена в timeout'
        # не дожидаясь завершения задачи, мгновенно запросить результат
        with pytest.raises(EngineExc.ProcessResultNotCompleted):
            engine.get_process_result(request_id=request_id)

    async def test_process_cleanup(self, test_engine_factory, eingine_io_schemas, settings):
        """Удаление устаревших ответов процессов"""
        _ = self
        settings.process_cleanup_enable = True  # включить функцию удаления устаревших задач
        settings.process_cleanup_result_ttl = 0.1  # время опроса проверки устаревших задач
        engine = test_engine_factory()
        await engine.start()
        request_id = '#001'
        # запустить задачу
        task = asyncio.create_task(
            engine.process(
                data=eingine_io_schemas.process_input_data,
                request_id=request_id
            )
        )
        await task
        # после вычисления ожидать n времени (чтобы задача была признана устаревшей)
        await asyncio.sleep(settings.process_cleanup_result_ttl)
        # проверка что объект процесса с результатом был удален
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._process_tasks_registry, target_state=False,
        ), 'устаревший результат не был удален'

    async def test_process_limit(self, test_engine_factory, eingine_io_schemas, settings):
        """Лимиты на одновременный запуск процессов, проверить что в один момент времени выполняется limit процессов"""
        _ = self
        tasks_count = 3
        settings.process_limit = 2  # Установка лимита на выполнение задач
        engine = test_engine_factory(settings_override=settings)
        await engine.start()
        tasks = []
        for i in range(tasks_count):  # запуск большего количества задач
            task = asyncio.create_task(
                engine.process(
                    data=eingine_io_schemas.process_input_data,
                    request_id=f'#00{i}',  # одинаковый id
                )
            )

            tasks.append(task)

        # ожидание запуска задач
        for i in range(settings.process_limit):
            assert await self.wait_for_task_state(
                request_id=f'#00{i}', registry=engine._process_tasks_registry, target_state=True,
            ), 'задача не была запущена в timeout'

        # проверка что количество запущенных в один момент времени задач не больше чем limit
        assert settings.process_limit == len(engine._process_tasks_registry), 'Запущенных задач больше лимита'
        # дождаться завершения задачи
        await asyncio.gather(*tasks)
        # проверка что все задачи выполнились (и те которые выходили за лимит одновременного запуска)
        assert len([True for task in tasks if task.done()]) == len(tasks), 'Не все задачи выполнились'

    async def test_process_stop_all_tasks(self, test_engine_factory, eingine_io_schemas, settings):
        """Проверка что все процессы отменяются по process_stop_all,
        включая те которые не попали в семафор на момент остановки всех процессов"""
        _ = self
        tasks_count = 3
        settings.process_limit = 2  # Установка лимита на выполнение процессов
        engine = test_engine_factory(settings_override=settings)
        await engine.start()
        tasks = []
        for i in range(tasks_count):  # запуск большего количества процессов
            task = asyncio.create_task(
                engine.process(
                    data=eingine_io_schemas.process_input_data,
                    request_id=f'#00{i}',  # одинаковый id
                )
            )

            tasks.append(task)
        # ожидание запуска задач
        for i in range(settings.process_limit):
            assert await self.wait_for_task_state(
                request_id=f'#00{i}', registry=engine._process_tasks_registry, target_state=True,
            ), 'задача не была запущена в timeout'
        await engine.stop()
        assert engine._process_tasks_registry == {}, 'задачи не были удалены из реестра'
        assert engine._process_stop_all is True, 'Флаг остановки всех задач не был установлен'

