from mirai import *

import pixiv_illust_provider
import pixiv_ranking_provider
import pixiv_shuffle_bookmarks_provider
import pixiv_shuffle_illust_provider
from settings import settings

qq = settings["mirai"]["qq"]
authKey = settings["mirai"]["auth_key"]
mirai_api_http_locate = f"""localhost:{settings["mirai"]["port"]}/"""

bot = Mirai(f"mirai://{mirai_api_http_locate}?authKey={authKey}&qq={qq}")


@bot.receiver("GroupMessage")
async def pixiv_ranking_provider_group_receiver(bot: Mirai, source: Source, group: Group, message: MessageChain):
    await pixiv_ranking_provider.receive(bot, source, group, message)


@bot.receiver("FriendMessage")
async def pixiv_ranking_provider_friend_receiver(bot: Mirai, source: Source, friend: Friend, message: MessageChain):
    await pixiv_ranking_provider.receive(bot, source, friend, message)


@bot.receiver("GroupMessage")
async def pixiv_illust_provider_group_receiver(bot: Mirai, source: Source, group: Group, message: MessageChain):
    await pixiv_illust_provider.receive(bot, source, group, message)


@bot.receiver("FriendMessage")
async def pixiv_illust_provider_friend_receiver(bot: Mirai, source: Source, friend: Friend, message: MessageChain):
    await pixiv_illust_provider.receive(bot, source, friend, message)


@bot.receiver("GroupMessage")
async def pixiv_shuffle_illust_provider_group_receiver(bot: Mirai, source: Source, group: Group, message: MessageChain):
    await pixiv_shuffle_illust_provider.receive(bot, source, group, message)


@bot.receiver("FriendMessage")
async def pixiv_shuffle_illust_provider_friend_receiver(bot: Mirai, source: Source, friend: Friend,
                                                        message: MessageChain):
    await pixiv_shuffle_illust_provider.receive(bot, source, friend, message)


@bot.receiver("FriendMessage")
async def pixiv_shuffle_bookmarks_provider_friend_receiver(bot: Mirai, source: Source,
                                                           friend: Friend, message: MessageChain):
    await pixiv_shuffle_bookmarks_provider.receive(bot, source, friend, message)


if __name__ == "__main__":
    bot.run()
