PixivBot
=====

集成NoneBot插件[nonebot-plugin-pixivbot](https://github.com/ssttkkl/nonebot-plugin-pixivbot)多协议版本的Bot。

## 触发语句

### 普通语句

所有数字参数均支持中文数字和罗马数字。

- **看看<类型>榜<范围>**：查看pixiv榜单（<类型>可省略，<范围>应为a-b或a）
  - 示例：看看榜、看看日榜、看看榜1-5、看看月榜一
- **来<数量>张图**：从推荐插画随机抽选一张插画（<数量>可省略，下同）
  - 示例：来张图、来五张图
- **来<数量>张<关键字>图**：搜索关键字，从搜索结果随机抽选一张插画
  - 示例：来张初音ミク图、来五张初音ミク图
  - 注：默认开启关键字翻译功能。Bot会在平时的数据爬取时记录各个Tag的中文翻译。在搜索时，若关键字的日文翻译存在，则使用日文翻译代替关键字进行搜索。
- **来<数量>张<用户>老师的图**：搜索用户，从插画列表中随机抽选一张插画
  - 示例：来张Rella老师的图、来五张Rella老师的图
- **看看图<插画ID>**：查看ID对应的插画
  - 示例：看看图114514
- **来<数量>张私家车**：从书签中随机抽选一张插画（发送者需绑定Pixiv账号，或者在配置中指定默认Pixiv账号）
  - 示例：来张私家车、来五张私家车
- **还要**：重复上一次请求
- **不够色**：获取上一张插画的相关插画

### 命令语句

- **/pixivbot schedule \<type\> \<schedule\> [..args]**：为本群（本用户）订阅类型为<type>的定时推送功能，时间满足<schedule>时进行推送
    - \<type\>：可选值有ranking, random_bookmark, random_recommended_illust, random_illust, random_user_illust
    - \<schedule\>：有三种格式，*00:30\*x*为每隔30分钟进行一次推送，*12:00*为每天12:00进行一次推送，*00:10+00:30\*x*为从今天00:10开始每隔30分钟进行一次推送（开始时间若是一个过去的时间点，则从下一个开始推送的时间点进行推送）
    - [..args]：
      - \<type\>为ranking时，接受\<mode\> \<range\>
      - \<type\>为random_bookmark时，接受\<pixiv_user_id\>
      - \<type\>为random_illust时，接受\<word\>
      - \<type\>为random_user_illust时，接受\<user\>
- **/pixivbot schedule**：查看本群（本用户）的所有订阅
- **/pixivbot unschedule <type>**：取消本群（本用户）的订阅
- **/pixivbot bind <pixiv_user_id>**：绑定Pixiv账号（用于随机书签功能）
- **/pixivbot unbind**：解绑Pixiv账号
- **/pixivbot invalidate_cache**：清除缓存（只有超级用户能够发送此命令）
- **/pixivbot**、**/pixivbot help**：查看帮助


## 开始使用

### 事前准备

登录pixiv账号并获取refresh_token。（参考：[@ZipFile Pixiv OAuth Flow](https://gist.github.com/ZipFile/c9ebedb224406f4f11845ab700124362)）

### 选择版本

- [反向WebSocket](./reverse-ws/README.md)
- 正向WebSocket（调试中）

## Special Thanks

[Mikubill/pixivpy-async](https://github.com/Mikubill/pixivpy-async)

[nonebot/nonebot2](https://github.com/nonebot/nonebot2)


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
