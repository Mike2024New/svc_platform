from infrastructure_settings_manager import get_settings_manager
from svc_platform.factories.schemas import SchemaSettings
from pathlib import Path

__all__ = ['settings_manager_factory']


def settings_manager_factory(json_file_path: Path):
    """Возвращает объект с настройками settings, и управление настройками"""
    settings_manager = get_settings_manager(
        json_file_path=json_file_path,
        settings_model=SchemaSettings(),
    )
    settings = settings_manager.settings
    return settings, settings_manager
