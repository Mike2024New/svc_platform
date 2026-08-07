import asyncio
from svc_platform.tests.conftest import EngineTestSuite


class EngineTestStreaming(EngineTestSuite):
    async def test_streaming(self, test_engine):
        """Проверка что стриминг вызывается и не падает, а также останавливается по команде stop"""
        _ = self
        engine, parameters = test_engine
        engine.start()

        async def callback(x):
            _ = x

        task = asyncio.create_task(engine.stream(data=parameters.streaming_input_data, callback=callback))
        await asyncio.sleep(2)
        engine.stop_stream()
        await task
