import asyncio, pytest
from svc_platform.engine import EngineExc
from svc_platform.tests.conftest import EngineTestSuite
from queue import Queue
from dataclasses import dataclass, field


class EngineTestStreaming(EngineTestSuite):
    @staticmethod
    async def wait_for_stream_first_chunk(stream_queue, timeout: float = 30.0, step: float = 0.1) -> bool:
        """
        Ожидание, появления первого чанка в очереди за отведенное время.
        (для тестов на машинах с разной производительностью)

        :param timeout: Максимальное время ожидания (сек)
        :param step: Шаг проверки (сек)
        :param stream_queue: очередь принимающая чанк
        :return: True если чанк появился, False если нет
        """
        attempts = int(timeout / step)
        for _ in range(attempts):
            if not stream_queue.empty():
                return True
        return False

    @staticmethod
    def stream_callback_factory(eingine_io_schemas, queue):
        async def callback(chunk: eingine_io_schemas.streaming_output_data):
            queue.put(chunk)

        return callback

    async def __run_stream_tasks(
            self, engine, eingine_io_schemas, request_id_map: list[str] = None, count: int = 1,
            wait_for_tasks_runned: bool = True,
    ):
        """
        Запускает стрим, и возвращает объект с списком задач, request_id, и очередями.
        (персонально для streaming)
        """

        @dataclass
        class StreamParameters:
            tasks_list: list[asyncio.Task] = field(default_factory=list)
            requests_id_list: list[str] = field(default_factory=list)
            stream_queue_list: list[Queue] = field(default_factory=list)

        stream_parameters = StreamParameters()

        for i in range(count):
            stream_queue = Queue()
            request_id = request_id_map[i] if request_id_map is not None else f'#00{i}'
            task = asyncio.create_task(
                engine.stream(
                    data=eingine_io_schemas.streaming_input_data,
                    callback=self.stream_callback_factory(eingine_io_schemas, stream_queue),
                    request_id=request_id,
                )
            )
            stream_parameters.tasks_list.append(task)
            stream_parameters.requests_id_list.append(request_id)
            stream_parameters.stream_queue_list.append(stream_queue)

        if wait_for_tasks_runned:
            # ожидание что стриминги были запущен
            for i in range(len(stream_parameters.tasks_list)):
                assert await self.wait_for_task_state(
                    request_id=stream_parameters.requests_id_list[i],
                    registry=engine._stream_tasks_registry,  # noqa
                    target_state=True,
                ), 'стриминг запущен не был'

        return stream_parameters

    async def test_stream(self, test_engine_factory, eingine_io_schemas):
        """Проверка что стриминг вызывается и не падает, а также останавливается по команде stop и убирается из реестра"""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        # создание одного стриминга
        stream_parameters = await self.__run_stream_tasks(
            engine=engine, eingine_io_schemas=eingine_io_schemas, count=1,
        )
        stream_queue = stream_parameters.stream_queue_list[0]
        request_id = stream_parameters.requests_id_list[0]

        # ожидание первого чанка (проверка что стриминг отдаёт результаты)
        assert await self.wait_for_stream_first_chunk(
            stream_queue=stream_queue,
        ) is True, 'стрим не возвращает чанки'
        # остановка стриминга
        engine.stop_stream(request_id=request_id)
        # ожидание что стриминг был остановлен
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._stream_tasks_registry, target_state=False,
        ), 'реестр задач не был очищен'

    async def test_stream_double_request_id(self, test_engine_factory, eingine_io_schemas, settings):
        """
        Попытка запустить процессы с двумя одинаковыми request_id (StreamRequestIdAlreadyExists)
        (при запуске нескольких задач асинхронно, limit > 1, нужно исключить пересечение)
        """
        _ = self
        settings.stream_limit = 2  # разрешить запуск двух задач одновременно
        engine = test_engine_factory(settings_override=settings)
        await engine.start()
        stream_parameters = await self.__run_stream_tasks(
            engine=engine,
            eingine_io_schemas=eingine_io_schemas,
            count=2,
            request_id_map=['#001', '#001'],  # два одинаковых id
        )

        # ожидание того что вылетит исключение StreamRequestIdAlreadyExists
        with pytest.raises(EngineExc.StreamRequestIdAlreadyExists):
            await asyncio.gather(*stream_parameters.tasks_list)

    async def test_stream_stop(self, test_engine_factory, eingine_io_schemas):
        """Прерывание, запуск streaming по id, прерывание streaming по id, проверка что реестр очищен."""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        stream_parameters = await self.__run_stream_tasks(
            engine=engine,
            eingine_io_schemas=eingine_io_schemas,
            count=1,
        )
        stream_queue = stream_parameters.stream_queue_list[0]
        request_id = stream_parameters.requests_id_list[0]

        # ожидание первого чанка (проверка что стриминг отдаёт результаты)
        assert await self.wait_for_stream_first_chunk(
            stream_queue=stream_queue,
        ) is True, 'стрим не возвращает чанки'

        engine.stop_stream(request_id=request_id)

        # ожидание что стриминг был остановлен
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._stream_tasks_registry, target_state=False,
        ), 'реестр не был очищен'

    async def test_stream_stop_no_request_id(self, test_engine_factory, eingine_io_schemas):
        """Попытка остановить streaming по неправильному id, должно выброситься исключение StreamNoFindReqestId"""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        stream_parameters = await self.__run_stream_tasks(
            engine=engine,
            eingine_io_schemas=eingine_io_schemas,
            count=1,
        )
        stream_queue = stream_parameters.stream_queue_list[0]

        # ожидание первого чанка (проверка что стриминг отдаёт результаты)
        assert await self.wait_for_stream_first_chunk(
            stream_queue=stream_queue,
        ) is True, 'стрим не возвращает чанки'

        # должно выброситься исключение StreamNoFindReqestId
        with pytest.raises(EngineExc.StreamNoFindReqestId):
            engine.stop_stream(request_id='#_no_correct_request_id_#')  # левый request_id

    async def test_stream_stop_all_tasks(self, test_engine_factory, eingine_io_schemas, settings):
        _ = self
        settings.stream_limit = 3
        engine = test_engine_factory()
        await engine.start()
        stream_parameters = await self.__run_stream_tasks(
            engine=engine,
            eingine_io_schemas=eingine_io_schemas,
            count=3,
        )

        # ожидание первого чанка (проверка что стриминг отдаёт результаты)
        for i in range(len(stream_parameters.tasks_list)):
            assert await self.wait_for_stream_first_chunk(
                stream_queue=stream_parameters.stream_queue_list[i],
            ) is True, 'стрим не возвращает чанки'

        # резкая остановка стриминга
        await engine.stop()
        # проверка что все переменные сброшены
        assert engine._stream_tasks_registry == {}, 'задачи не были удалены из реестра'
        assert engine._stream_stop_all is True, 'Флаг остановки всех задач не был установлен'
