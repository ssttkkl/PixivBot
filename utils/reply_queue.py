import typing as T
from functools import partial

from mirai import *
from mirai.event.message.base import BaseMessageComponent
from mirai.image import InternalImage

from utils.wait_queue import WaitQueue

__reply_queue = WaitQueue()


async def start_reply_queue():
    await __reply_queue.start()


async def stop_reply_queue():
    await __reply_queue.stop()


async def reply(bot: Mirai,
                source: Source,
                subject: T.Union[Group, Friend],
                message: T.Union[MessageChain,
                                 BaseMessageComponent,
                                 T.List[T.Union[BaseMessageComponent,
                                                InternalImage]],
                                 str]) -> T.NoReturn:
    """
    回复消息。若是群组则引用回复，若是好友则普通地回复。
    :param bot: Mirai Bot实例
    :param source: 原消息的Source
    :param subject: 回复的对象
    :param message: 回复的消息
    """

    # 因为mirai-api-http的问题，不能并发传图不然容易车祸
    if isinstance(subject, Group):
        await __reply_queue.do(partial(bot.sendGroupMessage, group=subject, message=message, quoteSource=source))
    elif isinstance(subject, Friend):
        await __reply_queue.do(partial(bot.sendFriendMessage, friend=subject, message=message))
