from typing import Any
from typing import Literal
from typing import Callable
from dataclasses import dataclass
from functools import wraps
from warnings import warn

"""
Единая точка логирования и мониторинга жизненного цикла всех SVC-сервисов. 

- К переменной message_bus_add подшивается программа обработки логов через slots_init.
- Если slots_init не был выполнен — выводятся print'ы в консоль (fallback).
- Можно заменить/дополнить на Kafka, logging, OpenTelemetry и т.д.
- Можно использовать не только для логирования но и для дополнительных хуков

К слотам можно навешивать декораторы с расширенной функциональностью.
"""

message_bus_add: Callable | None = None
slots_enable: bool = True


def slots_init(callback: Callable | None = None, enable: bool = True):
    global message_bus_add, slots_enable
    slots_enable = enable
    message_bus_add = callback


@dataclass
class Parameters:
    level: Literal['debug', 'info', 'warning', 'error', 'critical', 'start', 'stop', 'process']
    subcomponent: str
    message: str
    event: str
    request_id: str | None = None
    data: dict | None = None
    error: Exception | None = None


def slots_log_decorator(func):
    """
    Проброс событий в шину сообщений. С автоматическим определением вызывающего слота (имя функции например slot1)
    Защита от неисправностей в самих слотах, чтобы приложение не вылетало из-за ошибок в слотах
    """

    @wraps(func)
    def inner(*args, **kwargs):
        slot_name = f'core.{func.__name__}'
        try:
            parameters: Parameters = func(*args, **kwargs)
            if parameters.data is not None:
                parameters.data['slot'] = slot_name
            else:
                parameters.data = {'slot': slot_name}

            message = f"{parameters.message}\t@{slot_name}"
            if slots_enable:
                _ = kwargs
                if message_bus_add is not None:
                    message_bus_add(
                        level=parameters.level,
                        subcomponent=parameters.subcomponent,
                        message=parameters.message,
                        event=parameters.event,
                        request_id=parameters.request_id,
                        data=parameters.data,
                        error=parameters.error,
                    )
                else:
                    print(message)
        except Exception as err:
            print(err)
            warn(message=f'Не удалось обработать slots.{slot_name}, причина: {err}')

    return inner


@slots_log_decorator
def slot1(name: str, parameters: dict[str, Any], *args, **kwargs):
    """Запуск движка (engine.started)"""
    _ = args, kwargs, parameters
    return Parameters(
        level='start',
        subcomponent=name,
        message=f'[ {name}.ENGINE ] движок запущен',
        event=f'engine.start',
        data=parameters,
    )


@slots_log_decorator
def slot2(name: str, parameters: dict[str, Any], *args, **kwargs):
    """Остановка движка (engine.started)"""
    _ = args, kwargs, parameters
    return Parameters(
        level='stop',
        subcomponent=name,
        message=f'[ {name}.ENGINE ] движок остановлен',
        event=f'engine.stop',
        data=parameters,
    )


@slots_log_decorator
def slot3(name: str, err: Exception, *args, **kwargs):
    """Ошибка запуска движка"""
    _ = args, kwargs
    return Parameters(
        level='error',
        subcomponent=name,
        message=f'[ {name}.ENGINE ]  ошибка запуска движка:{err}',
        event=f'engine.start.error',
        error=err,
    )


@slots_log_decorator
def slot4(name: str, err: Exception, *args, **kwargs):
    """Ошибка остановки движка"""
    _ = args, kwargs
    return Parameters(
        level='error',
        subcomponent=name,
        message=f'[ {name}.ENGINE ]  ошибка остановки движка:{err}',
        event=f'engine.stop.error',
        error=err,
    )


@slots_log_decorator
def slot5(name: str, request_id: str, err: Exception, *args, **kwargs):
    """Ошибка процесса движка"""
    _ = args, kwargs
    return Parameters(
        level='error',
        subcomponent=name,
        message=f'[ {name}.PROCESS ] {request_id}:{err}',
        event=f'engine.process.error',
        error=err,
        request_id=request_id,
    )


@slots_log_decorator
def slot6(name: str, request_id: str, err: Exception, *args, **kwargs):
    """Ошибка execute метода движка"""
    _ = args, kwargs
    return Parameters(
        level='error',
        subcomponent=name,
        message=f'[ {name}.EXECUTE ] {request_id}:{err}',
        event=f'engine.execute.error',
        error=err,
    )


@slots_log_decorator
def slot7(name: str, request_id: str, err: Exception, *args, **kwargs):
    """Ошибка stream метода движка"""
    _ = args, kwargs
    return Parameters(
        level='error',
        subcomponent=name,
        message=f'[ {name}.STREAMING ] {request_id}:{err}',
        event=f'engine.stream.error',
        error=err,
        request_id=request_id,
    )


@slots_log_decorator
def slot8(name: str, request_id: str, *args, **kwargs):
    """stream start, начало стриминга"""
    _ = args, kwargs
    return Parameters(
        level='info',
        subcomponent=name,
        message=f'[ {name}.STREAMING ] {request_id} запущен',
        event=f'engine.stream.start',
        request_id=request_id,
        data={'timedelta_sec': 0},
    )


