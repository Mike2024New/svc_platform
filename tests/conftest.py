import pytest
from svc_platform.engine import Engine
from svc_platform.factories.message_bus_factory import message_bus_factory
from svc_platform.factories.settings_manager_factory import settings_manager_factory
from svc_platform.schemas import SettingsExample
from svc_platform.slots import slots_init


@pytest.fixture(scope="module")
def engine_class():
    """Фабрика класса Engine. Дочерний сервис может переопределить."""
    return Engine


@pytest.fixture(scope="module")
def settings_class():
    """Фабрика класса Settings. Дочерний сервис может переопределить."""
    return SettingsExample


@pytest.fixture(scope="module")
def test_engine(engine_class, settings_class):
    # единая точка сборки приложения (созданные объекты можно переопределять как угодно)
    settings, settings_manager = settings_manager_factory(settings_model=SettingsExample())
    message_bus_add, message_bus_settings = message_bus_factory(settings=settings)
    message_bus_settings.set_component_name(component=f"{settings.name}_test")
    slots_init(callback=message_bus_add, enable=True)
    # Настройка тестового класса
    engine = engine_class(settings=settings)
    yield engine
