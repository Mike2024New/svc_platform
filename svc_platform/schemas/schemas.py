from pydantic import BaseModel


# расширяемая модель настроек
class BaseSettings(BaseModel):
    name: str = '<unnamed>'


# расширенная схема (для примера)
class SettingsExample(BaseSettings):
    samplerate: int = 16000
