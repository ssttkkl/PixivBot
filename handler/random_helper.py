import asyncio
import typing as T

from graia.application import MessageChain
from loguru import logger as log

from handler.abstract_message_handler import AbstractMessageHandler
from pixiv import make_illust_message, random_illust


async def random_and_generate_reply(handler: AbstractMessageHandler,
                                    illusts: T.Sequence[dict],
                                    number: int) -> T.AsyncGenerator[T.Union[str, MessageChain], None]:
    """
    从illusts中随机抽取number张画像，并生成Message
    :param handler: handler
    :param illusts: 所有的画像
    :param number: 要随机抽取的张数
    """

    if len(illusts) == 0:
        yield handler.not_found_message
    else:
        tasks = []
        if len(illusts) < number:
            for illust in illusts:
                log.info(f"""{handler.tag}: selected illust [{illust["id"]}]""")
                tasks.append(asyncio.create_task(make_illust_message(illust)))
        else:
            selected = dict()
            for i in range(number):
                # 保证不会抽到重复，若抽了10次还是一样的就放弃了（不会吧不会吧）
                retry = 1
                illust = random_illust(illusts, handler.random_method)
                while retry < 10 and illust["id"] in selected:
                    illust = random_illust(illusts, handler.random_method)
                    retry = retry + 1
                selected[illust["id"]] = illust
                log.info(f"""{handler.tag}: selected illust [{illust["id"]}]""")
            for i in selected:
                tasks.append(asyncio.create_task(make_illust_message(selected[i])))

        for task in asyncio.as_completed(tasks):
            try:
                yield await task
            except Exception as exc:
                yield handler.generate_error_message(exc)
