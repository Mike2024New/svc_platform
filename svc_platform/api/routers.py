import asyncio
import uuid
from fastapi import APIRouter, status, Depends, HTTPException, WebSocket
from starlette.websockets import WebSocketDisconnect
from svc_platform.engine import Engine
from svc_platform.slots_manager import slots
from svc_platform.engine import EngineExc
from svc_platform.schemas import EngineIOSchemas


def routers_factory(engine: Engine, settings, engine_io_schemas: EngineIOSchemas) -> list[APIRouter]:
    app_router = APIRouter(tags=[settings.name])

    # =============== DEPENDENCIES ========================

    def is_component_running() -> bool:
        if not engine.parameters['running']:
            slots.slot12(name=settings.name)
            raise HTTPException(
                detail=f'Компонент `{settings.name}` не запущен, запустите его через /start/.',
                status_code=400
            )
        return True

    # =============== PARAMETERS ========================

    @app_router.get('/parameters/', summary='Информация о параметрах компонента', status_code=status.HTTP_200_OK)
    async def parameters() -> dict:
        """Текущие параметры компонента"""
        return {'message': f'Параметры engine {settings.name}', 'parameters': engine.parameters}

    # =============== START ========================

    @app_router.get('/start/', summary='Запуск компонента', status_code=status.HTTP_200_OK)
    async def start() -> dict:
        """Запуск движка компонента (для того чтобы работали /process/, /execute/, /stream/)"""
        if engine.parameters['running']:
            raise HTTPException(detail=f'Компонент `{settings.name}` уже был запущен ранее.', status_code=400)
        try:
            await engine.start()
        except EngineExc.StartError:
            raise
        return {'message': f'Компонент `{settings.name}` запущен.', 'parameters': engine.parameters}

    # =============== STOP ========================

    @app_router.get('/stop/', summary='Остановка компонента', status_code=status.HTTP_200_OK)
    async def stop(_is_running: bool = Depends(is_component_running)) -> dict:
        """Остановка движка компонента (перестанут работать /process/, /execute/, /stream/)"""
        try:
            await engine.stop()
            return {'message': f'Компонент `{settings.name}` остановлен.', 'parameters': engine.parameters, }
        except EngineExc.StopError:
            raise

    # =============== PROCESS ========================

    @app_router.post('/process/', status_code=status.HTTP_202_ACCEPTED)
    async def process(data: engine_io_schemas.process_input_data, _is_running: bool = Depends(is_component_running)):
        """Запуск процесса вычисления входных данных. Результат можно посмотреть на /process_result/ по готовности"""
        request_id = str(uuid.uuid4())[:8]
        if engine.process_result_storage_size >= settings.process_limit_max_result:
            slots.slot32(name=settings.name, request_id=request_id)
            raise EngineExc.ProcessStorageLimit(
                f'Сервер перегружен. '
                f'Активных задач: {engine.process_result_storage_size}. '
                f'Лимит: {settings.process_limit_max_result}'
            )

        asyncio.create_task(engine.process(data, request_id=request_id))
        return {'message': f'Процесс {request_id} запущен', 'request_id': request_id}

    @app_router.get('/process_stop/', status_code=status.HTTP_200_OK)
    async def process_stop(request_id: str):
        try:
            engine.stop_process(request_id=request_id)
            return {'message': f'Процесс {request_id} остановлен'}
        except EngineExc.ProcessNoFindReqestId:
            raise

    @app_router.get('/process_result/', status_code=status.HTTP_200_OK)
    async def process_result(request_id: str) -> dict[str, str | engine_io_schemas.process_output_data]:
        """Получение результата по request_id (коду который вернул /process/)"""
        try:
            result = engine.get_process_result(request_id=request_id)
            return {'message': f'Результат для {request_id}', 'result': result}
        except (
                EngineExc.ProcessResultNotCompleted,  # процесс не завершен (вычисления ещё не готовы)
                EngineExc.ProcessNoFindReqestId,  # неизвестный request_id, нет такой задачи
        ):
            raise

    # =============== EXECUTE ========================

    @app_router.post('/execute/', status_code=status.HTTP_200_OK)
    async def execute(data: engine_io_schemas.execute_input_data,
                      _is_running: bool = Depends(is_component_running)):
        request_id = str(uuid.uuid4())[:8]
        asyncio.create_task(engine.execute(data, request_id=request_id))
        return {'message': f'execute {request_id} запущен', 'request_id': request_id}

    @app_router.get('/execute_stop/', status_code=status.HTTP_200_OK)
    async def execute_stop(request_id: str):
        try:
            engine.stop_execute(request_id=request_id)
            return {'message': f'execute {request_id} остановлен'}
        except EngineExc.ExecuteNoFindReqestId:
            raise

    # =============== STREAMING (/WS) ========================

    from pydantic import BaseModel
    from typing import Literal, Any

    class StreamResponse(BaseModel):
        type: Literal['error', 'result', 'end']
        close: bool = False
        message: str
        request_id: str
        error: str | None = None
        chunk: Any | None = None

    @app_router.websocket('/ws')
    async def streaming(websocket: WebSocket):
        await websocket.accept()
        closed_by_client = False
        request_id = str(uuid.uuid4())[:8]

        try:
            # если engine не включен, то отправить клиенту отказ
            if not engine.parameters['running']:
                await websocket.send_json(
                    StreamResponse(
                        type='error',
                        error='engine not started',
                        close=True,
                        message='Не включен engine',
                        request_id=request_id
                    ).model_dump()
                )
                return

            # получение входных данных от клиента (с валидацией)
            try:
                data = engine_io_schemas.producer_streaming_input_data(**await websocket.receive_json())
            except ValueError:
                await websocket.send_json(
                    StreamResponse(
                        type='error',
                        close=True,
                        error='no corrected input data',
                        message='Не верные входные данные.',
                        request_id=request_id,
                    ).model_dump()
                )
                return

            async def async_callback(chunk_in: engine_io_schemas.producer_streaming_output_data):
                """обработка чанков (отправка клиенту)"""
                nonlocal closed_by_client
                try:
                    if not closed_by_client:
                        await websocket.send_json(
                            StreamResponse(
                                type='result',
                                chunk=chunk_in,
                                message='стриминг продолжается',
                                request_id=request_id,
                            ).model_dump()
                        )
                except WebSocketDisconnect:
                    closed_by_client = True
                    if stream_started:  # закрыть стриминг если он был открыт
                        engine.stop_producer_stream(request_id=request_id)

            stream_started = True
            await engine.producer_stream(callback=async_callback, data=data, request_id=request_id)
            # сообщить клиенту что соединение закрыто
            if not closed_by_client:
                await websocket.send_json(
                    StreamResponse(
                        type='end',
                        close=True,
                        message='Стриминг завершен',
                        request_id=request_id,
                    ).model_dump()
                )

        except Exception as err:
            if not closed_by_client:
                try:
                    await websocket.send_json(
                        StreamResponse(
                            type='error',
                            error=str(err),
                            close=True,
                            message='Внутренняя ошибка сервера',
                            request_id=request_id,
                        ).model_dump()
                    )
                except Exception:  # noqa
                    pass
                try:
                    engine.stop_producer_stream(request_id=request_id)
                except EngineExc.StreamNoFindReqestId:
                    pass
            slots.slot11(name=settings.name, err=err, request_id=request_id)

    return [app_router]
