import json
import os
import pathlib
import threading
import time
import traceback
import typing as T
from pathlib import Path

import pixivpy3
from mirai.event.message.base import BaseMessageComponent
from pydantic.typing import NoneType

from settings import settings

__back_api__ = None
__api_init_time__ = 0
__lock__ = threading.RLock()

username: str = settings["pixiv"]["username"]
password: str = settings["pixiv"]["password"]

compress: bool = settings["illust"]["compress"]
compress_size: int = settings["illust"]["compress_size"]
compress_quantity: int = settings["illust"]["compress_quantity"]
download_dir: str = settings["illust"]["download_dir"]
download_quantity: str = settings["illust"]["download_quantity"]
download_replace: bool = settings["illust"]["download_replace"]
domain: T.Optional[str] = settings["illust"]["domain"]
reply_pattern: str = settings["illust"]["reply_pattern"]
r18_img_escape: bool = settings["illust"]["r18_img_escape"]
r18g_img_escape: bool = settings["illust"]["r18g_img_escape"]
r18g_img_escape_message: T.Optional[str] = settings["illust"]["r18g_img_escape_message"]
r18_img_escape_message: T.Optional[str] = settings["illust"]["r18_img_escape_message"]


def api() -> pixivpy3.ByPassSniApi:
    """
    获取PixivAPI的实例
    :return: PixivAPI的实例
    """
    global __api_init_time__, __back_api__, __lock__
    if time.time() - __api_init_time__ <= 1800:
        return __back_api__

    __lock__.acquire()
    try:
        __back_api__ = pixivpy3.ByPassSniApi()
        __back_api__.require_appapi_hosts()
        __back_api__.set_accept_language('zh-cn')
        __back_api__.login(username, password)
        __api_init_time__ = time.time()
    finally:
        __lock__.release()
    return __back_api__


def get_illusts_cached(load_from_pixiv_func: T.Callable[[], T.Sequence[dict]],
                       cache_file: T.Union[str, pathlib.Path],
                       cache_outdated_time: T.Union[NoneType, int]) -> T.Sequence[dict]:
    """
    尝试从缓存文件读取illusts，若不存在则从服务器获取并写入缓存文件
    :param load_from_pixiv_func: 用于从服务器获取illusts的函数，返回值应为包含illust的列表
    :param cache_file: 缓存文件路径
    :param cache_outdated_time: 缓存文件过期期限（单位：s）
    :return: 包含illust的列表
    """
    illusts = []
    cache_dirty = False  # 指示是否要写入缓存

    # 若缓存文件存在且未过期，读取缓存
    if os.path.exists(cache_file):
        now = time.time()
        mtime = os.path.getmtime(cache_file)
        if cache_outdated_time is None or now - mtime <= cache_outdated_time:
            with open(cache_file, "r", encoding="utf8") as f:
                content = json.load(f)
                if "illusts" in content:
                    illusts = content["illusts"]

    # 若没读到缓存，则从pixiv加载
    if len(illusts) == 0:
        try:
            illusts = load_from_pixiv_func()
            cache_dirty = True
        except:
            traceback.print_exc()
            # 从pixiv加载时发生异常，尝试读取缓存（即使可能已经过期）
            if os.path.exists(cache_file):
                with open(cache_file, "r", encoding="utf8") as f:
                    content = json.load(f)
                    if "illusts" in content:
                        illusts = content["illusts"]

    if cache_dirty:
        # 写入缓存
        dirpath, _ = os.path.split(cache_file)
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)

        with open(cache_file, "w", encoding="utf8") as f:
            content = dict(illusts=illusts)
            f.write(json.dumps(content))

    return illusts


