import requests
from svc_platform.tests.conftest import EngineTestSuite
from infrastructure_http_clients import ServerProbe


class ApiTestRun(EngineTestSuite):
    def test_server_start_stop(self, run_server):
        """Проверка что сервер корректно запускает и останавливает Engine"""
        _ = self
        url = run_server

        # запуск engine сервера
        try:
            ServerProbe.polling(url=url.start, timeout=10, interval=0.5, expected_status=200)
        except Exception as err:
            raise RuntimeError(f'Сервер не запускает engine. Причина: {err}')

        res = requests.get(url=url.parameters)
        data = res.json()
        assert data is not None
        running = data.get('parameters', {}).get('running', None)
        assert running is not None, 'parameters не возвращает флаг проверки состояния engine -> running'
        assert running == True, 'Engine не запущен, возвращает running = False, не смотря на /start/'

        # остановка engine сервера
        try:
            ServerProbe.polling(url=url.stop, timeout=10, interval=0.5, expected_status=200)
        except Exception as err:
            raise RuntimeError(f'Сервер не останавливает engine. Причина: {err}')
