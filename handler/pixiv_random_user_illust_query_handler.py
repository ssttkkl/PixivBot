import asyncio
import os
import typing as T

from graia.application import MessageChain, GraiaMiraiApplication, Group, Friend
from loguru import logger

from pixiv import get_illusts_with_cache, make_illust_filter, papi
from utils import match_groups, decode_chinese_int, launch
from .random_helper import random_and_generate_reply
from .abstract_message_handler import AbstractMessageHandler


class PixivRandomUserIllustQueryHandler(AbstractMessageHandler):
    def __find_attrs(self, message: MessageChain) -> T.Optional[T.Tuple[str, int]]:
        """
        找出消息中的搜索关键字
        :return: 搜索关键字，若未触发则为None
        """
        content = message.asDisplay()
        for x in self.trigger:
            result = match_groups(x, ["$illustrator", "$number"], content)
            if result is None:
                continue

            illustrator, number = result["$illustrator"], result["$number"]
            if number is None or number == "":
                number = 1
            elif number.isdigit():
                number = int(number)
            else:
                number = decode_chinese_int(number)
            return illustrator, number

        return None

    @staticmethod
    async def __get_user_id(keyword: str) -> T.Optional[int]:
        """
        获取指定关键词的画师id和名称
        :param keyword: 搜索关键词
        :return: 画师的id和名称
        """
        user_previews = (await launch(papi.search_user, word=keyword))["user_previews"]
        if len(user_previews) == 0:
            return None
        else:
            return user_previews[0]["user"]["id"]

    async def __get_illusts(self, user_id: int) -> T.Sequence[dict]:
        """
        获取指定画师的画像（从缓存或服务器）
        :param user_id: 画师的用户id
        :return: 画像列表
        """
        # 缓存文件路径
        dirname = os.path.join(os.path.curdir, self.search_cache_dir)
        filename = str(user_id) + ".json"
        cache_file = os.path.join(dirname, filename)

        illusts = await get_illusts_with_cache(cache_file=cache_file,
                                               cache_outdated_time=self.search_cache_outdated_time,
                                               search_func=papi.user_illusts,
                                               user_id=user_id,
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

        user_id = await self.__get_user_id(keyword)
        if user_id is None:
            await channel.put(self.not_found_message)
            return True
        logger.info(f"{self.tag}: got [{keyword}] user id [{user_id}]")

        illusts = await self.__get_illusts(user_id)
        logger.info(f"{self.tag}: found [{len(illusts)}] illusts")
        async for msg in random_and_generate_reply(self, illusts, number):
            await channel.put(msg)

        logger.info(f"{self.tag}: [{number}] of [{keyword}] ok")
        return True
