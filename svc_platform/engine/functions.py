import asyncio


async def stop_all_async_tasks(tasks_registry, timeout):
    """
    Срочная остановка всех выполняющихся задач, сперва пробует мягкую остановку, за тем идет через task_cancel
    На task_cancel лимит задаётся в настройках
    """
    if not tasks_registry:
        return

    # попытка мягкой остановки задач
    for task_data in tasks_registry.values():
        task_data.event.set()

    # жесткая отмена задач через cancel
    active_tasks = [data.task for data in tasks_registry.values() if not data.task.done()]

    for task in active_tasks:
        task.cancel()

    if active_tasks:
        try:
            # ожидание отмены текущих стримов
            await asyncio.wait_for(
                asyncio.gather(
                    *active_tasks,
                    return_exceptions=True  # подавить исключение (если задача уже была отм. ранее в процессе gather)
                ),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            pass
