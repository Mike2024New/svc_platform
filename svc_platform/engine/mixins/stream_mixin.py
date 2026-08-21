import asyncio
from time import perf_counter
from typing import Generic, Callable, Awaitable
from svc_platform.slots_manager import slots
from svc_platform.engine.exc import EngineExc
from svc_platform.engine.functions import stop_all_async_tasks
from svc_platform.engine.types import StreamTask
from svc_platform.schemas import engine_types as e_types
from svc_platform.schemas import SettingsSchemaType


class StreamMixin(Generic[e_types.ProducerStreamInputDataType]):
    def __init__(self, settings: SettingsSchemaType):
        self._settings = settings
        self._stream_tasks_registry: dict[str, StreamTask] = {}
        self._stream_semaphore = asyncio.Semaphore(self._settings.producer_stream_limit)
        self._stream_stop_all = False  # во внешнем движке нужно установить эту переменную в false в методе start

    def stream_current_tasks(self) -> int:
        """Текущее количество задач"""
        return len(self._stream_tasks_registry)

    async def stream(
            self, callback: Callable[[bytes], Awaitable[None]],
            queue: asyncio.Queue[e_types.ProducerStreamInputDataType],
            request_id: str, *args, **kwargs
    ) -> None:
        """
        (Не переопределять этот метод, бизнес логику реализовывать в _on_producer_stream)
        Паттерн 1 запрос -> ответ порциями (пример llm получает промпт и начинает выдавать ответ токенами порционно)
        :param queue:
        :param callback: функция применяемая к чанкам стриминга (например выдача токенов от llm)
        :param request_id: id запроса
        (Не переопределять этот метод, бизнес логику реализовывать в _on_producer_stream)
        """
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
                task = asyncio.create_task(
                    self._on_stream(
                        queue=queue,
                        callback=callback,
                        event=event,
                        request_id=request_id,
                    )
                )

                self._stream_tasks_registry[request_id] = StreamTask(
                    event=event,
                    task=task,
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
                self.stop_stream(request_id=request_id)  # отмена задачи
                raise
            finally:
                if self._stream_tasks_registry.get(request_id) is not None:
                    self._stream_tasks_registry[request_id].event.set()
                self._stream_tasks_registry.pop(request_id, None)

    async def _on_stream(
            self, queue: asyncio.Queue[e_types.ProducerStreamInputDataType],
            callback: Callable[[bytes], Awaitable[None]],
            event: asyncio.Event, *args, **kwargs
    ) -> None:
        """
        (Заглушка! В наследниках полностью переопределить метод, (без super) )
        Реализация логики стриминга.

        ------------------------------------------------------------------------------
        ⚠ Требования к реализации:
            ✔ Метод должен завершаться при сигнале event ( проверка is_set() )
            ✔ Метод возвращает None
            ✔ Результат обрабатывается в callback функции (опционально, так как при стриме не всегда нужен ответ)
            ✔ В callback функцию должен попадать результат по схеме EngineIOSchemas.producer_streaming_output_data
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
        _ = self, args, kwargs  # игнорировать variable unused
        # временная заглушка, имитирующая полезную нагрузку (возвращает тот же ответ)
        i = 0
        while not event.is_set():
            print(123)
            data = await queue.get()
            if i == 10:
                print(i / 0)
            if data is None:
                event.set()
                break
            await callback(data)
            i += 1

    def stop_stream(self, request_id: str):
        """
        (Не переопределять этот метод, бизнес логику реализовывать в _on_producer_stream)
        Остановка запущенного стриминга по request_id, если такой стриминг был запущен
        :param request_id: id процесса
        :return: None
        (Не переопределять этот метод, бизнес логику реализовывать в _on_producer_stream)
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
        (Не переопределять этот метод, бизнес логику реализовывать в _on_producer_stream)
        Досрочная остановка всех текущих стримингов, например при закрытии экземпляра приложения
        :return:None
        (Не переопределять этот метод, бизнес логику реализовывать в _on_producer_stream)
        """
        self._stream_stop_all = True
        await stop_all_async_tasks(
            tasks_registry=self._stream_tasks_registry,
            timeout=self._settings.producer_stream_cancel_all_timeout,
        )


# пример использования
async def main():
    from svc_platform.schemas import BaseSettings
    from svc_platform.slots_manager import slots_init, handler_print_message_factory
    slots_init(enable=True, handlers_list=[handler_print_message_factory()])
    request_id = '#001'
    stream = StreamMixin(settings=BaseSettings(producer_stream_limit=1, producer_stream_cancel_all_timeout=10))

    async def callback(x):
        print(x)

    queue = asyncio.Queue()
    event = asyncio.Event()

    async def producer():
        i = 0
        while not event.is_set():
            await queue.put(f'chunk{i}')
            await asyncio.sleep(0.2)
            i += 1

    stream_task = asyncio.create_task(
        stream.stream(
            callback=callback,
            queue=queue,
            request_id=request_id,
        )
    )
    producer_task = asyncio.create_task(producer())

    await asyncio.sleep(1)
    #
    stream.stop_stream(request_id=request_id)
    event.set()

    await  stream_task # если добавить это, то всё остановится
    await producer_task


if __name__ == '__main__':
    asyncio.run(main())
