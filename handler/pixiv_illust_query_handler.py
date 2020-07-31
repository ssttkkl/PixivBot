import asyncio
import re
import typing as T

from mirai import *

from pixiv import make_illust_message, papi, PixivResultError
from utils import log, message_content, launch
from .abstract_message_handler import AbstractMessageHandler


class PixivIllustQueryHandler(AbstractMessageHandler):
    def __check_triggered(self, message: MessageChain) -> bool:
        """
        返回此消息是否触发
        """
        content = message_content(message)
        for x in self.trigger:
            if x in content:
                return True
        return False

    async def make_msg(self, illust_id):
        result = await launch(papi.illust_detail, illust_id=illust_id)
        if "error" in result:
            raise PixivResultError(result["error"])
        else:
            msg = await make_illust_message(result["illust"])
            log.info(f"""{self.tag}: [{result["illust"]["id"]}] ok""")
            return msg

    async def generate_reply(self, bot: Mirai, source: Source, subject: T.Union[Group, Friend], message: MessageChain):
        if self.__check_triggered(message):
            content = message_content(message)

            regex = re.compile("[1-9][0-9]*")
            ids = [int(x) for x in regex.findall(content)]
            log.info(f"{self.tag}: {ids}")

            tasks = []
            for x in ids:
                tasks.append(asyncio.create_task(self.make_msg(x)))

            for ft in asyncio.as_completed(tasks):
                yield ft.result()
