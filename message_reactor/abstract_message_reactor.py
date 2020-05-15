import traceback
import typing as T

from mirai import *

from bot_utils import reply, asyncio


class AbstractMessageReactor:
    def __init__(self, settings: dict):
        self.settings = settings

    def __getattr__(self, item):
        return self.settings[item]

    async def generate_reply(self, bot: Mirai, source: Source, subject: T.Union[Group, Friend], message: MessageChain):
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
            tasks = []
            async for msg in self.generate_reply(bot, source, subject, message):
                tasks.append(reply(bot, source, subject, msg))
            await asyncio.gather(*tasks)
        except Exception as exc:
            traceback.print_exc()
            await reply(bot, source, subject, [Plain(str(exc)[:128])])
