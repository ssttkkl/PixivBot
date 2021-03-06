import json
import typing as T
from pathlib import Path

from utils import launch, CacheManager
from .illust_utils import has_tag
from .pixiv_api import papi
from .pixiv_error import PixivResultError

__search_cache_manager = CacheManager()


async def start_search_helper():
    await __search_cache_manager.start()


async def stop_search_helper():
    await __search_cache_manager.stop()


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

    async def __to_bytes():
        illusts = await get_illusts(search_func=search_func, illust_filter=illust_filter,
                                    search_item_limit=search_item_limit, search_page_limit=search_page_limit,
                                    *args, **kwargs)

        return json.dumps(dict(illusts=illusts)).encode('UTF-8')

    b = await __search_cache_manager.get(cache_file, __to_bytes,
                                         cache_outdated_time=cache_outdated_time, timeout=30)
    return json.loads(b.decode('UTF-8'))["illusts"]


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
