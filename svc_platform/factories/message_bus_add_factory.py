import uuid
from pathlib import Path
from infrastructure_message_bus import message_bus_factory, MessagePrintSettings, FileLogSettings
from typing import Literal

"""
Настройка шины сообщений компонента.
Логирование в файл. Печать в терминал.
Настройка просмотрщика логов.
"""


def message_bus_add_factory(
        settings,
        logs_file_path: Path,
        raw_message: bool = False,
        max_files: int = 10,
        max_size_mb: int = 10,
        ignore_levels: list[Literal[
            'debug', 'info', 'warning', 'error', 'critical', 'start', 'stop', 'process',]] | None = None,
        ignore_levels_invers: bool = False,
):
    """

    :param ignore_levels_invers:
    :param ignore_levels:
    :param settings: настройки приложения на базе схемы
    :param logs_file_path: путь к папке с логами
    :param raw_message: печатать сообщение в терминал в виде сырой json строки
    :param max_size_mb: ротация логов, максимальный размер файла
    :param max_files: ротация логов, максимальное количество файлов
    :return:
    """
    # создание папки с логами
    logs_file_path.parent.mkdir(exist_ok=True, parents=True)
    message_bus_add, message_bus_settings = message_bus_factory(
        component_id=str(uuid.uuid4())[:8],
        component_name=settings.name,
        print_message=True,
        # подключение сообщений
        message_print_settings=MessagePrintSettings(
            print_date=True,  # печатать дату в сообщениях
            raw_message=raw_message,  # сырая json строка
            ignore_levels=ignore_levels,  # игнорировать уровни логирования
            ignore_levels_invers=ignore_levels_invers,  # инвертировать игнорирование уровней логирования
        ),
        # подключение логирования в файл
        file_log_json_path=logs_file_path,
        file_log_settings=FileLogSettings(
            max_files=max_files,
            max_size_mb=max_size_mb,
            rotation_disable=False,  # отключить ротацию файлов
        )
    )
    return message_bus_add, message_bus_settings
