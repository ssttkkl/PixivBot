import asyncio
import typing as T

from mirai import *

from message_reactor import *
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

reactor = {
    "ranking": PixivRankingProvider(settings["ranking"]),
    "illust": PixivIllustProvider(settings["illust"]),
    "shuffle_illust": PixivShuffleIllustProvider(settings["shuffle_illust"]),
    "shuffle_illustrator_illust": PixivShuffleIllustratorIllustProvider(settings["shuffle_illustrator_illust"]),
    "shuffle_bookmarks": PixivShuffleBookmarksProvider(settings["shuffle_bookmarks"])
}


async def on_receive(function_dict: dict, bot: Mirai, source: Source, subject: T.Union[Group, Friend],
                     message: MessageChain):
    if function_dict["listen"] is not None and subject.id not in function_dict["listen"]:
        return

    for key in reactor:
        if function_dict[key]:
            await reactor[key].receive(bot, source, subject, message)


@bot.receiver("GroupMessage")
async def group_receiver(bot: Mirai, source: Source, group: Group, message: MessageChain):
    await on_receive(settings["function"]["group"], bot, source, group, message)


@bot.receiver("FriendMessage")
async def friend_receiver(bot: Mirai, source: Source, friend: Friend, message: MessageChain):
    await on_receive(settings["function"]["friend"], bot, source, friend, message)


if __name__ == "__main__":
    bot.run()
