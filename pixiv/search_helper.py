import json
import time
import traceback
import typing as T
from pathlib import Path

import aiofiles

from utils import launch, log
from .illust_utils import has_tag
from .pixiv_api import papi
from .pixiv_error import PixivResultError


async def get_illusts(search_func: T.Callable,
                      illust_filter: T.Optional[T.Callable[[dict], bool]] = None,
                      search_item_limit: T.Optional[int] = None,
                      search_page_limit: T.Optional[int] = None,
                      *args, **kwargs) -> T.List[dict]:
    """
    反复调用search_func自动翻页获取illusts，实现illust的生成器
    :param search_func: 用于从服务器获取illusts的函数，返回值应为包含键"illusts"的词典
    :param illust_filter: 对每个illust调用以过滤不符合的，返回True为包含，False为不包含
    :param search_item_limit: 最多生成多少项，若未指定则无限制
    :param search_page_limit: 最多翻页多少次，若未指定则无限制
    :param args: 初次调用search_func时的参数
    :param kwargs: 初次调用search_func时的参数
    :return: illust的生成器
    """

    if search_item_limit is None:
        search_item_limit = 2 ** 31
    if search_page_limit is None:
        search_page_limit = 2 ** 31

    page = 0
    ans = []

    search_result = await launch(search_func, *args, **kwargs)
    if "error" in search_result:
        raise PixivResultError(search_result["error"])

    while len(ans) < search_item_limit and page < search_page_limit:
        for illust in search_result["illusts"]:
            if illust_filter is None or illust_filter(illust):
                ans.append(illust)
                if len(ans) >= search_item_limit:
                    break
        else:
            next_qs = papi.parse_qs(next_url=search_result["next_url"])
            if next_qs is None:
                break
            search_result = await launch(search_func, **next_qs)
            if "error" in search_result:
                raise PixivResultError(search_result["error"])
            page = page + 1

    return ans


async def get_illusts_with_cache(cache_file: T.Union[str, Path],
                                 cache_outdated_time: T.Optional[int],
                                 search_func: T.Callable,
                                 illust_filter: T.Optional[T.Callable[[dict], bool]] = None,
                                 search_item_limit: T.Optional[int] = None,
                                 search_page_limit: T.Optional[int] = None,
                                 *args, **kwargs) -> T.List[dict]:
    """
    尝试从缓存文件读取illusts，若不存在则从服务器获取并写入缓存文件
    :param cache_file: 缓存文件路径
    :param cache_outdated_time: 缓存文件过期期限（单位：s）
    :param search_func: 用于从服务器获取illusts的函数，返回值应为包含illust的列表
    :param illust_filter: 对每个illust调用以过滤不符合的，返回True为包含，False为不包含
    :param search_item_limit: 最多生成多少项，若未指定则无限制
    :param search_page_limit: 最多翻页多少次，若未指定则无限制
    :param args: 初次调用search_func时的参数
    :param kwargs: 初次调用search_func时的参数
    :return: 包含illust的列表
    """
    if not isinstance(cache_file, Path):
        cache_file = Path(cache_file)

    illusts = []

    # 若缓存文件存在且未过期，读取缓存
    if cache_file.exists():
        now = time.time()
        mtime = cache_file.stat().st_mtime
        if cache_outdated_time is None or now - mtime <= cache_outdated_time:
            async with aiofiles.open(cache_file, "r", encoding="utf8") as f:
                content = json.loads(await f.read())
                if "illusts" in content and len(content["illusts"]) > 0:
                    illusts = content["illusts"]
            log.debug(f"cache was loaded from {cache_file}")
            return illusts

    # 若没读到缓存，则从pixiv加载
    try:
        illusts = await get_illusts(search_func=search_func, illust_filter=illust_filter,
                                    search_item_limit=search_item_limit, search_page_limit=search_page_limit,
                                    *args, **kwargs)
    except:
        traceback.print_exc()
        # 从pixiv加载时发生异常，尝试读取缓存（即使可能已经过期）
        if cache_file.exists():
            async with aiofiles.open(cache_file, "r", encoding="utf8") as f:
                content = json.loads(await f.read())
                if "illusts" in content:
                    illusts = content["illusts"]
            log.debug(f"because failed to fetch data on server, cache was loaded from {cache_file}")
            return illusts

    # 写入缓存
    if len(illusts) > 0:
        dirpath = cache_file.parent
        dirpath.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(cache_file, "w", encoding="utf8") as f:
            content = dict(illusts=illusts)
            await f.write(json.dumps(content))
        log.debug(f"cache was saved to {cache_file}")

    return illusts


def make_illust_filter(block_tags: T.Collection[str],
                       bookmark_lower_bound: int,
                       view_lower_bound: int):
    def illust_filter(illust) -> bool:
        # 标签过滤
        for tag in block_tags:
            if has_tag(illust, tag):
                return False
        # 书签下限过滤
        if illust["total_bookmarks"] < bookmark_lower_bound:
            return False
        # 浏览量下限过滤
        if illust["total_view"] < view_lower_bound:
            return False
        return True

    return illust_filter
