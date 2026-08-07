import uuid
from pathlib import Path
from typing import Literal
from infrastructure_path_utils import get_root_dir_path
from infrastructure_message_bus import message_bus_factory as message_bus
from infrastructure_message_bus import MessagePrintSettings, FileLogSettings
from svc_platform.schemas import SettingsSchemaType

__all__ = ['message_bus_factory']


def message_bus_factory(
        settings: SettingsSchemaType,
        file_log_json_path: Path | None = None,
        print_message: bool = True,
        print_message_date: bool = True,
        raw_message: bool = False,
        ignore_levels: list[Literal[
            'debug', 'info', 'warning', 'error', 'critical', 'start', 'stop', 'process',]] = None,
        ignore_levels_invers: bool = False,
        rotate_max_files: int = 10,
        rotate_max_size_mb: int = 10,
):
    """
    :param settings: схема модели с настройками
    :param file_log_json_path: желаемый путь к логам с названием файла, по умолчанию /<root_dir>/logs/log.jsonl
    :param print_message: печатать сообщения в консоль? (не отменяет логирования в файл)
    :param print_message_date: печатать дату в сообщении в консоли (занимает место на экране)?
    :param raw_message: печатать сырую строку с данными в сообщениях (вместо человекочитаемых)?
    :param ignore_levels_invers: инвертировать список игнорирования уровней шины сообщений
    :param ignore_levels: игнорировать конкретные уровни шины сообщений (при печати в консоль)?
    :param rotate_max_files: ротация логов максимальное количество файлов
    :param rotate_max_size_mb: ротация логов максимальный размер одного файла
    :return Шина сообщений и объект управления некоторыми параметрами (например определить имя компонента или trace_id)
    """
    component_name = settings.name

    file_log_json_path = file_log_json_path or get_root_dir_path() / 'logs' / 'log.jsonl'
    file_log_json_path.parent.mkdir(exist_ok=True, parents=True)

    message_bus_add, message_bus_settings = message_bus(
        component_id=str(uuid.uuid4())[:8],
        component_name=component_name,
        print_message=print_message,
        # подключение сообщений
        message_print_settings=MessagePrintSettings(
            print_date=print_message_date,  # печатать дату в сообщениях
            raw_message=raw_message,  # сырая json строка
            ignore_levels=ignore_levels or [],  # игнорировать уровни логирования
            ignore_levels_invers=ignore_levels_invers,  # инвертировать игнорирование уровней логирования
        ),
        # подключение логирования в файл
        file_log_json_path=file_log_json_path,
        file_log_settings=FileLogSettings(
            max_files=rotate_max_files,
            max_size_mb=rotate_max_size_mb,
            rotation_disable=False,  # отключить ротацию файлов
        )
    )
    return message_bus_add, message_bus_settings
