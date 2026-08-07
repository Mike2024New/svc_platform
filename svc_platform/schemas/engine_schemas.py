from pydantic import BaseModel

__all__ = ['EngineIOSchemas']


class ExecuteInputData(BaseModel):
    text: str = 'example'


class ProcessInputData(BaseModel):
    text: str = 'example'


class ProcessOutputData(BaseModel):
    text: str = 'stub'


class StreamingInputData(BaseModel):
    text: str = 'example'


class EngineIOSchemas:
    process_input_data = ProcessInputData
    execute_input_data = ExecuteInputData
    process_output_data = ProcessOutputData
    streaming_input_data = StreamingInputData
