import inspect
from typing import Any
from typing import Literal
from typing import Callable

"""
Единая точка логирования и мониторинга жизненного цикла всех SVC-сервисов. 

- К переменной message_bus_add подшивается программа обработки логов через slots_init.
- Если slots_init не был выполнен — выводятся print'ы в консоль (fallback).
- Можно заменить/дополнить на Kafka, logging, OpenTelemetry и т.д.
"""

message_bus_add: Callable | None = None
slots_enable: bool = True


def slots_init(callback: Callable | None = None, enable: bool = True):
    global message_bus_add, slots_enable
    slots_enable = enable
    message_bus_add = callback


def slots_log(
        level: Literal['debug', 'info', 'warning', 'error', 'critical', 'start', 'stop', 'process'],
        subcomponent: str,
        message: str,
        event: str,
        request_id: str | None = None,
        data: dict | None = None,
        error: Exception | None = None,
        slot_name: str = '',
        **kwargs
):
    if slot_name:
        slot_name = f"{slot_name}: "
        if data is not None:
            data['slot'] = slot_name
        else:
            data = {'slot': slot_name}

    if slots_enable:
        _ = kwargs
        if message_bus_add is not None:
            message_bus_add(
                level=level,
                subcomponent=subcomponent,
                message=f"{slot_name}{message}",
                event=event,
                data=data,
                error=error,
                request_id=request_id,
            )
        else:
            print(f"{slot_name}{message}")


