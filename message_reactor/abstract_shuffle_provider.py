import asyncio
import typing as T

from mirai import *

from bot_utils import api
from message_reactor.abstract_message_reactor import AbstractMessageReactor
from pixiv_api import shuffle_illust


class AbstractShuffleProvider(AbstractMessageReactor):
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
                    print(f"""illust [{illust["id"]}] selected.""")
                    tasks.append(asyncio.create_task(api.illust_to_message(illust)))
            else:
                selected_illust_id = set()
                for i in range(number):
                    # 保证不会抽到重复，若抽了10次还是一样的就放弃了（不会吧不会吧）
                    retry_times = 0
                    illust = shuffle_illust(illusts, self.shuffle_method)
                    while retry_times < 10 and illust["id"] in selected_illust_id:
                        illust = shuffle_illust(illusts, self.shuffle_method)
                        retry_times = retry_times + 1
                    selected_illust_id.add(illust["id"])
                    print(f"""illust [{illust["id"]}] selected.""")
                    tasks.append(asyncio.create_task(api.illust_to_message(illust)))
            while tasks:
                done, tasks = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    yield task.result()
