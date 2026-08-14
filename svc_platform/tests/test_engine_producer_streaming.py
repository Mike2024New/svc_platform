import asyncio, pytest
from svc_platform.engine import EngineExc
from svc_platform.tests.conftest import EngineTestSuite
from queue import Queue
from dataclasses import dataclass, field


@dataclass
class TaskParameters:
    """Модель для запускаемых execute, process, stream"""
    tasks_list: list[asyncio.Task] = field(default_factory=list)
    requests_id_list: list[str] = field(default_factory=list)
    stream_queue_list: list[Queue] = field(default_factory=list)


class EngineTestProducerStreaming(EngineTestSuite):
    @staticmethod
    async def _wait_for_stream_first_chunk(stream_queue, timeout: float = 30.0, step: float = 0.1) -> bool:
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
    def _stream_callback_factory(engine_io_schemas, queue):
        async def callback(chunk: engine_io_schemas.producer_streaming_output_data):
            queue.put(chunk)

        return callback

    async def _run_stream_tasks(
            self, engine, engine_io_schemas, request_id_map: list[str] = None, count: int = 1,
            wait_for_tasks_runned: bool = True,
    ) -> TaskParameters:
        """
        Запускает стрим, и возвращает объект с списком задач, request_id, и очередями.
        (персонально для streaming)
        """
        stream_parameters = TaskParameters()

        for i in range(count):
            stream_queue = Queue()
            request_id = request_id_map[i] if request_id_map is not None else f'#00{i}'
            task = asyncio.create_task(
                engine.producer_stream(
                    data=engine_io_schemas.producer_streaming_input_data,
                    callback=self._stream_callback_factory(engine_io_schemas, stream_queue),
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
                    registry=engine._producer_stream_tasks_registry,  # noqa
                    target_state=True,
                ), 'стриминг запущен не был'

        return stream_parameters

    async def test_producer_stream(self, test_engine_factory, engine_io_schemas):
        """Проверка, что producer_stream запускается, что тип корректен, что возвращает чанки и удаляется из реестра
        после остановки."""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        stream_parameters = await self._run_stream_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=1,
        )
        stream_queue = stream_parameters.stream_queue_list[0]
        request_id = stream_parameters.requests_id_list[0]

        # ожидание первого чанка (проверка что стриминг отдаёт результаты)
        assert await self._wait_for_stream_first_chunk(
            stream_queue=stream_queue,
        ) is True, 'стрим не возвращает чанки'

        # анализ 1 чанка, что вернулся корректный тип данных
        chunk = stream_queue.get(timeout=1)

        try:
            # Валидация чанка
            engine_io_schemas.producer_streaming_output_data.model_validate_json(chunk)
        except Exception:
            raise ValueError(
                f'producer_stream -> _on_producer_stream, возвращает чанк не согласованный со схемой {engine_io_schemas.process_output_data.__class__.__name__} (либо его мутирует callback)'
            )

        # остановка стриминга
        engine.stop_producer_stream(request_id=request_id)
        # ожидание что стриминг был остановлен
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._producer_stream_tasks_registry, target_state=False,
        ), 'реестр задач не был очищен'

    async def test_producer_stream_double_request_id(self, test_engine_factory, engine_io_schemas, settings):
        """
        Проверка, что запуск двух producer_stream в одном захвате семафора с одинаковым request_id вызывает исключение
        StreamRequestIdAlreadyExists
        """
        _ = self
        if settings.stream_limit <= 1:
            return  # не требуется тест на лимит запущенных процессов, так как в фикстуре разрешен всего 1
        settings.stream_limit = 2  # разрешить запуск двух задач одновременно
        engine = test_engine_factory(settings_override=settings)
        await engine.start()
        stream_parameters = await self._run_stream_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=2,
            request_id_map=['#001', '#001'],  # два одинаковых id
        )

        # ожидание того что вылетит исключение StreamRequestIdAlreadyExists
        with pytest.raises(EngineExc.StreamRequestIdAlreadyExists):
            await asyncio.gather(*stream_parameters.tasks_list)

    async def test_producer_stream_stop(self, test_engine_factory, engine_io_schemas):
        """Проверка, что producer_stream останавливается по request_id и удаляется из реестра."""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        stream_parameters = await self._run_stream_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=1,
        )
        stream_queue = stream_parameters.stream_queue_list[0]
        request_id = stream_parameters.requests_id_list[0]

        # ожидание первого чанка (проверка что стриминг отдаёт результаты)
        assert await self._wait_for_stream_first_chunk(
            stream_queue=stream_queue,
        ) is True, 'стрим не возвращает чанки'

        # прервать стриминг
        engine.stop_producer_stream(request_id=request_id)

        # ожидание что стриминг был остановлен
        assert await self.wait_for_task_state(
            request_id=request_id, registry=engine._producer_stream_tasks_registry, target_state=False,
        ), 'реестр не был очищен'

    async def test_producer_stream_stop_no_request_id(self, test_engine_factory, engine_io_schemas):
        """Проверка, что остановка producer_stream по несуществующему request_id вызывает исключение
        StreamNoFindReqestId и не влияет на активные стримы."""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        stream_parameters = await self._run_stream_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=1,
        )
        stream_queue = stream_parameters.stream_queue_list[0]
        request_id = stream_parameters.requests_id_list[0]

        # ожидание первого чанка (проверка что стриминг отдаёт результаты)
        assert await self._wait_for_stream_first_chunk(
            stream_queue=stream_queue,
        ) is True, 'стрим не возвращает чанки'

        # должно выброситься исключение StreamNoFindReqestId
        with pytest.raises(EngineExc.StreamNoFindReqestId):
            engine.stop_producer_stream(request_id='#_no_correct_request_id_#')  # левый request_id
        assert request_id in engine._producer_stream_tasks_registry, 'стрим был прерван по неверному request_id'

    #

    async def test_producer_stream_limit(self, test_engine_factory, engine_io_schemas, settings):
        """Проверка, что producer_stream не запускает больше задач, чем установлено в stream_limit."""
        _ = self
        if settings.stream_limit <= 1:
            return  # не требуется тест на лимит запущенных процессов, так как в фикстуре разрешен всего 1
        tasks_count = settings.stream_limit + 1  # всего 2 задачи
        settings.stream_limit = 1  # ограничение семафора в 1 задачу
        engine = test_engine_factory()
        await engine.start()
        stream_parameters = await self._run_stream_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=tasks_count,
            wait_for_tasks_runned=False,
        )
        # 1 задача
        first_task = stream_parameters.tasks_list[0]
        first_task_request_id = stream_parameters.requests_id_list[0]
        first_task_queue = stream_parameters.stream_queue_list[0]
        # 2 задача
        second_task_request_id = stream_parameters.requests_id_list[1]
        second_task_queue = stream_parameters.stream_queue_list[1]

        # дождаться запуска 1 стрима
        assert await self.wait_for_task_state(
            request_id=first_task_request_id,
            registry=engine._producer_stream_tasks_registry,
            target_state=True,
        )
        # ожидание первого чанка (проверка что стриминг отдаёт результаты)
        assert await self._wait_for_stream_first_chunk(
            stream_queue=first_task_queue,
        ) is True, 'стрим не возвращает чанки'
        # второй стрим не должен был появиться в реестре, так как ещё не запущен (лимит 1)
        assert second_task_request_id not in engine._producer_stream_tasks_registry
        # ожидание завершения 1 стрима
        await first_task
        # первый стрим должен быть удален из реестра так как выполнен
        assert first_task_request_id not in engine._producer_stream_tasks_registry
        # ожидание запуска 2 стрима
        assert await self.wait_for_task_state(
            request_id=second_task_request_id,
            registry=engine._producer_stream_tasks_registry,
            target_state=True,
        )
        # второй стрим запустился и выдает 1 чанк
        assert await self._wait_for_stream_first_chunk(
            stream_queue=second_task_queue,
        ) is True, 'стрим не возвращает чанки'

    async def test_producer_stream_stop_all_tasks(self, test_engine_factory, engine_io_schemas, settings):
        """Проверка, что остановка движка останавливает все producer_stream и устанавливает флаг остановки."""
        _ = self
        engine = test_engine_factory()
        await engine.start()
        stream_parameters = await self._run_stream_tasks(
            engine=engine,
            engine_io_schemas=engine_io_schemas,
            count=settings.stream_limit,
        )

        # ожидание первого чанка (проверка что стриминг отдаёт результаты)
        for i in range(len(stream_parameters.tasks_list)):
            assert await self._wait_for_stream_first_chunk(
                stream_queue=stream_parameters.stream_queue_list[i],
            ) is True, 'стрим не возвращает чанки'

        # резкая остановка движка
        await engine.stop()
        # проверка что все переменные сброшены
        assert engine._producer_stream_tasks_registry == {}, 'задачи не были удалены из реестра'
        assert engine._producer_stream_stop_all is True, 'Флаг остановки всех задач не был установлен'
