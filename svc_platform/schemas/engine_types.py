from svc_platform.schemas import EngineIOSchemas, BaseSettings, Settings, Parameters
from typing import TypeVar

# =============== ДЖЕНЕРИКИ ТИПОВ ===============
# TypeVar с bound задает "верхнюю границу" — тип-ограничение.
# В дочерних проектах нужно переопределить эти TypeVar,
# подставив свои модели-наследники из EngineIOSchemas и также переопределив BaseSettings.
#
# Это позволяет:
# 1. IDE видеть точные типы (автокомплит полей voice, speed и т.д.)
# 2. Pydantic валидировать данные по расширенным схемам
# 3. Сохранить типобезопасность на всех уровнях
#
# Механизм: TypeVar → Generic → наследование с типами
# Чтобы не забыть это всё и не мучиться с этим каждый раз, лучше сделать репозиторий копируемый шаблон где это всё сделано
# ====================================================
BaseSettingsType = TypeVar('BaseSettingsType', bound=BaseSettings)
ParametersType = TypeVar('ParametersType', bound=Parameters)
SettingsType = TypeVar('SettingsType', bound=Settings)
ProcessInputDataType = TypeVar('ProcessInputDataType', bound=EngineIOSchemas.process_input_data)
ProcessOutputDataType = TypeVar('ProcessOutputDataType', bound=EngineIOSchemas.process_output_data)
ExecuteInputDataType = TypeVar('ExecuteInputDataType', bound=EngineIOSchemas.execute_input_data)
StreamInputDataType = TypeVar('StreamInputDataType', bound=EngineIOSchemas.streaming_input_data)
StreamOutputDataType = TypeVar('StreamOutputDataType', bound=EngineIOSchemas.streaming_output_data)
