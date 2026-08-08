import requests
from svc_platform.tests.conftest import EngineTestSuite
from time import sleep


class ApiTestExecute(EngineTestSuite):
    def test_execute(self, test_server, eingine_io_schemas):
        """Проверка что execute запускается и возвращает request_id"""
        _ = self
        url = test_server
        requests.get(url=url.start, timeout=10)  # запуск engine
        # проверка что execute запущен
        res = requests.post(
            url=url.execute,
            json=eingine_io_schemas.execute_input_data.model_dump()
        )
        assert res.status_code == 200
        data = res.json()
        assert data is not None
        request_id = data.get('request_id', None)
        assert request_id is not None, f'/execute/ не вернул request_id'

    def test_execute_interrupted(self, test_server, eingine_io_schemas):
        """Проверка что execute запускается и возвращает request_id"""
        _ = self
        url = test_server
        requests.get(url=url.start, timeout=10)  # запуск engine
        # проверка что execute запущен
        res = requests.post(
            url=url.execute,
            json=eingine_io_schemas.execute_input_data.model_dump()
        )
        assert res.status_code == 200
        data = res.json()
        request_id = data.get('request_id', None)
        sleep(0.4)
        res = requests.get(url.execute_stop, params={'request_id': request_id})
        assert res.status_code == 200, '/execute/ задача не была отменена'
