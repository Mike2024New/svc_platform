from svc_platform.tests.conftest import EngineTestSuite


class EngineTestRun(EngineTestSuite):
    async def test_start_stop(self, test_engine_factory, engine_io_schemas, settings):
        """Запуск и остановка движка, проверка по parameters['running']"""
        _ = self
        engine = test_engine_factory(settings_override=settings)
        assert engine.parameters['running'] == False
        await engine.start()
        assert engine.parameters['running'] == True
        await engine.stop()

    async def test_double_start(self, test_engine_factory, engine_io_schemas, settings):
        """Двойной запуск движка, не ломает работу компонента, проверка по parameters['running']"""
        _ = self
        engine = test_engine_factory(settings_override=settings)
        assert engine.parameters['running'] == False
        await engine.start()
        await engine.start()
        assert engine.parameters['running'] == True
        await engine.stop()
