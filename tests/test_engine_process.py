import asyncio

import pytest
from svc_platform.engine import EngineExc

"""
Тесты для проверки цепочки process движка, взаимодействие между методами:
process             - запуск вычислительного процесса (запускает on_process с переопределенной логикой)
on_process          - скрытая логика вычислительного процесса (например stt распознает аудио в текст) 
stop_process        - прерывание процесса
get_process_result  - получение результата процесса по готовности, если не готов то ProcessResultNotCompleted, если отменен то ProcessCancelled
"""


async def test_process_get_result(test_engine):
    """Проверка что get_result_process возвращает ожидаемый результат"""
    engine = test_engine
    engine.start()

    request_id = '#000'
    on_process_result = 'stub'
    # установка тестовых параметров по умолчанию
    # запуск задачи вычисления результата
    task = asyncio.create_task(engine.process(data=1, request_id=request_id))
    await task
    result = engine.get_process_result(request_id=request_id)
    assert result == on_process_result


async def test_process_result_not_completed(test_engine):
    """Проверка что срабатывает исключение ProcessResultNotCompleted при преждевременном запрашивании результата"""
    engine = test_engine
    engine.start()

    request_id = '#000'
    on_process_result = 'stub'
    # запуск задачи вычисления результата
    task = asyncio.create_task(engine.process(data=1, request_id=request_id))
    # попытка взять результат раньше готовности
    await asyncio.sleep(0.1)
    with pytest.raises(EngineExc.ProcessResultNotCompleted):
        engine.get_process_result(request_id=request_id)
    await task
    result = engine.get_process_result(request_id=request_id)
    assert result == on_process_result


# проверить тест прерывания
# async def test_process_interrupted(test_engine):
#     """Проверка что прерывание отрабатывает корректно, и выбрасывается исключение ProcessCancelled"""
#     engine = test_engine
#     engine.start()
#
#     request_id = '#000'
#     # запуск задачи вычисления результата
#     task = asyncio.create_task(engine.process(data=1, request_id=request_id))
#     # прерывание вычисления
#     await asyncio.sleep(0.1)
#     engine.stop_process(request_id=request_id)
#
#     await asyncio.sleep(0.1)
#     # при попытке взять результат должно быть возбуждено исключение Cancelled
#     with pytest.raises(EngineExc.ProcessCancelled):
#         engine.get_process_result(request_id=request_id)
#     # при повторной попытке взять результат requests уже должен затереться
#     with pytest.raises(EngineExc.ProcessResultNoFindReqestId):
#         engine.get_process_result(request_id=request_id)
#     await task


async def test_process_unknow_request_id(test_engine):
    """Неизвестный id подан в get_process_result"""
    engine = test_engine
    engine.start()

    request_id = '#000'
    # запуск задачи вычисления результата
    task = asyncio.create_task(engine.process(data=1, request_id=request_id))
    await asyncio.sleep(0.1)
    # при неизвестном request_id должно выстрелить исключение
    with pytest.raises(EngineExc.ProcessResultNoFindReqestId):
        engine.get_process_result(request_id='000')

    await task
