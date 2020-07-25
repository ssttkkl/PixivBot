import asyncio
import typing as T

from mirai import *

from handler import *
from pixiv import clean_cache, auth
from utils import settings, log, launch, start_reply_queue

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
    "ranking":
        PixivRankingQueryHandler("ranking query", settings["ranking"]),
    "illust":
        PixivIllustQueryHandler("illust query", settings["illust"]),
    "random_illust":
        PixivRandomIllustQueryHandler("random illust query", settings["random_illust"]),
    "random_user_illust":
        PixivRandomUserIllustQueryHandler("random user illust query", settings["random_user_illust"]),
    "random_bookmark":
        PixivRandomBookmarkQueryHandler("random bookmark query", settings["random_bookmarks"])
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


@bot.subroutine
async def prepare_bot(bot: Mirai):
    start_reply_queue()

    async def watchman():
        while True:
            await launch(auth)
            await launch(clean_cache)
            # 睡一个小时
            await asyncio.sleep(3600)

    asyncio.create_task(watchman())


if __name__ == "__main__":
    bot.run()
