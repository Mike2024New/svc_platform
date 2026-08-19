from pydantic import BaseModel, Field
from typing import TypeVar
from infrastructure_path_utils import get_root_dir_path


# расширяемая модель настроек
class BaseSettings(BaseModel):
    name: str = get_root_dir_path().parts[-1]
    # настройки команд
    execute_limit: int = Field(default=3, description='Максимальное колличество команд выполняемых одновременно')
    execute_cancel_all_timeout: float = Field(default=10.0, description='Время на завершение команд если остановка')
    # настройки процесса
    process_limit: int = Field(default=3, description='Максимальное колличество процессов выполняемых одновременно')
    process_limit_max_result: int = Field(default=3, description='Не брать в работу процессы выше этого лимита')
    process_cancel_all_timeout: float = Field(default=10.0, description='Время на завершение процессов если остановка')
    process_cleanup_enable: bool = Field(default=True, description='Включить цикл удаления устаревших результатов')
    process_cleanup_interval: float = Field(default=1, description='Интервал просмотра устаревания выполненных задач')
    process_cleanup_result_ttl: float = Field(default=300, description='Время хранения результата (в секундах)')
    # настройки стриминга
    producer_stream_limit: int = Field(default=3, description='Максимальное колво стримингов выполняемых одновременно')
    producer_stream_cancel_all_timeout: float = Field(default=10.0, description='Время на завершение процессов (stop)')


SettingsSchemaType = TypeVar('SettingsSchemaType', bound=BaseSettings)


# расширенная схема (для примера)
class Settings(BaseSettings):
    pass
