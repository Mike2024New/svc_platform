from pydantic import BaseModel, Field
from infrastructure_path_utils import get_root_dir_path


# Базовые (системные параметры engine)
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
    stream_limit: int = Field(default=3, description='Максимальное колво стримингов выполняемых одновременно')
    stream_cancel_all_timeout: float = Field(default=10.0, description='Время на завершение процессов (stop)')


# класс с специальными параметрами, например samplerate для audio_input, или silero, при выборе голосовой модели
class Parameters(BaseModel):
    samplerate: int = 16000


# сборка системных настроек и специальных параметров
class Settings(BaseSettings):
    parameters: Parameters = Field(default=Parameters())
