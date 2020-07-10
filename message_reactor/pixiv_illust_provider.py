import asyncio
import re
import typing as T

from mirai import *

from bot_utils import plain_str, api
from message_reactor.abstract_message_reactor import AbstractMessageReactor


class PixivIllustProvider(AbstractMessageReactor):
    def __check_triggered(self, message: MessageChain) -> bool:
        """
        返回此消息是否触发
        """
        content = plain_str(message)
        for x in self.trigger:
            if x in content:
                return True
        return False

    async def generate_reply(self, bot: Mirai, source: Source, subject: T.Union[Group, Friend], message: MessageChain):
        if self.__check_triggered(message):
            content = plain_str(message)
            regex = re.compile("[1-9][0-9]*")

            tasks = []
            for x in regex.finditer(content):
                illust_id = int(x.group())
                print(f"pixiv illust {illust_id} asked.")
                tasks.append(asyncio.create_task(api.run_in_executor(api.illust_detail, illust_id=illust_id)))

            while tasks:
                done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    result = task.result()
                    if "error" in result:
                        msg = [Plain(result["error"]["user_message"])]
                    else:
                        msg = await api.illust_to_message(result["illust"])
                    yield msg
