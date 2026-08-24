from infrastructure_cli_utils import CliSettings
from infrastructure_path_utils import get_root_dir_path
from infrastructure_builder import BuildParameters
from svc_platform.factories import cli_factory, server_factory, api_factory, engine_factory, log_viewer_factory
from svc_platform.engine import Engine
from svc_platform.slots_manager import slots_init
from svc_platform.slots_manager.handlers import handler_message_bus_log_factory

"""
Пример сборки cli приложения
Базовая сборка cli.py по умолчанию. Централизованная точка сборки.
(Именно это нужно будет сделать в сервисах которые будут построены на базе этого репозитория - там это распределить по файлам)
"""
from svc_platform.factories.message_bus_factory import message_bus_factory
from svc_platform.factories.settings_manager_factory import settings_manager_factory
from svc_platform.schemas import Settings, EngineIOSchemas

# единая точка сборки приложения (созданные объекты можно переопределять как угодно)
# получение настроек (из схемы Settings)
settings, settings_manager = settings_manager_factory(settings_model=Settings(), reset_json=True)
# получение шины сообщений
message_bus_add, message_bus_settings = message_bus_factory(settings=settings)
# получение engine
engine = engine_factory(engine_class=Engine, settings=settings)

from svc_platform.api.routers import routers_factory

# подключение стандартных системных роутеров
standard_routers_list = routers_factory(
    engine=engine,
    settings=settings,
    engine_io_schemas=EngineIOSchemas(),
    include_start_router=True,
    include_end_router=True,
)

# настройка api
api_modul = api_factory(
    engine=engine,
    settings=settings,
    standard_routers_list=standard_routers_list,
)
# настройка сервера
server = server_factory(
    settings=settings,
    api_modul=api_modul,
    middleware_err_enable=True,
    routers_list=[]
)

# настройка логирования
slots_init(
    enable=True,
    handlers_list=[handler_message_bus_log_factory(message_bus_add)],
    # show_only_slots=[13, 14],
    # show_only_slots_inverse=True,
)

# настройки отображения cli.py команд
cli_settings = CliSettings(
    enable_run_server=True,
    enable_settings_show=True,
    enable_settings_edit=True,
    enable_folder_command=True,
    enable_git_push=True,
    enable_register_sync=True,
    enable_build_command=True,
    enable_run_test=True,
    # enable_run_command=True, # для интерактива
    enable_log_viewer=True,
)
# настройка сборки приложения (bin/exe)
build_settings = BuildParameters(
    name=settings.name,
    entry_point_path=get_root_dir_path() / 'cli.py',  # заменить на cli.py
    open_folder=False,
    clear_old_distributive=True,
    venv_dir_name='.venv',
    console=True,
    add_data=[],
    add_binary=[],
    excluded=[],
    hidden_imports=[],
    copy_dirs=[],
)

if __name__ == '__main__':
    app = cli_factory(
        server=server,
        cli_settings=cli_settings,
        settings=settings,
        settings_manager=settings_manager,
        build_settings=build_settings,
        trace_id_callback=lambda trace_id: message_bus_settings.set_trace_id(trace_id=trace_id),
        log_viewer=log_viewer_factory(),
    )
    app()
