import asyncio
import json
import math
import os
import threading
import time
import traceback
import typing as T
from concurrent.futures.thread import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

import aiofiles
import pixivpy3
from PIL import ImageFile
from mirai.event.message.base import BaseMessageComponent

from settings import settings

username: str = settings["pixiv"]["username"]
password: str = settings["pixiv"]["password"]
bypass: bool = settings["pixiv"]["bypass"]

compress: bool = settings["illust"]["compress"]
compress_size: int = settings["illust"]["compress_size"]
compress_quantity: int = settings["illust"]["compress_quantity"]
download_dir: str = settings["illust"]["download_dir"]
download_quantity: str = settings["illust"]["download_quantity"]
download_replace: bool = settings["illust"]["download_replace"]
domain: T.Optional[str] = settings["illust"]["domain"]
reply_pattern: str = settings["illust"]["reply_pattern"]
block_tags: T.Sequence[str] = settings["illust"]["block_tags"]
block_mode: str = settings["illust"]["block_mode"]
block_message: str = settings["illust"]["block_message"]


class PixivAPI:
    def __init__(self):
        self.__back_api__ = None
        self.__api_init_time__ = 0
        self.__executor__ = ThreadPoolExecutor(max_workers=4)
        self.__lock__ = threading.Lock()

    def __getattr__(self, item):
        return item

    async def run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        if isinstance(func, str):
            api = await self.__api()
            result = await loop.run_in_executor(self.__executor__, lambda: api.__getattribute__(func)(*args, **kwargs))
        else:
            result = await loop.run_in_executor(self.__executor__, lambda: func(*args, **kwargs))
        return result

    async def __refresh_api(self):
        self.__lock__.acquire()
        try:
            if bypass:
                self.__back_api__ = pixivpy3.ByPassSniApi()
                await self.run_in_executor(self.__back_api__.require_appapi_hosts)
            else:
                self.__back_api__ = pixivpy3.AppPixivAPI()

            self.__back_api__.set_accept_language('zh-cn')
            await self.run_in_executor(self.__back_api__.login, username, password)
            self.__api_init_time__ = time.time()
        finally:
            self.__lock__.release()

    async def __api(self) -> pixivpy3.AppPixivAPI:
        """
        获取PixivAPI的实例
        :return: PixivAPI的实例
        """
        if time.time() - self.__api_init_time__ <= 1800:
            return self.__back_api__
        else:
            await self.__refresh_api()
            return self.__back_api__

    async def get_user_id(self):
        return (await self.__api()).user_id

    async def iter_illusts(self,
                           search_func: str,
                           illust_filter: T.Optional[T.Callable[[dict], bool]] = None,
                           search_item_limit: T.Optional[int] = None,
                           search_page_limit: T.Optional[int] = None,
                           *args, **kwargs):
        """
        反复调用search_func自动翻页获取illusts，实现illust的生成器
        :param search_func: 用于从服务器获取illusts的函数，返回值应为包含键"illusts"的词典
        :param illust_filter: 对每个illust调用以过滤不符合的，返回True为包含，False为不包含
        :param search_item_limit: 最多生成多少项，若未指定则无限制
        :param search_page_limit: 最多翻页多少次，若未指定则无限制
        :param args: 初次调用search_func时的参数
        :param kwargs: 初次调用search_func时的参数
        :return: illust的生成器
        """

        if search_item_limit is None:
            search_item_limit = 2 ** 32
        if search_page_limit is None:
            search_page_limit = 2 ** 32

        page = 0
        counter = 0

        search_result = await self.run_in_executor(search_func, *args, **kwargs)

        while counter < search_item_limit and page < search_page_limit:
            for illust in search_result["illusts"]:
                if illust_filter is None or illust_filter(illust):
                    counter = counter + 1
                    yield illust
                    if counter >= search_item_limit:
                        break
            else:
                next_qs = await self.run_in_executor(self.parse_qs, next_url=search_result["next_url"])
                if next_qs is None:
                    break
                search_result = await self.run_in_executor(search_func, **next_qs)
                page = page + 1

    async def get_illusts_cached(self,
                                 cache_file: T.Union[str, Path],
                                 cache_outdated_time: T.Optional[int],
                                 search_func: str,
                                 illust_filter: T.Callable[[dict], bool],
                                 search_item_limit: T.Optional[int] = None,
                                 search_page_limit: T.Optional[int] = None,
                                 *args, **kwargs) -> T.Sequence[dict]:
        """
        尝试从缓存文件读取illusts，若不存在则从服务器获取并写入缓存文件
        :param cache_file: 缓存文件路径
        :param cache_outdated_time: 缓存文件过期期限（单位：s）
        :param search_func: 用于从服务器获取illusts的函数，返回值应为包含illust的列表
        :param illust_filter: 对每个illust调用以过滤不符合的，返回True为包含，False为不包含
        :param search_item_limit: 最多生成多少项，若未指定则无限制
        :param search_page_limit: 最多翻页多少次，若未指定则无限制
        :param args: 初次调用search_func时的参数
        :param kwargs: 初次调用search_func时的参数
        :return: 包含illust的列表
        """
        if not isinstance(cache_file, Path):
            cache_file = Path(cache_file)

        illusts = []
        cache_dirty = False  # 指示是否成功读取缓存

        # 若缓存文件存在且未过期，读取缓存
        if cache_file.exists():
            now = time.time()
            mtime = cache_file.stat().st_mtime
            if cache_outdated_time is None or now - mtime <= cache_outdated_time:
                async with aiofiles.open(cache_file, "r", encoding="utf8") as f:
                    content = json.loads(await f.read())
                    if "illusts" in content and len(content["illusts"]) > 0:
                        illusts = content["illusts"]

        # 若没读到缓存，则从pixiv加载
        if len(illusts) == 0:
            try:
                illusts = await self.get_illusts(search_func=search_func, illust_filter=illust_filter,
                                                 search_item_limit=search_item_limit,
                                                 search_page_limit=search_page_limit, *args, **kwargs)
                cache_dirty = True
            except:
                traceback.print_exc()
                # 从pixiv加载时发生异常，尝试读取缓存（即使可能已经过期）
                if cache_file.exists():
                    async with aiofiles.open(cache_file, "r", encoding="utf8") as f:
                        content = json.loads(await f.read())
                        if "illusts" in content:
                            illusts = content["illusts"]

        # 写入缓存
        if cache_dirty and len(illusts) > 0:
            dirpath = cache_file.parent
            dirpath.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(cache_file, "w", encoding="utf8") as f:
                content = dict(illusts=illusts)
                await f.write(json.dumps(content))

        return illusts

    async def get_illusts(self,
                          search_func: str,
                          illust_filter: T.Optional[T.Callable[[dict], bool]] = None,
                          search_item_limit: T.Optional[int] = None,
                          search_page_limit: T.Optional[int] = None,
                          *args, **kwargs):
        """
        反复调用search_func自动翻页获取illusts
        :param search_func: 用于从服务器获取illusts的函数，返回值应为包含键"illusts"的词典
        :param illust_filter: 对每个illust调用以过滤不符合的，返回True为包含，False为不包含
        :param search_item_limit: 最多生成多少项，若未指定则无限制
        :param search_page_limit: 最多翻页多少次，若未指定则无限制
        :param args: 初次调用search_func时的参数
        :param kwargs: 初次调用search_func时的参数
        :return: illust的列表
        """
        illusts = []
        async for x in self.iter_illusts(search_func, illust_filter, search_item_limit, search_page_limit, *args,
                                         **kwargs):
            illusts.append(x)
        return illusts

    async def download_illust(self, illust: dict) -> Path:
        """
        保存给定illust
        :param illust: 给定illust
        :return: illust保存的路径
        """
        dirpath = Path("./" + download_dir)
        dirpath.mkdir(parents=True, exist_ok=True)

        if download_quantity == "original":
            if len(illust["meta_pages"]) > 0:
                url = illust["meta_pages"][0]["image_urls"]["original"]
            else:
                url = illust["meta_single_page"]["original_image_url"]
        else:
            url = illust["image_urls"][download_quantity]
        if domain is not None:
            url = url.replace("i.pximg.net", domain)

        # 从url中截取的文件名
        filename = os.path.basename(url)
        filepath = dirpath.joinpath(filename)

        # 上面的文件名将后缀改为jpg的文件名（用于检查是否存在压缩过的文件）
        filename_compressed = os.path.splitext(filename)[0] + ".compressed.jpg"
        filepath_compressed = dirpath.joinpath(filename_compressed)

        if not download_replace and filepath_compressed.exists():
            return filepath_compressed
        elif download_replace or not filepath.exists():
            await self.run_in_executor(self.download, url=url, path=dirpath, name=filename, replace=download_replace)

        if not compress:
            return filepath
        else:
            await compress_illust(filepath, filepath_compressed)
            os.remove(str(filepath))
            return filepath_compressed

    async def illust_to_message(self, illust: dict) -> T.Sequence[BaseMessageComponent]:
        """
        将给定illust按照模板转换为message
        :param illust: 给定illust
        :return: 转换后的message
        """
        from mirai import Plain, Image

        string = reply_pattern.replace("$title", illust["title"]) \
            .replace("$tags", " ".join(map(lambda x: x["name"], illust["tags"]))) \
            .replace("$id", str(illust["id"]))

        illegal_tags = []
        for tag in block_tags:
            if has_tag(illust, tag):
                illegal_tags.append(tag)

        if len(illegal_tags) > 0:
            block_message_formatted = block_message.replace("%tag", ' '.join(illegal_tags))
            if block_mode == "escape_img":
                message = [Plain(string + '\n' + block_message_formatted)]
            elif block_mode == "fully_block":
                message = [Plain(block_message_formatted)]
            else:
                raise ValueError("illegal block_mode value: " + block_mode)
        else:
            filename = await self.download_illust(illust)
            message = [Plain(string), Image.fromFileSystem(filename)]

        return message


