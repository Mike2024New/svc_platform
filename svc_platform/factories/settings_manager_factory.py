from typing import Any
from typing import TypeVar
from pathlib import Path
from infrastructure_path_utils import get_root_dir_path
from infrastructure_settings_manager import get_settings_manager
from svc_platform.schemas import BaseSettings

__all__ = ['settings_manager_factory']

SettingsSchema = TypeVar('SettingsSchema', bound=BaseSettings)


def settings_manager_factory(
        settings_model: SettingsSchema,
        json_file_path: Path | None = None,
) -> tuple[SettingsSchema, Any]:
    """
    Возвращает объект с настройками settings, и управление настройками
    :param settings_model: Экземпляр класса pydantic модели (Настройки приложения)
    :param json_file_path: путь куда сохраняются настройки из схемы, например /root/settings.json (по умолчанию будут сохранены в корень проекта)
    :return: схема с настройками, управление схемой настроек (можно менять их через apply)
    """
    json_file_path = json_file_path or get_root_dir_path() / 'settings.json'

    settings_manager = get_settings_manager(
        json_file_path=json_file_path,
        settings_model=settings_model,
    )
    settings = settings_manager.settings
    return settings, settings_manager
