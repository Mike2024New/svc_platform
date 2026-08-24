import requests
from svc_platform.tests.conftest import EngineTestSuite


class ApiTestRun(EngineTestSuite):
    def test_server_start_stop(self, test_server, engine_io_schemas):
        """Проверка что сервер корректно запускает и останавливает Engine через http"""
        _ = self
        url = test_server

        # запуск engine сервера
        try:
            requests.post(url=url.start, timeout=10, json=engine_io_schemas.engine_parameters.model_dump())
        except Exception as err:
            raise RuntimeError(f'Сервер не запускает engine. Причина: {err}')

        # проверка параметров
        res = requests.get(url=url.parameters)
        data = res.json()
        assert data is not None
        running = data.get('parameters', {}).get('running', None)
        assert running is not None, 'parameters не возвращает флаг проверки состояния engine -> running'
        assert running == True, 'Engine не запущен, возвращает running = False, не смотря на /start/'

        # остановка engine сервера
        try:
            requests.get(url=url.stop, timeout=10)
        except Exception as err:
            raise RuntimeError(f'Сервер не останавливает engine. Причина: {err}')
