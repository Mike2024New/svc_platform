import uuid
import asyncio
import threading, atexit
from time import perf_counter
from typing import Any, Awaitable, Callable, TypeVar
from svc_platform import slots
from svc_platform.schemas import BaseSettings
from svc_platform.engine.exc import EngineExc

__all__ = ['engine_factory', 'Engine']

T = TypeVar('T', bound=BaseSettings)


class Engine:
    def __init__(self, settings: BaseSettings):
        """

        :param settings: системные настройки приложения (settings.json)
        """
        atexit.register(self.stop)
        self._settings = settings
        self._running = False
        self.parameters: dict[str, Any] = {'running': self._running}
        self._on_set_parameters()
        # стоп сигналы
        self._stop_component = threading.Event()
        self._stop_streaming = asyncio.Event()
        self._stop_execute = threading.Event()
        self._stop_process = threading.Event()
        self._process: dict[str, Any] = {}
        self._streaming_running = False

    def _on_set_parameters(self):
        """логика записи параметров (например информация об используемом устройстве)"""
        pass

    def start(self, *args, **kwargs) -> None:
        """Запуск движка, выполняет тяжелую логику запуска (например whisper или llm), метод идемпотентен."""
        _ = self, args, kwargs  # игнорировать variable unused
        if self._running:
            return
        self._stop_component.clear()
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
        self._stop_component.set()
        self._running = False
        self.parameters['running'] = False
        try:
            self.stop_stream()  # остановить стриминг если он продолжается
            self._on_stop(*args, **kwargs)
            slots.slot2(self._settings.name, parameters=self.parameters)
        except Exception as err:
            slots.slot3(name=self._settings.name, err=err)
            raise err
        # базовая логика, наследники должны вызывать super (либо без super для переопределения метода полностью)

    async def process(self, data: Any, request_id: str = str(uuid.uuid4())[:8], *args, **kwargs) -> None:
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
        :param request_id: id запроса (например для цепочки http запросов)
        :param data: Входные данные
        :return: Результат обработки или None если сервис не запущен
        (логику метода определять в _on_execute)
        """
        _ = self, data, args, kwargs  # игнорировать variable unused
        start_time = perf_counter()
        slots.slot16(name=self._settings.name, request_id=request_id)
        if not self._running:
            return None
        try:
            process = asyncio.Event()
            # добавление ячейки результата (со своим процессом)
            self._process[request_id] = {'event': process, 'result': None, 'cancelled': False}
            result = await self._on_process(data, process=process, *args, **kwargs)
            end_time = round(perf_counter() - start_time, 2)
            slots.slot17(name=self._settings.name, request_id=request_id, end_time=end_time)
            # добавление результата в ячейку
            self._process[request_id]['result'] = result
        except asyncio.CancelledError:
            self._stop_process.set()  # явная остановка процесса
            slots.slot20(name=self._settings.name, request_id=request_id)
            self._process[request_id]['cancelled'] = True
            raise
        except Exception as err:
            slots.slot5(name=self._settings.name, err=err)
            raise
        finally:
            self._stop_process.clear()
        return None

    def get_process_result(self, request_id):
        if request_id not in self._process:
            raise EngineExc.ProcessResultNoFindReqestId(f'Не запущен процесс для request_id: {request_id}')

        if self._process[request_id]['cancelled']:
            self._process.pop(request_id)  # утилизация задачи
            raise EngineExc.ProcessCancelled(f'Задача `{request_id}` была отменена.')

        if self._process[request_id]['result'] is None:
            raise EngineExc.ProcessResultNotCompleted('результат ещё не готов')

        result = self._process[request_id]['result']
        self._process.pop(request_id)  # утилизация задачи
        return result

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
        start_time = perf_counter()
        _ = self, data, args, kwargs  # игнорировать variable unused
        if not self._running or self._streaming_running:
            return

        self._streaming_running = True
        self._stop_streaming.clear()
        task = asyncio.create_task(self._on_stream(data, callback, *args, **kwargs))

        request_id = str(uuid.uuid4())[:8]
        try:
            slots.slot8(name=self._settings.name, request_id=request_id)
            while not self._stop_streaming.is_set():
                if task.done():
                    exc = task.exception()
                    if exc:  # если в стриме происходит неучтенная ошибка, то пробросить её вверх (она критическая)
                        raise exc
                    break
                await asyncio.sleep(0.1)
            end_time = round(perf_counter() - start_time, 2)
            slots.slot9(name=self._settings.name, request_id=request_id, end_time=end_time)
        except Exception as err:
            slots.slot7(name=self._settings.name, request_id=request_id, err=err)
            raise
        finally:
            if task.done():
                task.cancel()
            self._streaming_running = False
            self._stop_streaming.clear()

    def stop_stream(self) -> None:
        """Явная остановка стриминга (например через http)"""
        self._stop_streaming.set()

    def stop_execute(self) -> None:
        self._stop_execute.set()

    def stop_process(self, request_id: str) -> None:
        self._process[request_id]['event'].set()
        self._process[request_id]['cancelled'] = True  # сообщить что задача отменена

    async def execute(self, data: Any, *args, **kwargs) -> None:
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
        start_time = perf_counter()
        request_id = str(uuid.uuid4())[:8]
        slots.slot18(name=self._settings.name, request_id=request_id)
        if not self._running:
            return
        try:
            await self._on_execute(data, *args, **kwargs)
            end_time = round(perf_counter() - start_time, 2)
            slots.slot19(name=self._settings.name, request_id=request_id, end_time=end_time)
        except asyncio.CancelledError:
            self._stop_execute.set()  # явная остановка исполнителя
            print(f'Остановка приложения')
            raise
        except Exception as err:
            slots.slot6(name=self._settings.name, err=err)
            raise
        finally:
            self._stop_execute.clear()

    def _on_start(self, *args, **kwargs) -> None:
        pass

    def _on_stop(self, *args, **kwargs) -> None:
        pass

    async def _on_stream(self, data, callback, *args, **kwargs) -> None:
        _ = self, data, args, kwargs  # игнорировать variable unused
        # временная заглушка, имитирующая полезную нагрузку
        i = 0
        while True:
            i += 1
            await callback(f'stream chunk:{i} #stub')
            await asyncio.sleep(0.2)

    async def _on_process(self, data: Any, process, *args, **kwargs) -> Any | None:
        """Процесс вычислений, например transcribate у whisper (перевод аудио в текст). Может быть прерван через stop_process"""
        _ = self, data, args, kwargs
        for _ in range(5):  # 5 итераций по 0.5 сек -> 2.5 сек
            if process.is_set():  # досрочная остановка
                return None
            await asyncio.sleep(0.5)  # иммитация длительной нагрузки вычислений
        return 'stub'  # для непереопределенного метода будет возвращаться заглушка

    async def _on_execute(self, data: Any, *args, **kwargs) -> None:
        """Метод исполнительный, например tts. Следит за состоянием переменной self._stop_execute.is_set()"""
        _ = self, data, args, kwargs
        for i in 'This is a #stub. Example TTS Voice synthesis in progress. Long text for example.'.split():
            await asyncio.sleep(0.1)
            if self._stop_execute.is_set():  # досрочная остановка
                return
            print(i)


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
        samplerate: int = 16000


    class EngineExtend(Engine):
        def __init__(self, settings: SettingsExtend):
            super().__init__(settings=settings)
            self._settings = settings
            self.execute_stop = asyncio.Event()
            # расширенные поля доступны через точечную нотацию
            print(self._settings.name)
            print(self._settings.samplerate)

        async def execute(self, data, *args, **kwargs):
            try:
                await self._on_execute(data, *args, **kwargs)
            except asyncio.CancelledError:
                self.execute_stop.set()  # явная остановка исполнителя
                print(f'Остановка приложения')
                raise  # важно пробросить CancelledError дальше
            except Exception as err:
                slots.slot6(name=self._settings.name, err=err)
                raise

        async def _on_execute(self, data: Any, *args, **kwargs) -> None:
            for i in 'This is a stub. Example TTS Voice synthesis in progress.':
                await asyncio.sleep(0.1)
                if self.execute_stop.is_set():
                    print()
                    break
                print(i, end='')


    async def main():
        from svc_platform.factories.settings_manager_factory import settings_manager_factory
        from svc_platform.slots import slots_init
        slots_init(callback=None, enable=False)
        current_settings, _ = settings_manager_factory(settings_model=SettingsExtend())
        engine = engine_factory(engine_class=Engine, settings=current_settings)
        engine.start()

        async def callback(x):
            print(x)

        task = asyncio.create_task(engine.stream(data=1, callback=callback))
        await asyncio.sleep(2)
        engine.stop_stream()
        await task


    asyncio.run(main())