async def compress_illust(filepath: Path, filepath_compressed: Path):
    """
    压缩一个已经保存的illust
    :param filepath: 原illust保存的路径
    :param filepath_compressed: 压缩后的illust保存的路径
    """
    from PIL import Image

    async with aiofiles.open(filepath, "rb") as f:
        p = ImageFile.Parser()
        while True:
            s = await f.read(1024)
            if not s:
                break
            p.feed(s)
        img = p.close()

    w, h = img.size
    if w > compress_size or h > compress_size:
        ratio = min(compress_size / w, compress_size / h)
        img_cp = img.resize((int(ratio * w), int(ratio * h)), Image.ANTIALIAS)
    else:
        img_cp = img.copy()
    img_cp = img_cp.convert("RGB")

    with BytesIO() as bio:
        img_cp.save(bio, format="JPEG", optimize=True, quantity=compress_quantity)
        async with aiofiles.open(filepath_compressed, "wb") as f:
            bytes = bio.getvalue()
            await f.write(bytes)


def get_illust_filter(search_filter_tags: T.Collection[str],
                      search_bookmarks_lower_bound: T.Optional[int],
                      search_view_lower_bound: T.Optional[int]):
    def illust_filter(illust) -> bool:
        # 标签过滤
        for tag in search_filter_tags:
            if has_tag(illust, tag):
                return False
        # 书签下限过滤
        if search_bookmarks_lower_bound is not None and illust["total_bookmarks"] < search_bookmarks_lower_bound:
            return False
        # 浏览量下限过滤
        if search_view_lower_bound is not None and illust["total_view"] < search_view_lower_bound:
            return False
        return True

    return illust_filter


