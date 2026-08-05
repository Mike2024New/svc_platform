import uuid
from infrastructure_path_utils import get_root_dir_path
from infrastructure_message_bus import message_bus_factory as message_bus
from infrastructure_message_bus import MessagePrintSettings, FileLogSettings


def message_bus_factory(settings):
    # настройки оптимальны, при необходимости можно будет вынести в параметры
    component_name = settings.name
    file_log_json_path = get_root_dir_path() / 'logs' / 'log.jsonl'
    file_log_json_path.parent.mkdir(exist_ok=True, parents=True)

    message_bus_add, message_bus_settings = message_bus(
        component_id=str(uuid.uuid4())[:8],
        component_name=component_name,
        print_message=True,
        # подключение сообщений
        message_print_settings=MessagePrintSettings(
            print_date=True,  # печатать дату в сообщениях
            raw_message=False,  # сырая json строка
            ignore_levels=[],  # игнорировать уровни логирования
            ignore_levels_invers=False,  # инвертировать игнорирование уровней логирования
        ),
        # подключение логирования в файл
        file_log_json_path=file_log_json_path,
        file_log_settings=FileLogSettings(
            max_files=10,
            max_size_mb=10,
            rotation_disable=False,  # отключить ротацию файлов
        )
    )
    return message_bus_add, message_bus_settings
