from infrastructure_server.server_v2.main import ExceptionHandlersProtocol
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from svc_platform.engine.exc import EngineExc

"""
Обработчики для отлова специфических исключений
"""


class ExceptionHandlers(ExceptionHandlersProtocol):
    @classmethod
    def register(cls, app: FastAPI):
        """В этом методе прописать нужные обработчики (применяются после middleware)"""

        @app.exception_handler(ZeroDivisionError)
        async def exception_zero_divizion_error(request: Request, exc: Exception):
            """Просто для примера: обработчик ответственный за исключение ZeroDivisionError"""
            error = f'Ошибка, делить на ноль могут только монахи математики 6 дана с чёрным поясом'
            print(error)
            return JSONResponse(
                status_code=status.HTTP_418_IM_A_TEAPOT,
                content={'error': error, 'detail': str(exc), 'path': request.url.path}
            )

        @app.exception_handler(EngineExc.ProcessResultNoFindReqestId)
        async def exc_handler1(request: Request, exc: Exception):
            """Не найден заданный request_id"""
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    'error': exc.__class__.__name__,
                    'detail': str(exc),
                    'path': request.url.path
                }
            )

        @app.exception_handler(EngineExc.ProcessCancelled)
        async def exc_handler2(request: Request, exc: Exception):
            """Процесс был отменен"""
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    'error': exc.__class__.__name__,
                    'detail': str(exc),
                    'path': request.url.path
                }
            )

        @app.exception_handler(EngineExc.ProcessResultNotCompleted)
        async def exc_handler3(request: Request, exc: Exception):
            """Процесс ещё не завершен"""
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content={
                    'error': exc.__class__.__name__,
                    'detail': str(exc),
                    'path': request.url.path
                }
            )

        @app.exception_handler(EngineExc.ExecuteNoFindReqestId)
        async def exc_handler4(request: Request, exc: Exception):
            """Попытка остановить несуществующий execute"""
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    'error': exc.__class__.__name__,
                    'detail': str(exc),
                    'path': request.url.path
                }
            )

        @app.exception_handler(EngineExc.StartError)
        async def exc_handler5(request: Request, exc: Exception):
            """Ошибка при запуске движка"""
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    'error': exc.__class__.__name__,
                    'detail': str(exc),
                    'path': request.url.path
                }
            )

        @app.exception_handler(EngineExc.StopError)
        async def exc_handler6(request: Request, exc: Exception):
            """Ошибка при остановке движка"""
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    'error': exc.__class__.__name__,
                    'detail': str(exc),
                    'path': request.url.path
                }
            )

        @app.exception_handler(EngineExc.ProcessStorageLimit)
        async def exc_handler7(request: Request, exc: Exception):
            """Ошибка при остановке движка"""
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    'error': exc.__class__.__name__,
                    'detail': str(exc),
                    'path': request.url.path
                }
            )

        ...  # другие обработчики ...


if __name__ == '__main__':
    class ExceptionHandlersExt(ExceptionHandlersProtocol):
        @staticmethod
        def register(app: FastAPI) -> None:
            super().register(app=app)


    ex = ExceptionHandlersExt()
