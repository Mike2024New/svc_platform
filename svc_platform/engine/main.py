import asyncio
from typing import Any, Awaitable, Callable
from svc_platform import slots
from svc_platform.engine.exc import EngineExc
# Миксины
from svc_platform.engine.mixins import ExecuteMixin
from svc_platform.engine.mixins import ProcessMixin
from svc_platform.engine.mixins import StreamMixin
# Типы
from svc_platform.schemas import engine_types as e_types

__all__ = ['Engine']


class Engine(ExecuteMixin,ProcessMixin,StreamMixin):
    def __init__(self, settings: e_types.BaseSettingsType, ):
        """
        :param settings: системные настройки приложения (settings.json)
        """
        self._settings = settings
        self._running = False
        self.parameters: dict[str, Any] = {'running': self._running}
        self._on_set_parameters()
        self._stop_component = asyncio.Event()  # состояние Engine

        # подключение модулей:
        ExecuteMixin.__init__(self, settings=settings)
        ProcessMixin.__init__(self, settings=settings)
        StreamMixin.__init__(self, settings=settings)

    def _on_set_parameters(self):
        """логика записи параметров (например информация об используемом устройстве)"""
        self.parameters['settings'] = self._settings.model_dump()

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
            self, callback: Callable[[e_types.StreamOutputDataType], Awaitable[None]], data: e_types.StreamInputDataType,
            request_id: str, *args, **kwargs
    ) -> None:
        if not self._running:  # разрешить метод если запущен движок
            slots.slot31(name=self._settings.name, request_id=request_id)
        return await super().stream(callback=callback, data=data, request_id=request_id, *args, **kwargs)


if __name__ == '__main__':
    async def main():
        from svc_platform.schemas import BaseSettings
        from svc_platform.factories import settings_manager_factory, engine_factory
        from svc_platform.slots import slots_init
        from svc_platform.schemas import EngineIOSchemas

        slots_init(callback=None, enable=True)
        # текущие настройки
        current_settings, _ = settings_manager_factory(
            reset_json=True,  # перезаписать json
            settings_model=BaseSettings(
                process_limit=2,
                process_cleanup_result_ttl=1
            )
        )
        engine = engine_factory(engine_class=Engine, settings=current_settings)
        print(engine.parameters)
        request_id = '#001'

        await engine.start()

        async def callback(x):
            print(x)

        task = asyncio.create_task(
            engine.stream(
                callback=callback,
                data=EngineIOSchemas.streaming_input_data(),
                request_id=request_id,
            )
        )
        # await asyncio.sleep(0.5)
        # await engine.stop()
        await task
        await asyncio.sleep(6)


    asyncio.run(main())
