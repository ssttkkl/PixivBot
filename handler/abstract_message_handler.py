import abc
import asyncio
import typing as T
from abc import abstractmethod

from graia.application import GraiaMiraiApplication, MessageChain, Friend, Group


class AbstractMessageHandler(metaclass=abc.ABCMeta):
    tag: str
    settings: dict

    def __init__(self, tag: str, settings: dict, **kwargs):
        self.tag = tag
        self.settings = settings

    def __getattr__(self, item: str):
        return self.settings[item]

    @abstractmethod
    async def handle(self, app: GraiaMiraiApplication,
                     subject: T.Union[Group, Friend],
                     message: MessageChain,
                     channel: asyncio.Queue) -> bool:
        """
        处理消息
        :param app: GraiaMiraiApplication
        :param subject: 消息发送者
        :param message: 接收到的消息
        :param channel: 用于发送消息的Queue
        :return: 返回值指示HandlerManager是否应继续分发该消息，即是否拦截下该消息
        """
        raise NotImplementedError
