import os
import re
import typing as T

from mirai import *

from bot_utils import reply, plain_str, api, decode_chinese_int
from message_reactor.abstract_shuffle_provider import AbstractShuffleProvider
from pixiv_api import get_illust_filter


class PixivShuffleIllustratorIllustProvider(AbstractShuffleProvider):
    def __check_triggered__(self, message: MessageChain) -> T.Optional[T.Tuple[str, int]]:
        """
        找出消息中的搜索关键字
        :return: 搜索关键字，若未触发则为None
        """
        content = plain_str(message)
        for x in self.trigger:
            pos = dict(illustrator=x.find("$illustrator"), number=x.find("$number"))

            regex = x
            if pos["number"] != -1:
                regex = regex.replace("$number", "(.*)")
            if pos["illustrator"] != -1:
                regex = regex.replace("$illustrator", "(.*)")
            match_result = re.search(regex, content)

            if match_result is not None:
                if pos["illustrator"] != -1 and pos["number"] != -1:
                    if pos["illustrator"] < pos["number"]:
                        illustrator, number = match_result.group(1), match_result.group(2)
                    else:
                        illustrator, number = match_result.group(2), match_result.group(1)
                elif pos["illustrator"] != -1:
                    illustrator, number = match_result.group(1), "1"
                elif pos["number"] != -1:
                    illustrator, number = "", match_result.group(1)
                else:
                    illustrator, number = "", "1"

                try:
                    if number.isdigit():
                        number = int(number)
                    else:
                        number = decode_chinese_int(number)
                except:
                    number = 1
                return illustrator, number

        return None

    async def __get_illustrator_id__(self, keyword: str) -> T.Optional[int]:
        """
        获取指定关键词的画师id和名称
        :param keyword: 搜索关键词
        :return: 画师的id和名称
        """
        user_previews = (await api.run_in_executor(api.search_user, word=keyword))["user_previews"]
        if len(user_previews) == 0:
            return None
        else:
            return user_previews[0]["user"]["id"]

    async def __get_illusts__(self, illustrator_id: int) -> T.Sequence[dict]:
        """
        获取指定画师的画像（从缓存或服务器）
        :param illustrator_id: 画师的用户id
        :return: 画像列表
        """
        # 缓存文件路径
        dirname = os.path.join(os.path.curdir, self.search_cache_dir)
        filename = str(illustrator_id) + ".json"
        cache_file = os.path.join(dirname, filename)

        illusts = await api.get_illusts_cached(cache_file=cache_file,
                                               cache_outdated_time=self.search_cache_outdated_time,
                                               search_func=api.user_illusts,
                                               user_id=illustrator_id,
                                               illust_filter=get_illust_filter(
                                                   search_filter_tags=self.search_filter_tags,
                                                   search_bookmarks_lower_bound=self.search_bookmarks_lower_bound,
                                                   search_view_lower_bound=self.search_view_lower_bound),
                                               search_item_limit=self.search_item_limit,
                                               search_page_limit=self.search_page_limit)
        return illusts

    async def generate_reply(self, bot: Mirai, source: Source, subject: T.Union[Group, Friend], message: MessageChain):
        trigger_result = self.__check_triggered__(message)
        if trigger_result is not None:
            illustrator, number = trigger_result

            print(f"pixiv shuffle illustrator illust [{illustrator}] asked.")
            illustrator_id = await self.__get_illustrator_id__(illustrator)
            if illustrator_id is None:
                await reply(bot, source, subject, [Plain(self.not_found_message)])
            else:
                print(f"illustrator id [illustrator_id] selected.")
                illusts = await self.__get_illusts__(illustrator_id)
                print(f"[{len(illusts)}] illusts were found.")
                async for msg in self.random_and_generate_reply(illusts, number):
                    yield msg
