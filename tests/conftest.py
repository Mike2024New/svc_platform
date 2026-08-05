import pytest
from svc_platform.engine import Engine
from svc_platform.schemas.schemas import SettingsExample
from svc_platform.helper import settings


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
    engine = engine_class(settings=settings)
    yield engine
