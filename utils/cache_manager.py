import asyncio
import time
import typing as T
from pathlib import Path

import aiofiles
from loguru import logger as log

from .utils import launch


class CacheManager:
    def __init__(self):
        # 用于处理查询请求，由__worker统一处理
        self.__query_queue = asyncio.Queue()

        # 用于清理__waiting中已完成缓存的请求，由__worker统一处理
        self.__done_queue = asyncio.Queue()

        # 用于处理清理请求，由__worker统一处理
        self.__clear_queue = asyncio.Queue()

        # 保存正在生成缓存的请求，键：cache_file，值：Event
        self.__waiting = dict()

        self.__worker_task = None
        self.__worker_lock = asyncio.Lock()

        self.__auto_clear_task = None
        self.__auto_clear_lock = asyncio.Lock()

        # 自动清理的目录/文件列表，元素为元组(file, outdated_time)
        self.auto_clear_list = []

    async def get(self, cache_file: Path,
                  func: T.Callable[[], T.Coroutine[T.Any, T.Any, bytes]],
                  cache_outdated_time: T.Optional[int] = None,
                  timeout: T.Optional[int] = None) -> bytes:
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        await self.__query_queue.put(("get", fut, cache_file, func, cache_outdated_time, timeout))
        return await fut

    async def clear_outdated(self, file: Path, cache_outdated_time: int) -> T.NoReturn:
        event = asyncio.Event()
        await self.__query_queue.put(("clear", event, file, cache_outdated_time))
        return await event.wait()

    async def __worker(self):
        pending = [
            asyncio.create_task(self.__query_queue.get()),
            asyncio.create_task(self.__done_queue.get()),
            asyncio.create_task(self.__clear_queue.get())
        ]
        while True:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for c in done:
                res: tuple = c.result()
                if res[0] == "done":
                    try:
                        await self.__on_done(*res[1:])
                    finally:
                        self.__done_queue.task_done()
                        pending.add(asyncio.create_task(self.__done_queue.get()))
                elif res[0] == "get":
                    try:
                        await self.__on_get(*res[1:])
                    finally:
                        self.__query_queue.task_done()
                        pending.add(asyncio.create_task(self.__query_queue.get()))
                elif res[0] == "clear":
                    try:
                        await self.__on_clear(*res[1:])
                    finally:
                        self.__query_queue.task_done()
                        pending.add(asyncio.create_task(self.__clear_queue.get()))

    async def start(self) -> bool:
        async with self.__worker_lock:
            if self.__worker_task is not None and not self.__worker_task.cancelled():
                return False
            self.__worker_task = asyncio.create_task(self.__worker())
            return True

    async def stop(self) -> bool:
        async with self.__worker_lock:
            t = self.__worker_task
            if t is None or t.cancelled():
                return False
            return t.cancel()

    async def __auto_clear_worker(self, duration: int):
        while True:
            await asyncio.sleep(duration)
            for f, t in self.auto_clear_list:
                if t is not None:
                    await self.clear_outdated(f, t)

    async def enable_auto_clear(self, duration: int):
        async with self.__auto_clear_lock:
            if self.__auto_clear_task is not None:
                self.__auto_clear_task.cancel()
            self.__auto_clear_task = asyncio.create_task(self.__auto_clear_worker(duration))

    async def disable_auto_clear(self) -> bool:
        async with self.__auto_clear_lock:
            t = self.__auto_clear_task
            if t is None or t.cancelled():
                return False
            return t.cancel()

    async def __on_done(self, cache_file: Path):
        # log.debug(f"done {cache_file}")
        self.__waiting.pop(cache_file)

    async def __on_get(self, fut: asyncio.Future,
                       cache_file: Path,
                       func: T.Callable[[], T.Coroutine[T.Any, T.Any, bytes]],
                       cache_outdated_time: T.Optional[int] = None,
                       timeout: T.Optional[int] = None):
        # log.debug(f"get {cache_file}")
        del_if_outdated(cache_file, cache_outdated_time)
        if not cache_file.exists():
            if cache_file not in self.__waiting:
                event = asyncio.Event()
                self.__waiting[cache_file] = event
                asyncio.create_task(self.__get_and_cache(fut, event, cache_file, func, timeout))
            else:
                event = self.__waiting[cache_file]
                asyncio.create_task(self.__wait_and_read_cache(event, fut, cache_file))
        else:
            asyncio.create_task(self.__read_cache(fut, cache_file))

    async def __on_clear(self, event: asyncio.Event,
                         file: Path,
                         cache_outdated_time: T.Optional[int] = None):
        # log.debug(f"clear {file}")
        def work(f: Path):
            if f.is_dir():
                for c in f.iterdir():
                    work(c)
            del_if_outdated(f, cache_outdated_time)

        await launch(work, file)
        event.set()

    async def __get_and_cache(self, fut: asyncio.Future,
                              event: asyncio.Event,
                              cache_file: Path,
                              func: T.Callable[[], T.Coroutine[T.Any, T.Any, bytes]],
                              timeout: T.Optional[int] = None):
        try:
            b = await asyncio.wait_for(func(), timeout)
            fut.set_result(b)

            async with aiofiles.open(cache_file, "wb") as f:
                await f.write(b)
            log.info(f"cache saved to {cache_file}")
            await self.__done_queue.put(("done", cache_file))
        except Exception as e:
            fut.set_exception(e)
        finally:
            event.set()

    async def __wait_and_read_cache(self, event: asyncio.Event,
                                    fut: asyncio.Future,
                                    cache_file: Path):
        try:
            await event.wait()
            await self.__read_cache(fut, cache_file)
        except Exception as e:
            fut.set_exception(e)

    async def __read_cache(self, fut: asyncio.Future,
                           cache_file: Path):
        try:
            async with aiofiles.open(cache_file, "rb") as f:
                b = await f.read()
            log.info(f"cache load from {cache_file}")
            fut.set_result(b)
        except Exception as e:
            fut.set_exception(e)


def del_if_outdated(file: Path, outdated_time: T.Optional[int]):
    if file.exists():
        now = time.time()
        mtime = file.stat().st_mtime
        if outdated_time is not None and now - mtime > outdated_time:
            file.unlink()
            log.info(f"deleted outdated cache {file}")
