import typing as T

from loguru import logger as log
from mirai import *

from handler import *
from settings import *

qq = settings["mirai"]["qq"]
authKey = settings["mirai"]["auth_key"]
host = settings["mirai"]["host"]
port = settings["mirai"]["port"]
locate = f"{host}:{port}/"
if settings["mirai"]["enable_websocket"]:
    locate = locate + "ws"

url = f"mirai://{locate}?authKey={authKey}&qq={qq}"
log.info("Connecting " + url)
bot = Mirai(url)

handlers = {
    "ranking_query":
        PixivRankingQueryHandler("ranking query", settings["ranking"]),
    "illust_query":
        PixivIllustQueryHandler("illust query", settings["illust"]),
    "random_illust_query":
        PixivRandomIllustQueryHandler("random illust query", settings["shuffle_illust"]),
    "random_user_illust_query":
        PixivRandomUserIllustQueryHandler("random user illust query", settings["shuffle_illustrator_illust"]),
    "random_bookmark_query":
        PixivRandomBookmarkQueryHandler("random bookmark query", settings["shuffle_bookmarks"])
}


async def on_receive(function_dict: dict, bot: Mirai, source: Source, subject: T.Union[Group, Friend],
                     message: MessageChain):
    if function_dict["listen"] is not None and subject.id not in function_dict["listen"]:
        return

    for key in handlers:
        if function_dict[key]:
            await handlers[key].receive(bot, source, subject, message)


@bot.receiver("GroupMessage")
async def group_receiver(bot: Mirai, source: Source, group: Group, message: MessageChain):
    await on_receive(settings["function"]["group"], bot, source, group, message)


@bot.receiver("FriendMessage")
async def friend_receiver(bot: Mirai, source: Source, friend: Friend, message: MessageChain):
    await on_receive(settings["function"]["friend"], bot, source, friend, message)


if __name__ == "__main__":
    bot.run()
