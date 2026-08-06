from svc_platform.tests.conftest import EngineTestSuite


class EngineTestRun(EngineTestSuite):
    def test_start_stop(self, test_engine):
        _ = self  # IDE узбагойся
        engine = test_engine
        assert engine.parameters['running'] == False
        engine.start()
        assert engine.parameters['running'] == True
        engine.stop()

    def test_double_start(self, test_engine):
        _ = self
        engine = test_engine
        engine.start()
        engine.start()
        assert engine.parameters['running'] == True
        engine.stop()
