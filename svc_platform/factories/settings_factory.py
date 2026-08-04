from infrastructure_path_utils import get_root_dir_path
from infrastructure_settings_manager import get_settings_manager
from pathlib import Path
from typing import TypeVar
from pydantic import BaseModel

__all__ = ['settings_manager_factory']
T = TypeVar('T', bound=BaseModel)

from typing import Any


def settings_manager_factory(settings_model: T, json_file_path: Path | None = None) -> tuple[T, Any]:
    """
    Возвращает объект с настройками settings, и управление настройками
    :param settings_model: Экземпляр класса pydantic модели
    :param json_file_path: путь к файлу с настройками (Если не передан, то будет создан в корне settings.json)
    :return:
    """

    if json_file_path is None:
        json_file_path = get_root_dir_path()

    settings_manager = get_settings_manager(
        json_file_path=json_file_path / 'settings.json',
        settings_model=settings_model,
    )
    settings = settings_manager.settings
    return settings, settings_manager
