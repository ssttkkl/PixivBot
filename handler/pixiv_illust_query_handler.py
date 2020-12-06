import asyncio
import re
import typing as T

from graia.application import GraiaMiraiApplication, Group, Friend, MessageChain
from loguru import logger

from pixiv import make_illust_message, papi, PixivResultError
from utils import launch
from .abstract_message_handler import AbstractMessageHandler


class PixivIllustQueryHandler(AbstractMessageHandler):

    async def handle(self, app: GraiaMiraiApplication,
                     subject: T.Union[Group, Friend],
                     message: MessageChain,
                     channel: asyncio.Queue) -> bool:
        # 检测是否触发
        accept = False
        content = message.asDisplay()
        for x in self.trigger:
            if x in content:
                accept = True
                break

        if not accept:
            return False

        # 提取消息中的所有id
        regex = re.compile("[1-9][0-9]*")
        ids = [int(x) for x in regex.findall(content)]
        logger.info(f"{self.tag}: {ids}")

        # 每个id建立一个task，以获取插画并扔到channel中
        async def make_msg(illust_id):
            try:
                result = await launch(papi.illust_detail, illust_id=illust_id)
                if "error" in result:
                    raise PixivResultError(result["error"])
                else:
                    msg = await make_illust_message(result["illust"])
                    logger.info(f"""{self.tag}: [{result["illust"]["id"]}] ok""")
            except Exception as exc:
                msg = self.handle_and_make_error_message(exc)

            await channel.put(msg)

        tasks = []
        for x in ids:
            tasks.append(asyncio.create_task(make_msg(x)))

        await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
        return True
