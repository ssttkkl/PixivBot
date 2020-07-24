import traceback
import typing as T

from mirai import *

from pixiv import PixivResultError
from utils import reply, log


class AbstractMessageHandler:
    def __init__(self, tag: str, settings: dict):
        self.tag = tag
        self.settings = settings

    def __getattr__(self, item: str):
        return self.settings[item]

    async def generate_reply(self, bot: Mirai, source: Source, subject: T.Union[Group, Friend],
                             message: MessageChain):
        raise NotImplementedError
        yield

    async def receive(self, bot: Mirai, source: Source, subject: T.Union[Group, Friend],
                      message: MessageChain) -> T.NoReturn:
        """
        接收消息
        :param bot: Mirai Bot实例
        :param source: 消息的Source
        :param subject: 消息的发送对象
        :param message: 消息
        """
        try:
            async for msg in self.generate_reply(bot, source, subject, message):
                await reply(bot, source, subject, msg)
        except PixivResultError as exc:
            log.info(f"{self.tag}: {exc.error()}")
            await reply(bot, source, subject, [Plain(exc.error()[:128])])
        except Exception as exc:
            traceback.print_exc()
            await reply(bot, source, subject, [Plain(str(exc)[:128])])
