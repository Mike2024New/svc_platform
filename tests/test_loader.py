import pytest

from svc_platform.tests.test_engine_run import EngineTestRun
from svc_platform.tests.test_engine_execute import EngineTestExecute
from svc_platform.tests.test_engine_process import EngineTestProcess
from svc_platform.tests.test_engine_streaming import EngineTestStreaming
from svc_platform.engine import Engine

"""Точка сборки тестов"""


class TestTts(EngineTestRun, EngineTestExecute, EngineTestProcess, EngineTestStreaming):
    @pytest.fixture
    def engine_class(self):
        return Engine  # точка подмены движка

    @pytest.fixture
    def logs_enable(self):
        return False  # управление логами (вкл/выкл)
