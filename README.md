PixivBot
=====

仅集成了NoneBot插件[nonebot-plugin-pixivbot](https://github.com/ssttkkl/nonebot-plugin-pixivbot)的Bot。

注：本项目已彻底从Mirai/Graia框架迁移至NoneBot2框架，旧版本用户请重新进行配置。

## 环境配置

1. 将本仓库clone到本地；
2. 别忘了`pip install -r requirement.txt`安装依赖包；
3. 下载go-cqhttp并配置连接（参考[CQHTTP 协议使用指南 | NoneBot](https://v2.nonebot.dev/guide/cqhttp-guide.html)）；
3. 安装MongoDB（用于保存缓存）；
4. 在.env.prod中修改配置（至少需要下述的最小配置项才能工作）；
5. 运行`python /src/plugins/nonebot-plugin-pixivbot/mongo_helper.py`配置索引（本插件依赖MongoDB的TTL索引自动清理过期缓存）；
6. `nb run`运行bot。

## 触发语句

普通语句：

- **看看榜**：查看pixiv榜单的第1到第3名（榜单类型和默认查询范围可以在设置文件更改）
- **看看榜*21-25***：查看pixiv榜单的第21到第25名
- **看看榜*50***：查看pixiv榜单的第50名
- **来张图**：从推荐插画随机抽选一张插画
- **来张*初音ミク*图**：搜索关键字*初音ミク*，从搜索结果随机抽选一张插画
- **来张*森倉円*老师的图**：搜索画师*森倉円*，从该画师的插画列表里随机抽选一张插画
- **看看图*114514***：查看id为*114514*的插画
- **来张私家车**：从书签中随机抽选一张插画

订阅语句（只有SUPERUSER才能触发）：

- **/pixivbot subscribe \<type\> \<schedule\>**：为本群（本用户）订阅类型为<type>的定时推送功能，时间满足<schedule>时进行推送
    - \<type\>：可选值有ranking, random_bookmark, random_recommended_illust
    - \<schedule\>：有三种格式，*00:30\*x*为每隔30分钟进行一次推送，*12:00*为每天12:00进行一次推送，*00:10+00:30\*x*为从今天00:10开始每隔30分钟进行一次推送（开始时间若是一个过去的时间点，则从下一个开始推送的时间点进行推送）
- **/pixivbot subscribe**：查看本群（本用户）的所有订阅
- **/pixivbot unsubscribe \<type\>**：取消本群（本用户）的订阅
    - \<type\>：可选值有all, ranking, random_bookmark, random_recommended_illust

## 注意事项

1. 必须登录pixiv账号并获取refresh_token才能使用。（参考：[@ZipFile Pixiv OAuth Flow](https://gist.github.com/ZipFile/c9ebedb224406f4f11845ab700124362)）
2. **搜索请求**太频繁会撞Rate Limit、收到警告甚至被ban号，不建议大群内使用。（或者只开放部分功能当普通的涩图bot）
3. 根据1和2，建议使用小号登录。
4. 学业繁忙，issue可能不会及时处理。

## .env

最小配置：
```
PIXIV_MONGO_CONN_URL=
PIXIV_MONGO_DATABASE_NAME=pixiv_bot
PIXIV_REFRESH_TOKEN=
SUPERUSERS=[]
```

这里给出配置文件模型的python代码定义：

```python
pixiv_refresh_token: str
pixiv_mongo_conn_url: str
pixiv_mongo_database_name: str
pixiv_proxy: typing.Optional[str]
pixiv_query_timeout: int = 60

pixiv_block_tags: typing.List[str] = []
pixiv_block_action: str = "no_image"  # ['no_image', 'completely_block', 'no_reply']

pixiv_download_quantity: str = "original"  # ['original', 'square_medium', 'medium', 'large']
pixiv_download_custom_domain: typing.Optional[str]

pixiv_compression_enabled: bool = False
pixiv_compression_max_size: typing.Optional[int]
pixiv_compression_quantity: typing.Optional[float]

pixiv_illust_query_enabled = True

pixiv_query_cooldown = 0
pixiv_no_query_cooldown_users = []

pixiv_ranking_query_enabled = True
pixiv_ranking_default_mode: str = "day"  # ['day', 'week', 'month', 'day_male', 'day_female', 'week_original', 'week_rookie', 'day_manga']
pixiv_ranking_default_range = [1, 3]
pixiv_ranking_fetch_item = 150
pixiv_ranking_max_item_per_msg = 5

pixiv_random_illust_query_enabled = True
pixiv_random_illust_method = "bookmark_proportion"  # ['bookmark_proportion', 'view_proportion', 'timedelta_proportion', 'uniform']
pixiv_random_illust_min_bookmark = 0
pixiv_random_illust_min_view = 0
pixiv_random_illust_max_page = 20
pixiv_random_illust_max_item = 500

pixiv_random_recommended_illust_query_enabled = True
pixiv_random_recommended_illust_method = "uniform"  # ['bookmark_proportion', 'view_proportion', 'timedelta_proportion', 'uniform']
pixiv_random_recommended_illust_min_bookmark = 0
pixiv_random_recommended_illust_min_view = 0
pixiv_random_recommended_illust_max_page = 40
pixiv_random_recommended_illust_max_item = 1000

pixiv_random_user_illust_query_enabled = True
pixiv_random_user_illust_method = "timedelta_proportion"  # ['bookmark_proportion', 'view_proportion', 'timedelta_proportion', 'uniform']
pixiv_random_user_illust_min_bookmark = 0
pixiv_random_user_illust_min_view = 0
pixiv_random_user_illust_max_page = 2 ** 31
pixiv_random_user_illust_max_item = 2 ** 31

pixiv_random_bookmark_query_enabled = True
pixiv_random_bookmark_user_id = 0
pixiv_random_bookmark_method = "uniform"  # ['bookmark_proportion', 'view_proportion', 'timedelta_proportion', 'uniform']
pixiv_random_bookmark_min_bookmark = 0
pixiv_random_bookmark_min_view = 0
pixiv_random_bookmark_max_page = 2 ** 31
pixiv_random_bookmark_max_item = 2 ** 31

pixiv_poke_action: typing.Optional[str] = "random_recommended_illust"  # ["", "ranking", "random_recommended_illust", "random_bookmark"]
```

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
