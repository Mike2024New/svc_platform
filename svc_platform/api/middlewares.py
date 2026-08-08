from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from svc_platform.engine import Engine

"""
Промежуточный слой
"""
from typing import TypeVar

T = TypeVar('T', bound=Engine)


def system_middlewares_factory(engine: T) -> list[tuple[type(BaseHTTPMiddleware), dict]]:
    """
    Фабрика системных промежуточных слоёв
    :param engine: связь с движком (на всякий случай)
    :return:
    """
    _ = engine

    class SystemMiddleware(BaseHTTPMiddleware):
        def __init__(self, app):
            super().__init__(app)

        async def dispatch(self, request: Request, call_next):
            try:
                ...  # полезная нагрузка до (выдачи конента пользователю)
                response = await call_next(request)
                ...  # полезная нагрузка после (выдачи контента пользователю)
                return response
            except Exception:
                raise

    middlewares_list = [
        (SystemMiddleware, {}),  # промежуточный слой + дополнительные параметры для __init__
    ]
    return middlewares_list
