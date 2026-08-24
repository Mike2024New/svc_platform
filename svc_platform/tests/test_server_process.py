import requests
from svc_platform.tests.conftest import EngineTestSuite
from infrastructure_http_clients import ServerProbe


class ApiTestProcess(EngineTestSuite):
    def test_process(self, test_server, engine_io_schemas):
        """Проверка цепочки process, отправка запроса, получение ответа, проверка что ответ соответствует модели"""
        _ = self
        url = test_server
        requests.get(url=url.start, timeout=10)  # запуск engine
        # проверка что execute запущен
        res = requests.post(
            url=url.process,
            json=engine_io_schemas.process_input_data.model_dump()
        )
        assert res.status_code == 202
        data = res.json()
        assert data is not None, '/process/ не вернул json'
        request_id = data.get('request_id', None)
        assert request_id is not None, f'/process/ не вернул request_id'
        # дождаться от сервера результат
        result = ServerProbe.polling(
            url=url.process_result,
            params={'request_id': request_id},
            expected_status=200,
            interval=2,
        )
        data = result.json()
        assert data is not None, '/process_result/ не вернул json'
        assert data is not None, '/process_result/ вернул ответ без поля result'
        try:
            engine_io_schemas.process_output_data.model_validate(data)
        except ValueError:
            raise RuntimeError(f'api /process_result/ возвращает не корректную модель ответа')
