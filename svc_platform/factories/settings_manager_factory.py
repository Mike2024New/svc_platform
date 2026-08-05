from typing import Any
from typing import TypeVar
from pydantic import BaseModel
from infrastructure_path_utils import get_root_dir_path
from infrastructure_settings_manager import get_settings_manager

__all__ = ['settings_manager_factory']

SettingsSchema = TypeVar('SettingsSchema', bound=BaseModel)


def settings_manager_factory(
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


if __name__ == '__main__':
    from svc_platform.schemas import SettingsExample

    settings_manager_factory(settings_model=SettingsExample(name='main'))
