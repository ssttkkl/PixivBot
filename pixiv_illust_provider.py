import re
import traceback
import typing as T

import pixiv_api
from bot_utils import *
from settings import settings


async def receive(bot: Mirai, source: Source, subject: T.Union[Group, Friend], message: MessageChain):
    try:
        plain = message.getFirstComponent(Plain)
        if plain is None:
            return
        content = plain.toString()

        if settings["illust"]["trigger"] in content:
            for match_result in re.finditer("[1-9][0-9]*", content):
                illust_id = int(match_result.group())
                print(f"pixiv illust {illust_id} asked.")

                result = pixiv_api.api().illust_detail(illust_id)
                if "error" in result:
                    error_message = [Plain(result["error"]["user_message"])]
                    await reply(bot, source, subject, error_message)
                else:
                    await reply(bot, source, subject, pixiv_api.illust_to_message(result["illust"]))
    except Exception as exc:
        traceback.print_exc()
        await reply(bot, source, subject, [Plain(str(exc)[:128])])
