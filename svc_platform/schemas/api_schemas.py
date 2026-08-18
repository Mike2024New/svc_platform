from pydantic import BaseModel
from typing import Literal, Any


class StreamResponse(BaseModel):
    type: Literal['error', 'result', 'end']
    close: bool = False
    message: str
    request_id: str | None = None
    error: str | None = None
    data: Any | None = None
