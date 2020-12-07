import asyncio
import typing as T

from graia.application import GraiaMiraiApplication, MessageChain, Friend, Group, Source, FriendMessage, GroupMessage
from graia.broadcast import Broadcast
from loguru import logger

from handler.abstract_message_handler import AbstractMessageHandler
from utils import reply
from sortedcontainers import SortedKeyList


class HandlerManager:
    handlers: SortedKeyList

    def __init__(self, bcc: Broadcast):
        self.handlers = SortedKeyList(key=lambda x: -x["priority"]) # 为了按优先级降序排序

        @bcc.receiver(FriendMessage)
        async def on_receive_friend_message(app: GraiaMiraiApplication,
                                            friend: Friend,
                                            message: MessageChain):
            await self.__on_receive(app, friend, message)

        @bcc.receiver(GroupMessage)
        async def on_receive_group_message(app: GraiaMiraiApplication,
                                           group: Group,
                                           message: MessageChain):
            await self.__on_receive(app, group, message)

    def register(self, handler: AbstractMessageHandler, **kwargs):
        self.handlers.add({
            "handler": handler,
            "priority": kwargs.get("priority", 8),
            "allow_friend": kwargs.get("allow_friend", None),
            "allow_group": kwargs.get("allow_group", None)
        })

    def unregister(self, handler: AbstractMessageHandler):
        for h in self.handlers:
            if h["handler"] == handler:
                self.handlers.remove(h)
                break

    async def __on_receive(self, app: GraiaMiraiApplication,
                           subject: T.Union[Group, Friend],
                           message: MessageChain) -> T.NoReturn:
        src = message.get(Source)
        if len(src) == 0:
            src = None
        else:
            src = src[0]

        channel = asyncio.Queue(1)

        async def consumer(channel: asyncio.Queue):
            while True:
                try:
                    msg = await channel.get()
                    # logger.info("我摸到了！")
                    await reply(app, subject, msg, src)
                    # logger.info("我发完了！")
                    channel.task_done()
                except asyncio.CancelledError as exc:
                    # logger.info("我溜了！")
                    break
                except Exception as exc:
                    logger.exception(exc)
                    channel.task_done()

        consumer_task = asyncio.create_task(consumer(channel))

        try:
            for h in self.handlers:
                handler: AbstractMessageHandler = h["handler"]
                allow_group: T.Optional[T.Sequence[int]] = h["allow_group"]
                allow_friend: T.Optional[T.Sequence[int]] = h["allow_friend"]

                # 检查发送者是否有权限
                if isinstance(subject, Group):
                    if (allow_group is not None) and (subject.id not in allow_group):
                        continue
                elif isinstance(subject, Friend):
                    if (allow_friend is not None) and (subject.id not in allow_friend):
                        continue

                # 若handler拦截了这条消息
                try:
                    if await handler.handle(app, subject, message, channel):
                        break
                except Exception as exc:
                    logger.exception(exc)
                    pass
        finally:
            await channel.join()
            consumer_task.cancel()
