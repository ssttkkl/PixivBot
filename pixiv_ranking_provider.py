import re
import traceback

import pixiv_api
from bot_utils import *
from settings import settings

trigger = settings["ranking"]["trigger"]

for key in trigger:
    if isinstance(trigger[key], str):
        trigger[key] = [trigger[key]]

default_ranking_mode: str = settings["ranking"]["default_ranking_mode"]
default_range: str = settings["ranking"]["default_range"]
item_pattern: str = settings["ranking"]["item_pattern"]
item_per_page_group: int = settings["ranking"]["item_per_page_group"]
item_per_page_friend: int = settings["ranking"]["item_per_page_friend"]


def __find_ranking_mode__(message: MessageChain) -> T.Optional[str]:
    """
    找出消息中所指定的排行榜种类
    :return: 排行榜种类，若没有则为None
    """
    content = plain_str(message)

    for key in trigger:
        for x in trigger[key]:
            if x in content:
                if key == "default":
                    return default_ranking_mode
                else:
                    return key
    return None


def __findall_ranges__(message: MessageChain) -> T.List[T.Tuple[int]]:
    """
    找出消息中指定的所有排行范围
    :return: 排行范围的列表
    """
    content = plain_str(message)

    regex = "[1-9][0-9]*-[1-9][0-9]*"
    res = re.findall(regex, content)
    if len(res) == 0:
        res = re.findall(regex, default_range)

    return [tuple(map(int, x.split('-'))) for x in res]


def __generate_reply__(mode: str, begin: int, end: int, item_per_page: int) -> T.Generator[list, None, None]:
    """
    生成回复消息
    :param mode: 排行榜种类
    :param begin: 起始排名
    :param end: 结束排名
    :param item_per_page: 每条消息包含多少条
    :return: message的生成器
    """
    illusts = list(pixiv_api.iter_illusts(search_func=pixiv_api.api().illust_ranking,
                                          illust_filter=lambda x: True,
                                          init_qs=dict(mode=mode),
                                          search_item_limit=end,
                                          search_page_limit=None))[begin - 1:]

    message = []
    rank = begin
    for illust in illusts:
        string = item_pattern.replace("$rank", str(rank)) \
            .replace("$title", illust["title"]) \
            .replace("$id", str(illust["id"]))
        message.append(Plain(string))
        if rank % item_per_page == 0:
            yield message
            message = []
        rank = rank + 1

    if len(message) > 0:
        yield message


async def receive(bot: Mirai, source: Source, subject: T.Union[Group, Friend], message: MessageChain) -> T.NoReturn:
    """
    接收消息
    :param bot: Mirai Bot实例
    :param source: 消息的Source
    :param subject: 消息的发送对象
    :param message: 消息
    """
    try:
        mode = __find_ranking_mode__(message)
        if mode is not None:
            for begin, end in __findall_ranges__(message):
                print(f"pixiv {mode} ranking {begin}-{end} asked.")

                if isinstance(subject, Group):
                    item_per_page: int = item_per_page_group
                elif isinstance(subject, Friend):
                    item_per_page: int = item_per_page_friend
                else:
                    raise TypeError(f"param \"subject\" expect type Group or Friend, not {type(subject)}. ")

                for message in __generate_reply__(mode, begin, end, item_per_page):
                    await reply(bot, source, subject, message)
    except Exception as exc:
        traceback.print_exc()
        await reply(bot, source, subject, [Plain(str(exc)[:128])])
