"""
Базовые тесты компонента
"""
import threading
import pytest
import uuid

from svc_platform.slots import message_bus_settings
from svc_platform.factories import settings_manager_factory, engine_factory
from svc_platform.engine import Engine
from svc_platform.schemas.schemas import SettingsExample


@pytest.fixture(scope="module")
def test_engine():
    settings, settings_manager = settings_manager_factory(settings_model=SettingsExample(name='example_app'))
    engine = engine_factory(engine_class=Engine, settings=settings)
    message_bus_settings.set_trace_id(trace_id=str(uuid.uuid4())[:8])
    message_bus_settings.set_component_name(component=f'{settings.name}_test_engine')
    yield engine


def test_engine_base(test_engine):
    """Базовая проверка корректной работы движка"""
    threading.Thread(target=lambda: test_engine.start(), daemon=True).start()  # запуск
    assert hasattr(test_engine, 'parameters') == True
    assert test_engine._running == True
    test_engine.stop()  # остановка
    assert test_engine._running == False


def test_engine_double_start(test_engine):
    """Проверка, что повторный запуск не ломает состояние и не запускает второй экземпляр"""
    threading.Thread(target=lambda: test_engine.start(), daemon=True).start()
    threading.Thread(target=lambda: test_engine.start(), daemon=True).start()
    assert test_engine._running == True
    test_engine.stop()
    assert test_engine._running == False
