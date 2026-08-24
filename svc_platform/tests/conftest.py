import threading, pytest, asyncio
from typing import Generator
from dataclasses import dataclass
from svc_platform.engine import Engine
from svc_platform.factories import message_bus_factory, server_factory, api_factory, routers_factory
from svc_platform.schemas import Settings
from svc_platform.slots_manager import slots_init, handler_print_message_factory
from svc_platform.schemas import EngineIOSchemas
from svc_platform.api.urls import Urls
from infrastructure_process_utils import find_free_port
from infrastructure_http_clients import ServerProbe
from svc_platform.factories import engine_factory


@dataclass
class TestParameters:
    """Предопределенные параметры для тестов (engine_io_schemas)"""
    engine_parameters: EngineIOSchemas.parameters
    process_input_data: EngineIOSchemas.process_input_data
    process_output_data: EngineIOSchemas.process_output_data
    execute_input_data: EngineIOSchemas.execute_input_data
    streaming_input_data: EngineIOSchemas.streaming_input_data
    streaming_output_data: EngineIOSchemas.streaming_output_data
    request_id: str = '#000'


class EngineTestSuite:
    """Тесты переносимые в дочерние проекты (при необходимости можно переопределять тесты там). А также подменять движки"""

    @pytest.fixture
    def engine_io_schemas(self):
        """Схема input/output/stream движка, важно в дочерних проектах переопределять эти схемы с параметрами"""
        parameters = EngineIOSchemas.parameters()
        return TestParameters(
            engine_parameters=parameters,
            process_input_data=EngineIOSchemas.process_input_data(text='stub'),
            process_output_data=EngineIOSchemas.process_output_data(result='stub'),
            execute_input_data=EngineIOSchemas.execute_input_data(text='stub'),
            streaming_input_data=EngineIOSchemas.streaming_input_data(text='stub'),
            streaming_output_data=EngineIOSchemas.streaming_output_data(text='stub'),
        )

    @pytest.fixture
    def settings(self):
        """Системные настройки приложения"""
        settings_model = Settings(
            execute_limit=3,
            process_limit=3,
            stream_limit=3,
        )
        return settings_model

    @pytest.fixture
    def test_engine_factory(self, settings):
        """Фабрика для создания Engine с кастомными настройками"""

        def _create_engine(settings_override=None):
            custom_settings = settings_override or settings
            engine = engine_factory(
                engine_class=Engine,
                settings=settings_override or settings
            )
            # если нужно логирование через шину сообщений:
            message_bus_add, message_bus_settings = message_bus_factory(settings=custom_settings)
            message_bus_settings.set_component_name(component=f"{custom_settings.name}_test")
            slots_init(
                handlers_list=[
                    # handler_message_bus_log_factory(message_bus_add),
                    handler_print_message_factory(),
                ],
                enable=False,
            )
            return engine

        return _create_engine

    @pytest.fixture
    def test_server(self, test_engine_factory, settings) -> Generator[Urls, None, None]:
        """Фикстура для тестов сервера, расширяет Engine."""
        _ = self
        engine = test_engine_factory()
        # подключение системных роутеров (start, stop, execute и др., проброс типизации/документации через EngineIOSchemas)
        system_routers = routers_factory(engine=engine, settings=settings, engine_io_schemas=EngineIOSchemas())
        # сборка системных роутеров (можно не передавать system_routers, тогда не подключатся стандартные эндпоинты start, stop, execute и др.)
        api_modul = api_factory(engine=engine, settings=settings, standard_routers_list=system_routers)
        # создание объекта сервера (запуск остановка)
        server = server_factory(settings=settings, api_modul=api_modul)
        port = find_free_port(start_port=8000, max_attempts=100, ignore_ports_list=[])  # поиск свободного порта
        url = Urls(port=port, host='localhost')

        def start_server():
            server.start(port=port, log_level='warning', host='localhost')

        threading.Thread(target=start_server).start()
        ServerProbe.polling(url=url.health, timeout=10, interval=0.5, expected_status=200)
        yield url  # url подвязанный на выбранный порт
        ServerProbe.polling(url=url.shutdown, timeout=10, interval=0.5, expected_status=200)

    @staticmethod
    async def wait_for_task_state(
            request_id, registry, target_state: bool = True, timeout: float = 5.0, step: float = 0.1,
    ):
        """
        Ожидание, что задача в реестре достигнет целевого состояния (появится или исчезнет) за отведенное время.
        (для тестов на машинах с разной производительностью)

        :param request_id: ID задачи
        :param registry: Словарь задач с ключами request_id (например, engine._execute_tasks_registry)
        :param target_state: True — ожидание появления задачи, False — ожидание исчезновения задачи
        :param timeout: Максимальное время ожидания (сек)
        :param step: Шаг проверки (сек)
        """
        attempts = int(timeout / step)
        for _ in range(attempts):
            await asyncio.sleep(step)
            if (request_id in registry) == target_state:
                return True
        return False
