import asyncio
import time
import typing as T
from pathlib import Path

import aiofiles

from utils import log


class CacheManager:
    def __init__(self):
        # 用于处理请求，当调用get时将(future, cache_file, func, outdated_time)入队，由__worker统一处理
        self.__query_queue = asyncio.Queue()

        # 用于清理__waiting中已完成缓存的请求，当生成缓存完毕后将cache_file入队，由__worker统一处理
        self.__done_queue = asyncio.Queue()

        # 保存正在生成缓存的请求，键：cache_file，值：Event
        self.__waiting = dict()

    async def get(self, cache_file: Path,
                  func: T.Callable[[], T.Coroutine[T.Any, T.Any, bytes]],
                  outdated_time: T.Optional[int] = None):
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        await self.__query_queue.put((fut, cache_file, func, outdated_time))
        return await fut

    async def __worker(self):
        pending = [asyncio.create_task(self.__query_queue.get()), asyncio.create_task(self.__done_queue.get())]
        while True:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for c in done:
                res = c.result()
                if isinstance(res, Path):
                    try:
                        await self.__on_done(res)
                    finally:
                        self.__done_queue.task_done()
                        pending.add(asyncio.create_task(self.__done_queue.get()))
                else:
                    try:
                        await self.__on_query(*res)
                    finally:
                        self.__query_queue.task_done()
                        pending.add(asyncio.create_task(self.__query_queue.get()))

    def start(self):
        return asyncio.create_task(self.__worker())

    async def __on_done(self, cache_file: Path):
        self.__waiting.pop(cache_file)

    async def __on_query(self, fut: asyncio.Future,
                         cache_file: Path,
                         func: T.Callable[[], T.Coroutine[T.Any, T.Any, bytes]],
                         outdated_time: T.Optional[int] = None):
        try:
            if cache_file.exists():
                now = time.time()
                mtime = cache_file.stat().st_mtime
                if outdated_time is not None and now - mtime > outdated_time:
                    cache_file.unlink()
                    log.info(f"deleted outdated cache {cache_file}")

            if not cache_file.exists():
                if cache_file not in self.__waiting:
                    event = asyncio.Event()
                    self.__waiting[cache_file] = event
                    asyncio.create_task(self.__get_and_cache(fut, event, cache_file, func))
                else:
                    event = self.__waiting[cache_file]
                asyncio.create_task(self.__wait_and_read_cache(event, fut, cache_file))
            else:
                asyncio.create_task(self.__read_cache(fut, cache_file))
        except Exception as exc:
            fut.set_exception(exc)

    async def __get_and_cache(self, fut: asyncio.Future,
                              event: asyncio.Event,
                              cache_file: Path,
                              func: T.Callable[[], T.Coroutine[T.Any, T.Any, bytes]]):
        try:
            b = await func()
            async with aiofiles.open(cache_file, "wb") as f:
                await f.write(b)
            log.info(f"cache saved to {cache_file}")
            await self.__done_queue.put(cache_file)
            event.set()
        except Exception as exc:
            fut.set_exception(exc)

    async def __read_cache(self, fut: asyncio.Future,
                           cache_file: Path):
        try:
            async with aiofiles.open(cache_file, "rb") as f:
                b = await f.read()
            log.info(f"cache load from {cache_file}")
            fut.set_result(b)
        except Exception as e:
            fut.set_exception(e)

    async def __wait_and_read_cache(self, event: asyncio.Event,
                                    fut: asyncio.Future,
                                    cache_file: Path):
        try:
            await event.wait()
            await self.__read_cache(fut, cache_file)
        except Exception as e:
            fut.set_exception(e)
