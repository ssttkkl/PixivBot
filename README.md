MiraiPixiv
=====

支持**查看pixiv榜单**，**查看指定id插画**，**随机抽选指定关键字插画**，**随机抽选书签插画**，**随机抽选指定画师插画**功能。

## 使用方式

1.  配置[mirai-console](https://github.com/mamoe/mirai-console)（参见[这个](https://github.com/mamoe/mirai-console/blob/master/docs/Run.md)）与[mirai-api-http](https://github.com/project-mirai/mirai-api-http)（参见[这个](https://github.com/project-mirai/mirai-api-http/blob/master/README.md)）

> 本人环境：
> 
> - mirai-core-all: 1.3.3
> - mirai-console: 1.0-M4
> - mirai-console-pure: 1.0-M4
> - mirai-api-http: 1.8.4

2. `pip install -r requirements.txt`（或 `poetry update`如果你使用[poetry](https://python-poetry.org/)）
3. `python bot.py`（或 `poetry run python bot.py`如果你使用[poetry](https://python-poetry.org/)）

初次使用请将`settings.template.json`拷贝为`settings.json`，并填写mirai与pixiv栏目的信息。

## 触发语句（可以在设置中更改）

- **看看榜**：查看pixiv榜单的第1到第20名（默认范围可在`settings.json`中更改）
- **看看榜*20-30***：查看pixiv榜单的第20到第30名
- **来张*FGO*图**：搜索关键字*FGO*，从搜索结果随机抽选一张插画
- **来*3*张*FGO*图**、**来*三*张*FGO*图**：搜索关键字*FGO*，从搜索结果随机抽选*三*张插画
- **来张*森倉円*老师的作品**：搜索画师*森倉円*，从该画师的插画列表里随机抽选一张插画
- **来*5*张*森倉円*老师的作品**、**来*五*张*森倉円*老师的作品**：搜索画师*森倉円*，从该画师的插画列表里随机抽选*五*张插画
- **看看图*114514***：查看id为*114514*的插画
- **看看图 *114514* *1919810***：分别查看id为*114514*与*1919810*的插画
- **来张私家车**：从书签中随机抽选一张插画
- **来十张私家车**、**来10张私家车**：从书签中随机抽选*十*张插画

## Special Thanks

[upbit/pixivpy](https://github.com/upbit/pixivpy)

[mamoe/mirai](https://github.com/mamoe/mirai)

[GraiaProject/Application](https://github.com/GraiaProject/Application)

## LICENSE

[AGPLv3](https://github.com/ssttkkl/MiraiPixiv/blob/master/LICENSE)