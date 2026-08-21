from svc_platform.slots_manager.core.main import slots_decorator, Parameters
from typing import Any


@slots_decorator(core=True)
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


@slots_decorator(core=True)
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


@slots_decorator(core=True)
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


@slots_decorator(core=True)
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


@slots_decorator(core=True)
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


@slots_decorator(core=True)
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


@slots_decorator(core=True)
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


@slots_decorator(core=True)
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


@slots_decorator(core=True)
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


@slots_decorator(core=True)
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


@slots_decorator(core=True)
def slot12(name: str, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='warning',
        subcomponent=name,
        message=f'[ {name}.ENGINE ] движок не запущен, нужно запустить его через start ',
        event=f'server is not started',
    )


@slots_decorator(core=True)
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


@slots_decorator(core=True)
def slot14(name, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='stop',
        subcomponent=name,
        message=f'[ {name}.SERVER ] сервер остановлен',
        event=f'server stop',
    )


@slots_decorator(core=True)
def slot15(name, err, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='error',
        subcomponent=name,
        message=f'[ {name}.server ] ошибка запуска сервера:{err}',
        event=f'engine.server.error',
        error=err,
    )


@slots_decorator(core=True)
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


@slots_decorator(core=True)
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


@slots_decorator(core=True)
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


@slots_decorator(core=True)
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


@slots_decorator(core=True)
def slot20(name, request_id: str, end_time: float, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='warning',
        subcomponent=name,
        message=f'[ {name}.PROCESS ] {request_id} отменен (task.cancel)',
        event=f'engine.process.interrupted.cancel',
        request_id=request_id,
        data={'timedelta_sec': end_time},
    )


@slots_decorator(core=True)
def slot21(name, request_id: str, end_time: float, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='warning',
        subcomponent=name,
        message=f'[ {name}.EXECUTE ] {request_id} отменен (task.cancel)',
        event=f'engine.execute.interrupted',
        request_id=request_id,
        data={'timedelta_sec': end_time},
    )


@slots_decorator(core=True)
def slot22(name, request_id: str, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='warning',
        subcomponent=name,
        message=f'[ {name}.PROCESS ] {request_id} истек и удален',
        event=f'engine.engine.process.cleanup',
        request_id=request_id,
    )


@slots_decorator(core=True)
def slot23(name, request_id: str, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='warning',
        subcomponent=name,
        message=f'[ {name}.PROCESS ] `{request_id}` отменен',
        event=f'engine.process.interrupted.cancel',
        request_id=request_id,
    )


@slots_decorator(core=True)
def slot24(name: str, request_id: str, end_time: float, *args, **kwargs):
    """stream stop, остановка движка"""
    _ = args, kwargs
    return Parameters(
        level='info',
        subcomponent=name,
        message=f'[ {name}.STREAMING ] `{request_id}` остановлен',
        event=f'engine.streaming.canceled',
        request_id=request_id,
        data={'timedelta_sec': end_time},
    )


@slots_decorator(core=True)
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


@slots_decorator(core=True)
def slot26(name: str, request_id: float, *args, **kwargs):
    """Результат процесса получен"""
    _ = args, kwargs
    return Parameters(
        level='info',
        subcomponent=name,
        message=f'[ {name}.PROCESS ] {request_id} получен результат.',
        event=f'engine.process.get_result',
    )


@slots_decorator(core=True)
def slot27(name: str, request_id: str, end_time: float, *args, **kwargs):
    """execute , принудительная остановка команды"""
    _ = args, kwargs
    return Parameters(
        level='info',
        subcomponent=name,
        message=f'[ {name}.EXECUTE ] `{request_id}` отменен (task.cancel)',
        event=f'engine.execute.canceled',
        request_id=request_id,
        data={'timedelta_sec': end_time},
    )


@slots_decorator(core=True)
def slot28(name: str, request_id: str, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='warning',
        subcomponent=name,
        message=f'[ {name}.EXECUTE ] {request_id} не запущен, так как не запущен движок. ',
        event=f'engine.execute.not_started',
    )


@slots_decorator(core=True)
def slot29(name, request_id: str, end_time: float, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='warning',
        subcomponent=name,
        message=f'[ {name}.PROCESS ] {request_id} остановлен',
        event=f'engine.process.interrupted.stop',
        request_id=request_id,
        data={'timedelta_sec': end_time},
    )


@slots_decorator(core=True)
def slot30(name: str, request_id: str, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='warning',
        subcomponent=name,
        message=f'[ {name}.PROCESS ] {request_id} не запущен, так как не запущен движок. ',
        event=f'engine.process.not_started',
    )


@slots_decorator(core=True)
def slot31(name: str, request_id: str, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='warning',
        subcomponent=name,
        message=f'[ {name}.STREAM ] {request_id} не запущен, так как не запущен движок. ',
        event=f'engine.stream.not_started',
    )


@slots_decorator(core=True)
def slot32(name: str, request_id: str, *args, **kwargs):
    _ = args, kwargs
    return Parameters(
        level='warning',
        subcomponent=name,
        message=f'[ {name}.PROCESS ] {request_id} не запущен, переполнен process storage. ',
        event=f'engine.process.storage_overflow',
    )
