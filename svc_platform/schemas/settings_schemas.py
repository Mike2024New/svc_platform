from pydantic import BaseModel
from typing import TypeVar


# расширяемая модель настроек
class BaseSettings(BaseModel):
    name: str = '<unnamed>'


SettingsSchemaType = TypeVar('SettingsSchemaType', bound=BaseSettings)


# расширенная схема (для примера)
class SettingsExample(BaseSettings):
    samplerate: int = 16000
