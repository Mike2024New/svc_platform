from svc_platform.engine import Engine
from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import Callable
from svc_platform.slots_manager import slots
from svc_platform.schemas import engine_types as e_types


def lifespan_factory(engine: Engine, settings: e_types.SettingsType) -> Callable:
    _ = settings

    @asynccontextmanager
    async def lifespan(_application: FastAPI):
        yield
        await engine.stop()  # явная остановка компонента
        slots.slot14(settings.name)

    return lifespan
