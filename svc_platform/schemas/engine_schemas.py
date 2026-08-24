from typing import Any
from pydantic import BaseModel, ConfigDict
from svc_platform.schemas.settings_schemas import Parameters

__all__ = ['EngineIOSchemas']


class EngineIOBase(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ExecuteInputData(EngineIOBase):
    text: str = 'This is a #stub. Example TTS Voice synthesis in progress. Long text for example.'
    step_time: float = 0.5


class ProcessInputData(EngineIOBase):
    text: str = 'stub'


class ProcessOutputData(EngineIOBase):
    result: Any


class StreamingInputData(EngineIOBase):
    text: str = 'stub'
    iterations: int = 10


class StreamingOutputData(EngineIOBase):
    text: str = 'stub'


# сборка I/O моделей для типизации engine и standart_api_routers(/process/, /execute/, /streaming/)
class EngineIOSchemas:
    parameters = Parameters  # передача параметров engine
    process_input_data = ProcessInputData
    execute_input_data = ExecuteInputData
    process_output_data = ProcessOutputData
    streaming_input_data = StreamingInputData
    streaming_output_data = StreamingOutputData
