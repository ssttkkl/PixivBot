import asyncio
import re
import typing as T

from graia.application import GraiaMiraiApplication, Group, Friend, MessageChain
from graia.broadcast import ExecutionStop
from loguru import logger

from pixiv import make_illust_message, papi, PixivResultError
from utils import launch
from .sender_filter_query_handler import SenderFilterQueryHandler


class PixivIllustQueryHandler(SenderFilterQueryHandler):

    def judge(self, app: GraiaMiraiApplication,
              subject: T.Union[Group, Friend],
              message: MessageChain):
        super().judge(app, subject, message)
        content = message.asDisplay()
        for x in self.trigger:
            if x in content:
                return
        raise ExecutionStop()

    async def make_msg(self, illust_id):
        result = await launch(papi.illust_detail, illust_id=illust_id)
        if "error" in result:
            raise PixivResultError(result["error"])
        else:
            msg = await make_illust_message(result["illust"])
            logger.info(f"""{self.tag}: [{result["illust"]["id"]}] ok""")
            return msg

    async def generate_reply(self, app: GraiaMiraiApplication,
                             subject: T.Union[Group, Friend],
                             message: MessageChain) -> T.AsyncGenerator[str, T.Any]:
        content = message.asDisplay()

        regex = re.compile("[1-9][0-9]*")
        ids = [int(x) for x in regex.findall(content)]
        logger.info(f"{self.tag}: {ids}")

        tasks = []
        for x in ids:
            tasks.append(asyncio.create_task(self.make_msg(x)))

        for ft in asyncio.as_completed(tasks):
            try:
                yield await ft
            except Exception as exc:
                yield self.generate_error_message(exc)
