import asyncio
from time import perf_counter
from typing import Generic, Callable, Awaitable
from svc_platform.slots_manager import slots
from svc_platform.engine.exc import EngineExc
from svc_platform.schemas import SettingsSchemaType, EngineIOSchemas
from svc_platform.engine.functions import stop_all_async_tasks
from svc_platform.engine.types import StreamTask
from svc_platform.schemas import engine_types as e_types


class StreamMixin(Generic[e_types.StreamInputDataType]):
    def __init__(self, settings: SettingsSchemaType):
        self._settings = settings
        self._stream_tasks_registry: dict[str, StreamTask] = {}
        self._stream_semaphore = asyncio.Semaphore(self._settings.stream_limit)
        self._stream_stop_all = False  # во внешнем движке нужно установить эту переменную в false в методе start

    async def stream(
            self, callback: Callable[[e_types.StreamOutputDataType], Awaitable[None]],
            data: e_types.StreamInputDataType,
            request_id: str, *args, **kwargs
    ) -> None:
        _ = self, args, kwargs  # игнорировать variable unused

        async with self._stream_semaphore:  # защита от конфликта корутин (превышения лимита)

            if self._stream_stop_all:
                return

            if request_id in self._stream_tasks_registry:
                raise EngineExc.StreamRequestIdAlreadyExists(f'Стриминг `{request_id}` уже запущен.')
            start_time = perf_counter()
            # создание и запуск задачи
            event = asyncio.Event()
            try:
                self._stream_tasks_registry[request_id] = StreamTask(
                    event=event,
                    task=asyncio.create_task(
                        self._on_stream(
                            data=data,
                            callback=callback,
                            event=event,
                            request_id=request_id,
                        )
                    )
                )
                slots.slot8(name=self._settings.name, request_id=request_id)
                await self._stream_tasks_registry[request_id].task
                end_time = round(perf_counter() - start_time, 2)
                slots.slot9(name=self._settings.name, request_id=request_id, end_time=end_time)

            except asyncio.CancelledError:
                end_time = round(perf_counter() - start_time, 2)
                slots.slot24(name=self._settings.name, request_id=request_id, end_time=end_time)
            except Exception as err:
                slots.slot7(name=self._settings.name, request_id=request_id, err=err)
                raise
            finally:
                if self._stream_tasks_registry.get(request_id) is not None:
                    self._stream_tasks_registry[request_id].event.set()
                self._stream_tasks_registry.pop(request_id, None)

    async def _on_stream(
            self, data: e_types.StreamInputDataType, callback, event: asyncio.Event, request_id: str, *args, **kwargs
    ) -> None:
        """
        (Заглушка! В наследниках полностью переопределить метод, (без super) )
        Реализация логики стриминга.

        ------------------------------------------------------------------------------
        ⚠ Требования к реализации:
            ✔ Метод должен завершаться при сигнале event ( проверка is_set() )
            ✔ Метод возвращает None
            ✔ Результат обрабатывается в callback функции
            ✔ Переопределяется в наследниках без super (чтобы убрать заглушку)
        ------------------------------------------------------------------------------

        :param data: входные данные
        :param callback: функция применяемая к входным данным
        :param event: стоп сигнал (метод должен завершать работу когда event is_set())
        :param request_id: идентификатор цепочки стриминга
        :return: None

        Описание заглушки:
        Принимает входные данные, печатает в консоль сообщение заглушку 20 раз подряд, имитируя стриминг

        (Заглушка! В наследниках полностью переопределить метод, (без super) )
        """
        _ = self, data, args, kwargs  # игнорировать variable unused
        # временная заглушка, имитирующая полезную нагрузку
        iterations = 20
        time_step = 0.1
        for i in range(iterations):
            if event.is_set():
                return
            await callback(f'stream {request_id} stub: chunk {str(i + 1).zfill(2)}/{iterations}')
            await asyncio.sleep(time_step)

    def stop_stream(self, request_id: str):
        """
        (Не переопределять этот метод, бизнес логику реализовывать в _on_stream)
        Остановка запущенного стриминга по request_id, если такой стриминг был запущен
        :param request_id: id процесса
        :return: None
        (Не переопределять этот метод, бизнес логику реализовывать в _on_stream)
        """
        if request_id not in self._stream_tasks_registry:
            raise EngineExc.StreamNoFindReqestId(f'Не запущен stream для request_id: {request_id}')

        # мягкая остановка задачи через испускание сигнала
        self._stream_tasks_registry[request_id].event.set()

        # жесткая остановка задачи, если она не была завершена
        task = self._stream_tasks_registry[request_id].task
        if not task.done():
            task.cancel()

    async def _stream_stop_all_tasks(self):
        """
        (Не переопределять этот метод, бизнес логику реализовывать в _on_stream)
        Досрочная остановка всех текущих стримингов, например при закрытии экземпляра приложения
        :return:None
        (Не переопределять этот метод, бизнес логику реализовывать в _on_stream)
        """
        self._stream_stop_all = True
        await stop_all_async_tasks(
            tasks_registry=self._stream_tasks_registry,
            timeout=self._settings.stream_cancel_all_timeout,
        )


# пример использования
async def main():
    from svc_platform.schemas import BaseSettings
    request_id = '#001'
    request_id2 = '#002'
    stream = StreamMixin(settings=BaseSettings(stream_limit=1, stream_cancel_all_timeout=10))

    async def callback(x):
        print(x)

    task = asyncio.create_task(
        stream.stream(
            callback=callback,
            data=EngineIOSchemas.streaming_input_data(),
            request_id=request_id,
        )
    )

    task2 = asyncio.create_task(
        stream.stream(
            callback=callback,
            data=EngineIOSchemas.streaming_input_data(),
            request_id=request_id2,
        )
    )

    await asyncio.sleep(0.6)
    stream.stop_stream(request_id=request_id)
    await task
    await task2


if __name__ == '__main__':
    asyncio.run(main())
