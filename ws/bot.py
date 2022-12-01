#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import nonebot
import uvloop
from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter
from nonebot.adapters.kaiheila import Adapter as KaiheilaAdapter
from nonebot.adapters.telegram import Adapter as TelegramAdapter

uvloop.install()
nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(OnebotV11Adapter)
driver.register_adapter(KaiheilaAdapter)
driver.register_adapter(TelegramAdapter)

nonebot.load_from_toml("pyproject.toml")


if __name__ == "__main__":
    nonebot.logger.warning("Always use `nb run` to start the bot instead of manually running!")
    nonebot.run()
