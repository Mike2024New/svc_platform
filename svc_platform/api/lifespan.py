from svc_platform.engine import Engine
from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import Callable


def lifespan_factory(engine: Engine, settings) -> Callable:
    _ = settings

    @asynccontextmanager
    async def lifespan(_application: FastAPI):
        yield
        engine.stop()  # явная остановка компонента

    return lifespan
