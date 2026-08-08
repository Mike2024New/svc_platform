from infrastructure_server import server_factory_v2, ServerV2
from fastapi import APIRouter
from svc_platform.factories.api_factory import ApiFactoryResult
from svc_platform.schemas import SettingsSchemaType


def server_factory(
        settings: SettingsSchemaType,
        api_modul: ApiFactoryResult,
        routers_list: list[APIRouter] | None = None, middleware_err_enable: bool = True
) -> ServerV2:
    """

    :param routers_list:  кастомные роутеры (расширение стандартных роутеров, например для БД сервисов)
    :param settings: схема настроек
    :param api_modul: базовый роутер (стандартные эндпоинты ApiFactoryResult - логика определия /start/ /stop/ /process/ и т.д.)
    :param middleware_err_enable: проглатывать системные ошибки и не возбуждать исключения в консоли?
    :return:
    """
    routers_list = routers_list or []
    routers_list = api_modul.routers_list + routers_list
    server = server_factory_v2(
        app_name=settings.name,
        # включение системных API:
        api_shudtown=True,
        api_pid=True,
        # подключение роутеров приложения:
        routers_list=routers_list,
        # функции start/start_err/stop сервер (логирование):
        callback_start=api_modul.callback_start,
        callback_start_error=api_modul.callback_start_error,
        callback_end=api_modul.callback_end,
        # lifespan (явная остановка компонентов)
        lifespan=api_modul.lifespan,
        middleware_err_enable=middleware_err_enable,
        exception_handlers=api_modul.exception_handlers_class(),  # подключение кастомных обработчиков ошибок
        middlewares_list=api_modul.middlewares_list,
    )
    return server
