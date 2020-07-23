import os
import typing as T

from loguru import logger as log
from mirai import *

from handler.abstract_random_query_handler import AbstractRandomQueryHandler
from pixiv_utils import get_illust_filter
from utils import api, message_content, match_groups, decode_chinese_int


class PixivRandomBookmarkQueryHandler(AbstractRandomQueryHandler):
    async def __get_bookmarks(self) -> T.Sequence[dict]:
        """
        获取书签的画像（从缓存或服务器）
        """
        # 缓存文件路径
        cache_file = os.path.abspath(self.search_cache_filename)

        if self.user_id is not None:
            user_id = self.user_id
        else:
            user_id = api.get_user_id()

        illusts = await api.get_illusts_cached(cache_file=cache_file,
                                               cache_outdated_time=self.search_cache_outdated_time,
                                               search_func=api.user_bookmarks_illust,
                                               user_id=user_id,
                                               illust_filter=get_illust_filter(
                                                   search_filter_tags=self.search_filter_tags,
                                                   search_bookmarks_lower_bound=self.search_bookmarks_lower_bound,
                                                   search_view_lower_bound=self.search_view_lower_bound),
                                               search_item_limit=self.search_item_limit,
                                               search_page_limit=self.search_page_limit)
        return illusts

    def __find_number(self, message: MessageChain) -> T.Optional[int]:
        """
        找出消息中所指定的数字（随机多少张书签）
        :return: 数字。若未触发则为None，若未指定数字则为1
        """
        content = message_content(message)
        for x in self.trigger:
            result = match_groups(x, ["$number"], content)
            if result is None:
                continue

            number = result["$number"]
            if number is None or number == "":
                number = 1
            elif number.isdigit():
                number = int(number)
            else:
                number = decode_chinese_int(number)
            return number

        return None

    async def generate_reply(self, bot: Mirai, source: Source, subject: T.Union[Group, Friend], message: MessageChain):
        number = self.__find_number(message)
        if number is None:
            return
        log.info(f"{self.tag}: [{number}]")

        illusts = await self.__get_bookmarks()
        log.info(f"{self.tag}: found [{len(illusts)}] bookmarks")
        async for msg in self.random_and_generate_reply(illusts, number):
            yield msg

        log.info(f"{self.tag}: [{number}] ok")
