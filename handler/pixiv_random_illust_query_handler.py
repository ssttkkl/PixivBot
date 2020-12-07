import asyncio
import os
import re
import typing as T

from graia.application import MessageChain, GraiaMiraiApplication, Group, Friend
from loguru import logger

from pixiv import get_illusts_with_cache, make_illust_filter, get_illusts, papi
from utils import match_groups, decode_chinese_int
from .random_helper import random_and_generate_reply
from .abstract_message_handler import AbstractMessageHandler


class PixivRandomIllustQueryHandler(AbstractMessageHandler):
    def __find_attrs(self, message: MessageChain) -> T.Optional[T.Tuple[str, int]]:
        """
        找出消息中所指定的关键字和数字
        :return: 关键字和数字。若未触发则为None，若未指定关键字则为""，若未指定数字则为1
        """
        content = message.asDisplay()
        for x in self.trigger:
            result = match_groups(x, ["$keyword", "$number"], content)
            if result is None:
                continue

            keyword, number = result["$keyword"], result["$number"]
            if keyword is None:
                keyword = ""
            if number is None or number == "":
                number = 1
            elif number.isdigit():
                number = int(number)
            else:
                number = decode_chinese_int(number)
            return keyword, number

        return None

    async def __get_illusts(self, keyword: str) -> T.Sequence[dict]:
        """
        获取搜索的画像（从缓存或服务器）
        """
        if not keyword:  # 若未指定关键词，则从今日排行榜中选取
            illusts = await get_illusts(search_func=papi.illust_ranking,
                                        search_page_limit=1)
        else:
            # 缓存文件路径
            dirpath = os.path.join(os.path.curdir, self.search_cache_dir)
            filename = re.sub("\.[<>/\\\|:\"*?]", "_", keyword) + ".json"  # 转义非法字符
            cache_file = os.path.join(dirpath, filename)

            illusts = await get_illusts_with_cache(cache_file=cache_file,
                                                   cache_outdated_time=self.search_cache_outdated_time,
                                                   search_func=papi.search_illust,
                                                   word=keyword,
                                                   illust_filter=make_illust_filter(
                                                       block_tags=self.block_tags,
                                                       bookmark_lower_bound=self.bookmark_lower_bound,
                                                       view_lower_bound=self.view_lower_bound),
                                                   search_item_limit=self.search_item_limit,
                                                   search_page_limit=self.search_page_limit)

        return illusts

    async def handle(self, app: GraiaMiraiApplication,
                     subject: T.Union[Group, Friend],
                     message: MessageChain,
                     channel: asyncio.Queue) -> bool:
        attrs = self.__find_attrs(message)
        if attrs is None:
            return False

        keyword, number = attrs
        if number > self.limit_per_query:
            await channel.put(self.overlimit_message)
            return True

        logger.info(f"{self.tag}: [{number}] of [{keyword}]")

        illusts = await self.__get_illusts(keyword)
        logger.info(f"{self.tag}: found [{len(illusts)}] illusts")
        async for msg in random_and_generate_reply(self, illusts, number):
            await channel.put(msg)

        logger.info(f"{self.tag}: [{number}] of [{keyword}] ok")
        return True
