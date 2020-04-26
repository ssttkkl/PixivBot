import os
import re
import traceback

import pixiv_api
from bot_utils import *
from settings import settings

trigger = settings["shuffle_illust"]["trigger"]

if isinstance(trigger, str):
    trigger = [trigger]

not_found_message: str = settings["shuffle_illust"]["not_found_message"]
shuffle_method: str = settings["shuffle_illust"]["shuffle_method"]
search_r18: bool = settings["shuffle_illust"]["search_r18"]
search_r18g: bool = settings["shuffle_illust"]["search_r18g"]
search_cache_dir: str = settings["shuffle_illust"]["search_cache_dir"]
search_cache_outdated_time: T.Optional[int] = settings["shuffle_illust"]["search_cache_outdated_time"]
search_bookmarks_lower_bound: T.Optional[int] = settings["shuffle_illust"]["search_bookmarks_lower_bound"]
search_view_lower_bound: T.Optional[int] = settings["shuffle_illust"]["search_view_lower_bound"]
search_item_limit: T.Optional[int] = settings["shuffle_illust"]["search_item_limit"]
search_page_limit: T.Optional[int] = settings["shuffle_illust"]["search_page_limit"]


def __get_illusts__(keyword: str) -> T.Sequence[dict]:
    """
    获取搜索的画像（从缓存或服务器）
    """
    if not keyword:  # 若未指定关键词，则从今日排行榜中选取
        return pixiv_api.api().illust_ranking()["illusts"]

    def illust_filter(illust) -> bool:
        # R-18/R-18G规避
        if pixiv_api.has_tag(illust, "R-18") and not search_r18:
            return False
        if pixiv_api.has_tag(illust, "R-18G") and not search_r18g:
            return False
        # 书签下限过滤
        if search_bookmarks_lower_bound is not None and illust["total_bookmarks"] < search_bookmarks_lower_bound:
            return False
        # 浏览量下限过滤
        if search_view_lower_bound is not None and illust["total_view"] < search_view_lower_bound:
            return False
        return True

    def load_from_pixiv() -> T.Sequence[dict]:
        illusts = list(pixiv_api.iter_illusts(search_func=pixiv_api.api().search_illust,
                                              illust_filter=illust_filter,
                                              init_qs=dict(word=keyword),
                                              search_item_limit=search_item_limit,
                                              search_page_limit=search_page_limit))
        print(f"{len(illusts)} [{keyword}] illusts were found.")
        return illusts

    # 缓存文件路径
    dirpath = os.path.join(os.path.curdir, search_cache_dir)
    filename = re.sub("\.[<>/\\\|:\"*?]", "_", keyword) + ".json"  # 转义非法字符
    cache_file = os.path.join(dirpath, filename)

    illusts = pixiv_api.get_illusts_cached(load_from_pixiv_func=load_from_pixiv,
                                           cache_file=cache_file,
                                           cache_outdated_time=search_cache_outdated_time)
    return illusts


def __find_keyword__(message: MessageChain) -> T.Optional[str]:
    """
    找出消息中所指定的关键字
    :return: 关键字，若未触发则为None，若未指定则为""
    """
    content = plain_str(message)
    for x in trigger:
        regex = x.replace("$keyword", "(.*)")
        match_result = re.search(regex, content)
        if match_result is not None:
            return match_result.group(1)
    return None


async def receive(bot: Mirai, source: Source, subject: T.Union[Group, Friend], message: MessageChain) -> T.NoReturn:
    """
    接收消息
    :param bot: Mirai Bot实例
    :param source: 消息的Source
    :param subject: 消息的发送对象
    :param message: 消息
    """
    try:
        keyword = __find_keyword__(message)
        if keyword is None:
            return

        print(f"pixiv shuffle illust [{keyword}] asked.")
        illusts = __get_illusts__(keyword)
        if len(illusts) > 0:
            illust = pixiv_api.shuffle_illust(illusts, shuffle_method)
            print(f"""illust {illust["id"]} selected.""")
            await reply(bot, source, subject, pixiv_api.illust_to_message(illust))
        else:
            await reply(bot, source, subject, [Plain(not_found_message)])
    except Exception as exc:
        traceback.print_exc()
        await reply(bot, source, subject, [Plain(str(exc)[:128])])
