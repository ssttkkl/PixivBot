import asyncio
import re
import typing as T

from graia.application import MessageChain, GraiaMiraiApplication, Group, Friend
from graia.application.message.elements.internal import Plain
from graia.template import Template
from loguru import logger

from pixiv import get_illusts, papi
from .abstract_message_handler import AbstractMessageHandler


class PixivRankingQueryHandler(AbstractMessageHandler):
    def __find_ranking_mode(self, message: MessageChain) -> T.Optional[str]:
        """
        找出消息中所指定的排行榜种类
        :return: 排行榜种类，若没有则为None
        """
        content = message.asDisplay()
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
        content = message.asDisplay()

        regex = "[1-9][0-9]*-[1-9][0-9]*"
        res = re.search(regex, content)
        if res is None:
            res = re.search(regex, self.default_range)

        begin, end = res.group().split('-')
        return int(begin), int(end)

    def __make_msg(self, rank: int, illust: dict) -> MessageChain:
        return Template(self.item_pattern).render(
            rank=Plain(str(rank)),
            title=Plain(illust["title"]),
            id=Plain(str(illust["id"]))
        )

    async def handle(self, app: GraiaMiraiApplication,
                     subject: T.Union[Group, Friend],
                     message: MessageChain,
                     channel: asyncio.Queue) -> bool:
        mode = self.__find_ranking_mode(message)
        if mode is None:
            return False

        begin, end = self.__find_ranges(message)
        logger.info(f"{self.tag}: [{mode}] [{begin}-{end}]")

        illusts = await get_illusts(search_func=papi.illust_ranking,
                                    mode=mode,
                                    search_item_limit=end)

        if isinstance(subject, Group):
            item_per_msg = self.item_per_group_message
        elif isinstance(subject, Friend):
            item_per_msg = self.item_per_friend_message
        else:
            raise TypeError(f"type(subject) expect Group or Friend, got {type(subject)}.")

        msg = MessageChain.create([])
        item_cur_msg = 0
        rank = begin
        for illust in illusts[begin - 1:]:
            msg.plus(self.__make_msg(rank, illust))
            item_cur_msg = item_cur_msg + 1
            if item_cur_msg == item_per_msg:
                await channel.put(msg)
                msg = MessageChain.create([])
                item_cur_msg = 0
            rank = rank + 1

        if item_cur_msg > 0:
            await channel.put(msg)

        logger.info(f"{self.tag}: [{mode}] [{begin}-{end}] ok")
        return True
