import traceback

import pixiv_api
from bot_utils import *
from settings import settings

trigger = settings["shuffle_bookmarks"]["trigger"]

if isinstance(trigger, str):
    trigger: T.Sequence[str] = [trigger]

user_id: int = settings["shuffle_bookmarks"]["user_id"]
not_found_message: str = settings["shuffle_bookmarks"]["not_found_message"]
shuffle_method: str = settings["shuffle_bookmarks"]["shuffle_method"]
search_cache_filename: str = settings["shuffle_bookmarks"]["search_cache_filename"]
search_cache_outdated_time: T.Optional[int] = settings["shuffle_bookmarks"]["search_cache_outdated_time"]
search_bookmarks_lower_bound: T.Optional[int] = settings["shuffle_bookmarks"]["search_bookmarks_lower_bound"]
search_view_lower_bound: T.Optional[int] = settings["shuffle_bookmarks"]["search_view_lower_bound"]
search_item_limit: T.Optional[int] = settings["shuffle_bookmarks"]["search_item_limit"]
search_page_limit: T.Optional[int] = settings["shuffle_bookmarks"]["search_page_limit"]
search_filter_tags: T.Sequence[str] = settings["shuffle_bookmarks"]["search_filter_tags"]


def __get_bookmarks__() -> T.Sequence[dict]:
    """
    获取书签的画像（从缓存或服务器）
    """
    import os

    def illust_filter(illust) -> bool:
        # 标签过滤
        for tag in search_filter_tags:
            if pixiv_api.has_tag(illust, tag):
                return False
        # 书签下限过滤
        if search_bookmarks_lower_bound is not None and illust["total_bookmarks"] < search_bookmarks_lower_bound:
            return False
        # 浏览量下限过滤
        if search_view_lower_bound is not None and illust["total_view"] < search_view_lower_bound:
            return False
        return True

    def load_from_pixiv() -> T.Sequence[dict]:
        illusts = list(pixiv_api.iter_illusts(search_func=pixiv_api.api().user_bookmarks_illust,
                                              illust_filter=illust_filter,
                                              init_qs=dict(user_id=pixiv_api.api().user_id),
                                              search_item_limit=search_item_limit,
                                              search_page_limit=search_page_limit))
        print(f"{len(illusts)} illust were found in user [{user_id}]'s bookmarks.")
        return illusts

    # 缓存文件路径
    cache_file = os.path.abspath(search_cache_filename)

    illusts = pixiv_api.get_illusts_cached(load_from_pixiv_func=load_from_pixiv,
                                           cache_file=cache_file,
                                           cache_outdated_time=search_cache_outdated_time)
    return illusts


def __check_triggered__(message: MessageChain) -> bool:
    """
    检查消息是否触发
    """
    content = plain_str(message)
    for x in trigger:
        if x in content:
            return True
    return False


async def receive(bot: Mirai, source: Source, subject: T.Union[Group, Friend], message: MessageChain) -> T.NoReturn:
    """
    接收消息
    :param bot: Mirai Bot实例
    :param source: 消息的Source
    :param subject: 消息的发送对象
    :param message: 消息
    """
    try:
        if __check_triggered__(message):
            print(f"pixiv shuffle bookmarks asked.")
            illusts = __get_bookmarks__()
            if len(illusts) > 0:
                illust = pixiv_api.shuffle_illust(illusts, shuffle_method)
                print(f"""illust {illust["id"]} selected.""")
                await reply(bot, source, subject, pixiv_api.illust_to_message(illust))
            else:
                await reply(bot, source, subject, [Plain(not_found_message)])

    except Exception as exc:
        traceback.print_exc()
        await reply(bot, source, subject, [Plain(str(exc)[:128])])
