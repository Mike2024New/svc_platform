import asyncio
from svc_platform.tests.conftest import EngineTestSuite


class EngineTestExecute(EngineTestSuite):
    async def test_execute(self, test_engine):
        """Проверка что execute запускается и отрабатывает корректно и без ошибок"""
        _ = self
        engine = test_engine
        engine.start()

        # проверка что execute процесс запускается
        task = asyncio.create_task(engine.execute(data=1))
        await task
        engine.stop()

    async def test_execute_interrupted(self, test_engine):
        _ = self
        engine = test_engine
        engine.start()
        request_id = '#001'
        task = asyncio.create_task(engine.execute(data=1, request_id=request_id))
        await asyncio.sleep(0.1)
        engine.stop_execute(request_id=request_id)
        await task
        engine.stop()
