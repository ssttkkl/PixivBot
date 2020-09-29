import asyncio
import typing as T

from graia.application import MessageChain
from graia.application.message.elements.internal import Plain, Image
from graia.template import Template

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
    msg = Template(reply_pattern).render(
        title=Plain(illust["title"]),
        tags=Plain(" ".join(map(lambda x: x["name"], illust["tags"]))),
        id=Plain(str(illust["id"]))
    )

    illegal_tags = []
    for tag in block_tags:
        if has_tag(illust, tag):
            illegal_tags.append(tag)

    if len(illegal_tags) > 0:
        block_msg = Template(block_message).render(
            tag=Plain(' '.join(illegal_tags))
        )
        if block_mode == "escape_img":
            return msg.plusWith(block_msg)
        elif block_mode == "fully_block":
            return block_msg
        else:
            raise ValueError("illegal block_mode value: " + block_mode)

    try:
        b = await cache_illust(illust)
        img_msg = MessageChain.create([Image.fromUnsafeBytes(b)])
    except asyncio.TimeoutError:
        img_msg = MessageChain.create([Plain(download_timeout_message)])
    except Exception as e:
        img_msg = MessageChain.create([Plain(f"{type(e)} {str(e)}")])
    msg.plus(img_msg)

    return msg
