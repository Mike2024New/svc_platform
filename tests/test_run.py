from svc_platform.tests.test_engine_run import EngineTestRun
from svc_platform.tests.test_engine_execute import EngineTestExecute
from svc_platform.tests.test_engine_process import EngineTestProcess
from svc_platform.tests.test_engine_producer_streaming import EngineTestProducerStreaming

"""
запуск тестов, подключение и отключение тестов в классе TestEngine
"""


class TestsEngine(
    # EngineTestRun,
    EngineTestProcess,
    # EngineTestExecute,
    # EngineTestProducerStreaming,
):
    pass
