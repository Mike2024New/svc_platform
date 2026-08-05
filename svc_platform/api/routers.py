from fastapi import APIRouter, status, Depends, HTTPException, WebSocket
from starlette.websockets import WebSocketDisconnect
from typing import Any
from svc_platform.engine import Engine
from svc_platform import slots


def routres_factory(engine: Engine, settings) -> list[APIRouter]:
    app_router = APIRouter(tags=[settings.name])

    def is_component_running() -> bool:
        if not engine.parameters['running']:
            slots.slot12(name=settings.name)
            raise HTTPException(
                detail=f'Компонент `{settings.name}` не запущен, запустите его через /start/.',
                status_code=400
            )
        return True

    @app_router.get('/parameters/', summary='Информация о параметрах компонента', status_code=status.HTTP_200_OK)
    async def parameters() -> dict:
        """Текущие параметры компонента"""
        return engine.parameters

    @app_router.get('/start/', summary='Запуск компонента', status_code=status.HTTP_200_OK)
    async def start() -> dict:
        if engine.parameters['running']:
            raise HTTPException(detail=f'Компонент `{settings.name}` уже был запущен ранее.', status_code=400)
        engine.start()
        return {'message': f'Компонент `{settings.name}` запущен.', 'parameters': engine.parameters}

    @app_router.get('/stop/', summary='Остановка компонента', status_code=status.HTTP_200_OK)
    async def stop(_is_running: bool = Depends(is_component_running)) -> dict:
        engine.stop()
        return {
            'message': f'Компонент `{settings.name}` остановлен.',
            'parameters': engine.parameters,
        }

    @app_router.post('/process/')
    async def process(data, _is_running: bool = Depends(is_component_running)):
        result = engine.process(data)
        return {'message': 'результат выполнения операции', 'result': result}

    @app_router.websocket('/ws')
    async def streaming(websocket: WebSocket):
        await websocket.accept()
        closed_by_client = False

        try:
            # оповещение клиента
            if not engine.parameters['running']:
                await websocket.send_json({'type': 'close', 'msg': 'Connection closed, server not started.'})
                return

            data = await websocket.receive_json()  # получение входных данных от клиента

            async def async_callback(chunk_in: Any):
                """обработка чанков (отправка клиенту)"""
                nonlocal closed_by_client
                try:
                    if not closed_by_client:
                        await websocket.send_json({'type': 'data', 'chunk': chunk_in})
                except WebSocketDisconnect:
                    closed_by_client = True
                    engine.stream_stop()

            await engine.stream(callback=async_callback, data=data)
            # сообщить клиенту что соединение закрыто
            if not closed_by_client:
                await websocket.send_json({'type': 'close', 'msg': 'Connection closed.'})

        except Exception as err:
            if not closed_by_client:
                try:
                    await websocket.send_json({'type': 'err', 'detail': f'server error, connection close'})
                except Exception:  # noqa
                    pass
                engine.stream_stop()
            slots.slot11(name=settings.name, err=err)

    return [app_router]
