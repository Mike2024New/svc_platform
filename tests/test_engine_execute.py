import asyncio


async def test_execute(test_engine):
    """Проверка что execute запускается и отрабатывает корректно и без ошибок"""
    engine, *_ = test_engine
    engine.start()

    # проверка что execute процесс запускается
    task = asyncio.create_task(engine.execute(data=1))
    await task


async def test_execute_interrupted(test_engine):
    engine, *_ = test_engine
    engine.start()
    task = asyncio.create_task(engine.execute(data=1))
    await asyncio.sleep(0.1)
    engine.stop_execute()
    await task
