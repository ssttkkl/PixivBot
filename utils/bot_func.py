import asyncio
import typing as T
from functools import partial

from loguru import logger as log
from mirai import *
from mirai.event.message.base import BaseMessageComponent
from mirai.image import InternalImage

from utils.wait_queue import WaitQueue

upload_queue = WaitQueue()


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

    if isinstance(subject, Group):
        t = "group"
    elif isinstance(subject, Friend):
        t = "friend"
    else:
        raise TypeError(f"type(subject) = {type(subject)}, except Group or Friend")

    # 因为mirai-api-http的问题，不能并发传图不然容易车祸
    if isinstance(message, list):
        new_message = []
        for msg in message:
            if isinstance(msg, InternalImage):
                try:
                    img = await upload_queue.do(partial(bot.uploadImage, t, msg))
                    new_message.append(img)
                except asyncio.exceptions.TimeoutError:
                    log.warning("Timeout when upload image")
                    new_message.append(Plain("Timeout when upload image"))
            else:
                new_message.append(msg)
        message = new_message

    if isinstance(subject, Group):
        await bot.sendGroupMessage(group=subject, message=message, quoteSource=source)
    elif isinstance(subject, Friend):
        await bot.sendFriendMessage(friend=subject, message=message)


def message_content(message: MessageChain) -> str:
    """
    提取消息中的文本
    """
    return ''.join([x.toString() for x in message.getAllofComponent(Plain)])
