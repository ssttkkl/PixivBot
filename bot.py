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


@bot.receiver("GroupMessage")
async def group_receiver(bot: Mirai, source: Source, group: Group, message: MessageChain):
    if group_function["listen"] is not None and group.id not in group_function["listen"]:
        return

    if group_function["ranking"]:
        await pixiv_ranking_provider.receive(bot, source, group, message)
    if group_function["illust"]:
        await pixiv_illust_provider.receive(bot, source, group, message)
    if group_function["shuffle_illust"]:
        await pixiv_shuffle_illust_provider.receive(bot, source, group, message)
    if group_function["shuffle_bookmarks"]:
        await pixiv_shuffle_bookmarks_provider.receive(bot, source, group, message)
    if group_function["shuffle_illustrator"]:
        await pixiv_shuffle_illustrator_illust_provider.receive(bot, source, group, message)


@bot.receiver("FriendMessage")
async def friend_receiver(bot: Mirai, source: Source, friend: Friend, message: MessageChain):
    if friend_function["listen"] is not None and friend.id not in friend_function["listen"]:
        return

    if friend_function["ranking"]:
        await pixiv_ranking_provider.receive(bot, source, friend, message)
    if friend_function["illust"]:
        await pixiv_illust_provider.receive(bot, source, friend, message)
    if friend_function["shuffle_illust"]:
        await pixiv_shuffle_illust_provider.receive(bot, source, friend, message)
    if friend_function["shuffle_bookmarks"]:
        await pixiv_shuffle_bookmarks_provider.receive(bot, source, friend, message)
    if friend_function["shuffle_illustrator"]:
        await pixiv_shuffle_illustrator_illust_provider.receive(bot, source, friend, message)


if __name__ == "__main__":
    bot.run()
