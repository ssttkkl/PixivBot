import re
import traceback
import typing as T

import pixiv_api
from bot_utils import *
from settings import settings


def __fetch_illust_ranking__(mode: str, topn: int):
    cnt = 0
    next_qs = dict(mode=mode)
    while True:
        search_result = pixiv_api.api().illust_ranking(**next_qs)
        for illust in search_result["illusts"]:
            cnt = cnt + 1
            yield illust
            if cnt >= topn:
                return
        next_qs = pixiv_api.api().parse_qs(search_result["next_url"])
        if next_qs is None:
            break


def __find_ranking_mode__(message: MessageChain):
    trigger = settings["ranking"]["trigger"]
    default_ranking_mode = settings["ranking"]["default_ranking_mode"]

    for plain in message.getAllofComponent(Plain):
        mode = None
        for key in trigger:
            if trigger[key] in plain.toString():
                mode = key
                break
        if mode == "default":
            mode = default_ranking_mode
        if mode is not None:
            return mode
    return None


def __findall_ranges__(message: MessageChain):
    default_range = settings["ranking"]["default_range"]

    empty = True
    regex = re.compile("[1-9][0-9]*-[1-9][0-9]*")
    for plain in message.getAllofComponent(Plain):
        for match_result in regex.finditer(plain.toString()):
            empty = False
            begin, end = map(int, match_result.group().split('-'))
            yield begin, end

    if empty:
        for match_result in regex.finditer(default_range):
            begin, end = map(int, match_result.group().split('-'))
            yield begin, end


def __generate_messages__(mode: str, begin: int, end: int, item_per_page: int):
    pattern: str = settings["ranking"]["item_pattern"]

    illusts = list(__fetch_illust_ranking__(mode, end))[begin - 1:]

    message = []
    rank = begin
    for illust in illusts:
        string = pattern.replace("$rank", str(rank)) \
            .replace("$title", illust["title"]) \
            .replace("$id", str(illust["id"]))
        message.append(Plain(string))
        if rank % item_per_page == 0:
            yield message
            message = []
        rank = rank + 1

    if len(message) > 0:
        yield message


async def receive(bot: Mirai, source: Source, subject: T.Union[Group, Friend], message: MessageChain):
    try:
        mode = __find_ranking_mode__(message)
        if mode is not None:
            for begin, end in __findall_ranges__(message):
                print(f"pixiv {mode} ranking {begin}-{end} asked.")

                if isinstance(subject, Group):
                    item_per_page: int = settings["ranking"]["item_per_page_group"]
                elif isinstance(subject, Friend):
                    item_per_page: int = settings["ranking"]["item_per_page_friend"]
                else:
                    raise TypeError(f"param \"subject\" expect type Group or Friend, not {type(subject)}. ")

                for message in __generate_messages__(mode, begin, end, item_per_page):
                    await reply(bot, source, subject, message)
    except Exception as exc:
        traceback.print_exc()
        await reply(bot, source, subject, [Plain(str(exc)[:128])])
