import re
import traceback
import typing as T

from mirai import *

import pixiv_api
from bot_utils import reply
from settings import settings


def __find_illustrator__(message: MessageChain) -> T.Optional[str]:
    trigger = settings["shuffle_illustrator_illust"]["trigger"]
    regex = re.compile(trigger.replace("$illustrator", "(.*)"))

    for plain in message.getAllofComponent(Plain):
        match_result = regex.search(plain.toString())
        if match_result is not None:
            return match_result.group(1)
    return None


def __get_illusts__(illustrator: str) -> T.Sequence[dict]:
    import os

    search_item_limit: int = settings["shuffle_illustrator_illust"]["search_item_limit"]
    search_page_limit: int = settings["shuffle_illustrator_illust"]["search_page_limit"]
    search_r18: bool = settings["shuffle_illustrator_illust"]["search_r18"]
    search_r18g: bool = settings["shuffle_illustrator_illust"]["search_r18g"]
    search_cache_dir: str = settings["shuffle_illustrator_illust"]["search_cache_dir"]

    search_cache_outdated_time: T.Optional[int] = settings["shuffle_illustrator_illust"]["search_cache_outdated_time"] \
        if "search_cache_outdated_time" in settings["shuffle_illustrator_illust"] else None  # nullable
    search_bookmarks_lower_bound: T.Optional[int] = settings["shuffle_illustrator_illust"]["search_bookmarks_lower_bound"] \
        if "search_bookmarks_lower_bound" in settings["shuffle_illustrator_illust"] else None  # nullable
    search_view_lower_bound: T.Optional[int] = settings["shuffle_illustrator_illust"]["search_view_lower_bound"] \
        if "search_view_lower_bound" in settings["shuffle_illustrator_illust"] else None  # nullable

    illustrator = pixiv_api.api().search_user(illustrator)["user_previews"][0]["user"]
    illustrator_id: int = illustrator["id"]
    illustrator_name: str = illustrator["name"]

    def illust_filter(illust: dict) -> bool:
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
        illusts = list(pixiv_api.iter_illusts(search_func=pixiv_api.api().user_illusts,
                                              illust_filter=illust_filter,
                                              init_qs=dict(user_id=illustrator_id),
                                              search_item_limit=search_item_limit,
                                              search_page_limit=search_page_limit))
        print(f"[{illustrator_name} ({illustrator_id})]'s {len(illusts)} illusts were found.")
        return illusts

    # 缓存文件路径
    dirname = os.path.join(os.path.curdir, search_cache_dir)
    filename = str(illustrator_id) + ".json"
    cache_file = os.path.join(dirname, filename)

    illusts = pixiv_api.get_illusts_cached(load_from_pixiv_func=load_from_pixiv,
                                           cache_file=cache_file,
                                           cache_outdated_time=search_cache_outdated_time)
    return illusts


async def receive(bot: Mirai, source: Source, subject: T.Union[Group, Friend], message: MessageChain):
    not_found_message: str = settings["shuffle_illustrator_illust"]["not_found_message"]
    shuffle_method: str = settings["shuffle_illustrator_illust"]["shuffle_method"]

    try:
        illustrator = __find_illustrator__(message)
        if illustrator is None:
            return

        print(f"pixiv shuffle illustrator illust [{illustrator}] asked.")
        illusts = __get_illusts__(illustrator)
        if len(illusts) > 0:
            illust = pixiv_api.shuffle_illustrator_illust(illusts, shuffle_method)
            print(f"""illust {illust["id"]} selected.""")
            await reply(bot, source, subject, pixiv_api.illust_to_message(illust))
        else:
            await reply(bot, source, subject, [Plain(not_found_message)])
    except Exception as exc:
        traceback.print_exc()
        await reply(bot, source, subject, [Plain(str(exc)[:128])])
