PixivBot
===== 

[![Build and Publish](https://github.com/ssttkkl/PixivBot/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/ssttkkl/PixivBot/actions/workflows/docker-publish.yml)

~~集成插件[nonebot-plugin-pixivbot](https://github.com/ssttkkl/nonebot-plugin-pixivbot)多协议版本的NoneBot实例的Docker镜像，适用于Docker方式部署。~~

~~非Docker方式可自行创建NoneBot实例并安装[nonebot-plugin-pixivbot](https://github.com/ssttkkl/nonebot-plugin-pixivbot)插件。~~

本项目将不再更新，请自行使用NoneBot2安装[nonebot-plugin-pixivbot](https://github.com/ssttkkl/nonebot-plugin-pixivbot)插件进行使用。

## 开始使用

### 事前准备

登录pixiv账号并获取refresh_token。（参考：[@ZipFile Pixiv OAuth Flow](https://gist.github.com/ZipFile/c9ebedb224406f4f11845ab700124362)）

### 选择版本

- [反向驱动器](./reverse/README.md)：支持OneBot V11
- [正向WS驱动器](./ws/README.md)：支持OneBot V11、KOOK（开黑啦）、Telegram

### 添加其他插件

1. 配置并启动Bot容器

2. 安装nb-cli
 
```shell
docker exec bot pip install nb-cli
```

3. 安装其他插件
```shell
docker exec bot nb plugin install <插件名>
```

4. 重启容器
```shell
docker restart bot
```

## Special Thanks

[Mikubill/pixivpy-async](https://github.com/Mikubill/pixivpy-async)

[nonebot/nonebot2](https://github.com/nonebot/nonebot2)

## 在线乞讨

<details><summary>点击请我打两把maimai</summary>

![](https://github.com/ssttkkl/ssttkkl/blob/main/afdian-ssttkkl.jfif)

</details>

## LICENSE

```
MIT License

Copyright (c) 2021 ssttkkl

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

```
