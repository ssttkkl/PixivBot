import threading
import time
import os

from pixivpy3 import ByPassSniApi

from settings import settings

__back_api__ = None
__api_init_time__ = 0
__lock__ = threading.RLock()


def api():
    global __api_init_time__, __back_api__, __lock__
    if time.time() - __api_init_time__ <= 1800:
        return __back_api__

    __lock__.acquire()
    try:
        username: str = settings["pixiv"]["username"]
        password: str = settings["pixiv"]["password"]

        __back_api__ = ByPassSniApi()
        __back_api__.require_appapi_hosts()
        __back_api__.set_accept_language('zh-cn')
        __back_api__.login(username, password)
        __api_init_time__ = time.time()
    finally:
        __lock__.release()
    return __back_api__


def shuffle_illust(illusts, shuffle_method):
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


def has_tag(illust, tag: str):
    tag = tag.lower()
    for x in illust["tags"]:
        tag_name: str = x["name"].lower()
        if tag in tag_name:
            return True
    return False


def download_illust(illust):
    download_dir: str = settings["illust"]["download_dir"]
    download_quantity: str = settings["illust"]["download_quantity"]
    download_replace: bool = settings["illust"]["download_replace"]
    domain = settings["illust"]["domain"] \
        if "domain" in settings["illust"] else None  # nullable

    dirname = f"./{download_dir}"
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    if download_quantity == "original":
        if len(illust["meta_pages"]) > 0:
            url: str = illust["meta_pages"][0]["image_urls"]["original"]
        else:
            url: str = illust["meta_single_page"]["original_image_url"]
    else:
        url: str = illust["image_urls"][download_quantity]

    # 从url中截取的文件名
    filename = os.path.basename(url)
    fullpath = os.path.join(dirname, filename)
    
    # 上面的文件名将后缀改为jpg的文件名（用于检查是否存在压缩过的文件）
    basename, extension = os.path.splitext(filename)
    filename_as_jpg = basename + ".jpg"
    fullpath_as_jpg = os.path.join(dirname, filename_as_jpg)

    filepath_to_process = None
    
    # 检查本地是否存在
    if not download_replace:
        if os.path.exists(fullpath):
            filepath_to_process = fullpath
        elif os.path.exists(fullpath_as_jpg):
            filepath_to_process = fullpath_as_jpg
    
    # 如果本地不存在则下载
    if filepath_to_process is None:
        if domain is not None:
            url = url.replace("i.pximg.net", domain)
        api().download(url=url, path=dirname)
        filepath_to_process = fullpath

    return compress_illust(filepath_to_process)


def compress_illust(fullpath):
    compress: bool = settings["illust"]["compress"]
    if not compress:
        return fullpath

    from PIL import Image
    compress_size: int = settings["illust"]["compress_size"]
    compress_quantity: int = settings["illust"]["compress_quantity"]

    with Image.open(fullpath) as img:
        w, h = img.size
        if w > compress_size or h > compress_size:
            ratio = min(compress_size / w, compress_size / h)
            img_cp = img.resize((int(ratio * w), int(ratio * h)), Image.ANTIALIAS)
        else:
            img_cp = img.copy()
        img_cp = img_cp.convert("RGB")

    # 将原来的文件删除，然后保存压缩后的文件
    try:
        os.remove(fullpath)
    finally:
        dirname, basename = os.path.split(fullpath)
        basename, _ = os.path.splitext(basename)
        basename = basename + ".jpg"
        fullpath = os.path.join(dirname, basename)
        img_cp.save(fullpath, optimize=True, quantity=compress_quantity)
        return fullpath


def illust_to_message(illust, flash=False):
    from mirai import Plain, Image

    pattern: str = settings["illust"]["reply_pattern"]
    r18_img_escape: bool = settings["illust"]["r18_img_escape"]
    r18g_img_escape: bool = settings["illust"]["r18g_img_escape"]
    r18g_img_escape_message: str = settings["illust"]["r18g_img_escape_message"] \
        if "r18g_img_escape_message" in settings["illust"] and settings["illust"]["r18g_img_escape_message"] is not None \
        else ""  # nullable
    r18_img_escape_message: str = settings["illust"]["r18_img_escape_message"] \
        if "r18_img_escape_message" in settings["illust"] and settings["illust"]["r18_img_escape_message"] is not None \
        else ""  # nullable

    string = pattern.replace("$title", illust["title"]) \
        .replace("$tags", " ".join(map(lambda x: x["name"], illust["tags"]))) \
        .replace("$id", str(illust["id"]))
    message = [Plain(string)]

    if has_tag(illust, "R-18G") and r18g_img_escape:
        message.append(Plain(r18g_img_escape_message))
    elif has_tag(illust, "R-18") and r18_img_escape:
        message.append(Plain(r18_img_escape_message))
    else:
        filename = download_illust(illust)
        message.append(Image.fromFileSystem(filename))

    return message
