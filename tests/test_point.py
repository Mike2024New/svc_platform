import pytest

from svc_platform.tests.test_engine_run import EngineTestRun
from svc_platform.tests.test_engine_execute import EngineTestExecute
from svc_platform.tests.test_engine_process import EngineTestProcess
from svc_platform.engine import Engine


class TestTts(EngineTestRun, EngineTestExecute, EngineTestProcess):
    @pytest.fixture
    def engine_class(self):
        return Engine  # точка подмены движка
