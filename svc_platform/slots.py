from typing import Any

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
    print(f'{name}.engine.start')  # залогировать параметры при старте


def slot2(name: str, parameters: dict[str, Any], *args, **kwargs):
    """Остановка движка (engine.started)"""
    _ = args, kwargs, parameters
    print(f'{name}.engine.stop')  # залогировать параметры при старте


def slot3(name: str, err: Exception, *args, **kwargs):
    """Ошибка запуска движка"""
    _ = args, kwargs
    print(f'{name}.engine.start error -> {err}')


def slot4(name: str, err: Exception, *args, **kwargs):
    """Ошибка остановки движка"""
    _ = args, kwargs
    print(f'{name}.engine.stop.error -> {err}')


def slot5(name: str, err: Exception, *args, **kwargs):
    """Ошибка процесса движка"""
    _ = args, kwargs
    print(f'{name}.engine.process.error -> {err}')


def slot6(name: str, err: Exception, *args, **kwargs):
    """Ошибка execute метода движка"""
    _ = args, kwargs
    print(f'{name}.engine.execute.error -> {err}')


def slot7(name: str, err: Exception, *args, **kwargs):
    """Ошибка stream метода движка"""
    _ = args, kwargs
    print(f'{name}.engine.stream.error -> {err}')


def slot8(name: str, *args, **kwargs):
    """stream start, начало стриминга"""
    _ = args, kwargs
    print(f'{name}.engine.stream.start')


def slot9(name: str, *args, **kwargs):
    """stream stop, остановка движка"""
    _ = args, kwargs
    print(f'{name}.engine.stream.stop')


def slot10(name: str, *args, **kwargs):
    """api.stream - клиент отключился"""
    _ = args, kwargs
    print(f'{name}.api.stream client disconnected')


def slot11(name: str, err: Exception, *args, **kwargs):
    """api.stream - ошибка соединение будет разорвано"""
    _ = args, kwargs
    print(f'{name}.api.stream.error disconnected, err -> {err}')


def slot12(name: str, *args, **kwargs):
    _ = args, kwargs
    print(f'{name}.api.is_component_running server is not started')


def slot13(name, data):
    print(f'{name}.server.start {data}')


def slot14(name):
    print(f'{name}.server.stop')


def slot15(name, error_data):
    print(f'{name}.server.sart.error -> {error_data}')
