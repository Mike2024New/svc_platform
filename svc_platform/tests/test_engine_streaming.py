import asyncio
from svc_platform.tests.conftest import EngineTestSuite


class EngineTestStreaming(EngineTestSuite):
    async def test_streaming(self, test_engine, eingine_io_schemas):
        """Проверка что стриминг вызывается и не падает, а также останавливается по команде stop"""
        _ = self
        await test_engine.start()

        async def callback(chunk: eingine_io_schemas.streaming_output_data):
            print(chunk)

        task = asyncio.create_task(
            test_engine.stream(
                data=eingine_io_schemas.streaming_input_data,
                callback=callback,
                request_id=eingine_io_schemas.request_id,
            )
        )
        await asyncio.sleep(2)
        test_engine.stop_stream(request_id=eingine_io_schemas.request_id)
        await task
