# import asyncio
#
#
# async def test_streaming(test_engine):
#     """Проверка что стриминг вызывается и не падает, а также останавливается по команде stop"""
#     engine = test_engine
#     engine.start()
#
#     async def callback(x):
#         _ = x
#
#     task = asyncio.create_task(engine.stream(data=1, callback=callback))
#     await asyncio.sleep(2)
#     engine.stop_stream()
#     await task
