#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import nonebot
from nonebot.adapters.onebot.v11 import Adapter


nonebot.init()
app = nonebot.get_asgi()

driver = nonebot.get_driver()
driver.register_adapter(Adapter)

nonebot.load_plugins("src/plugins")


if __name__ == "__main__":
    nonebot.logger.warning("请使用指令[nb run]来运行此项目!")
    nonebot.run()
