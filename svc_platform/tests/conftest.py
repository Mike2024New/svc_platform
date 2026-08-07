import pytest
from typing import Generator
from dataclasses import dataclass
from svc_platform.engine import Engine
from svc_platform.factories.message_bus_factory import message_bus_factory
from svc_platform.factories.settings_manager_factory import settings_manager_factory
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
        return EngineIOSchemas.process_input_data(text='stub', iterations=5, step_time=0.5)

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
