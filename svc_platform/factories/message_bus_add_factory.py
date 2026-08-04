import uuid
from pathlib import Path
from infrastructure_message_bus import message_bus_factory, MessagePrintSettings, FileLogSettings

"""
Настройка шины сообщений компонента.
Логирование в файл. Печать в терминал.
Настройка просмотрщика логов.
"""


def message_bus_add_factory(
        settings,
        logs_file_path: Path,
):
    """

    :param settings: настройки приложения на базе схемы
    :param logs_file_path: путь к папке с логами
    :return:
    """
    message_bus_add, message_bus_settings = message_bus_factory(
        component_id=str(uuid.uuid4())[:8],
        component_name=settings.name,
        print_message=True,
        # подключение сообщений
        message_print_settings=MessagePrintSettings(
            print_date=True,  # печатать дату в сообщениях
            raw_message=False,  # сырая json строка
            ignore_levels=[],  # игнорировать уровни логирования
            ignore_levels_invers=False,  # инвертировать игнорирование уровней логирования
        ),
        # подключение логирования в файл
        file_log_json_path=logs_file_path,
        file_log_settings=FileLogSettings(
            max_files=10,
            max_size_mb=10,
            rotation_disable=False,  # отключить ротацию файлов
        )
    )
    return message_bus_add, message_bus_settings
