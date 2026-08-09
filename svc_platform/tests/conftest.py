import threading, pytest
from typing import Generator
from dataclasses import dataclass
from svc_platform.engine import Engine
from svc_platform.factories import message_bus_factory, settings_manager_factory, server_factory, api_factory
from svc_platform.schemas import SettingsExample
from svc_platform.slots import slots_init
from svc_platform.schemas import EngineIOSchemas
from svc_platform.api.urls import Urls
from infrastructure_process_utils import find_free_port
from infrastructure_http_clients import ServerProbe
from svc_platform.factories import engine_factory


@dataclass
class Parameters:
    process_input_data: EngineIOSchemas.process_input_data
    process_output_data: EngineIOSchemas.process_output_data
    execute_input_data: EngineIOSchemas.execute_input_data
    streaming_input_data: EngineIOSchemas.streaming_input_data
    streaming_output_data: EngineIOSchemas.streaming_output_data
    request_id: str = '#000'


class EngineTestSuite:
    """Тесты переносимые в дочерние проекты (при необходимости можно переопределять тесты там). А также подменять движки"""

    @pytest.fixture
    def eingine_io_schemas(self):
        """Схема input/output движка"""
        return Parameters(
            process_input_data=EngineIOSchemas.process_input_data(text='stub', iterations=5),
            process_output_data=EngineIOSchemas.process_output_data(result='stub'),
            execute_input_data=EngineIOSchemas.execute_input_data(text='stub'),
            streaming_input_data=EngineIOSchemas.streaming_input_data(text='stub'),
            streaming_output_data=EngineIOSchemas.streaming_output_data(text='stub'),
        )

    @pytest.fixture
    def settings(self):
        """Системные настройки приложения"""
        settings_model = SettingsExample(
            execute_limit=3,
            process_limit=3,
            process_result_ttl=0.5,  # время хранения результата после вычисления
        )
        settings, settings_manager = settings_manager_factory(settings_model=settings_model)
        return settings, settings_manager

    @pytest.fixture
    def test_engine(self, settings) -> Generator[Engine, None, None]:
        """Фикстура для Engine тестов."""
        _ = self
        settings, settings_manager = settings
        engine = engine_factory(engine_class=Engine, settings=settings)
        message_bus_add, message_bus_settings = message_bus_factory(settings=settings)
        message_bus_settings.set_component_name(component=f"{settings.name}_test")
        slots_init(callback=message_bus_add, enable=True)
        yield engine

    @pytest.fixture
    def test_server(self, test_engine, settings) -> Generator[Urls, None, None]:
        """Фикстура для тестов сервера, расширяет Engine."""
        _ = self
        engine = test_engine
        settings, settings_manager = settings
        api_modul = api_factory(engine=engine, settings=settings, standart_api_schemas=EngineIOSchemas())
        server = server_factory(settings=settings, api_modul=api_modul, middleware_err_enable=True, routers_list=[])
        port = find_free_port(start_port=8000, max_attempts=100, ignore_ports_list=[])  # поиск свободного порта
        url = Urls(port=port, host='localhost')

        def start_server():
            server.start(port=port, log_level='warning', host='localhost')

        threading.Thread(target=start_server).start()
        ServerProbe.polling(url=url.health, timeout=10, interval=0.5, expected_status=200)
        yield url  # url подвязанный на выбранный порт
        ServerProbe.polling(url=url.shutdown, timeout=10, interval=0.5, expected_status=200)
