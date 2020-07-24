import asyncio
import threading
import typing as T

from loguru import logger as log
from mirai import *
from mirai.event.message.base import BaseMessageComponent
from mirai.image import InternalImage

reply_lock = asyncio.Lock()


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
    async with reply_lock:
        log.debug("reply lock acquired")
        if isinstance(subject, Group):
            await bot.sendGroupMessage(group=subject, message=message, quoteSource=source)
        elif isinstance(subject, Friend):
            await bot.sendFriendMessage(friend=subject, message=message)
        log.debug("reply lock released")


def message_content(message: MessageChain) -> str:
    """
    提取消息中的文本
    """
    return ''.join([x.toString() for x in message.getAllofComponent(Plain)])