def slot1(name: str, parameters: dict[str, Any], *args, **kwargs):
    """Запуск движка (engine.started)"""
    _ = args, kwargs, parameters
    slots_log(
        level='start',
        subcomponent=name,
        message=f'{name}.engine.start',
        event=f'engine.start',
        data=parameters,
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot2(name: str, parameters: dict[str, Any], *args, **kwargs):
    """Остановка движка (engine.started)"""
    _ = args, kwargs, parameters
    slots_log(
        level='stop',
        subcomponent=name,
        message=f'{name}.engine.stop',
        event=f'engine.stop',
        data=parameters,
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot3(name: str, err: Exception, *args, **kwargs):
    """Ошибка запуска движка"""
    _ = args, kwargs
    slots_log(
        level='error',
        subcomponent=name,
        message=f'{name}.engine.start.error -> {err}',
        event=f'engine.start.error',
        error=err,
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot4(name: str, err: Exception, *args, **kwargs):
    """Ошибка остановки движка"""
    _ = args, kwargs
    slots_log(
        level='error',
        subcomponent=name,
        message=f'{name}.engine.stop.error -> {err}',
        event=f'engine.stop.error',
        error=err,
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot5(name: str, err: Exception, *args, **kwargs):
    """Ошибка процесса движка"""
    _ = args, kwargs
    slots_log(
        level='error',
        subcomponent=name,
        message=f'{name}.engine.process.error -> {err}',
        event=f'engine.process.error',
        error=err,
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot6(name: str, err: Exception, *args, **kwargs):
    """Ошибка execute метода движка"""
    _ = args, kwargs
    slots_log(
        level='error',
        subcomponent=name,
        message=f'{name}.engine.execute.error -> {err}',
        event=f'engine.execute.error',
        error=err,
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot7(name: str, request_id: str, err: Exception, *args, **kwargs):
    """Ошибка stream метода движка"""
    _ = args, kwargs
    slots_log(
        level='error',
        subcomponent=name,
        message=f'{name}.engine.stream.error -> {err}',
        event=f'engine.stream.error',
        error=err,
        request_id=request_id,
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot8(name: str, request_id: str, *args, **kwargs):
    """stream start, начало стриминга"""
    _ = args, kwargs
    slots_log(
        level='process',
        subcomponent=name,
        message=f'{name}.engine.stream.start',
        event=f'engine.stream.start',
        request_id=request_id,
        data={'timedelta_sec': 0},
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot9(name: str, request_id: str, end_time: float, *args, **kwargs):
    """stream stop, остановка движка"""
    _ = args, kwargs
    slots_log(
        level='process',
        subcomponent=name,
        message=f'{name}.engine.stream.stop',
        event=f'engine.stream.stop',
        request_id=request_id,
        data={'timedelta_sec': end_time},
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot11(name: str, err: Exception, *args, **kwargs):
    """api.stream - ошибка соединение будет разорвано"""
    _ = args, kwargs
    slots_log(
        level='error',
        subcomponent=name,
        message=f'{name}.api.stream.error disconnected, err -> {err}',
        event=f'engine.api.stream.error',
        error=err,
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot12(name: str, *args, **kwargs):
    _ = args, kwargs
    slots_log(
        level='warning',
        subcomponent=name,
        message=f'{name}.api.warning  server is not started',
        event=f'server is not started',
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot13(name, data, *args, **kwargs):
    _ = args, kwargs
    slots_log(
        level='start',
        subcomponent=name,
        message=f'{name}.server.start {data}',
        event=f'server start',
        data=data,
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot14(name, *args, **kwargs):
    _ = args, kwargs
    slots_log(
        level='stop',
        subcomponent=name,
        message=f'{name}.server.stop',
        event=f'server stop',
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot15(name, err, *args, **kwargs):
    _ = args, kwargs
    slots_log(
        level='error',
        subcomponent=name,
        message=f'{name}.server.start.error -> {err}',
        event=f'engine.server.error',
        error=err,
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot16(name, request_id: str, *args, **kwargs):
    _ = args, kwargs
    slots_log(
        level='process',
        subcomponent=name,
        message=f'{name}.engine.start.process',
        event=f'engine.start.process',
        request_id=request_id,
        data={'timedelta_sec': 0},
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot17(name, end_time: float, request_id: str, *args, **kwargs):
    _ = args, kwargs
    slots_log(
        level='process',
        subcomponent=name,
        message=f'{name}.engine.stop.process',
        event=f'engine.stop.process',
        request_id=request_id,
        data={'timedelta_sec': end_time},
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot18(name, request_id: str, *args, **kwargs):
    _ = args, kwargs
    slots_log(
        level='process',
        subcomponent=name,
        message=f'{name}.engine.start.execute',
        event=f'engine.start.execute',
        request_id=request_id,
        data={'timedelta_sec': 0},
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot19(name, end_time: float, request_id: str, *args, **kwargs):
    _ = args, kwargs
    slots_log(
        level='process',
        subcomponent=name,
        message=f'{name}.engine.stop.execute',
        event=f'engine.stop.execute',
        request_id=request_id,
        data={'timedelta_sec': end_time},
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot20(name, request_id: str, *args, **kwargs):
    _ = args, kwargs
    slots_log(
        level='warning',
        subcomponent=name,
        message=f'{name}.engine.process.interrupted.cancel',
        event=f'engine.process.interrupted.cancel',
        request_id=request_id,
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot21(name, request_id: str, *args, **kwargs):
    _ = args, kwargs
    slots_log(
        level='warning',
        subcomponent=name,
        message=f'{name}.engine.execute.interrupted',
        event=f'engine.execute.interrupted',
        request_id=request_id,
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot22(name, request_id: str, *args, **kwargs):
    _ = args, kwargs
    slots_log(
        level='warning',
        subcomponent=name,
        message=f'{name}.engine.process.cleanup',
        event=f'engine.engine.process.cleanup',
        request_id=request_id,
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )


def slot23(name, request_id: str, *args, **kwargs):
    _ = args, kwargs
    slots_log(
        level='warning',
        subcomponent=name,
        message=f'{name}.engine.process задача `{request_id}` была отменена',
        event=f'engine.process.interrupted.cancel',
        request_id=request_id,
        slot_name=f'core.{inspect.currentframe().f_code.co_name}',
    )
