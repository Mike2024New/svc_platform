from svc_platform.api.routers import routres_factory
from svc_platform.api.lifespan import lifespan_factory
from svc_platform.api.middlewares import system_middlewares_factory

__all__ = [
    'routres_factory',
    'lifespan_factory',
    'system_middlewares_factory',
]
