from typing import TypeVar
from svc_platform.schemas import engine_types as e_types
from svc_platform.engine import Engine

__all__ = ['engine_factory']

EngineType = TypeVar('EngineType', bound=Engine)


def engine_factory(
        engine_class: type[EngineType], settings: e_types.SettingsType
) -> EngineType:
    """
    расширяемая фабрика приложения
    :param engine_class: класс на базе которого будет создан engine (Классы наследники Engine)
    :param settings: настройки
    :return: экземпляр движка для запуска
    """
    return engine_class(settings)
