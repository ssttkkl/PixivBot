import asyncio
import re
import typing as T

from loguru import logger as log
from mirai import *

from utils import message_content, api
from handler.abstract_message_handler import AbstractMessageHandler


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

    async def generate_reply(self, bot: Mirai, source: Source, subject: T.Union[Group, Friend], message: MessageChain):
        if self.__check_triggered(message):
            content = message_content(message)

            regex = re.compile("[1-9][0-9]*")
            ids = [int(x) for x in regex.findall(content)]
            log.info(f"{self.tag}: {ids}")

            tasks = []
            for x in ids:
                tasks.append(asyncio.create_task(api.run_in_executor(api.illust_detail, illust_id=x)))

            while tasks:
                done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    result = task.result()
                    if "error" in result:
                        msg = [Plain(result["error"]["user_message"])]
                        log.info(f"""{self.tag}: error""")
                    else:
                        msg = await api.illust_to_message(result["illust"])
                        log.info(f"""{self.tag}: [{result["illust"]["id"]}] ok""")
                    yield msg
