import asyncio, uuid, json
from fastapi import APIRouter, status, Depends, HTTPException, WebSocket, Response
from fastapi.responses import JSONResponse
from starlette.websockets import WebSocketDisconnect
from svc_platform.engine import Engine
from svc_platform.slots_manager import slots
from svc_platform.engine import EngineExc
from svc_platform.schemas import engine_types as e_types
from svc_platform.schemas import EngineIOSchemas, StreamResponse


def routers_factory(
        engine: Engine,
        settings: e_types.SettingsType,
        engine_io_schemas: EngineIOSchemas,
        include_start_router: bool = True,
        include_end_router: bool = True,
) -> list[APIRouter]:
    app_router = APIRouter(tags=[settings.name])

    # =============== DEPENDENCIES ========================

    def is_component_running() -> bool:
        running = engine.get_parameters()['running']
        if not running:
            slots.slot12(name=settings.name)
            raise HTTPException(
                detail=f'Компонент `{settings.name}` не запущен, запустите его через /start/.',
                status_code=400
            )
        return True

    # =============== PARAMETERS ========================

    @app_router.get('/parameters/', summary='Информация о параметрах компонента', status_code=status.HTTP_200_OK)
    async def get_parameters() -> dict:
        """Текущие параметры компонента"""
        return {'message': f'Параметры engine {settings.name}', 'parameters': engine.get_parameters()}

    # =============== START ========================
    if include_start_router:
        # ⚠️ нужно будет убрать дублирование

        @app_router.post('/start/', summary='Запуск компонента', status_code=status.HTTP_200_OK)
        async def start(start_parameters: engine_io_schemas.parameters | None = None) -> dict:
            """Запуск движка компонента, позволяет персонально для него передать параметры (для того чтобы работали /process/, /execute/, /stream/)"""
            running = engine.get_parameters()['running']
            if running:
                raise HTTPException(detail=f'Компонент `{settings.name}` уже был запущен ранее.', status_code=400)
            try:
                await engine.start(start_parameters)
            except EngineExc.StartError:
                raise
            return {'message': f'Компонент `{settings.name}` запущен.'}

        # для совместимости с уже существующими компонентами которые используют get запросы
        @app_router.get('/start/', summary='Запуск компонента', status_code=status.HTTP_200_OK)
        async def start() -> dict:
            """⚠️ Устаревший метод в новых версиях лучше использовать post. Запуск движка компонента (для того чтобы работали /process/, /execute/, /stream/)"""
            running = engine.get_parameters()['running']
            if running:
                raise HTTPException(detail=f'Компонент `{settings.name}` уже был запущен ранее.', status_code=400)
            try:
                await engine.start()
            except EngineExc.StartError:
                raise
            return {'message': f'Компонент `{settings.name}` запущен.'}

    # =============== STOP ========================

    if include_end_router:

        @app_router.get('/stop/', summary='Остановка компонента', status_code=status.HTTP_200_OK)
        async def stop(_is_running: bool = Depends(is_component_running)) -> dict:
            """Остановка движка компонента (перестанут работать /process/, /execute/, /stream/)"""
            try:
                await engine.stop()
                return {'message': f'Компонент `{settings.name}` остановлен.'}
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

    @app_router.get('/process_result/')
    async def process_result(request_id: str):
        """Получение результата по request_id (коду который вернул /process/)"""
        try:
            result = engine.get_process_result(request_id=request_id)
            if result is None:
                raise HTTPException(status_code=404, detail="Результат не найден")
            # Если результат — строка или словарь → JSON
            if isinstance(result, (str, dict)):
                return JSONResponse({
                    'message': f'Результат для {request_id}',
                    'result': result
                })
            # Если результат — байты → бинарный ответ (можно будет расширить заголовки?)
            # В фабрике сервера параметр headers?
            if isinstance(result, bytes):
                return Response(
                    content=result,
                    media_type="application/octet-stream",
                    headers={
                        "Content-Disposition": f"attachment; filename=result_{request_id}.bin"
                    }
                )
            # Если результат — что-то другое → JSON
            return {'message': f'Результат для {request_id}', 'result': result}

        except EngineExc.ProcessResultNotCompleted:
            raise HTTPException(status_code=202, detail="Результат ещё не готов")
        except EngineExc.ProcessNoFindReqestId:
            raise HTTPException(status_code=404, detail="Задача не найдена")

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
    @app_router.websocket('/ws')
    async def stream(websocket: WebSocket):
        await websocket.accept()
        input_queue = asyncio.Queue()
        # обработка базовых ошибок из middleware (проверка что engine включен, и что есть свободные потоки)
        middleware_state = websocket.scope.get("state", {})
        request_id = middleware_state.get('request_id', str(uuid.uuid4())[:8])
        if middleware_state.get('err', None) is not None:
            middleware_message = middleware_state['err']
            await websocket.send_bytes(
                json.dumps(middleware_message).encode('utf-8')
            )

        async def producer(data):
            try:
                if isinstance(data, bytes):
                    await websocket.send_bytes(data)
                else:
                    await websocket.send_json(data)
            except (WebSocketDisconnect, RuntimeError):  # если клиент ещё не отключился
                pass  # просто выход так как клиент штатно отключился

        async def consumer():
            try:
                while True:
                    # обработка входных данных (перевод из байтов)
                    data = await websocket.receive_bytes()
                    try:
                        data = json.loads(data.decode('utf-8'))  # попытка перевести данные в json
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass  # пробросить дальше, так как это голые байты
                    await input_queue.put(data)
            except WebSocketDisconnect:
                raise  # обязательно выброс исключения, чтобы вызвать в endpoint stop_stream (в finally)

        consumer_task = asyncio.create_task(consumer())
        stream_task = asyncio.create_task(
            engine.stream(
                callback=producer,
                queue=input_queue,
                request_id=request_id,
            )
        )
        try:
            await asyncio.gather(consumer_task, stream_task)
        except (asyncio.CancelledError, WebSocketDisconnect):
            pass  # клиент отключился планово
        except Exception as err:

            slots.slot11(name=settings.name, err=err, request_id=request_id)
            data_send_err = StreamResponse(
                type='error',
                close=True,
                message="Ошибка на сервере, стриминг отменён.",
                request_id=request_id,
                error=str(err),
            ).model_dump()
            try:
                await producer(data_send_err)
            except:  # noqa
                pass
        finally:
            if websocket.client_state.name == 'CONNECTED':
                await websocket.close()
            try:
                engine.stop_stream(request_id=request_id)  # остановить стрим
            except EngineExc.StreamNoFindReqestId:
                pass

    return [app_router]
