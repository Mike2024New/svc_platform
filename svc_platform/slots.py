from typing import Any
from svc_platform.message_bus import message_bus_add

"""
Набор функций-слотов, для вынесения дополнительной логики из модулей. (Сократить код сделав его удобочитабельным).
ВАЖНО! 
    - Каждая функция уникальна и вызов в проекте возможен только 1 раз.
    - Функции не упорядочены.
    
Пример назначения логирование (сейчас своя шина сообщений, но при необходимости можно будет заменить и на logging).
"""


def slot1(name: str, parameters: dict[str, Any], *args, **kwargs):
    """Запуск движка (engine.started)"""
    _ = args, kwargs, parameters
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
    message_bus_add(
        level='error',
        subcomponent=name,
        message=f'{name}.engine.execute.error -> {err}',
        event=f'engine.execute.error',
        error=err,
    )


def slot7(name: str, err: Exception, *args, **kwargs):
    """Ошибка stream метода движка"""
    _ = args, kwargs
    message_bus_add(
        level='error',
        subcomponent=name,
        message=f'{name}.engine.stream.error -> {err}',
        event=f'engine.stream.error',
        error=err,
    )


def slot8(name: str, *args, **kwargs):
    """stream start, начало стриминга"""
    _ = args, kwargs
    message_bus_add(
        level='start',
        subcomponent=name,
        message=f'{name}.engine.stream.start',
        event=f'engine.stream.start',
    )


def slot9(name: str, *args, **kwargs):
    """stream stop, остановка движка"""
    _ = args, kwargs
    message_bus_add(
        level='stop',
        subcomponent=name,
        message=f'{name}.engine.stream.stop',
        event=f'engine.stream.stop',
    )


def slot10(name: str, *args, **kwargs):
    """api.stream - клиент отключился"""
    _ = args, kwargs
    message_bus_add(
        level='info',
        subcomponent=name,
        message=f'{name}.api.stream client disconnected',
        event=f'engine.api.stream client disconnected',
    )


def slot11(name: str, err: Exception, *args, **kwargs):
    """api.stream - ошибка соединение будет разорвано"""
    _ = args, kwargs
    message_bus_add(
        level='error',
        subcomponent=name,
        message=f'{name}.api.stream.error disconnected, err -> {err}',
        event=f'engine.api.stream.error',
        error=err,
    )


def slot12(name: str, *args, **kwargs):
    _ = args, kwargs
    message_bus_add(
        level='warning',
        subcomponent=name,
        message=f'{name}.api.warning  server is not started',
        event=f'server is not started',
    )


def slot13(name, data):
    message_bus_add(
        level='start',
        subcomponent=name,
        message=f'{name}.server.start {data}',
        event=f'server start',
        data=data,
    )


def slot14(name):
    message_bus_add(
        level='stop',
        subcomponent=name,
        message=f'{name}.server.stop',
        event=f'server stop',
    )


def slot15(name, err):
    message_bus_add(
        level='error',
        subcomponent=name,
        message=f'{name}.server.start.error -> {err}',
        event=f'engine.start.error',
        error=err,
    )
