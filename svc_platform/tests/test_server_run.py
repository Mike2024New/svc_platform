from svc_platform.tests.conftest import EngineTestSuite
import requests
from time import sleep


class ApiTestRun(EngineTestSuite):
    def test_server_health(self, test_api):
        _ = self
        pass
        # attempt = 10
        # простой поллинг сервера
        # for _ in range(attempt):
        #     res = requests.get(url='http://localhost:8000/health/')
        #     if res.status_code == 200:
        #         return
        #     sleep(1)
        # raise RuntimeError(f'Сервер не ответил спустя {attempt} секунд после старта.')

    # async def test_server_engine_start(self, test_api):
    #     _ = self
    #     # запуск engine сервера
    #     result = requests.get(url='http://localhost:8000/start/')
    #     if result.status_code != 200:
    #         raise RuntimeError(f'Сервер при запуске, выдает ошибку: {result.json()}')
    #
    #     # остановка engine сервера
    #     result = requests.get(url='http://localhost:8000/stop/')
    #     if result.status_code != 200:
    #         raise RuntimeError(f'Сервер при остановке, выдает ошибку: {result.json()}')
