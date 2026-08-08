import asyncio
from svc_platform.tests.conftest import EngineTestSuite


class EngineTestExecute(EngineTestSuite):
    async def test_execute(self, test_engine, eingine_io_schemas):
        """Проверка что execute запускается и отрабатывает корректно и без ошибок"""
        _ = self
        await test_engine.start()
        # проверка что execute процесс запускается
        task = asyncio.create_task(
            test_engine.execute(
                data=eingine_io_schemas.execute_input_data,
                request_id=eingine_io_schemas.request_id
            )
        )
        await task
        await test_engine.stop()

    async def test_execute_interrupted(self, test_engine, eingine_io_schemas):
        """Проверка корректности прерывания execute по id"""
        _ = self
        await test_engine.start()
        task = asyncio.create_task(
            test_engine.execute(
                data=eingine_io_schemas.execute_input_data,
                request_id=eingine_io_schemas.request_id
            )
        )
        await asyncio.sleep(0.1)
        test_engine.stop_execute(request_id=eingine_io_schemas.request_id)
        await task
        await test_engine.stop()

    async def test_execute_limit(self, test_engine, eingine_io_schemas, settings):
        pass
