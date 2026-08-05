import uuid
from typing import Any
from typing import TypeVar
from pydantic import BaseModel
from infrastructure_path_utils import get_root_dir_path
from infrastructure_settings_manager import get_settings_manager
from infrastructure_message_bus import message_bus_factory, MessagePrintSettings, FileLogSettings
from svc_platform.schemas import settings_model

__all__ = ['settings_manager_singleton']

SettingsSchema = TypeVar('SettingsSchema', bound=BaseModel)


def settings_manager_singleton(
        settings_model: SettingsSchema
) -> tuple[SettingsSchema, Any]:
    """
    Возвращает объект с настройками settings, и управление настройками
    :param settings_model: Экземпляр класса pydantic модели
    :return:
    """
    json_file_path = get_root_dir_path()

    settings_manager = get_settings_manager(
        json_file_path=json_file_path / 'settings.json',
        settings_model=settings_model,
    )
    settings = settings_manager.settings
    return settings, settings_manager


def get_message_bus(settings):
    # настройки оптимальны, при необходимости можно будет вынести в параметры
    component_name = settings.name
    file_log_json_path = get_root_dir_path() / 'logs' / 'log.jsonl'
    file_log_json_path.parent.mkdir(exist_ok=True, parents=True)

    message_bus_add, message_bus_settings = message_bus_factory(
        component_id=str(uuid.uuid4())[:8],
        component_name=component_name,
        print_message=True,
        # подключение сообщений
        message_print_settings=MessagePrintSettings(
            print_date=True,  # печатать дату в сообщениях
            raw_message=False,  # сырая json строка
            ignore_levels=[],  # игнорировать уровни логирования
            ignore_levels_invers=False,  # инвертировать игнорирование уровней логирования
        ),
        # подключение логирования в файл
        file_log_json_path=file_log_json_path,
        file_log_settings=FileLogSettings(
            max_files=10,
            max_size_mb=10,
            rotation_disable=False,  # отключить ротацию файлов
        )
    )
    return message_bus_add, message_bus_settings


settings, settings_manager = settings_manager_singleton(settings_model=settings_model)
message_bus_add, message_bus_settings = get_message_bus(settings=settings)
