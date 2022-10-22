PixivBot (Reverse)
=====

## 开始使用

### 事前准备

登录pixiv账号并获取refresh_token。（参考：[@ZipFile Pixiv OAuth Flow](https://gist.github.com/ZipFile/c9ebedb224406f4f11845ab700124362)）

### 通过 Docker 配置（推荐非 Windows 用户使用此方式）

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

先将配置项写入文件/etc/pixivbot/.env.prod（更多的配置项参考下文）
```
PIXIV_MONGO_CONN_URL=mongodb://pixiv_bot:pixiv_bot@bot-mongo:27017/pixiv_bot?authSource=pixiv_bot
PIXIV_MONGO_DATABASE_NAME=pixiv_bot
PIXIV_REFRESH_TOKEN=  # 前面获取的REFRESH_TOKEN
SUPERUSERS=["onebot:123456"]  # 能够发送超级命令的用户（JSON数组，元素格式为"adapter:user_id"）
BLOCKLIST=["onebot:114514", "kaiheila:1919810"]  # Bot不响应的用户，可以避免Bot之间相互调用（JSON数组，元素格式为"adapter:user_id"）
```
```
# 拉取PixivBot镜像
$ docker pull ssttkkl/pixiv-bot:reverse

# 运行一个名为bot的PixivBot容器，监听8080端口，配置文件挂载到宿主机的/etc/pixivbot/.env.prod文件下
$ docker run --network bot-net -v /etc/pixivbot/.env.prod:/app/.env.prod --name bot -e HOST=0.0.0.0 -e PORT=8080 -d ssttkkl/pixiv-bot:reverse
```

5. 安装[Mrs4s/go-cqhttp](https://github.com/Mrs4s/go-cqhttp)（仅当需要搭建QQ Bot时）

先将配置项写入文件/etc/go-cqhttp/config.yml，使用反向WebSocket连接

```yml
account: # 账号相关
  uin: 123456 # QQ账号
  password: '' # 密码为空时使用扫码登录
  encrypt: false  # 是否开启密码加密
  status: 0      # 在线状态 请参考 https://docs.go-cqhttp.org/guide/config.html#在线状态
  relogin: # 重连设置
    delay: 3   # 首次重连延迟, 单位秒
    interval: 3   # 重连间隔
    max-times: 0  # 最大重连次数, 0为无限制

  # 是否使用服务器下发的新地址进行重连
  # 注意, 此设置可能导致在海外服务器上连接情况更差
  use-sso-address: true
  # 是否允许发送临时会话消息
  allow-temp-session: false

heartbeat:
  # 心跳频率, 单位秒
  # -1 为关闭心跳
  interval: 5

message:
  # 上报数据类型
  # 可选: string,array
  post-format: string
  # 是否忽略无效的CQ码, 如果为假将原样发送
  ignore-invalid-cqcode: false
  # 是否强制分片发送消息
  # 分片发送将会带来更快的速度
  # 但是兼容性会有些问题
  force-fragment: false
  # 是否将url分片发送
  fix-url: false
  # 下载图片等请求网络代理
  proxy-rewrite: ''
  # 是否上报自身消息
  report-self-message: false
  # 移除服务端的Reply附带的At
  remove-reply-at: false
  # 为Reply附加更多信息
  extra-reply-data: false
  # 跳过 Mime 扫描, 忽略错误数据
  skip-mime-scan: false

output:
  # 日志等级 trace,debug,info,warn,error
  log-level: warn
  # 日志时效 单位天. 超过这个时间之前的日志将会被自动删除. 设置为 0 表示永久保留.
  log-aging: 15
  # 是否在每次启动时强制创建全新的文件储存日志. 为 false 的情况下将会在上次启动时创建的日志文件续写
  log-force-new: true
  # 是否启用日志颜色
  log-colorful: true
  # 是否启用 DEBUG
  debug: false # 开启调试模式

# 默认中间件锚点
default-middlewares: &default
  # 访问密钥, 强烈推荐在公网的服务器设置
  access-token: ''
  # 事件过滤器文件目录
  filter: ''
  # API限速设置
  # 该设置为全局生效
  # 原 cqhttp 虽然启用了 rate_limit 后缀, 但是基本没插件适配
  # 目前该限速设置为令牌桶算法, 请参考:
  # https://baike.baidu.com/item/%E4%BB%A4%E7%89%8C%E6%A1%B6%E7%AE%97%E6%B3%95/6597000?fr=aladdin
  rate-limit:
    enabled: false # 是否启用限速
    frequency: 1  # 令牌回复频率, 单位秒
    bucket: 1     # 令牌桶大小

database: # 数据库相关设置
  leveldb:
    # 是否启用内置leveldb数据库
    # 启用将会增加10-20MB的内存占用和一定的磁盘空间
    # 关闭将无法使用 撤回 回复 get_msg 等上下文相关功能
    enable: true

  # 媒体文件缓存， 删除此项则使用缓存文件(旧版行为)
  cache:
    image: data/image.db
    video: data/video.db

# 连接服务列表
servers:
  - ws-reverse:
      universal: ws://bot:8080/onebot/v11/ws
```

```
# 拉取go-cqhttp镜像
$ docker pull silicer/go-cqhttp:latest

# 运行一个名为bot-gocq的go-cqhttp容器，数据目录挂载到宿主机的/etc/go-cqhttp目录下
$ docker run --network bot-net -v /etc/go-cqhttp:/data --name bot-gocq -d silicer/go-cqhttp:latest
```

#### 附：如何更新

```
# 停止旧Docker容器
$ docker stop bot

# 移除旧Docker容器
$ docker rm bot

# 移除旧Docker镜像
$ docker image rm ssttkkl/pixiv-bot:reverse

# 拉取新PixivBot镜像
$ docker pull ssttkkl/pixiv-bot:reverse

# 运行新容器
$ docker run --network bot-net -v /etc/pixivbot/.env.prod:/app/.env.prod --name bot -e HOST=0.0.0.0 -e PORT=8080 -d ssttkkl/pixiv-bot:reverse
```

### 手动配置（推荐 Windows 用户使用此方式）

参考[创建项目 | NoneBot](https://v2.nonebot.dev/docs/tutorial/create-project)创建一个Bot，安装对应适配器的[ssttkkl/nonebot-plugin-pixivbot](https://github.com/ssttkkl/nonebot-plugin-pixivbot)插件

## 配置

最小配置：
```
pixiv_refresh_token=  # 前面获取的REFRESH_TOKEN
pixiv_mongo_conn_url=  # MongoDB连接URL，格式：mongodb://<用户名>:<密码>@<主机>:<端口>/<数据库>
pixiv_mongo_database_name=  # 连接的MongoDB数据库
```

完整配置（除最小配置出现的配置项以外都是可选项，给出的是默认值）（NoneBot配置项这里不列出，参考[配置 | NoneBot](https://v2.nonebot.dev/docs/tutorial/configuration#%E8%AF%A6%E7%BB%86%E9%85%8D%E7%BD%AE%E9%A1%B9)）：
```
superuser=[]  # 能够发送超级命令的用户（JSON数组，格式为["onebot:123456", "kaiheila:1919810"]，下同）
blocklist=[]  # Bot不响应的用户，可以避免Bot之间相互调用（JSON数组）

pixiv_refresh_token=  # 前面获取的REFRESH_TOKEN
pixiv_mongo_conn_url=  # MongoDB连接URL，格式：mongodb://<用户名>:<密码>@<主机>:<端口>/<数据库>
pixiv_mongo_database_name=  # 连接的MongoDB数据库
pixiv_proxy=None  # 代理URL
pixiv_query_timeout=60  # 查询超时（单位：秒）
pixiv_simultaneous_query=8  # 向Pixiv查询的并发数

# 缓存过期时间（单位：秒）
pixiv_download_cache_expires_in = 3600 * 24 * 7
pixiv_illust_detail_cache_expires_in = 3600 * 24 * 7
pixiv_user_detail_cache_expires_in = 3600 * 24 * 7
pixiv_illust_ranking_cache_expires_in = 3600 * 6
pixiv_search_illust_cache_expires_in = 3600 * 24
pixiv_search_user_cache_expires_in = 3600 * 24
pixiv_user_illusts_cache_expires_in = 3600 * 24
pixiv_user_bookmarks_cache_expires_in = 3600 * 24
pixiv_related_illusts_cache_expires_in = 3600 * 24
pixiv_other_cache_expires_in = 3600 * 6

pixiv_block_tags=[]  # 当插画含有指定tag时会被过滤
pixiv_block_action=no_image  # 过滤时的动作，可选值：no_image(不显示插画，回复插画信息), completely_block(只回复过滤提示), no_reply(无回复)

pixiv_download_quantity=original  # 插画下载品质，可选值：original, square_medium, medium, large
pixiv_download_custom_domain=None  # 使用反向代理下载插画的域名

pixiv_compression_enabled=False  # 启用插画压缩
pixiv_compression_max_size=None  # 插画压缩最大尺寸
pixiv_compression_quantity=None  # 插画压缩品质（0到100）

pixiv_query_to_me_only=False  # 只响应关于Bot的查询
pixiv_command_to_me_only=False  # 只响应关于Bot的命令

pixiv_query_cooldown=0  # 每次查询的冷却时间
pixiv_no_query_cooldown_users=[]  # 在这个列表中的用户不受冷却时间的影响（JSON数组）
pixiv_max_item_per_query=10  # 每个查询最多请求的插画数量

pixiv_tag_translation_enabled=True  # 启用搜索关键字翻译功能（平时搜索时记录标签翻译，在查询时判断是否存在对应中日翻译）

pixiv_more_enabled=True  # 启用重复上一次请求（还要）功能
pixiv_query_expires_in=10*60  # 上一次请求的过期时间（单位：秒）

pixiv_illust_query_enabled=True  # 启用插画查询（看看图）功能

pixiv_ranking_query_enabled=True  # 启用榜单查询（看看榜）功能
pixiv_ranking_default_mode=day  # 默认查询的榜单，可选值：day, week, month, day_male, day_female, week_original, week_rookie, day_manga
pixiv_ranking_default_range=[1, 3]  # 默认查询的榜单范围
pixiv_ranking_fetch_item=150  # 每次从服务器获取的榜单项数（查询的榜单范围必须在这个数目内）
pixiv_ranking_max_item_per_query=5  # 每次榜单查询最多能查询多少项

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

pixiv_random_related_illust_query_enabled=True  # 启用关联插画随机抽选（不够色）功能
pixiv_random_related_illust_method=bookmark_proportion
pixiv_random_related_illust_min_bookmark=0
pixiv_random_related_illust_min_view=0
pixiv_random_related_illust_max_page=4
pixiv_random_related_illust_max_item=100

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

pixiv_poke_action=random_recommended_illust  # 【go-cqhttp限定】戳一戳功能，可选值：空, ranking, random_recommended_illust, random_bookmark
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
