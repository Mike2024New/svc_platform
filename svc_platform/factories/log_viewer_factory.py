from pathlib import Path
from infrastructure_path_utils import get_root_dir_path
from infrastructure_message_bus import LogViewer, LogViewerConfig, Filters

"""
Простой просмотрщик логов. ( `python cli.py log` )
"""


def log_viewer_factory(
        root_dir: Path | None = None,
        only_keys: list[Filters] | None = None,
        separator: str = '     ',
        exclude_dirs: list[str] | None = None,
):
    """

    :param separator: разделитель столбцов
    :param root_dir: корневая папка проекта (стартовая папка поиска логов)
    :param only_keys: порядок ключей (искать только ключи)
    :param exclude_dirs: папки в которых не нужно смотреть логи, по умолчанию отключена папка releases (куда собираются приложения)
    """
    if only_keys is None:
        f = Filters()
        only_keys = [f.component, f.level, f.event, f.trace_id, f.date, f.request_id, ]

    root_dir = root_dir or get_root_dir_path()

    exclude_dirs = exclude_dirs or ['releases', '.venv']

    log_viewer_cfg = LogViewerConfig(
        root_path=root_dir,
        only_keys=only_keys,
        separator=separator,
    )
    # исключить папки с релизами (чтобы логи не пересекались)
    log_viewer_cfg.exclude_dirs += exclude_dirs
    log_viewer = LogViewer(config=log_viewer_cfg)
    return log_viewer