def iter_illusts(search_func: T.Callable[..., dict],
                 illust_filter: T.Callable[[dict], bool],
                 init_qs: dict,
                 search_item_limit: T.Optional[int],
                 search_page_limit: T.Optional[int]) -> T.Generator[dict, None, None]:
    """
    反复调用search_func自动翻页获取illusts，实现illust的生成器
    :param search_func: 用于从服务器获取illusts的函数，返回值应为包含键"illusts"的词典
    :param illust_filter: 对每个illust调用以过滤不符合的，返回True为包含，False为不包含
    :param init_qs: 初次调用search_func时的参数
    :param search_item_limit: 最多生成多少项，若未指定则无限制
    :param search_page_limit: 最多翻页多少次，若未指定则无限制
    :return: illust的生成器
    """

    if search_item_limit is None:
        search_item_limit = 2 ** 32
    if search_page_limit is None:
        search_page_limit = 2 ** 32

    search_result = search_func(**init_qs)
    page = 1
    counter = 0

    while counter < search_item_limit and page < search_page_limit:
        for illust in search_result["illusts"]:
            # R-18/R-18G规避
            if illust_filter(illust):
                counter = counter + 1
                yield illust
                if counter >= search_item_limit:
                    break
        else:
            next_qs = api().parse_qs(search_result["next_url"])
            if next_qs is None:
                break
            search_result = search_func(**next_qs)
            page = page + 1


def shuffle_illust(illusts: T.Sequence[dict],
                   shuffle_method: str) -> dict:
    """
    从illusts随机抽选一个illust
    :param illusts: illust的列表
    :param shuffle_method: 随机抽选的方法，可选项：bookmarks_proportion, view_proportion, uniform
    :return: 随机抽选的一个illust
    """
    import random

    if shuffle_method == "bookmarks_proportion":
        bookmarks = list(map(lambda illust: int(illust["total_bookmarks"]), illusts))
        sum_bm = sum(bookmarks)
        possibility = list(map(lambda x: x / sum_bm, bookmarks))
    elif shuffle_method == "view_proportion":
        view = list(map(lambda illust: int(illust["total_view"]), illusts))
        sum_view = sum(view)
        possibility = list(map(lambda x: x / sum_view, view))
    elif shuffle_method == "uniform":
        possibility = [1 / len(illusts)] * len(illusts)
    else:
        raise ValueError("shuffle_method's value expects bookmarks_proportion, view_proportion or uniform. "
                         f"{shuffle_method} found.")

    for i in range(1, len(possibility)):
        possibility[i] = possibility[i] + possibility[i - 1]
    rand = random.random()
    for i in range(len(possibility)):
        if possibility[i] > rand:
            return illusts[i]
    return illusts[len(illusts) - 1]


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


def save_illust(illust: dict) -> Path:
    """
    保存给定illust
    :param illust: 给定illust
    :return: illust保存的路径
    """
    dirpath = Path("./" + download_dir)
    if not dirpath.exists():
        dirpath.mkdir()

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
        api().download(url=url, path=dirpath, name=filename, replace=download_replace)

    if not compress:
        return filepath
    else:
        compress_illust(filepath, filepath_compressed)
        os.remove(str(filepath))
        return filepath_compressed


def compress_illust(filepath: Path, filepath_compressed: Path):
    """
    压缩一个已经保存的illust
    :param filepath: 原illust保存的路径
    :param filepath_compressed: 压缩后的illust保存的路径
    """
    from PIL import Image

    with Image.open(filepath) as img:
        w, h = img.size
        if w > compress_size or h > compress_size:
            ratio = min(compress_size / w, compress_size / h)
            img_cp = img.resize((int(ratio * w), int(ratio * h)), Image.ANTIALIAS)
        else:
            img_cp = img.copy()
        img_cp = img_cp.convert("RGB")

    img_cp.save(filepath_compressed, optimize=True, quantity=compress_quantity)


def illust_to_message(illust: dict) -> T.Sequence[BaseMessageComponent]:
    """
    将给定illust按照模板转换为message
    :param illust: 给定illust
    :return: 转换后的message
    """
    from mirai import Plain, Image

    string = reply_pattern.replace("$title", illust["title"]) \
        .replace("$tags", " ".join(map(lambda x: x["name"], illust["tags"]))) \
        .replace("$id", str(illust["id"]))
    message = [Plain(string)]

    if has_tag(illust, "R-18G") and r18g_img_escape:
        message.append(Plain(r18g_img_escape_message))
    elif has_tag(illust, "R-18") and r18_img_escape:
        message.append(Plain(r18_img_escape_message))
    else:
        filename = save_illust(illust)
        message.append(Image.fromFileSystem(filename))

    return message
