from pixivpy3 import AppPixivAPI, ByPassSniApi

from utils import settings

if settings["pixiv"]["bypass"]:
    papi = ByPassSniApi()
    papi.require_appapi_hosts()
else:
    papi = AppPixivAPI()

papi.set_accept_language('zh-cn')
papi.login(settings["pixiv"]["username"], settings["pixiv"]["password"])