def shuffle_illust(illusts: T.Sequence[dict],
                   shuffle_method: str) -> dict:
    """
    从illusts随机抽选一个illust
    :param illusts: illust的列表
    :param shuffle_method: 随机抽选的方法，可选项：bookmarks_proportion, view_proportion, time_proportion, uniform
    :return: 随机抽选的一个illust
    """
    import random

    if shuffle_method == "bookmarks_proportion":
        # 概率正比于书签数
        bookmarks = list(map(lambda illust: int(illust["total_bookmarks"]), illusts))
        sum_bm = sum(bookmarks)
        probability = list(map(lambda x: x / sum_bm, bookmarks))
    elif shuffle_method == "view_proportion":
        # 概率正比于查看人数
        view = list(map(lambda illust: int(illust["total_view"]), illusts))
        sum_view = sum(view)
        probability = list(map(lambda x: x / sum_view, view))
    elif shuffle_method == "time_proportion":
        # 概率正比于 exp((当前时间戳 - 画像发布时间戳) / 3e7)
        def str_to_stamp(date_str: str):
            import time
            date_str, timezone_str = date_str[0:19], date_str[19:]
            stamp = time.mktime(time.strptime(date_str, "%Y-%m-%dT%H:%M:%S"))

            offset = 1 if timezone_str[0] == "-" else -1
            offset = offset * (int(timezone_str[1:3]) * 60 + int(timezone_str[4:])) * 60

            stamp = stamp + offset - time.timezone
            return stamp

        delta_time = list(map(lambda illust: time.time() - str_to_stamp(illust["create_date"]), illusts))
        probability = list(map(lambda x: math.exp(-x / 3e7), delta_time))
        sum_poss = sum(probability)
        for i in range(len(probability)):
            probability[i] = probability[i] / sum_poss
    elif shuffle_method == "uniform":
        # 概率相等
        probability = [1 / len(illusts)] * len(illusts)
    else:
        raise ValueError(
            "illegal shuffle_method value f\"{shuffle_method}\"")

    probability_distribution = [probability[0]]  # 概率分布
    for i in range(1, len(probability)):
        probability_distribution.append(probability[i] + probability_distribution[i - 1])

    def select() -> int:
        """
        利用二分查找概率分布中第一个大于随机数的位置
        :return: 索引
        """
        ran = random.random()

        first, last = 0, len(probability_distribution) - 1
        while first < last:
            mid = (first + last) // 2
            if probability_distribution[mid] > ran:
                last = mid
            else:
                first = mid + 1
        return first

    return illusts[select()]


def has_tag(illust: dict,
            tag: str) -> bool:
    """
    检查给定illust是否包含给定tag
    :param illust: 给定illust
    :param tag: 给定tag
    :return: 是否包含给定tag
    """
    tag = tag.lower()
    for x in illust["tags"]:
        tag_name: str = x["name"].lower()
        if tag in tag_name:
            return True
    return False
