import os
from typing import Any
from pathlib import Path
from infrastructure_path_utils import get_root_dir_path
from infrastructure_settings_manager import get_settings_manager
from svc_platform.schemas import SettingsSchemaType

__all__ = ['settings_manager_factory']


def settings_manager_factory(
        settings_model: SettingsSchemaType,
        json_file_path: Path | None = None,
        reset_json: bool = False,
) -> tuple[SettingsSchemaType, Any]:
    """
    Возвращает объект с настройками settings, и управление настройками
    :param reset_json: перезаписать settings.json (для обновления моделей)?
    :param settings_model: Экземпляр класса pydantic модели (Настройки приложения)
    :param json_file_path: путь куда сохраняются настройки из схемы, например /root/settings.json (по умолчанию будут сохранены в корень проекта)
    :return: схема с настройками, управление схемой настроек (можно менять их через apply)
    """
    json_file_path = json_file_path or get_root_dir_path() / 'settings.json'

    # сброс старого json
    if reset_json and json_file_path.exists():
        os.remove(json_file_path)

    settings_manager = get_settings_manager(
        json_file_path=json_file_path,
        settings_model=settings_model,
    )
    settings = settings_manager.settings
    return settings, settings_manager
