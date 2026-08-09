import asyncio
from typing import TypeVar
from dataclasses import dataclass
from svc_platform.schemas import EngineIOSchemas, BaseSettings


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


# =============== ДЖЕНЕРИКИ ТИПОВ ===============
# TypeVar с bound задает "верхнюю границу" — тип-ограничение.
# В дочерних проектах нужно переопределить эти TypeVar,
# подставив свои модели-наследники из EngineIOSchemas и также переопределив BaseSettings.
#
# Это позволяет:
# 1. IDE видеть точные типы (автокомплит полей voice, speed и т.д.)
# 2. Pydantic валидировать данные по расширенным схемам
# 3. Сохранить типобезопасность на всех уровнях
#
# Механизм: TypeVar → Generic → наследование с типами
# Чтобы не забыть это всё и не мучиться с этим каждый раз, лучше сделать репозиторий копируемый шаблон где это всё сделано
# ====================================================
BaseSettingsType = TypeVar('BaseSettingsType', bound=BaseSettings)
ProcessInputDataType = TypeVar('ProcessInputDataType', bound=EngineIOSchemas.process_input_data)
ProcessOutputDataType = TypeVar('ProcessOutputDataType', bound=EngineIOSchemas.process_output_data)
ExecuteInputDataType = TypeVar('ExecuteInputDataType', bound=EngineIOSchemas.execute_input_data)
StreamInputDataType = TypeVar('StreamInputDataType', bound=EngineIOSchemas.streaming_input_data)
StreamOutputDataType = TypeVar('StreamOutputDataType', bound=EngineIOSchemas.streaming_output_data)
