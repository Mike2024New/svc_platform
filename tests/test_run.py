from svc_platform.tests.test_engine_run import EngineTestRun
from svc_platform.tests.test_engine_execute import EngineTestExecute
from svc_platform.tests.test_engine_process import EngineTestProcess
from svc_platform.tests.test_engine_streaming import EngineTestStreaming
from svc_platform.tests.test_server_run import ApiTestRun
from svc_platform.tests.test_server_execute import ApiTestExecute
from svc_platform.tests.test_server_process import ApiTestProcess
from svc_platform.tests.test_server_stream import ApiTestStream

"""
запуск тестов, подключение и отключение тестов в классе TestEngine
"""


class TestsEngine(
    EngineTestRun,
    EngineTestExecute,
    EngineTestProcess,
    EngineTestStreaming,  # пока что пуст, будет расширен и автоматически применится в дочерних проектах
    ApiTestRun,
    ApiTestExecute,
    ApiTestProcess,
    ApiTestStream,  # пока что пуст, будет расширен и автоматически применится в дочерних проектах
):
    pass
