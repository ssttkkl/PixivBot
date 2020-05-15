from bot_utils import *
from message_reactor.abstract_shuffle_provider import AbstractShuffleProvider


class PixivShuffleIllustProvider(AbstractShuffleProvider):
    async def __get_illusts__(self, keyword: str) -> T.Sequence[dict]:
        """
        获取搜索的画像（从缓存或服务器）
        """
        if not keyword:  # 若未指定关键词，则从今日排行榜中选取
            illusts = await api.get_illusts(search_func=api.illust_ranking,
                                            search_page_limit=1)
        else:
            # 缓存文件路径
            dirpath = os.path.join(os.path.curdir, self.search_cache_dir)
            filename = re.sub("\.[<>/\\\|:\"*?]", "_", keyword) + ".json"  # 转义非法字符
            cache_file = os.path.join(dirpath, filename)

            illusts = await api.get_illusts_cached(cache_file=cache_file,
                                                   cache_outdated_time=self.search_cache_outdated_time,
                                                   search_func=api.search_illust,
                                                   word=keyword,
                                                   illust_filter=get_illust_filter(
                                                       search_filter_tags=self.search_filter_tags,
                                                       search_bookmarks_lower_bound=self.search_bookmarks_lower_bound,
                                                       search_view_lower_bound=self.search_view_lower_bound),
                                                   search_item_limit=self.search_item_limit,
                                                   search_page_limit=self.search_page_limit)

        return illusts

    def __check_triggered__(self, message: MessageChain) -> T.Optional[T.Tuple[str, int]]:
        """
        找出消息中所指定的关键字和数字
        :return: 关键字和数字，若未触发则为None，若未指定关键字则为""，若未指定数字则为1
        """
        content = plain_str(message)
        for x in self.trigger:
            result = search_groups(x, ["$keyword", "$number"], content)
            if result is not None:
                keyword, number = result

                if keyword is None:
                    keyword = ""
                if number is None or number == "":
                    number = "1"

                if number.isdigit():
                    number = int(number)
                else:
                    number = decode_chinese_int(number)
                return keyword, number

        return None

    async def generate_reply(self, bot: Mirai, source: Source, subject: T.Union[Group, Friend], message: MessageChain):
        trigger_result = self.__check_triggered__(message)
        if trigger_result is not None:
            keyword, number = trigger_result
            if number > self.limit_per_query:
                yield [Plain(self.overlimit_message)]
            else:
                print(f"[{number}] pixiv shuffle illust [{keyword}] asked.")
                illusts = await self.__get_illusts__(keyword)
                print(f"[{len(illusts)}] illusts were found.")
                async for msg in self.random_and_generate_reply(illusts, number):
                    yield msg
