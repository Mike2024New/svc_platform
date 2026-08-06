import pytest
from svc_platform.engine import Engine
from svc_platform.factories.message_bus_factory import message_bus_factory
from svc_platform.factories.settings_manager_factory import settings_manager_factory
from svc_platform.schemas import SettingsExample
from svc_platform.slots import slots_init


class EngineTestSuite:
    """Тесты переносимые в дочерние проекты (при необходимости можно переопределять тесты там). А также подменять движки"""

    @pytest.fixture
    def engine_class(self):
        return Engine

    @pytest.fixture
    def settings_class(self):
        return SettingsExample

    @pytest.fixture
    def test_engine(self, engine_class, settings_class):
        settings, settings_manager = settings_manager_factory(settings_model=SettingsExample())
        message_bus_add, message_bus_settings = message_bus_factory(settings=settings)
        message_bus_settings.set_component_name(component=f"{settings.name}_test")
        slots_init(callback=message_bus_add)
        yield engine_class(settings=settings)
