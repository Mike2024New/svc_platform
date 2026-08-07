from infrastructure_server import server_factory_v2


def server_factory(settings, api_modul, middleware_err_enable: bool = True):
    """

    :param settings:
    :param api_modul:
    :param middleware_err_enable: проглатывать системные ошибки и не возбуждать исключения в консоли?
    :return:
    """
    server = server_factory_v2(
        app_name=settings.name,
        # включение системных API:
        api_shudtown=True,
        api_pid=True,
        # подключение роутеров приложения:
        routers_list=api_modul.routers_list,
        # функции start/start_err/stop сервер (логирование):
        callback_start=api_modul.callback_start,
        callback_start_error=api_modul.callback_start_error,
        # lifespan (явная остановка компонентов)
        lifespan=api_modul.lifespan,
        middleware_err_enable=middleware_err_enable,
        exception_handlers=api_modul.exception_handlers,  # подключение кастомных обработчиков ошибок
        # middlewares_list=api_modul.middlewares_list,
    )
    return server
