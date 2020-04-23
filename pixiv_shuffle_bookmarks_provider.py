import traceback
import typing as T

import pixiv_api
from bot_utils import *
from settings import settings


def __bookmarks_cached__():
    import os
    import time
    import json

    search_item_limit: int = settings["shuffle_bookmarks"]["search_item_limit"]
    search_page_limit: int = settings["shuffle_bookmarks"]["search_page_limit"]
    search_r18: bool = settings["shuffle_bookmarks"]["search_r18"]
    search_r18g: bool = settings["shuffle_bookmarks"]["search_r18g"]
    search_cache_filename: str = settings["shuffle_bookmarks"]["search_cache_filename"]
    search_cache_outdated_time: int = settings["shuffle_bookmarks"]["search_cache_outdated_time"] # nullable

    # 缓存文件路径
    cache_file = os.path.join(os.path.curdir, search_cache_filename)

    content = dict(illusts=[])

    # 若缓存文件存在且未过期，读取缓存后返回
    if os.path.exists(cache_file):
        now = time.time()
        mtime = os.path.getmtime(cache_file)
        if search_cache_outdated_time is None or now - mtime <= search_cache_outdated_time:
            with open(cache_file, "r", encoding="utf8") as f:
                content = json.load(f)
                if "illusts" in content and len(content["illusts"]) > 0:
                    return content

    # 从pixiv加载
    try:
        illusts = []
        search_result = pixiv_api.api().user_bookmarks_illust(user_id=pixiv_api.api().user_id)
        page = 1
        while len(illusts) < search_item_limit and page < search_page_limit:
            for illust in search_result["illusts"]:
                # R-18/R-18G规避
                if pixiv_api.has_tag(illust, "R-18") and not search_r18:
                    continue
                if pixiv_api.has_tag(illust, "R-18G") and not search_r18g:
                    continue

                illusts.append(illust)
                if len(illusts) >= search_item_limit:
                    break
            else:
                next_qs = pixiv_api.api().parse_qs(search_result["next_url"])
                if next_qs is None:
                    break
                search_result = pixiv_api.api().user_bookmarks_illust(**next_qs)
                page = page + 1

        print(f"{len(illusts)} bookmarks found over {page} pages.")
        # 写入缓存
        with open(cache_file, "w", encoding="utf8") as f:
            content = dict(illusts=illusts)
            f.write(json.dumps(content))
        return content
    except:
        traceback.print_exc()
        # 从pixiv加载时发生异常，尝试读取缓存
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf8") as f:
                content = json.load(f)
        return content


async def receive(bot: Mirai, source: Source, subject: T.Union[Group, Friend], message: MessageChain):
    trigger: str = settings["shuffle_bookmarks"]["trigger"]
    not_found_message: str = settings["shuffle_bookmarks"]["not_found_message"]
    shuffle_method: str = settings["shuffle_bookmarks"]["shuffle_method"]

    try:
        content = message.toString()
        if trigger in content:
            print(f"pixiv shuffle bookmarks asked.")
            illusts = __bookmarks_cached__()["illusts"]
            if len(illusts) > 0:
                illust = pixiv_api.shuffle_illust(illusts, shuffle_method)
                print(f"""illust {illust["id"]} selected.""")
                await reply(bot, source, subject, pixiv_api.illust_to_message(illust))
            else:
                await reply(bot, source, subject, [Plain(not_found_message)])

    except Exception as exc:
        traceback.print_exc()
        await reply(bot, source, subject, [Plain(str(exc)[:128])])
