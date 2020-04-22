import re
import traceback
import typing as T

import pixiv_api
from bot_utils import *
from settings import settings


def __illust_ranking_topn__(mode, topn) -> dict:
    illusts = []
    search_result = pixiv_api.api().illust_ranking(mode=mode)
    while True:
        illusts.extend(search_result["illusts"])
        if len(illusts) >= topn:
            break
        next_qs = pixiv_api.api().parse_qs(search_result["next_url"])
        if next_qs is None:
            break
        search_result = pixiv_api.api().illust_ranking(**next_qs)
    return dict(illusts=illusts[:topn])


async def receive(bot: Mirai, source: Source, subject: T.Union[Group, Friend], message: MessageChain):
    try:
        content = message.toString()

        mode = None
        trigger = settings["ranking"]["trigger"]
        for key in trigger:
            if trigger[key] in content:
                mode = key
                break
        if mode == "default":
            mode = settings["ranking"]["default_ranking_mode"]

        if mode is not None:
            match_result = re.search(pattern="[1-9][0-9]*\\-[1-9][0-9]*", string=content)
            if match_result is None:
                match_result = re.search(pattern="[1-9][0-9]*\\-[1-9][0-9]*",
                                         string=settings["ranking"]["default_range"])
            begin, end = map(int, match_result.group().split('-'))
            print(f"pixiv {mode} ranking {begin}-{end} asked.")

            ranking = __illust_ranking_topn__(mode, end)
            message = []

            if isinstance(subject, Group):
                item_per_page: int = settings["ranking"]["item_per_page_group"]
            elif isinstance(subject, Friend):
                item_per_page: int = settings["ranking"]["item_per_page_friend"]
            else:
                raise TypeError(f"param \"subject\" expect type Group or Friend, not {type(subject)}. ")

            pattern: str = settings["ranking"]["item_pattern"]
            rank = 1
            for illust in ranking["illusts"]:
                string = pattern.replace("$rank", str(rank)) \
                    .replace("$title", illust["title"]) \
                    .replace("$id", str(illust["id"]))
                message.append(Plain(string))
                if rank % item_per_page == 0:
                    await reply(bot, source, subject, message)
                    message = []
                rank = rank + 1

            if len(message) > 0:
                await reply(bot, source, subject, message)
    except Exception as exc:
        traceback.print_exc()
        await reply(bot, source, subject, [Plain(str(exc)[:128])])
