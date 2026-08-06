import pytest
from svc_platform.engine import Engine
from svc_platform.schemas import SettingsExample
from svc_platform.factories import settings_manager_factory


class EngineTestSuite:
    @pytest.fixture
    def engine_class(self):
        return Engine

    @pytest.fixture
    def settings_class(self):
        return SettingsExample

    @pytest.fixture
    def test_engine(self, engine_class, settings_class):
        settings, settings_manager = settings_manager_factory(settings_model=SettingsExample())
        yield engine_class(settings=settings)

    @staticmethod
    def test_start_stop(test_engine):
        engine = test_engine
        assert engine.parameters['running'] == False
        engine.start()
        assert engine.parameters['running'] == True
        engine.stop()
