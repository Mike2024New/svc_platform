from svc_platform.tests.conftest import EngineTestSuite


class EngineTestRun(EngineTestSuite):
    async def test_start_stop(self, test_engine, eingine_io_schemas):
        _ = self
        assert test_engine.parameters['running'] == False
        await test_engine.start()
        assert test_engine.parameters['running'] == True
        await test_engine.stop()

    async def test_double_start(self, test_engine, eingine_io_schemas):
        _ = self
        await test_engine.start()
        await test_engine.start()
        assert test_engine.parameters['running'] == True
        await test_engine.stop()
