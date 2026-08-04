import sys
from infrastructure_cli_utils import CliSettings, get_cli_app
from infrastructure_path_utils import get_root_dir_path


def cli_factory(
        cli_settings: CliSettings,
        build_settings=None,
        server=None,
        settings=None, settings_manager=None,
        log_viewer=None,
):
    """
    Фабрика сборщик для получения cli приложения
    :param log_viewer: просмотр логов (~logs_.jsonl)
    :param settings: настройки приложения
    :param settings_manager: управление настройками приложения (изменение через cli settings-edit)
    :param cli_settings: настройки включения/выключения методов
    :param build_settings: настройки сборщика exe (bin)
    :param server: настройка сервера (start, stop)
    :return: app - объект для запуска cli меню -> app()
    """
    # управление включением системных CLI команд:
    # создание cli интерфейса с пробросом необходимых настроек
    app = get_cli_app(
        name=settings.name,
        root_dir=get_root_dir_path(),
        exe_mode=getattr(sys, 'frozen', False),
        build_settings=build_settings,
        cli_settings=cli_settings,
        settings=settings,
        settings_manager=settings_manager,
        server=server,
        log_viewer=log_viewer,
    )
    return app
