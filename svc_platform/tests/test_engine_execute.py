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

    async def test_execute_interrupted(self, test_engine):
        _ = self
        engine = test_engine
        engine.start()
        task = asyncio.create_task(engine.execute(data=1))
        await asyncio.sleep(0.1)
        engine.stop_execute()
        await task
