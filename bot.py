import asyncio
import typing as T

from graia.application import GraiaMiraiApplication, Session
from graia.application.event.lifecycle import ApplicationLaunched, ApplicationShutdowned
from graia.application.message.chain import MessageChain
from graia.broadcast import Broadcast

from handler import *
from my_logger import MyLogger
from pixiv import start_auto_auth, start_search_helper, start_illust_cacher, stop_illust_cacher, stop_search_helper
from utils import settings, start_reply_queue, stop_reply_queue

loop = asyncio.get_event_loop()
bcc = Broadcast(loop=loop)
app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host=f"""http://{settings["mirai"]["host"]}:{settings["mirai"]["port"]}""",  # 填入 httpapi 服务运行的地址
        authKey=settings["mirai"]["auth_key"],  # 填入 authKey
        account=int(settings["mirai"]["qq"]),  # 你的机器人的 qq 号
        # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
        websocket=settings["mirai"]["enable_websocket"]
    ),
    logger=MyLogger()
)

handlers = {
    "ranking": PixivRankingQueryHandler(
        tag="ranking query",
        settings=settings["ranking"],
        bcc=bcc,
        allow_friend=settings["function"]["friend"]["listen"] if settings["function"]["friend"]["ranking"] else [],
        allow_group=settings["function"]["group"]["listen"] if settings["function"]["group"]["ranking"] else []
    ),
    "illust": PixivIllustQueryHandler(
        tag="illust query",
        settings=settings["illust"],
        bcc=bcc,
        allow_friend=settings["function"]["friend"]["listen"] if settings["function"]["friend"]["illust"] else [],
        allow_group=settings["function"]["group"]["listen"] if settings["function"]["group"]["illust"] else []
    ),
    "random_illust": PixivRandomIllustQueryHandler(
        tag="random illust query",
        settings=settings["random_illust"],
        bcc=bcc,
        allow_friend=settings["function"]["friend"]["listen"] if settings["function"]["friend"][
            "random_illust"] else [],
        allow_group=settings["function"]["group"]["listen"] if settings["function"]["group"]["random_illust"] else []
    ),
    "random_user_illust": PixivRandomUserIllustQueryHandler(
        tag="random user illust query",
        settings=settings["random_user_illust"],
        bcc=bcc,
        allow_friend=settings["function"]["friend"]["listen"] if settings["function"]["friend"][
            "random_user_illust"] else [],
        allow_group=settings["function"]["group"]["listen"] if settings["function"]["group"][
            "random_user_illust"] else []
    ),
    "random_bookmark": PixivRandomBookmarkQueryHandler(
        tag="random bookmark query",
        settings=settings["random_bookmarks"],
        bcc=bcc,
        allow_friend=settings["function"]["friend"]["listen"] if settings["function"]["friend"][
            "random_bookmark"] else [],
        allow_group=settings["function"]["group"]["listen"] if settings["function"]["group"][
            "random_bookmark"] else []
    )
}


@bcc.receiver(ApplicationLaunched, priority=16)
async def prepare_bot():
    start_auto_auth()
    await start_reply_queue()
    await start_search_helper()
    await start_illust_cacher()


@bcc.receiver(ApplicationShutdowned, priority=16)
async def close_bot():
    await stop_reply_queue()
    await stop_search_helper()
    await stop_illust_cacher()


if __name__ == "__main__":
    app.launch_blocking()
