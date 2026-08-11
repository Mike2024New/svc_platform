from svc_platform.slots_manager.core import Parameters, slots_decorator, slots_init

# handlers - кастомные обработчики слотов (можно расширять в проектах наследниках)
from svc_platform.slots_manager.handlers import handler_message_bus_log_factory

__all__ = [
    'slots_decorator',
    'slots_init',
    'Parameters',
    'handler_message_bus_log_factory',
]
