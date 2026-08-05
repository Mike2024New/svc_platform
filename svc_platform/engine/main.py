import uuid
import asyncio
import threading, atexit
from typing import Any, Awaitable, Callable, TypeVar
from svc_platform import slots
from svc_platform.schemas import BaseSettings

__all__ = ['engine_factory', 'Engine']

T = TypeVar('T', bound=BaseSettings)


class Engine:
    def __init__(self, settings: BaseSettings):
        atexit.register(self.stop)
        self._settings = settings
        self._running = False
        self.parameters: dict[str, Any] = {'running': self._running}
        self._on_set_parameters()
        self._component_stop = threading.Event()
        self._streaming_stop = asyncio.Event()
        self._streaming_running = False

    def _on_set_parameters(self):
        """логика записи параметров (например информация об используемом устройстве)"""
        pass

    def start(self, *args, **kwargs) -> None:
        """Запуск движка, выполняет тяжелую логику запуска (например whisper или llm), метод идемпотентен."""
        _ = self, args, kwargs  # игнорировать variable unused
        if self._running:
            return
        self._component_stop.clear()
        self._running = True
        self.parameters['running'] = True
        try:
            self._on_start(*args, **kwargs)
            slots.slot1(self._settings.name, parameters=self.parameters)
        except Exception as err:
            slots.slot3(name=self._settings.name, err=err)
            raise err

    def stop(self, *args, **kwargs) -> None:
        """Остановка движка, метод идемпотентный."""
        _ = self, args, kwargs  # игнорировать variable unused
        if not self._running:
            return
        self._component_stop.set()
        self._running = False
        self.parameters['running'] = False
        try:
            self.stream_stop()  # остановить стриминг если он продолжается
            self._on_stop(*args, **kwargs)
            slots.slot2(self._settings.name, parameters=self.parameters)
        except Exception as err:
            slots.slot3(name=self._settings.name, err=err)
            raise err
        # базовая логика, наследники должны вызывать super (либо без super для переопределения метода полностью)

    def process(self, data: Any, *args, **kwargs) -> Any | None:
        """
        (логику метода определять в _on_execute)
        Блокирующая обработка (batch режим).
        -------------------------------------------------------
        Паттерн: Один запрос → Один ответ
        Примеры:
            - STT: аудио → текст
            - TTS: текст → аудио
            - Классификация: данные → категория
        -------------------------------------------------------
        :param data: Входные данные
        :return: Результат обработки или None если сервис не запущен
        (логику метода определять в _on_execute)
        """
        _ = self, data, args, kwargs  # игнорировать variable unused
        if not self._running:
            return None
        try:
            return self._on_process(data, *args, **kwargs)
        except Exception as err:
            slots.slot5(name=self._settings.name, err=err)
            raise

    async def stream(self, callback: Callable[[Any], Awaitable[None]], data: Any, *args, **kwargs) -> None:
        """
        Стриминговая обработка (real-time режим). Метод асинхронный
        -------------------------------------------------------
        Паттерн: Один запрос → Много ответов (по частям)
        Примеры:
            - LLM: промпт → токены (через callback)
            - Real-time STT: аудио → фрагменты текста
            - TTS: текст → аудио фрагменты
        -------------------------------------------------------
        :param callback: Функция для каждого фрагмента результата
        :param data: Входные данные (опционально)
        :return: None
        """
        _ = self, data, args, kwargs  # игнорировать variable unused
        if not self._running or self._streaming_running:
            return

        self._streaming_running = True
        self._streaming_stop.clear()
        task = asyncio.create_task(self._on_stream(data, callback, *args, **kwargs))

        request_id = str(uuid.uuid4())[:8]
        try:
            slots.slot8(name=self._settings.name, request_id=request_id)
            while not self._streaming_stop.is_set():
                if task.done():
                    exc = task.exception()
                    if exc:  # если в стриме происходит неучтенная ошибка, то пробросить её вверх (она критическая)
                        raise exc
                    break
                await asyncio.sleep(0.1)
            slots.slot9(name=self._settings.name, request_id=request_id)
        except Exception as err:
            slots.slot7(name=self._settings.name, request_id=request_id, err=err)
            raise
        finally:
            if task.done():
                task.cancel()
            self._streaming_running = False
            self._streaming_stop.clear()

    async def _on_stream(self, data, callback, *args, **kwargs) -> None:
        _ = self, data, args, kwargs  # игнорировать variable unused
        # временная заглушка, имитирующая полезную нагрузку
        i = 0
        while True:
            i += 1
            await callback(f'stub chunk:{i}')
            await asyncio.sleep(0.2)

    def stream_stop(self) -> None:
        """Явная остановка стриминга (например через http)"""
        self._streaming_stop.set()

    def execute(self, data: Any, *args, **kwargs) -> None:
        """
        (логику метода определять в _on_execute)
        Исполнительный метод (action режим).
        ----------------------------------------------------
        Паттерн: Один запрос → Действие без ответа
        Примеры:
            - Audio Output: PCM аудио → воспроизведение
            - Управление устройством: команда → выполнение
            - Сохранение данных: информация → запись
        ----------------------------------------------------
        :param data: Входные данные (опционально)
        :return: None
        (логику метода определять в _on_execute)
        """
        _ = self, data, args, kwargs  # игнорировать variable unused
        if not self._running:
            return
        try:
            self._on_execute(data, *args, **kwargs)
        except Exception as err:
            slots.slot6(name=self._settings.name, err=err)
            raise

    def _on_start(self, *args, **kwargs) -> None:
        pass

    def _on_stop(self, *args, **kwargs) -> None:
        pass

    def _on_process(self, data: Any, *args, **kwargs) -> Any:
        _ = self, data, args, kwargs
        return ['stub']

    def _on_execute(self, data: Any, *args, **kwargs) -> None:
        _ = self, data, args, kwargs
        print('stub')


def engine_factory(engine_class: type(Engine), settings: T) -> Engine:
    """
    расширяемая фабрика приложения
    :param engine_class: класс на базе которого будет создан engine
    :param settings: настройки
    :return:
    """
    return engine_class(settings)


if __name__ == '__main__':
    # пример расширения класса и применения модели в наследниках
    class SettingsExtend(BaseSettings):
        samplerate: int


    class EngineExtend(Engine):
        def __init__(self, settings: SettingsExtend):
            super().__init__(settings=settings)
            self._settings = settings
            # расширенные поля доступны через точечную нотацию
            print(self._settings.name)
            print(self._settings.samplerate)
