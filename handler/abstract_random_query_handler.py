import asyncio
import typing as T

from mirai import *
from loguru import logger as log
from handler.abstract_message_handler import AbstractMessageHandler
from pixiv import make_illust_message, random_illust


class AbstractRandomQueryHandler(AbstractMessageHandler):
    async def random_and_generate_reply(self, illusts: T.Sequence[dict], number: int):
        """
        从illusts中随机抽取number张画像，并生成Message
        :param illusts: 所有的画像
        :param number: 要随机抽取的张数
        """
        if len(illusts) == 0:
            yield [Plain(self.not_found_message)]
        else:
            tasks = []
            if len(illusts) < number:
                for illust in illusts:
                    log.info(f"""{self.tag}: selected illust [{illust["id"]}]""")
                    tasks.append(asyncio.create_task(make_illust_message(illust)))
            else:
                selected = dict()
                for i in range(number):
                    # 保证不会抽到重复，若抽了10次还是一样的就放弃了（不会吧不会吧）
                    retry = 1
                    illust = random_illust(illusts, self.random_method)
                    while retry < 10 and illust["id"] in selected:
                        illust = random_illust(illusts, self.random_method)
                        retry = retry + 1
                    selected[illust["id"]] = illust
                    log.info(f"""{self.tag}: selected illust [{illust["id"]}]""")
                for i in selected:
                    tasks.append(asyncio.create_task(make_illust_message(selected[i])))
            while tasks:
                done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    yield task.result()
