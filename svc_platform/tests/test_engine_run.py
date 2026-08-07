from svc_platform.tests.conftest import EngineTestSuite


class EngineTestRun(EngineTestSuite):
    async def test_start_stop(self, test_engine):
        _ = self  # IDE узбагойся
        engine, parameters = test_engine
        assert engine.parameters['running'] == False
        await engine.start()
        assert engine.parameters['running'] == True
        await engine.stop()

    async def test_double_start(self, test_engine):
        _ = self
        engine, parameters = test_engine
        await engine.start()
        await engine.start()
        assert engine.parameters['running'] == True
        await engine.stop()
