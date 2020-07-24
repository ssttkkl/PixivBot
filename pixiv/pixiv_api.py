from pixivpy3 import AppPixivAPI, ByPassSniApi

from utils import settings,log

if settings["pixiv"]["bypass"]:
    papi = ByPassSniApi()
    papi.require_appapi_hosts()
else:
    papi = AppPixivAPI()

papi.set_accept_language('zh-cn')


def auth():
    papi.login(settings["pixiv"]["username"], settings["pixiv"]["password"])
    log.info("pixiv login succeeded")
