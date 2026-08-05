from typing import Any

"""
Набор функций-слотов, для вынесения дополнительной логики из модулей. (Сократить код сделав его удобочитабельным).
ВАЖНО! 
    - Каждая функция уникальна и вызов в проекте возможен только 1 раз.
    - Функции не упорядочены.
    
Пример назначения логирование (сейчас своя шина сообщений, но при необходимости можно будет заменить и на logging).
"""

from typing import Callable

message_bus_add: Callable | None = None


def slots_init(callback: Callable):
    global message_bus_add
    message_bus_add = callback


def slot1(name: str, parameters: dict[str, Any], *args, **kwargs):
    """Запуск движка (engine.started)"""
    _ = args, kwargs, parameters
    # print(f'{name}.engine.start')
    message_bus_add(
        level='start',
        subcomponent=name,
        message=f'{name}.engine.start',
        event=f'engine.start',
        data=parameters,
    )


def slot2(name: str, parameters: dict[str, Any], *args, **kwargs):
    """Остановка движка (engine.started)"""
    _ = args, kwargs, parameters
    # print(f'{name}.engine.stop')
    message_bus_add(
        level='stop',
        subcomponent=name,
        message=f'{name}.engine.stop',
        event=f'engine.stop',
        data=parameters,
    )


def slot3(name: str, err: Exception, *args, **kwargs):
    """Ошибка запуска движка"""
    _ = args, kwargs
    # print(f'{name}.engine.start.error -> {err}')
    message_bus_add(
        level='error',
        subcomponent=name,
        message=f'{name}.engine.start.error -> {err}',
        event=f'engine.start.error',
        error=err,
    )


def slot4(name: str, err: Exception, *args, **kwargs):
    """Ошибка остановки движка"""
    _ = args, kwargs
    # print(f'{name}.engine.stop.error -> {err}')
    message_bus_add(
        level='error',
        subcomponent=name,
        message=f'{name}.engine.stop.error -> {err}',
        event=f'engine.stop.error',
        error=err,
    )


def slot5(name: str, err: Exception, *args, **kwargs):
    """Ошибка процесса движка"""
    _ = args, kwargs
    # print(f'{name}.engine.process.error -> {err}')
    message_bus_add(
        level='error',
        subcomponent=name,
        message=f'{name}.engine.process.error -> {err}',
        event=f'engine.process.error',
        error=err,
    )


def slot6(name: str, err: Exception, *args, **kwargs):
    """Ошибка execute метода движка"""
    _ = args, kwargs
    # print(f'{name}.engine.execute.error -> {err}')
    message_bus_add(
        level='error',
        subcomponent=name,
        message=f'{name}.engine.execute.error -> {err}',
        event=f'engine.execute.error',
        error=err,
    )


def slot7(name: str, request_id: str, err: Exception, *args, **kwargs):
    """Ошибка stream метода движка"""
    _ = args, kwargs
    # print(f'{name}.engine.stream.error -> {err}')
    message_bus_add(
        level='error',
        subcomponent=name,
        message=f'{name}.engine.stream.error -> {err}',
        event=f'engine.stream.error',
        error=err,
        request_id=request_id,
    )


def slot8(name: str, request_id: str, *args, **kwargs):
    """stream start, начало стриминга"""
    _ = args, kwargs
    # print(f'{name}.engine.stream.start')
    message_bus_add(
        level='process',
        subcomponent=name,
        message=f'{name}.engine.stream.start',
        event=f'engine.stream.start',
        request_id=request_id,
        data={'timedelta_sec': 0},
    )


def slot9(name: str, request_id: str, end_time: float, *args, **kwargs):
    """stream stop, остановка движка"""
    _ = args, kwargs
    # print(f'{name}.engine.stream.stop')
    message_bus_add(
        level='process',
        subcomponent=name,
        message=f'{name}.engine.stream.stop',
        event=f'engine.stream.stop',
        request_id=request_id,
        data={'timedelta_sec': end_time},
    )


def slot11(name: str, err: Exception, *args, **kwargs):
    """api.stream - ошибка соединение будет разорвано"""
    _ = args, kwargs
    # print(f'{name}.api.stream.error disconnected, err -> {err}')
    message_bus_add(
        level='error',
        subcomponent=name,
        message=f'{name}.api.stream.error disconnected, err -> {err}',
        event=f'engine.api.stream.error',
        error=err,
    )


def slot12(name: str, *args, **kwargs):
    _ = args, kwargs
    # print(f"{name}.api.warning  server is not started")
    message_bus_add(
        level='warning',
        subcomponent=name,
        message=f'{name}.api.warning  server is not started',
        event=f'server is not started',
    )


def slot13(name, data, *args, **kwargs):
    _ = args, kwargs
    message_bus_add(
        level='start',
        subcomponent=name,
        message=f'{name}.server.start {data}',
        event=f'server start',
        data=data,
    )


def slot14(name, *args, **kwargs):
    _ = args, kwargs
    message_bus_add(
        level='stop',
        subcomponent=name,
        message=f'{name}.server.stop',
        event=f'server stop',
    )


def slot15(name, err, *args, **kwargs):
    _ = args, kwargs
    message_bus_add(
        level='error',
        subcomponent=name,
        message=f'{name}.server.start.error -> {err}',
        event=f'engine.server.error',
        error=err,
    )


def slot16(name, request_id: str, *args, **kwargs):
    _ = args, kwargs
    message_bus_add(
        level='process',
        subcomponent=name,
        message=f'{name}.engine.start.process',
        event=f'engine.start.process',
        request_id=request_id,
        data={'timedelta_sec': 0},
    )


def slot17(name, end_time: float, request_id: str, *args, **kwargs):
    _ = args, kwargs
    message_bus_add(
        level='process',
        subcomponent=name,
        message=f'{name}.engine.stop.process',
        event=f'engine.stop.process',
        request_id=request_id,
        data={'timedelta_sec': end_time},
    )


def slot18(name, request_id: str, *args, **kwargs):
    _ = args, kwargs
    message_bus_add(
        level='process',
        subcomponent=name,
        message=f'{name}.engine.start.execute',
        event=f'engine.start.execute',
        request_id=request_id,
        data={'timedelta_sec': 0},
    )


def slot19(name, end_time: float, request_id: str, *args, **kwargs):
    _ = args, kwargs
    message_bus_add(
        level='process',
        subcomponent=name,
        message=f'{name}.engine.stop.execute',
        event=f'engine.stop.execute',
        request_id=request_id,
        data={'timedelta_sec': end_time},
    )
