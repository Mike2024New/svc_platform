from svc_platform.engine import Engine
from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import Callable
from svc_platform import slots
from svc_platform.schemas import BaseSettings
from typing import TypeVar

T = TypeVar('T', bound=BaseSettings)


def lifespan_factory(engine: Engine, settings: T) -> Callable:
    _ = settings

    @asynccontextmanager
    async def lifespan(_application: FastAPI):
        yield
        engine.stop()  # явная остановка компонента
        slots.slot14(settings.name)

    return lifespan
