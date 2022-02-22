PixivBot
=====

仅集成了NoneBot插件[nonebot-plugin-pixivbot](https://github.com/ssttkkl/nonebot-plugin-pixivbot)的Bot。

注：本项目已彻底从Mirai/Graia框架迁移至NoneBot2框架，旧版本用户请重新进行配置。

## 开始使用

事前准备：登录pixiv账号并获取refresh_token。（参考：[@ZipFile Pixiv OAuth Flow](https://gist.github.com/ZipFile/c9ebedb224406f4f11845ab700124362)）

### 通过 Docker 配置（推荐）

1. 安装Docker

2. 创建一个Docker网络
```
# 创建名为bot-net的Docker网络
$ docker network create bot-net
```

3. 安装MongoDB
```
# 拉取MongoDB镜像
$ docker pull mongo:latest

# 运行一个名为bot-mongo的MongoDB容器
$ docker run --network bot-net -itd --name bot-mongo mongo:latest --auth

# 登入MongoDB终端
$ docker exec -it bot-mongo mongo pixiv_bot

# 切换到admin数据库
$ use admin

# 创建一个名为admin，密码为123456的管理员用户。
> db.createUser({ user:'admin',pwd:'123456',roles:[ { role:'userAdminAnyDatabase', db: 'admin'},"readWriteAnyDatabase"]})

# 使用上面创建的管理员用户进行认证
> db.auth('admin', '123456')

# 切换到pixiv_bot数据库
> use pixiv_bot

# 创建一个名为pixiv_bot，密码为pixiv_bot的用户，该用户拥有pixiv_bot数据库的所有权限。
> db.createUser({ user : "pixiv_bot", pwd : "pixiv_bot", roles: [ { role : "dbOwner", db : "pixiv_bot" } ] })

# 退出MongoDB终端
> exit
```

4. 安装PixivBot

先将配置项写入文件env-file.txt，以便下一步导入（更多的配置项参考下文）
```
PIXIV_MONGO_CONN_URL=mongodb://pixiv_bot:pixiv_bot@bot-mongo:27017
PIXIV_MONGO_DATABASE_NAME=pixiv_bot
PIXIV_REFRESH_TOKEN=前面获取的REFRESH_TOKEN
SUPERUSERS=[能够发送超级命令的用户，逗号隔开]
```
```
# 将仓库拷贝到本地
$ git clone https://github.com/ssttkkl/PixivBot.git
$ git submodule update --init --recursive

# 构建Docker镜像
$ docker build -t pixiv-bot .
# 启动一个名为bot的Docker容器，监听所有IP的8080端口
$ docker run --network bot-net --name bot -e HOST=0.0.0.0 -e PORT=8080 --env-file env-file.txt -d pixiv-bot:latest
```

5. 安装go-cqhttp

```
# 克隆go-cqhttp仓库
$ git clone https://github.com/Mrs4s/go-cqhttp.git

# 构建Docker镜像
$ cd go-cqhttp
$ docker build -t go-cqhttp .

# 运行一个go-cqhttp容器，数据文件挂载到宿主机的/etc/go-cqhttp目录下
$ docker run --network bot-net -v /etc/go-cqhttp:/data --name bot-gocq -it go-cqhttp:latest
```

编辑/etc/go-cqhttp/config.yml文件，使用反向WebSocket连接
```yml
account:
  uin: 机器人QQ号
  password: 机器人密码

message:
  post-format: array

servers:
  - ws-reverse:
      universal: ws://bot:8080/cqhttp/ws
```

再次启动go-cqhttp容器
```
$ docker restart bot-gocq
```

### 手动配置

1. `git clone https://github.com/ssttkkl/PixivBot.git`；
2. `git submodule update --init --recursive`；
3. `pip install -r requirement.txt`；
4. 下载go-cqhttp并配置连接（参考[CQHTTP 协议使用指南 | NoneBot](https://v2.nonebot.dev/guide/cqhttp-guide.html)）；
5. 安装MongoDB，创建一个数据库用于保存缓存，并创建一个能够访问该数据库的用户；
6. 在.env.prod中修改配置；
7. `nb run`运行bot。

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
- **/pixivbot bind <pixiv_user_id>**：绑定Pixiv账号（用于随机书签功能）
- **/pixivbot unbind**：解绑Pixiv账号
- **/pixivbot invalidate_cache**：清除缓存

## 注意事项

1. 必须登录pixiv账号并获取refresh_token才能使用。
2. 尽管作者已经尽力以高并发作为目标进行开发，但由于向Pixiv发送**搜索请求**太频繁会撞Rate Limit、收到警告甚至被ban号，因此不保证并发用户数量较大时还能够正常使用。（或者只开放部分功能当普通的涩图bot）
3. 根据1和2，建议使用小号登录。
4. 学业繁忙，issue可能不会及时处理。

## 配置

最小配置：
```
PIXIV_MONGO_CONN_URL=  # mongodb://<用户名>:<密码>@<主机>:<端口>
PIXIV_MONGO_DATABASE_NAME=  # 数据库名称
PIXIV_REFRESH_TOKEN=  # 前面获取的REFRESH_TOKEN
SUPERUSERS=[]  # 只有SUPERUSERS能够发送超级命令
```

完整配置（除最小配置出现的配置项以外都是可选项，给出的是默认值）：
```
pixiv_refresh_token=  # 前面获取的REFRESH_TOKEN
pixiv_mongo_conn_url=  # MongoDB连接URL，格式：mongodb://<用户名>:<密码>@<主机>:<端口>
pixiv_mongo_database_name=  # 连接的MongoDB数据库
pixiv_proxy=None  # 代理URL
pixiv_query_timeout=60  # 查询超时（单位：秒）
pixiv_simultaneous_query=8  # 向Pixiv查询的并发数

pixiv_block_tags=[]  # 当插画含有指定tag时会被过滤
pixiv_block_action=no_image  # 过滤时的动作，可选值：no_image(不显示插画，回复插画信息), completely_block(只回复过滤提示), no_reply(无回复)

pixiv_download_quantity=original  # 插画下载品质，可选值：original, square_medium, medium, large
pixiv_download_custom_domain=None  # 使用反向代理下载插画的域名

pixiv_compression_enabled=False  # 启用插画压缩
pixiv_compression_max_size=None  # 插画压缩最大尺寸
pixiv_compression_quantity=None  # 插画压缩品质（0到100）

pixiv_illust_query_enabled=True  # 启用插画查询（看看图）功能

pixiv_query_cooldown=0  # 每次查询的冷却时间
pixiv_no_query_cooldown_users=[]  # 在这个列表中的用户不受冷却时间的影响

pixiv_ranking_query_enabled=True  # 启用榜单查询（看看榜）功能
pixiv_ranking_default_mode=day  # 默认查询的榜单，可选值：day, week, month, day_male, day_female, week_original, week_rookie, day_manga
pixiv_ranking_default_range=[1, 3]  # 默认查询的榜单范围
pixiv_ranking_fetch_item=150  # 每次从服务器获取的榜单项数（查询的榜单范围必须在这个数目内）
pixiv_ranking_max_item_per_query=5  # 每次榜单查询最多能查询多少项
pixiv_ranking_max_item_per_msg=1  # 榜单查询的回复信息每条包含多少项

pixiv_random_illust_query_enabled=True  # 启用关键字插画随机抽选（来张xx图）功能
pixiv_random_illust_method=bookmark_proportion  # 随机抽选方法，下同，可选值：bookmark_proportion(概率与书签数成正比), view_proportion(概率与阅读量成正比), timedelta_proportion(概率与投稿时间和现在的时间差成正比), uniform(相等概率)
pixiv_random_illust_min_bookmark=0  # 过滤掉书签数小于该值的插画，下同
pixiv_random_illust_min_view=0  # 过滤掉阅读量小于该值的插画，下同
pixiv_random_illust_max_page=20  # 每次从服务器获取的查询结果页数，下同
pixiv_random_illust_max_item=500  # 每次从服务器获取的查询结果项数，下同

pixiv_random_recommended_illust_query_enabled=True  # 启用推荐插画随机抽选（来张图）功能
pixiv_random_recommended_illust_method=uniform
pixiv_random_recommended_illust_min_bookmark=0
pixiv_random_recommended_illust_min_view=0
pixiv_random_recommended_illust_max_page=40
pixiv_random_recommended_illust_max_item=1000

pixiv_random_user_illust_query_enabled=True  # 启用用户插画随机抽选（来张xx老师的图）功能
pixiv_random_user_illust_method=timedelta_proportion
pixiv_random_user_illust_min_bookmark=0
pixiv_random_user_illust_min_view=0
pixiv_random_user_illust_max_page=2147483647
pixiv_random_user_illust_max_item=2147483647

pixiv_random_bookmark_query_enabled=True  # 启用用户书签随机抽选（来张私家车）功能
pixiv_random_bookmark_user_id=0  # 当QQ用户未绑定Pixiv账号时，从该Pixiv账号的书签内抽选
pixiv_random_bookmark_method=uniform
pixiv_random_bookmark_min_bookmark=0
pixiv_random_bookmark_min_view=0
pixiv_random_bookmark_max_page=2147483647
pixiv_random_bookmark_max_item=2147483647

pixiv_poke_action=random_recommended_illust  # 戳一戳的功能，可选值：空, ranking, random_recommended_illust, random_bookmark
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
