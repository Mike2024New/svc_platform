import threading
import pytest
from typing import Generator
from dataclasses import dataclass
from svc_platform.engine import Engine
from svc_platform.factories import message_bus_factory, settings_manager_factory, server_factory, api_factory
from svc_platform.schemas import SettingsExample
from svc_platform.slots import slots_init
from svc_platform.schemas import EngineIOSchemas


@dataclass
class Parameters:
    process_input_data: EngineIOSchemas.process_input_data
    process_output_data: EngineIOSchemas.process_output_data
    execute_input_data: EngineIOSchemas.execute_input_data
    streaming_input_data: EngineIOSchemas.streaming_input_data
    request_id: str = '#000'


class EngineTestSuite:
    """Тесты переносимые в дочерние проекты (при необходимости можно переопределять тесты там). А также подменять движки"""

    @pytest.fixture
    def process_input_data(self):
        return EngineIOSchemas.process_input_data(text='stub', iterations=5)

    @pytest.fixture
    def process_output_data(self):
        return EngineIOSchemas.process_output_data(result='stub')

    @pytest.fixture
    def execute_input_data(self):
        return EngineIOSchemas.execute_input_data(text='stub')

    @pytest.fixture
    def streaming_input_data(self):
        return EngineIOSchemas.streaming_input_data(text='stub')

    @pytest.fixture
    def engine_class(self):
        return Engine

    @pytest.fixture
    def settings_class(self):
        return SettingsExample

    @pytest.fixture
    def logs_enable(self):
        return True

    @pytest.fixture
    def test_engine(
            self,
            engine_class, settings_class, logs_enable,
            process_input_data, process_output_data,
            execute_input_data, streaming_input_data,
    ) -> Generator[tuple[Engine, Parameters], None, None]:
        settings, settings_manager = settings_manager_factory(settings_model=SettingsExample())
        message_bus_add, message_bus_settings = message_bus_factory(settings=settings)
        message_bus_settings.set_component_name(component=f"{settings.name}_test")
        slots_init(callback=message_bus_add, enable=logs_enable)
        parameters = Parameters(
            process_input_data=process_input_data,
            process_output_data=process_output_data,
            execute_input_data=execute_input_data,
            streaming_input_data=streaming_input_data,
        )
        yield engine_class(settings=settings), parameters

    @pytest.fixture
    def test_api(self, engine_class):
        _ = self  # IDE узбагойся
        # получить настройки (на базе schemas.BaseSettings)
        settings, settings_manager = settings_manager_factory(settings_model=SettingsExample())
        message_bus_add, message_bus_settings = message_bus_factory(settings=settings)
        message_bus_settings.set_component_name(component=f"{settings.name}_example")
        # включить слоты передав в них шину сообщений (если не передать шину fallback на принты)
        slots_init(callback=message_bus_add, enable=True)
        # создать экземпляр движка (движок может быть переопределенным в дочерних проектах)
        engine = engine_class(settings=settings)
        # подключить api ядра ( маршруты /start/, /stop/, /process/, /execute/ и так далее)
        api_modul = api_factory(engine=engine, settings=settings, standart_api_schemas=EngineIOSchemas())
        # создать сервер пробросив в него настройки, api_modul и при необходимости кастомные роутеры
        server = server_factory(settings=settings, api_modul=api_modul, middleware_err_enable=True, routers_list=[])

        def start_server():
            server.start(port=8000, log_level='warning', host='localhost')

        threading.Thread(target=start_server).start()
        from time import sleep
        sleep(2)
        yield  # в этой точке выполняются другие тесты
        # ручная остановка сервера
        server.stop()
