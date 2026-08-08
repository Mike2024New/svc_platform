from pydantic import BaseModel, Field
from typing import TypeVar


# расширяемая модель настроек
class BaseSettings(BaseModel):
    name: str = 'unnamed'
    execute_limit: int = Field(
        default=1,
        description='Максимальное количество execute одновременно (защита от перегрузки).'
    )
    process_limit: int = Field(
        default=1,
        description='Максимальное количество process одновременно (защита от перегрузки).'
    )
    process_result_ttl: float = Field(
        default=300,
        description='Время хранения результата после вычисления (в секундах), после задача и результат удалятся (защита от перегрузки).'
    )


SettingsSchemaType = TypeVar('SettingsSchemaType', bound=BaseSettings)


# расширенная схема (для примера)
class SettingsExample(BaseSettings):
    samplerate: int = 16000
