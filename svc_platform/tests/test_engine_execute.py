import asyncio
from svc_platform.tests.conftest import EngineTestSuite


class EngineTestExecute(EngineTestSuite):
    async def test_execute(self, test_engine):
        """Проверка что execute запускается и отрабатывает корректно и без ошибок"""
        _ = self
        engine, parameters = test_engine
        await engine.start()
        # проверка что execute процесс запускается
        task = asyncio.create_task(engine.execute(data=parameters.execute_input_data, request_id=parameters.request_id))
        await task
        await engine.stop()

    async def test_execute_interrupted(self, test_engine):
        """Проверка корректности прерывания execute по id"""
        _ = self
        engine, parameters = test_engine
        await engine.start()
        task = asyncio.create_task(engine.execute(data=parameters.execute_input_data, request_id=parameters.request_id))
        await asyncio.sleep(0.1)
        engine.stop_execute(request_id=parameters.request_id)
        await task
        await engine.stop()
