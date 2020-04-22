import typing

from mirai import *


async def reply(bot: Mirai, source: Source, subject: typing.Union[Group, Friend], message):
    if isinstance(subject, Group):
        await bot.sendGroupMessage(group=subject, message=message, quoteSource=source)
    elif isinstance(subject, Friend):
        await bot.sendFriendMessage(friend=subject, message=message)
