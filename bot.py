import asyncio
import typing as T

from mirai import *

import pixiv_illust_provider
import pixiv_ranking_provider
import pixiv_shuffle_bookmarks_provider
import pixiv_shuffle_illust_provider
import pixiv_shuffle_illustrator_illust_provider
from settings import settings

qq = settings["mirai"]["qq"]
authKey = settings["mirai"]["auth_key"]
port = settings["mirai"]["port"]
mirai_api_http_locate = f"localhost:{port}/"
if settings["mirai"]["enable_websocket"]:
    mirai_api_http_locate = mirai_api_http_locate + "ws"

url = f"mirai://{mirai_api_http_locate}?authKey={authKey}&qq={qq}"
print("Connecting " + url)
bot = Mirai(url)

group_function = settings["function"]["group"]
friend_function = settings["function"]["friend"]


async def on_receive(function_dict: dict, bot: Mirai, source: Source, subject: T.Union[Group, Friend],
                     message: MessageChain):
    if function_dict["listen"] is not None and subject.id not in function_dict["listen"]:
        return

    if function_dict["ranking"]:
        await pixiv_ranking_provider.receive(bot, source, subject, message)
    if function_dict["illust"]:
        await pixiv_illust_provider.receive(bot, source, subject, message)
    if function_dict["shuffle_illust"]:
        await pixiv_shuffle_illust_provider.receive(bot, source, subject, message)
    if function_dict["shuffle_bookmarks"]:
        await pixiv_shuffle_bookmarks_provider.receive(bot, source, subject, message)
    if function_dict["shuffle_illustrator"]:
        await pixiv_shuffle_illustrator_illust_provider.receive(bot, source, subject, message)


@bot.receiver("GroupMessage")
async def group_receiver(bot: Mirai, source: Source, group: Group, message: MessageChain):
    asyncio.create_task(on_receive(group_function, bot, source, group, message))


@bot.receiver("FriendMessage")
async def friend_receiver(bot: Mirai, source: Source, friend: Friend, message: MessageChain):
    asyncio.create_task(on_receive(friend_function, bot, source, friend, message))


if __name__ == "__main__":
    bot.run()

