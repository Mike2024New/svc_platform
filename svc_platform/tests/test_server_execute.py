import requests, asyncio, aiohttp
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

    async def test_execute_aiohttp_base(self, test_server, eingine_io_schemas, test_engine_factory):
        """Базовый асинхронный тест с несколькими запросами, проверка что request_id не дублируются в engine"""
        _ = self
        url = test_server
        requests.get(url=url.start, timeout=10)  # запуск engine

        async def fetch_data(session_in, json_data):
            async with session_in.post(url.execute, json=json_data) as response:
                response = await response.json()
                return response

        data = eingine_io_schemas.execute_input_data
        data = data.model_dump()

        # запуск задач
        async with aiohttp.ClientSession() as session:
            tasks = []
            for _ in range(2):
                task = asyncio.create_task(fetch_data(session, json_data=data))
                tasks.append(task)

            result = await asyncio.gather(*tasks)
            request_id_list = set()
            for i in result:
                request_id = i.get('request_id')
                assert request_id is not None, 'execute не вернул request_id'
                request_id_list.add(request_id)
            assert len(request_id_list) == len(tasks), 'У execute дублируются request_id на разных задачах'
