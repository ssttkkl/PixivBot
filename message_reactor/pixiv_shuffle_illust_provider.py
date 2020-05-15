import re

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
            pos = dict(keyword=x.find("$keyword"), number=x.find("$number"))

            regex = x
            if pos["number"] != -1:
                regex = regex.replace("$number", "(.*)")
            if pos["keyword"] != -1:
                regex = regex.replace("$keyword", "(.*)")
            match_result = re.search(regex, content)

            if match_result is not None:
                if pos["keyword"] != -1 and pos["number"] != -1:
                    if pos["keyword"] < pos["number"]:
                        keyword, number = match_result.group(1), match_result.group(2)
                    else:
                        keyword, number = match_result.group(2), match_result.group(1)
                elif pos["keyword"] != -1:
                    keyword, number = match_result.group(1), "1"
                elif pos["number"] != -1:
                    keyword, number = "", match_result.group(1)
                else:
                    keyword, number = "", "1"

                try:
                    if number.isdigit():
                        number = int(number)
                    else:
                        number = decode_chinese_int(number)
                except:
                    number = 1
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
