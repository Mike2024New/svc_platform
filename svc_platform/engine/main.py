import asyncio
from typing import Any, Awaitable, Callable
from svc_platform.slots_manager import slots
from svc_platform.engine.exc import EngineExc
# Миксины
from svc_platform.engine.mixins import ExecuteMixin
from svc_platform.engine.mixins import ProcessMixin
from svc_platform.engine.mixins import StreamMixin
# Типы
from svc_platform.schemas import engine_types as e_types

__all__ = ['Engine']


class Engine(ExecuteMixin, ProcessMixin, StreamMixin):
    def __init__(self, settings: e_types.BaseSettingsType, ):
        """
        :param settings: системные настройки приложения (settings.json)
        """
        self._settings = settings
        self._running = False
        self.parameters: dict[str, Any] = {'running': self._running, 'settings': self._settings.model_dump()}
        self._on_set_parameters()
        self._stop_component = asyncio.Event()  # состояние Engine

        # подключение модулей:
        ExecuteMixin.__init__(self, settings=settings)
        ProcessMixin.__init__(self, settings=settings)
        StreamMixin.__init__(self, settings=settings)

    def _on_set_parameters(self):
        """логика записи параметров (например информация об используемом устройстве)"""
        pass

    # =============== START =================

    async def start(self, *args, **kwargs) -> None:
        """Запуск движка, выполняет тяжелую логику запуска (например whisper или llm), метод идемпотентен."""
        _ = self, args, kwargs  # игнорировать variable unused
        if self._running:
            return
        self._stop_component.clear()
        self._running = True
        self.parameters['running'] = True
        try:
            # 1. запуск Engine
            await self._on_start(*args, **kwargs)
            # 2. запуск цикла удаления устаревших результатов process
            if self._settings.process_cleanup_enable:
                asyncio.create_task(self._cleanup_old_processes_loop())
            slots.slot1(self._settings.name, parameters=self.parameters)
            # 3. Сброс stop переменных (для stop_all_tasks) - задачи снова можно брать в работу
            self._execute_stop_all = False
            self._process_stop_all = False
            self._stream_stop_all = False
        except Exception as err:
            slots.slot3(name=self._settings.name, err=err)
            raise EngineExc.StartError(err)

    async def _on_start(self, *args, **kwargs) -> None:
        pass

    # =============== STOP =================

    async def stop(self, *args, **kwargs) -> None:
        """Остановка движка, метод идемпотентный."""
        _ = self, args, kwargs  # игнорировать variable unused
        if not self._running:
            return
        self._stop_component.set()
        self._running = False
        self.parameters['running'] = False
        try:
            await self._on_stop(*args, **kwargs)
            # сбросить все tasks подключенных миксинов.
            await self._process_stop_all_tasks()  # остановить все процессы
            await self.execute_stop_all_tasks()  # остановить все команды
            await self._stream_stop_all_tasks()  # остановить все стриминговые задачи
            # сбросить все реестры
            self._execute_tasks_registry = {}
            self._process_tasks_registry = {}
            self._stream_tasks_registry = {}

            slots.slot2(self._settings.name, parameters=self.parameters)
        except Exception as err:
            slots.slot3(name=self._settings.name, err=err)
            raise EngineExc.StopError(err)
        # базовая логика, наследники должны вызывать super (либо без super для переопределения метода полностью)

    async def _on_stop(self, *args, **kwargs) -> None:
        pass

    # =============== PROCESS =================

    async def process(self, data: e_types.ProcessInputDataType, request_id: str, *args, **kwargs) -> None:
        if not self._running:  # разрешить метод если запущен движок
            slots.slot30(name=self._settings.name, request_id=request_id)
            return None
        return await super().process(data=data, request_id=request_id, *args, **kwargs)

    # ============== EXECUTE =================

    async def execute(self, data: e_types.ExecuteInputDataType, request_id: str, *args, **kwargs) -> None:
        if not self._running:  # разрешить метод если запущен движок
            slots.slot28(name=self._settings.name, request_id=request_id)
            return None
        return await super().execute(data=data, request_id=request_id, *args, **kwargs)

    # =============== STREAM =================

    async def stream(
            self, callback: Callable[[bytes], Awaitable[None]],
            queue: asyncio.Queue[e_types.ProducerStreamInputDataType],
            request_id: str, *args, **kwargs
    ) -> None:

        if not self._running:  # разрешить метод если запущен движок
            slots.slot31(name=self._settings.name, request_id=request_id)
            return None
        return await super().stream(callback=callback, queue=queue, request_id=request_id, *args, **kwargs)


if __name__ == '__main__':
    async def main():
        from svc_platform.schemas import BaseSettings
        from svc_platform.factories import settings_manager_factory, engine_factory
        from svc_platform.slots_manager import slots_init, handler_print_message_factory
        from svc_platform.schemas import EngineIOSchemas

        slots_init(handlers_list=[handler_print_message_factory()], enable=True)
        # текущие настройки
        current_settings, _ = settings_manager_factory(
            reset_json=True,  # перезаписать json
            settings_model=BaseSettings()
        )
        engine = engine_factory(engine_class=Engine, settings=current_settings)
        await engine.start()
        tasks = []
        for i in range(2):
            task = asyncio.create_task(engine.process(request_id=f'#00{i}', data=EngineIOSchemas.process_input_data()))
            tasks.append(task)

        await asyncio.sleep(1)
        engine.stop_process(request_id='#000')
        await asyncio.sleep(0.2)
        # print(engine._process_tasks_registry)

        await asyncio.gather(*tasks)


    asyncio.run(main())
