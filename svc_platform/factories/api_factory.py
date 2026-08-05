from svc_platform.engine import Engine
from fastapi import APIRouter
from svc_platform.api import routres_factory, lifespan_factory
from svc_platform import slots

"""
Реализация серверной логики запуска компонента
"""
__all__ = ['api_factory']

from dataclasses import dataclass
from typing import Callable


@dataclass
class ApiFactoryResult:
    engine: Engine
    routers_list: list[APIRouter]
    lifespan: Callable
    callback_start: Callable
    callback_start_error: Callable


def api_factory(
        engine: Engine, settings
) -> ApiFactoryResult:
    """
    Сборщик всех фабрик генерирующих api приложения (при необходимости можно эти объекты переопределять в ApiFactoryResult)
    :param settings: настройки приложения
    :param engine: компонент выполняющий полезную нагрузку
    :return: объект для запуска сервера -> ApiFactoryResult
    """
    try:
        routers_list = routres_factory(engine=engine, settings=settings)
        lifespan = lifespan_factory(engine=engine, settings=settings)
    except Exception as err:
        raise RuntimeError(f'Ошибка сборки api: {err}')

    return ApiFactoryResult(
        engine=engine,
        routers_list=routers_list,  # можно расширить на выходе
        lifespan=lifespan,  # можно переопределить на выходе
        callback_start_error=lambda error_data: slots.slot15(name=settings.name, err=error_data),
        callback_start=lambda data: slots.slot13(name=settings.name, data=data),  # логирование запуска
    )
