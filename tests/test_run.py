from svc_platform.tests.test_engine_run import EngineTestRun
from svc_platform.tests.test_engine_execute import EngineTestExecute
from svc_platform.tests.test_engine_process import EngineTestProcess
from svc_platform.tests.test_engine_streaming import EngineTestStreaming

"""
запуск тестов, подключение и отключение тестов в классе TestEngine
"""


class TestsEngine(
    EngineTestRun,
    EngineTestExecute,
    EngineTestProcess,
    # EngineTestStreaming,
):
    pass
