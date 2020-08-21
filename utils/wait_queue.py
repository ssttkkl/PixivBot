import asyncio
import typing as T


class WaitQueue:
    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self.__queue = asyncio.Queue(1)
        self.__worker_task = None
        self.__worker_lock = asyncio.Lock()

    async def do(self, func: T.Callable[[], T.Coroutine]):
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        await self.__queue.put((fut, func))
        return await fut

    async def __worker(self) -> T.NoReturn:
        while True:
            fut, func = await self.__queue.get()
            try:
                res = await asyncio.wait_for(func(), timeout=self.timeout)
                fut.set_result(res)
            except Exception as exc:
                fut.set_exception(exc)
            finally:
                self.__queue.task_done()

    async def start(self) -> bool:
        async with self.__worker_lock:
            if self.__worker_task is not None and not self.__worker_task.cancelled():
                return False
            self.__worker_task = asyncio.create_task(self.__worker())
            return True

    async def stop(self) -> bool:
        async with self.__worker_lock:
            t: asyncio.Task = self.__worker_task
            if t is None or t.cancelled():
                return False
            return t.cancel()
