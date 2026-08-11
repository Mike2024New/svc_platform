import asyncio
from datetime import datetime

from dataclasses import dataclass, field
from svc_platform.schemas import EngineIOSchemas

# ============== Классы для задач ===============
@dataclass
class Task:
    event: asyncio.Event
    task: asyncio.Task


@dataclass
class ExecuteTask(Task): ...


@dataclass
class StreamTask(Task): ...


@dataclass
class ProcessTask(Task):
    result: EngineIOSchemas.process_output_data | None = None
    completed_at: float | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now())

