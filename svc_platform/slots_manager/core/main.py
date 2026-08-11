import re
import threading
from typing import Any
from functools import wraps
from warnings import warn
from typing import Callable
from dataclasses import dataclass
from typing import Literal
from queue import Queue, Empty

__all__ = ['Parameters', 'slots_init', 'slots_decorator']


@dataclass
class Parameters:
    level: Literal['debug', 'info', 'warning', 'error', 'critical', 'start', 'stop', 'process']
    subcomponent: str
    message: str
    event: str
    request_id: str | None = None
    data: dict | None = None
    error: Exception | None = None
    slot_name: str | None = None


_queue: Queue = Queue()
_init: bool = False
_enable: bool = False
_handlers_list: list[Callable[[Parameters], None]] = []
_show_only_slots: list[int] = []
_show_only_slots_inverse: bool = False
_stop = threading.Event()
_worker_stop = threading.Event()


def worker():
    while not _worker_stop.is_set():
        try:
            parameters: Parameters = _queue.get(timeout=1)
            for callback in _handlers_list:
                try:
                    callback(parameters)
                except Exception as handler_err:
                    warn(f'Слот {parameters.slot_name}. Ошибка в обработчике слотов: {handler_err}')
        except Empty:
            pass
        except Exception as err:
            warn(f'Ошибка при обработке слотов: {err}')


def slots_init(
        enable: bool = True,
        handlers_list: list[Callable[[Parameters], None]] = None,
        show_only_slots: list[int] | None = None,
        show_only_slots_inverse: bool = False,
):
    """
    Активация модуля slots (функции обработчика событий)
    :param enable: on/off
    :param handlers_list: список обработчиков, см. подробнее в svc_platform.slots_manager.handlers
    :param show_only_slots: показывать только конкретные слоты (может быть удобно для отслеживания конкретных)
    :param show_only_slots_inverse: инвертировать show_only_slots - будет игнорировать указанные слоты
    :return: None
    """
    global _enable, _handlers_list, _init, _show_only_slots, _show_only_slots_inverse
    if enable:
        _init = True
        _enable = enable
        _handlers_list = handlers_list or []
        _show_only_slots = show_only_slots or []
        _show_only_slots_inverse = show_only_slots_inverse
        threading.Thread(target=worker, daemon=True).start()  # запуск очереди обработки слотов в отдельном потоке


def slots_decorator(core: bool = False):
    """
    Проброс слотов в slots_manager (передает туда Parameters, вместе с slot_name).
    Дальше в slots_manager назначаются функции обработки событий, например логирование.
    Защита от неисправностей в самих слотах, чтобы приложение не падало из-за ошибок в реализации слотов
    :param core: является ли данный слот ядром (svc_platform) - для svc_platform да, для проектов наследников нет.
    """

    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            if not _init:
                warn('не инициализирован slots_manager, обработчик событий не подключен.')
            slot_name = f'{"core." if core else "svc."}{func.__name__}'

            # фильтрация слотов (если список _show_only_slots не пустой)
            if _show_only_slots:
                """Пропуск слотов кроме избранных"""
                match = re.search(r'slot(\d{1,6})', slot_name)
                if match is None:
                    warn(message=f'Не корректное название функции слота `{slot_name}`, правильный формат `slot0`')
                    return

                slot_number = int(match.group(1))
                if not _show_only_slots_inverse:
                    if slot_number not in _show_only_slots:
                        return
                else:
                    if slot_number in _show_only_slots:
                        return

            # применение callback функций
            try:
                parameters: Parameters = func(*args, **kwargs)
                parameters.slot_name = slot_name

                def handler_execute():
                    if _enable:
                        _queue.put(parameters)

                # запуск обработчиков в отдельном потоке, чтобы не замедлялся основной процесс (в перспективе рассмотреть подход с очередью)
                threading.Thread(target=handler_execute, daemon=True).start()

            except Exception as err:
                print(err)
                warn(message=f'Не удалось обработать slots.{slot_name}, причина: {err}')

        return inner

    return decorator


if __name__ == '__main__':
    """Пример использования"""


    # создается функция слот (к которой обращается приложение) ! к каждому слоту допускается только 1 обращение
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


    # инициализируется слот менеджер с передачей колбеков, через enable можно отключить весь slots
    slots_init(enable=True, handlers_list=[lambda parameters: print(parameters)])
    # обращение к слот функции
    slot1(name='app', parameters={'key': 'val'})
