import asyncio
import pytest
from svc_platform.engine import EngineExc
from svc_platform.tests.conftest import EngineTestSuite

"""
Тесты для проверки цепочки process движка, взаимодействие между методами:
process             - запуск вычислительного процесса (запускает on_process с переопределенной логикой)
on_process          - скрытая логика вычислительного процесса (например stt распознает аудио в текст) 
stop_process        - прерывание процесса
get_process_result  - получение результата процесса по готовности, если не готов то ProcessResultNotCompleted, если отменен то ProcessCancelled
"""


class EngineTestProcess(EngineTestSuite):
    async def test_process_get_result(self, test_engine, eingine_io_schemas):
        """Проверка что get_result_process возвращает ожидаемый результат"""
        _ = self
        await test_engine.start()

        request_id = '#000'
        data = eingine_io_schemas.process_input_data
        # запуск задачи вычисления результата
        task = asyncio.create_task(
            test_engine.process(
                data=data,
                request_id=request_id
            )
        )
        await task
        result = test_engine.get_process_result(request_id=request_id)
        assert result.result == data

    async def test_process_result_not_completed(self, test_engine, eingine_io_schemas):
        """Проверка что срабатывает исключение ProcessResultNotCompleted при преждевременном запрашивании результата"""
        _ = self
        await test_engine.start()

        request_id = '#000'
        data = eingine_io_schemas.process_input_data
        # запуск задачи вычисления результата
        task = asyncio.create_task(
            test_engine.process(
                data=data, request_id=request_id
            )
        )
        # попытка взять результат раньше готовности
        await asyncio.sleep(0.1)
        with pytest.raises(EngineExc.ProcessResultNotCompleted):
            test_engine.get_process_result(request_id=request_id)
        await task
        result = test_engine.get_process_result(request_id=request_id)
        assert result.result == data

    # проверить тест прерывания
    async def test_process_interrupted(self, test_engine, eingine_io_schemas):
        """Проверка что прерывание отрабатывает корректно, и выбрасывается исключение ProcessCancelled"""
        _ = self
        await test_engine.start()
        # запуск задачи вычисления результата
        task = asyncio.create_task(
            test_engine.process(
                data=eingine_io_schemas.process_input_data,
                request_id=eingine_io_schemas.request_id
            )
        )
        # прерывание вычисления
        await asyncio.sleep(0.1)
        test_engine.stop_process(request_id=eingine_io_schemas.request_id)
        await asyncio.sleep(0.1)
        # при повторной попытке взять результат requests уже должен затереться
        with pytest.raises(EngineExc.ProcessResultNoFindReqestId):
            test_engine.get_process_result(request_id=eingine_io_schemas.request_id)
        await task

    async def test_process_unknow_request_id(self, test_engine, eingine_io_schemas):
        """Неизвестный id подан в get_process_result"""
        _ = self
        await test_engine.start()

        # запуск задачи вычисления результата
        task = asyncio.create_task(
            test_engine.process(
                data=eingine_io_schemas.process_input_data,
                request_id=eingine_io_schemas.request_id
            )
        )
        await asyncio.sleep(0.1)
        # при неизвестном request_id должно выстрелить исключение
        with pytest.raises(EngineExc.ProcessResultNoFindReqestId):
            test_engine.get_process_result(request_id='000')

        await task
