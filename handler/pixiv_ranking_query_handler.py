import re
import typing as T

from mirai import *

from pixiv import get_illusts, papi
from utils import log, message_content
from .abstract_message_handler import AbstractMessageHandler


class PixivRankingQueryHandler(AbstractMessageHandler):
    def __find_ranking_mode(self, message: MessageChain) -> T.Optional[str]:
        """
        找出消息中所指定的排行榜种类
        :return: 排行榜种类，若没有则为None
        """
        content = message_content(message)
        for key in self.trigger:
            for x in self.trigger[key]:
                if x in content:
                    if key == "default":
                        return self.default_ranking_mode
                    else:
                        return key
        return None

    def __find_ranges(self, message: MessageChain) -> T.Tuple[int, int]:
        """
        找出消息中指定的排行范围
        :return: 排行范围的列表
        """
        content = message_content(message)

        regex = "[1-9][0-9]*-[1-9][0-9]*"
        res = re.search(regex, content)
        if res is None:
            res = re.search(regex, self.default_range)

        begin, end = res.group().split('-')
        return int(begin), int(end)

    async def generate_reply(self, bot: Mirai, source: Source, subject: T.Union[Group, Friend], message: MessageChain):
        mode = self.__find_ranking_mode(message)
        if mode is None:
            return

        begin, end = self.__find_ranges(message)
        log.info(f"{self.tag}: [{mode}] [{begin}-{end}]")

        illusts = await get_illusts(search_func=papi.illust_ranking,
                                    mode=mode,
                                    search_item_limit=end)

        message = []
        rank = begin
        for illust in illusts[begin - 1:]:
            string = self.item_pattern.replace("$rank", str(rank)) \
                .replace("$title", illust["title"]) \
                .replace("$id", str(illust["id"]))
            message.append(Plain(string))
            rank = rank + 1

        if isinstance(subject, Group):
            item_per_page = self.item_per_group_message
        elif isinstance(subject, Friend):
            item_per_page = self.item_per_friend_message
        else:
            raise TypeError(f"type(subject) expect Group or Friend, but {type(subject)} found.")

        for i in range(0, len(message), item_per_page):
            if i + item_per_page < len(message):
                j = i + item_per_page
            else:
                j = len(message)
            yield message[i:j]

        log.info(f"{self.tag}: [{mode}] [{begin}-{end}] ok")
