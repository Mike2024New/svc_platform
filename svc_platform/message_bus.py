from svc_platform.factories import message_bus_add_factory
from svc_platform.schemas import BaseSettings
from svc_platform.factories import settings_manager_factory
from infrastructure_path_utils import get_root_dir_path

__all__ = ['message_bus_add', 'message_bus_settings']

settings, settings_manager = settings_manager_factory(settings_model=BaseSettings(name='demo_svc'))

logs_file_path = get_root_dir_path() / 'logs' / 'log.jsonl'

message_bus_add, message_bus_settings = message_bus_add_factory(
    settings=settings,
    logs_file_path=logs_file_path,
)
