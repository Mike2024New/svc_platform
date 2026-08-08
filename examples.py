import threading
from svc_platform.factories import engine_factory, api_factory, server_factory
from svc_platform.factories.message_bus_factory import message_bus_factory
from svc_platform.factories.settings_manager_factory import settings_manager_factory
from svc_platform.schemas import SettingsExample
from svc_platform.slots import slots_init
from svc_platform.schemas import EngineIOSchemas
from svc_platform.engine import Engine
import uuid


def example1():
    """
    Подъём и остановка сервера с сборкой настроек. Без cli.py, просто как отдельный скрипт (например для тестирования)
    """
    # получить настройки (на базе schemas.BaseSettings)
    settings, settings_manager = settings_manager_factory(settings_model=SettingsExample())
    message_bus_add, message_bus_settings = message_bus_factory(settings=settings)
    # опционально: изменить название компонента, например example
    message_bus_settings.set_component_name(component=f"{settings.name}_example")
    # опционально: добавить trace_id трассировка в логах (полезно для ситуации когда запущено несколько серверов)
    message_bus_settings.set_trace_id(trace_id=str(uuid.uuid4())[:8])
    # включить слоты передав в них шину сообщений (если не передать шину fallback на принты)
    slots_init(callback=message_bus_add, enable=True)
    # создать экземпляр движка (движок может быть переопределенным в дочерних проектах)
    engine = engine_factory(engine_class=Engine, settings=settings)
    # подключить api ядра ( маршруты /start/, /stop/, /process/, /execute/ и так далее)
    api_modul = api_factory(engine=engine, settings=settings, standart_api_schemas=EngineIOSchemas())
    # создать сервер пробросив в него настройки, api_modul и при необходимости кастомные роутеры
    server = server_factory(settings=settings, api_modul=api_modul, middleware_err_enable=True, routers_list=[])

    # запустить сервер, остановка через http://localhost:8000/shutdown/ либо server.stop
    def start_server():
        server.start(port=8000, log_level='warning', host='localhost')

    threading.Thread(target=start_server).start()
    input('...enter чтобы выйти...\n')
    server.stop()


if __name__ == '__main__':
    example1()
