from typing import Any
from pydantic import BaseModel, ConfigDict

__all__ = ['EngineIOSchemas']


class EngineIOBase(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ExecuteInputData(EngineIOBase):
    text: str = 'This is a #stub. Example TTS Voice synthesis in progress. Long text for example.'
    step_time: float = 0.5


class ProcessInputData(EngineIOBase):
    text: str = 'stub'
    iterations: int = 20


class ProcessOutputData(EngineIOBase):
    result: Any


class ProducerStreamingInputData(EngineIOBase):
    text: str = 'stub'
    iterations: int = 10


class ProducerStreamingOutputData(EngineIOBase):
    text: str = 'stub'


# сборка I/O моделей для типизации engine и standart_api_routers(/process/, /execute/, /streaming/)
class EngineIOSchemas:
    process_input_data = ProcessInputData
    execute_input_data = ExecuteInputData
    process_output_data = ProcessOutputData
    producer_streaming_input_data = ProducerStreamingInputData
    producer_streaming_output_data = ProducerStreamingOutputData
