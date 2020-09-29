import typing as T
from functools import partial

from graia.application import MessageChain, Group, GraiaMiraiApplication, Friend, Source
from graia.application.message.elements.internal import Plain

from utils.wait_queue import WaitQueue

__reply_queue = WaitQueue()


async def start_reply_queue():
    await __reply_queue.start()


async def stop_reply_queue():
    await __reply_queue.stop()


async def reply(app: GraiaMiraiApplication,
                subject: T.Union[Group, Friend],
                message: T.Union[MessageChain, str],
                quote: T.Optional[T.Union[Source, int]]) -> T.NoReturn:
    """
    回复消息。
    :param app: GraiaMiraiApplication实例
    :param subject: 回复的对象
    :param message: 回复的消息
    :param quote: 引用回复的消息源
    """

    if isinstance(message, str):
        message = MessageChain.create([Plain(message)])

    # 因为mirai-api-http的问题，不能并发传图不然容易车祸
    if isinstance(subject, Group):
        await __reply_queue.do(partial(app.sendGroupMessage, group=subject, message=message, quote=quote))
    elif isinstance(subject, Friend):
        await __reply_queue.do(partial(app.sendFriendMessage, target=subject, message=message, quote=quote))
    else:
        raise TypeError(f"type(subject) expect Group or Friend, got {type(subject)}.")
