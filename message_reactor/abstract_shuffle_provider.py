import asyncio
import typing as T

from mirai import *

from bot_utils import api
from message_reactor.abstract_message_reactor import AbstractMessageReactor
from pixiv_api import shuffle_illust


class AbstractShuffleProvider(AbstractMessageReactor):
    async def random_and_generate_reply(self, illusts: T.Sequence[dict], number: int):
        if len(illusts) > 0:
            tasks = []
            for i in range(number):
                illust = shuffle_illust(illusts, self.shuffle_method)
                print(f"""illust [{illust["id"]}] selected.""")
                tasks.append(asyncio.create_task(api.illust_to_message(illust)))
            while tasks:
                done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    yield task.result()
        else:
            yield [Plain(self.not_found_message)]
