import asyncio
import typing as T

ret_type = T.TypeVar("ret_type")


class WaitQueue:
    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self.__queue = asyncio.Queue(1)

    async def do(self, func: T.Callable[[], T.Coroutine]):
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        await self.__queue.put((fut, func))
        return await fut

    async def __worker(self) -> T.NoReturn:
        while True:
            fut, func = await self.__queue.get()
            try:
                fut: asyncio.Future
                res = await asyncio.wait_for(func(), timeout=self.timeout)
                fut.set_result(res)
            except Exception as exc:
                fut.set_exception(exc)
            finally:
                self.__queue.task_done()

    def start(self):
        asyncio.create_task(self.__worker())
