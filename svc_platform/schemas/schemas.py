from pydantic import BaseModel


# расширяемая модель настроек
class BaseSettings(BaseModel):
    name: str


# расширенная схема (для примера)
class SettingsExample(BaseSettings):
    samplerate: int = 16000


settings_model = SettingsExample(name='svc_platform')
