import asyncio
import typing as T

from graia.application import MessageChain
from graia.application.message.elements.internal import Plain, Image

from utils import settings
from .illust_cacher import cache_illust
from .illust_utils import has_tag

block_tags: T.Sequence[str] = settings["illust"]["block_tags"]
block_mode: str = settings["illust"]["block_mode"]
block_message: str = settings["illust"]["block_message"]
download_timeout_message: str = settings["illust"]["download_timeout_message"]
reply_pattern: str = settings["illust"]["reply_pattern"]


async def make_illust_message(illust: dict) -> MessageChain:
    """
    将给定illust按照模板转换为message
    :param illust: 给定illust
    :return: 转换后的message
    """

    string = reply_pattern.replace("$title", illust["title"]) \
        .replace("$tags", " ".join(map(lambda x: x["name"], illust["tags"]))) \
        .replace("$id", str(illust["id"]))

    illegal_tags = []
    for tag in block_tags:
        if has_tag(illust, tag):
            illegal_tags.append(tag)

    message = []

    if len(illegal_tags) > 0:
        block_message_formatted = block_message.replace("%tag", ' '.join(illegal_tags))
        if block_mode == "escape_img":
            message.append(Plain(string + '\n' + block_message_formatted))
        elif block_mode == "fully_block":
            message.append(Plain(block_message_formatted))
        else:
            raise ValueError("illegal block_mode value: " + block_mode)
    else:
        message.append(Plain(string))
        try:
            b = await cache_illust(illust)
            message.append(Image.fromUnsafeBytes(b))
        except asyncio.TimeoutError:
            message.append(Plain(download_timeout_message))
        except Exception as e:
            message.append(Plain(f"{type(e)} {str(e)}"))

    return MessageChain.create(message)
