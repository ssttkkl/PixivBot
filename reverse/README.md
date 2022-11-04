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
$ docker exec -it bot-mongo mongosh pixiv_bot

# 切换到admin数据库
$ use admin

# 创建一个名为admin，密码为123456的管理员用户。（此处仅为示范，建议设置较高强度的密码）
> db.createUser({ user:'admin',pwd:'123456',roles:[ { role:'userAdminAnyDatabase', db: 'admin'},"readWriteAnyDatabase"]})

# 使用上面创建的管理员用户进行认证
> db.auth('admin', '123456')

# 切换到pixiv_bot数据库
> use pixiv_bot

# 创建一个名为pixiv_bot，密码为pixiv_bot的用户，该用户拥有pixiv_bot数据库的所有权限。（此处仅为示范，建议设置较高强度的密码）
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

# 拉取新PixivBot镜像
$ docker pull ssttkkl/pixiv-bot:reverse

# 运行新容器
$ docker run --network bot-net -v /etc/pixivbot/.env.prod:/app/.env.prod --name bot -e HOST=0.0.0.0 -e PORT=8080 -d ssttkkl/pixiv-bot:reverse
```

### 手动配置（推荐 Windows 用户使用此方式）

参考[创建项目 | NoneBot](https://v2.nonebot.dev/docs/tutorial/create-project)创建一个Bot，安装[ssttkkl/nonebot-plugin-pixivbot](https://github.com/ssttkkl/nonebot-plugin-pixivbot)插件。

## 配置项

参考[ssttkkl/nonebot-plugin-pixivbot/README.md](https://github.com/ssttkkl/nonebot-plugin-pixivbot/blob/main/README.md#%E9%85%8D%E7%BD%AE)

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
