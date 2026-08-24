import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from svc_platform.engine import Engine
from svc_platform.schemas import engine_types as e_types

"""
Промежуточный слой
"""
from typing import TypeVar

T = TypeVar('T', bound=Engine)


def system_middlewares_factory(
        engine: T, settings: e_types.SettingsType
) -> list[tuple[type(BaseHTTPMiddleware), dict]]:
    """
    Фабрика системных промежуточных слоёв
    :param settings:
    :param engine: связь с движком (на всякий случай)
    """
    _ = engine, settings

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

    from starlette.types import Receive, Scope, Send

    class WebsocketValidationMiddleware(BaseHTTPMiddleware):
        def __init__(self, app):
            super().__init__(app)

        async def __call__(self, scope: Scope, receive: Receive, send: Send):
            # Проверка что это websocket запрос
            # логика до стрима
            if scope["type"] == "websocket":
                request_id = str(uuid.uuid4())[:8]
                err = None
                if not engine.parameters['running']:
                    err = {
                        "type": "error",
                        "error": "engine not started",
                        "close": True,
                        "message": "Не включен engine",
                        "request_id": request_id
                    }

                elif settings.stream_limit <= 1:
                    if engine.stream_current_tasks() > 0:
                        err = {
                            "type": "error",
                            "error": "stream limit exceeded",
                            "close": True,
                            "message": "Стриминг уже запущен (лимит 1)",
                            "request_id": request_id
                        }

                scope["state"]["err"] = err
                scope["state"]["request_id"] = request_id

            # вернуть управление основному приложению FastAPI
            await self.app(scope, receive, send)
            # логика после стрима
            if scope["type"] == "websocket":
                pass

    middlewares_list = [
        (SystemMiddleware, {}),  # промежуточный слой + дополнительные параметры для __init__
        (WebsocketValidationMiddleware, {}),  # промежуточный слой для обработки стимов
    ]
    return middlewares_list
