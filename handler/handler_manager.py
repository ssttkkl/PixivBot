import asyncio
import typing as T

from graia.application import GraiaMiraiApplication, MessageChain, Friend, Group, Source, FriendMessage, GroupMessage
from graia.broadcast import Broadcast
from loguru import logger

from handler.abstract_message_handler import AbstractMessageHandler
from utils import reply


class HandlerManager:
    handlers: T.Dict[str, AbstractMessageHandler]
    handler_priority: T.Dict[str, int]
    handler_allow_friend: T.Dict[str, T.Optional[T.Sequence[int]]]
    handler_allow_group: T.Dict[str, T.Optional[T.Sequence[int]]]

    def __init__(self, bcc: Broadcast):
        self.handlers = {}
        self.handler_priority = {}
        self.handler_allow_friend = {}
        self.handler_allow_group = {}

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
        self.handlers[handler.tag] = handler
        self.handler_priority[handler.tag] = kwargs.get("priority", 8)
        self.handler_allow_friend[handler.tag] = kwargs.get("allow_friend", None)
        self.handler_allow_group[handler.tag] = kwargs.get("allow_group", None)

    def unregister(self, handler: AbstractMessageHandler):
        del (self.handlers[handler.tag])
        del (self.handler_priority[handler.tag])
        del (self.handler_allow_friend[handler.tag])
        del (self.handler_allow_group[handler.tag])

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
            handlers = []
            for tag in self.handlers:
                handlers.append(self.handlers[tag])
            handlers.sort(key=lambda x: self.handler_priority[x.tag])

            for handler in handlers:
                handler: AbstractMessageHandler

                # 检查发送者是否有权限
                if isinstance(subject, Group):
                    if (self.handler_allow_group[handler.tag] is not None) \
                            and (subject.id not in self.handler_allow_group[handler.tag]):
                        continue
                elif isinstance(subject, Friend):
                    if (self.handler_allow_friend[handler.tag] is not None) \
                            and (subject.id not in self.handler_allow_friend[handler.tag]):
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
