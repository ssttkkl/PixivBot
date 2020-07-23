import os
import time
import typing as T
from pathlib import Path

from utils import settings, log


def clean_cache():
    __auto_remove(Path(settings["illust"]["download_dir"]),
                  settings["illust"]["download_outdated_time"])

    __auto_remove(Path(settings["random_illust"]["search_cache_dir"]),
                  settings["random_illust"]["search_cache_outdated_time"])

    __auto_remove(Path(settings["random_user_illust"]["search_cache_dir"]),
                  settings["random_user_illust"]["search_cache_outdated_time"])

    __auto_remove(Path(settings["random_bookmarks"]["search_cache_filename"]),
                  settings["random_bookmarks"]["search_cache_outdated_time"])


def __auto_remove(file: Path, outdated_time: T.Optional[int]) -> bool:
    if not file.exists():
        return False

    if file.is_dir():
        for c in file.iterdir():
            __auto_remove(c, outdated_time)
    else:
        now = time.time()
        mtime = file.stat().st_mtime
        # 加上十分钟的缓冲期，避免文件正在使用时被删除
        if outdated_time is None or now - mtime <= outdated_time + 600:
            return False

        file.unlink()
        log.debug(f"removed outdated file {file}")
