import requests, asyncio, json
from svc_platform.tests.conftest import EngineTestSuite
from infrastructure_streaming import consume_stream


class ApiTestStream(EngineTestSuite):
    async def test_stream(self, test_server, eingine_io_schemas):
        """Проверка что stream запускается и не падает, проверка что тело ответа корректно"""
        _ = self
        url = test_server
        requests.get(url=url.start, timeout=10)  # запуск engine

        def callback(response):
            for key in ('type', 'close', 'request_id', 'error', 'chunk'):
                assert key in response, f'В теле ответа api стриминга отсутствует ключ {key}'

        event = asyncio.Event()
        data = eingine_io_schemas.streaming_input_data.model_dump_json()
        task = consume_stream(url=url.streaming_ws, callback=callback, event=event, data=data)
        await task

    async def test_stream_send_no_correct_data(self, test_server, eingine_io_schemas):
        """Проверка что stream валидирует входные данные, и возвращает понятную ошибку"""
        _ = self
        url = test_server
        requests.get(url=url.start, timeout=10)  # запуск engine

        def callback(response):
            assert response.get('type') == 'error'
            assert response.get('close') == True
            assert response.get('error') is not None

        event = asyncio.Event()
        data = json.dumps({'demo': 'no correct data'})  # специально не корректные данные
        task = consume_stream(url=url.streaming_ws, callback=callback, event=event, data=data)
        await task

    async def test_stream_engine_not_started(self, test_server, eingine_io_schemas):
        """Проверка что сервер отказывает в стриминге если engine не включен"""
        _ = self
        url = test_server

        def callback(response):
            assert response.get('type') == 'error'
            assert response.get('close') == True
            assert response.get('error') is not None

        event = asyncio.Event()
        data = eingine_io_schemas.streaming_input_data.model_dump_json()
        task = consume_stream(url=url.streaming_ws, callback=callback, event=event, data=data)
        await task

    async def test_stream_client_close_connect(self, test_engine_factory, test_server, eingine_io_schemas):
        """Проверка что клиент может корректно отключиться и после отключения сервер закрывает стриминг"""
        _ = self
        url = test_server
        requests.get(url=url.start, timeout=10)  # запуск engine

        event = asyncio.Event()
        iterations = 0
        request_id = None

        def callback(response):
            nonlocal iterations, request_id
            iterations += 1
            if request_id is None:
                request_id = response.get('request_id')
            if iterations == 3:
                event.set()

        data = eingine_io_schemas.streaming_input_data.model_dump_json()
        task = consume_stream(url=url.streaming_ws, callback=callback, event=event, data=data)
        await task
        await asyncio.sleep(0.2)
        assert request_id not in test_engine_factory._stream_tasks_registry, f'Сервер не закрыл stream соединение после отключения клиента'

    async def test_stream_many_connections(self, test_engine_factory, test_server, eingine_io_schemas, settings):
        """Проверка запуска нескольких стримингов, сервер держит нагрузку"""
        _ = self
        url = test_server
        requests.get(url=url.start, timeout=10)  # запуск engine

        def callback(response):
            _ = response
            print(response)

        data = eingine_io_schemas.streaming_input_data.model_dump_json()
        tasks = []
        test_engine_factory._stream_semaphore._value = 3
        for _ in range(3):
            task = asyncio.create_task(
                consume_stream(
                    url=url.streaming_ws,
                    callback=callback,
                    event=asyncio.Event(),
                    data=data,
                    timeout=20,
                )
            )
            tasks.append(task)

        await asyncio.gather(*tasks)
