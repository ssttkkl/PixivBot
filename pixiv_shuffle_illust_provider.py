import re
import traceback
import typing as T

import pixiv_api
from bot_utils import *
from settings import settings


def __search_cached__(keyword):
    import json
    import os
    import time

    search_item_limit: int = settings["shuffle_illust"]["search_item_limit"]
    search_page_limit: int = settings["shuffle_illust"]["search_page_limit"]
    search_r18: bool = settings["shuffle_illust"]["search_r18"]
    search_r18g: bool = settings["shuffle_illust"]["search_r18g"]
    search_cache_dir: str = settings["shuffle_illust"]["search_cache_dir"]
    search_cache_outdated_time: int = settings["shuffle_illust"]["search_cache_outdated_time"]

    # 缓存文件路径
    filename = re.sub("\.[<\>\/\\\|\:\"\*\?]", "_", keyword)  # 转义非法字符
    if search_r18:
        filename = filename + ".r18"
    if search_r18g:
        filename = filename + ".r18g"
    filename = filename + ".json"
    dirname = os.path.join(os.path.curdir, search_cache_dir)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    cache_file = os.path.join(dirname, filename)

    content = dict(illusts=[])

    # 若缓存文件存在且未过期，读取缓存后返回
    if os.path.exists(cache_file):
        now = time.time()
        mtime = os.path.getmtime(cache_file)
        if now - mtime <= search_cache_outdated_time:
            with open(cache_file, "r", encoding="utf8") as f:
                content = json.load(f)
                if "illusts" in content and len(content["illusts"]) > 0:
                    return content

    # 从pixiv加载
    try:
        illusts = []
        search_result = pixiv_api.api().search_illust(keyword)
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
                search_result = pixiv_api.api().search_illust(**next_qs)
                page = page + 1

        print(f"{len(illusts)} [{keyword}] illusts found over {page} pages.")
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
    try:
        plain = message.getFirstComponent(Plain)
        if plain is None:
            return
        content = plain.toString()

        trigger: str = settings["shuffle_illust"]["trigger"]
        match_result = re.match(pattern=trigger.replace("$keyword", "(.*)"), string=content)
        if match_result is None:
            return
        keyword = match_result.group(1)

        if keyword:  # 若指定关键词，则进行搜索
            print(f"pixiv shuffle illust [{keyword}] asked.")
            illusts = __search_cached__(keyword)["illusts"]
        else:  # 若未指定关键词，则从今日排行榜中选取
            print(f"pixiv shuffle illust from ranking asked.")
            illusts = pixiv_api.api().illust_ranking()["illusts"]

        if len(illusts) > 0:
            illust = pixiv_api.shuffle_illust(illusts)
            print(f"""illust {illust["id"]} selected.""")
            await reply(bot, source, subject, pixiv_api.illust_to_message(illust))
        else:
            not_found_message = [Plain(settings["shuffle_illust"]["not_found_message"])]
            await reply(bot, source, subject, not_found_message)

    except Exception as exc:
        traceback.print_exc()
        await reply(bot, source, subject, [Plain(str(exc)[:128])])
