import asyncio
from time import perf_counter
from typing import Generic, Callable, Awaitable
from svc_platform.slots_manager import slots
from svc_platform.engine.exc import EngineExc
from svc_platform.engine.functions import stop_all_async_tasks
from svc_platform.engine.types import StreamTask
from svc_platform.schemas import engine_types as e_types
from svc_platform.schemas import SettingsSchemaType, EngineIOSchemas


class ProducerStreamMixin(Generic[e_types.ProducerStreamInputDataType]):
    def __init__(self, settings: SettingsSchemaType):
        self._settings = settings
        self._producer_stream_tasks_registry: dict[str, StreamTask] = {}
        self._producer_stream_semaphore = asyncio.Semaphore(self._settings.stream_limit)
        self._producer_stream_stop_all = False  # во внешнем движке нужно установить эту переменную в false в методе start

    async def producer_stream(
            self, callback: Callable[[bytes], Awaitable[None]],
            data: e_types.ProducerStreamInputDataType,
            request_id: str, *args, **kwargs
    ) -> None:
        """
        (Не переопределять этот метод, бизнес логику реализовывать в _on_producer_stream)
        Паттерн 1 запрос -> ответ порциями (пример llm получает промпт и начинает выдавать ответ токенами порционно)
        :param data: входные данные (например промпт для llm)
        :param callback: функция применяемая к чанкам стриминга (например выдача токенов от llm)
        :param request_id: id запроса
        (Не переопределять этот метод, бизнес логику реализовывать в _on_producer_stream)
        """
        _ = self, args, kwargs  # игнорировать variable unused

        async with self._producer_stream_semaphore:  # защита от конфликта корутин (превышения лимита)

            if self._producer_stream_stop_all:
                return

            if request_id in self._producer_stream_tasks_registry:
                raise EngineExc.StreamRequestIdAlreadyExists(f'Стриминг `{request_id}` уже запущен.')
            start_time = perf_counter()
            # создание и запуск задачи
            event = asyncio.Event()
            try:
                self._producer_stream_tasks_registry[request_id] = StreamTask(
                    event=event,
                    task=asyncio.create_task(
                        self._on_producer_stream(
                            data=data,
                            callback=callback,
                            event=event,
                            request_id=request_id,
                        )
                    )
                )
                slots.slot8(name=self._settings.name, request_id=request_id)
                await self._producer_stream_tasks_registry[request_id].task
                end_time = round(perf_counter() - start_time, 2)
                slots.slot9(name=self._settings.name, request_id=request_id, end_time=end_time)

            except asyncio.CancelledError:
                end_time = round(perf_counter() - start_time, 2)
                slots.slot24(name=self._settings.name, request_id=request_id, end_time=end_time)
            except Exception as err:
                slots.slot7(name=self._settings.name, request_id=request_id, err=err)
                raise
            finally:
                if self._producer_stream_tasks_registry.get(request_id) is not None:
                    self._producer_stream_tasks_registry[request_id].event.set()
                self._producer_stream_tasks_registry.pop(request_id, None)

    async def _on_producer_stream(
            self, data: e_types.ProducerStreamInputDataType, callback, event: asyncio.Event, request_id: str, *args,
            **kwargs
    ) -> None:
        """
        (Заглушка! В наследниках полностью переопределить метод, (без super) )
        Реализация логики стриминга.

        ------------------------------------------------------------------------------
        ⚠ Требования к реализации:
            ✔ Метод должен завершаться при сигнале event ( проверка is_set() )
            ✔ Метод возвращает None
            ✔ Результат обрабатывается в callback функции
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
        _ = self, data, args, kwargs  # игнорировать variable unused
        # временная заглушка, имитирующая полезную нагрузку
        iterations = 20
        time_step = 0.1
        for i in range(iterations):
            if event.is_set():
                return
            text = f'stream {request_id} stub: chunk {str(i + 1).zfill(2)}/{iterations}'
            bytes_data = text.encode('utf-8')
            await callback(bytes_data)
            await asyncio.sleep(time_step) # для asyncio необходима хотябы минимальная задержка даже в 0

    def stop_producer_stream(self, request_id: str):
        """
        (Не переопределять этот метод, бизнес логику реализовывать в _on_producer_stream)
        Остановка запущенного стриминга по request_id, если такой стриминг был запущен
        :param request_id: id процесса
        :return: None
        (Не переопределять этот метод, бизнес логику реализовывать в _on_producer_stream)
        """
        if request_id not in self._producer_stream_tasks_registry:
            raise EngineExc.StreamNoFindReqestId(f'Не запущен stream для request_id: {request_id}')

        # мягкая остановка задачи через испускание сигнала
        self._producer_stream_tasks_registry[request_id].event.set()

        # жесткая остановка задачи, если она не была завершена
        task = self._producer_stream_tasks_registry[request_id].task
        if not task.done():
            task.cancel()

    async def _producer_stream_stop_all_tasks(self):
        """
        (Не переопределять этот метод, бизнес логику реализовывать в _on_producer_stream)
        Досрочная остановка всех текущих стримингов, например при закрытии экземпляра приложения
        :return:None
        (Не переопределять этот метод, бизнес логику реализовывать в _on_producer_stream)
        """
        self._producer_stream_stop_all = True
        await stop_all_async_tasks(
            tasks_registry=self._producer_stream_tasks_registry,
            timeout=self._settings.stream_cancel_all_timeout,
        )


# пример использования
async def main():
    from svc_platform.schemas import BaseSettings
    request_id = '#001'
    request_id2 = '#002'
    stream = ProducerStreamMixin(settings=BaseSettings(stream_limit=1, stream_cancel_all_timeout=10))

    async def callback(x):
        print(x)

    task = asyncio.create_task(
        stream.producer_stream(
            callback=callback,
            data=EngineIOSchemas.producer_streaming_input_data(),
            request_id=request_id,
        )
    )

    task2 = asyncio.create_task(
        stream.producer_stream(
            callback=callback,
            data=EngineIOSchemas.producer_streaming_input_data(),
            request_id=request_id2,
        )
    )

    await asyncio.sleep(0.6)
    stream.stop_producer_stream(request_id=request_id)
    await task
    await task2


if __name__ == '__main__':
    asyncio.run(main())
