import abc
import traceback
import typing as T
from abc import abstractmethod

from graia.application import GraiaMiraiApplication, MessageChain, Friend, Group, FriendMessage, GroupMessage, Source
from graia.broadcast import Broadcast
from graia.broadcast.builtin.decoraters import Depend
from loguru import logger

from pixiv import PixivResultError
from utils import reply


class AbstractMessageHandler(metaclass=abc.ABCMeta):
    def __init__(self, tag: str, settings: dict, bcc: Broadcast):
        self.tag = tag
        self.settings = settings

        def judge_friend_message_depend_target(app: GraiaMiraiApplication,
                                               friend: Friend,
                                               message: MessageChain):
            self.judge(app, friend, message)

        @bcc.receiver(FriendMessage,
                      headless_decoraters=[Depend(judge_friend_message_depend_target)])
        async def on_receive_friend_message(app: GraiaMiraiApplication,
                                      friend: Friend,
                                      message: MessageChain):
            await self.on_receive(app, friend, message)

        def judge_group_message_depend_target(app: GraiaMiraiApplication,
                                              group: Group,
                                              message: MessageChain):
            self.judge(app, group, message)

        @bcc.receiver(GroupMessage,
                      headless_decoraters=[Depend(judge_group_message_depend_target)])
        async def on_receive_group_message(app: GraiaMiraiApplication,
                                     group: Group,
                                     message: MessageChain):
            await self.on_receive(app, group, message)

    def __getattr__(self, item: str):
        return self.settings[item]

    def judge(self, app: GraiaMiraiApplication,
              subject: T.Union[Group, Friend],
              message: MessageChain):
        pass

    @abstractmethod
    async def generate_reply(self, app: GraiaMiraiApplication,
                             subject: T.Union[Group, Friend],
                             message: MessageChain) -> T.AsyncGenerator[T.Union[str, MessageChain], None]:
        raise NotImplementedError
        yield

    def generate_error_message(self, exc: Exception) -> str:
        if isinstance(exc, PixivResultError):
            logger.warning(f"{self.tag}: {exc.error()}")
            return exc.error()
        else:
            traceback.print_exc()
            return f"{type(exc)}: {str(exc)}"

    async def on_receive(self, app: GraiaMiraiApplication,
                         subject: T.Union[Group, Friend],
                         message: MessageChain) -> T.NoReturn:
        """
        接收消息
        :param app: GraiaMiraiApplication实例
        :param subject: 消息的发送对象
        :param message: 消息
        """
        src = message.get(Source)
        if len(src) == 0:
            src = None
        else:
            src = src[0]

        try:
            async for msg in self.generate_reply(app, subject, message):
                await reply(app, subject, msg, src)
        except Exception as exc:
            await reply(app, subject, self.generate_error_message(exc), src)