@slots_log_decorator
def slot9(name: str, request_id: str, end_time: float, *args, **kwargs):
    """stream stop, остановка движка"""
    _ = args, kwargs
    return Parameters(
        level='info',
        subcomponent=name,
        message=f'[ {name}.STREAMING ] {request_id} остановлен',
        event=f'engine.stream.stop',
        request_id=request_id,
        data={'timedelta_sec': end_time},
    )


@slots_log_decorator
def slot11(name: str, request_id: str, err: Exception, *args, **kwargs):
    """api.stream - ошибка соединение будет разорвано"""
    _ = args, kwargs
    return Parameters(
        level='error',
        subcomponent=name,
        message=f'[ {name}.STREAMING ] {request_id} остановлен, err:{err}',
        event=f'engine.api.stream.error',
        error=err,
    )


@slots_log_decorator
def slot12(name: str, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='warning',
        subcomponent=name,
        message=f'[ {name}.ENGINE ] движок не запущен, нужно запустить его через start ',
        event=f'server is not started',
    )


@slots_log_decorator
def slot13(name, data, *args, **kwargs):
    _ = args, kwargs
    message = (
        f'[ {name}.SERVER ] сервер запущен '
        f'-> port={data.get("port", "unknow")}, host={data.get("host", "unknow")}, pid={data.get("pid", "unknow")}'
    )
    return Parameters(
        level='start',
        subcomponent=name,
        message=message,
        event=f'server start',
        data=data,
    )


@slots_log_decorator
def slot14(name, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='stop',
        subcomponent=name,
        message=f'[ {name}.SERVER ] сервер остановлен',
        event=f'server stop',
    )


@slots_log_decorator
def slot15(name, err, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='error',
        subcomponent=name,
        message=f'[ {name}.server ] ошибка запуска сервера:{err}',
        event=f'engine.server.error',
        error=err,
    )


@slots_log_decorator
def slot16(name, request_id: str, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='info',
        subcomponent=name,
        message=f'[ {name}.PROCESS ] {request_id} запущен',
        event=f'engine.start.process',
        request_id=request_id,
        data={'timedelta_sec': 0},
    )


@slots_log_decorator
def slot17(name, end_time: float, request_id: str, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='info',
        subcomponent=name,
        message=f'[ {name}.PROCESS ] {request_id} выполнен',
        event=f'engine.stop.process',
        request_id=request_id,
        data={'timedelta_sec': end_time},
    )


@slots_log_decorator
def slot18(name, request_id: str, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='info',
        subcomponent=name,
        message=f'[ {name}.EXECUTE ] {request_id} запущен',
        event=f'engine.start.execute',
        request_id=request_id,
        data={'timedelta_sec': 0},
    )


@slots_log_decorator
def slot19(name, end_time: float, request_id: str, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='info',
        subcomponent=name,
        message=f'[ {name}.EXECUTE ] {request_id} выполнен',
        event=f'engine.stop.execute',
        request_id=request_id,
        data={'timedelta_sec': end_time},
    )


@slots_log_decorator
def slot20(name, request_id: str, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='warning',
        subcomponent=name,
        message=f'[ {name}.PROCESS ] {request_id} отменен (task.cancel)',
        event=f'engine.process.interrupted.cancel',
        request_id=request_id,
    )


@slots_log_decorator
def slot21(name, request_id: str, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='warning',
        subcomponent=name,
        message=f'[ {name}.EXECUTE ] {request_id} отменен (task.cancel)',
        event=f'engine.execute.interrupted',
        request_id=request_id,
    )


@slots_log_decorator
def slot22(name, request_id: str, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='warning',
        subcomponent=name,
        message=f'[ {name}.PROCESS ] {request_id} истек и удален',
        event=f'engine.engine.process.cleanup',
        request_id=request_id,
    )


@slots_log_decorator
def slot23(name, request_id: str, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='warning',
        subcomponent=name,
        message=f'[ {name}.PROCESS ] `{request_id}` отменен',
        event=f'engine.process.interrupted.cancel',
        request_id=request_id,
    )


@slots_log_decorator
def slot24(name: str, request_id: str, end_time: float, *args, **kwargs):
    """stream stop, остановка движка"""
    _ = args, kwargs
    return Parameters(
        level='info',
        subcomponent=name,
        message=f'[ {name}.STREAMING ] `{request_id}` отменен (task.cancel)',
        event=f'engine.streaming.canceled',
        request_id=request_id,
        data={'timedelta_sec': end_time},
    )


@slots_log_decorator
def slot25(name: str, timeout: float, *args, **kwargs):
    """stream stop, остановка движка"""
    _ = args, kwargs
    return Parameters(
        level='warning',
        subcomponent=name,
        message=f'[ {name}.STREAMING ] не удалось отменить стриминги в заданный таймаут.',
        event=f'engine.streaming.canceled.error',
        data={'timeout': timeout}
    )


@slots_log_decorator
def slot26(name: str, request_id: float, *args, **kwargs):
    """Результат процесса получен"""
    _ = args, kwargs
    return Parameters(
        level='info',
        subcomponent=name,
        message=f'[ {name}.PROCESS ] {request_id} получен результат.',
        event=f'engine.process.get_result',
    )
