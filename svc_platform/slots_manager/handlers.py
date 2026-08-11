from svc_platform.slots_manager.slots import Parameters

"""
Функции фабрики для обработки результата полученного из slot функций.
⚠ Требования к реализации:
✔ функция должна быть фабрикой
✔ функция возвращаемая фабрикой дожна принимать аргумент parameters имеющий поля:

    level: Literal['debug', 'info', 'warning', 'error', 'critical', 'start', 'stop', 'process'] - уровень события
    subcomponent: str - название компонента
    message: str - сообщение которое выведется в консоль
    event: str - событие (для машиночитаемого лога)
    request_id: str | None = None - id для отслеживания цепочки вызовов в рамках компонента
    data: dict | None = None - важные данные, например с какими параметрами был инициализирован engine
    error: Exception | None = None - ошибки если возникли в процессе работы (опционально)
    slot_name: str | None = None - название слот функции (определяется автоматически)
    
✔ Функция фабрика передается в функцию slots_init в аргумент handlers_list.

"""


def handler_print_message_factory():
    """Базовый обработчик для печати сообщений в консоль"""

    def handler_print_message(parameters: Parameters, **kwargs):
        _ = kwargs
        message = f"{parameters.message} ( {parameters.slot_name} )"
        print(message)

    return handler_print_message


def handler_message_bus_log_factory(message_bus_add):
    """
    Логирование через шину сообщений
    :param message_bus_add: шина сообщений из модуля infrastructure2.message_bus
    """

    def message_bus_log(parameters: Parameters, **kwargs):
        """Логирование через шину сообщений"""
        if parameters.data is not None:
            parameters.data['slot'] = parameters.slot_name
        else:
            parameters.data = {'slot': parameters.slot_name}

        message = f"{parameters.message} ( {parameters.slot_name} )"
        _ = kwargs
        message_bus_add(
            level=parameters.level,
            subcomponent=parameters.subcomponent,
            message=message,
            event=parameters.event,
            request_id=parameters.request_id,
            data=parameters.data,
            error=parameters.error,
        )

    return message_bus_log


...  # здесь могут быть другие функции обработчики, например интеграция с Kafka, logging, OpenTelemetry и т.д.
