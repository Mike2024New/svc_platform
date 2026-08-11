from svc_platform.api.routers import routers_factory
from svc_platform.api.lifespan import lifespan_factory
from svc_platform.api.middlewares import system_middlewares_factory
from svc_platform.api.urls import Urls

__all__ = [
    'routers_factory',
    'lifespan_factory',
    'system_middlewares_factory',
    'Urls',
]
