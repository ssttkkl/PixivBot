# -*- coding: utf8 -*-
import re
import typing as T

from mirai import Mirai, Source, Group, Friend, MessageChain
from mirai.event.message.base import BaseMessageComponent
from mirai.image import InternalImage

from pixiv_api import PixivAPI

api = PixivAPI()


async def reply(bot: Mirai,
                source: Source,
                subject: T.Union[Group, Friend],
                message: T.Union[MessageChain,
                                 BaseMessageComponent,
                                 T.Sequence[T.Union[BaseMessageComponent,
                                                    InternalImage]],
                                 str]) -> T.NoReturn:
    """
    回复消息。若是群组则引用回复，若是好友则普通地回复。
    :param bot: Mirai Bot实例
    :param source: 原消息的Source
    :param subject: 回复的对象
    :param message: 回复的消息
    """
    if isinstance(message, tuple):
        message = list(message)
    if isinstance(subject, Group):
        await bot.sendGroupMessage(group=subject, message=message, quoteSource=source)
    elif isinstance(subject, Friend):
        await bot.sendFriendMessage(friend=subject, message=message)


def plain_str(message: MessageChain) -> str:
    """
    提取消息中的文本
    """
    return ' '.join([x.toString() for x in message.getAllofComponent(Plain)])


__numerals__ = {'零': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
                '百': 100, '千': 1000, '万': 10000, '亿': 100000000}


def decode_chinese_int(text: str) -> int:
    """
    将中文整数转换为int
    :param text: 中文整数
    :return: 对应int
    """
    if text[0] == '负':
        return -decode_chinese_int(text[1:])
    if text[0] == '正':
        return decode_chinese_int(text[1:])

    ans = 0
    radix = 1
    for i in reversed(range(len(text))):
        digit = __numerals__[text[i]]
        if digit >= 10:
            if digit > radix:  # 成为新的基数
                radix = digit
                if i == 0:  # 若给定字符串省略了最前面的“一”，如十三、十五……
                    ans = ans + radix
            else:
                radix = radix * digit
        else:
            ans = ans + radix * digit

    return ans


def search_groups(pattern: str, flags: T.Sequence[str], text: str) -> T.List[T.Optional[str]]:
    """
    将字符串按照模板提取关键内容
    （譬如，pattern="来$number张$keyword图", flags=["$number", "$keyword"], text="来3张色图"，返回值=["3", "色"]）
    :param pattern: 模板串
    :param flags: 标志的占位串
    :param text: 匹配内容
    :return: 提取出的标志的列表。若某个标志搜寻失败，则对应值为None
    """
    flags_order = dict()
    for i, flag in enumerate(flags):
        flags_order[flag] = i

    position = []
    regex = pattern
    for flag in flags:
        p = pattern.find(flag)
        if p != -1:
            position.append((flag, p))
            regex = regex.replace(flag, "(.*)")
    position.sort(key=lambda x: x[1])

    match_result = re.search(regex, text)

    if match_result is None:
        return [None for _ in range(0, len(flags))]
    else:
        ans = dict()
        for i, (flag, p) in enumerate(position):
            ans[flag] = match_result.group(i + 1)

        ans_sorted = []
        for flag in flags:
            if flag not in ans:
                ans_sorted.append((None, flags_order[flag]))
            else:
                ans_sorted.append((ans[flag], flags_order[flag]))
        ans_sorted.sort(key=lambda x: x[1])

        return [x[0] for x in ans_sorted]
