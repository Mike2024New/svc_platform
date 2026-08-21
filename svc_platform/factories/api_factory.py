from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import APIRouter
from svc_platform.slots_manager import slots
from dataclasses import dataclass
from typing import Callable
from svc_platform.api import routers_factory, lifespan_factory, system_middlewares_factory
from svc_platform.engine import Engine
from svc_platform.schemas import EngineIOSchemas
from svc_platform.api.exception_handlers import ExceptionHandlers
from svc_platform.schemas import SettingsSchemaType

"""
Сборщик стандартного api ( /start/, /stop/, /process/, /execute/, /stream/ )
"""
__all__ = ['api_factory', 'ApiFactoryResult']


@dataclass
class ApiFactoryResult:
    engine: Engine  # экземпляр класса движка
    routers_list: list[APIRouter]  # системный роутер с маршрутами /process/, /execute/, /stream/
    lifespan: Callable
    callback_start: Callable | None  # функция которая выполняется после старта движка
    callback_start_error: Callable | None  # функция которая выполняется в случае ошибки запуска движка
    callback_end: Callable | None  # функция которая выполняется при ручной остановке сервера (server.stop)
    exception_handlers_class: type(ExceptionHandlers)  # класс, который можно расширить между api_factory->server
    middlewares_list: list[tuple[type(BaseHTTPMiddleware), dict]]


def api_factory(
        engine: Engine,
        settings: SettingsSchemaType,
        standart_api_schemas: EngineIOSchemas,
        include_start_router: bool = True,
        include_end_router: bool = True,
) -> ApiFactoryResult:
    """
    Сборщик всех фабрик генерирующих api приложения (при необходимости можно эти объекты переопределять в ApiFactoryResult)
    :param standart_api_schemas: Pydantic схемы для /process/, /execute/, /stream/
    :param settings: настройки приложения
    :param engine: компонент выполняющий полезную нагрузку
    :param include_start_router: включать системный роутер start
    :param include_end_router: включать системный роутер end
    :return: объект для запуска сервера -> ApiFactoryResult
    """
    try:
        routers_list = routers_factory(
            engine=engine,
            settings=settings,
            engine_io_schemas=standart_api_schemas,
            include_start_router=include_start_router,
            include_end_router=include_end_router,
        )
        lifespan = lifespan_factory(engine=engine, settings=settings)
    except Exception as err:
        raise RuntimeError(f'Ошибка сборки api: {err}')

    return ApiFactoryResult(
        engine=engine,
        routers_list=routers_list,  # можно расширить на выходе
        lifespan=lifespan,  # можно переопределить на выходе
        callback_start_error=lambda error_data: slots.slot15(name=settings.name, err=error_data),
        callback_start=lambda data: slots.slot13(name=settings.name, data=data),  # логирование запуска
        callback_end=None,
        exception_handlers_class=ExceptionHandlers,  # системный обработчик исключений
        middlewares_list=system_middlewares_factory(engine=engine, settings=settings),  # промежуточные слои для http
    )
