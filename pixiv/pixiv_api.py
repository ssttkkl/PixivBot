from pixivpy3 import AppPixivAPI, ByPassSniApi

from utils import settings, log

if settings["pixiv"]["proxy"] is not None:
    proxies = {
        'http': settings["pixiv"]["proxy"],
        'https': settings["pixiv"]["proxy"]
    }
else:
    proxies = None

if settings["pixiv"]["bypass"]:
    papi = ByPassSniApi(proxies=proxies)
    papi.require_appapi_hosts()
else:
    papi = AppPixivAPI(proxies=proxies)

papi.set_accept_language('zh-cn')


def auth():
    papi.login(settings["pixiv"]["username"], settings["pixiv"]["password"])
    log.info("pixiv login succeeded")
