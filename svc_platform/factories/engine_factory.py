from typing import TypeVar
from svc_platform.schemas import BaseSettings
from svc_platform.engine import Engine

__all__ = ['engine_factory']

EngineType = TypeVar('EngineType', bound=Engine)
SettingsSchema = TypeVar('SettingsSchema', bound=BaseSettings)


def engine_factory(engine_class: type[EngineType], settings: SettingsSchema) -> EngineType:
    """
    расширяемая фабрика приложения
    :param engine_class: класс на базе которого будет создан engine (Классы наследники Engine)
    :param settings: настройки
    :return: экземпляр движка для запуска
    """
    return engine_class(settings)


if __name__ == '__main__':
    """Пример, запуск и создание движка"""
    engine = engine_factory(engine_class=Engine, settings=BaseSettings())
    engine.start()
    engine.stop()
