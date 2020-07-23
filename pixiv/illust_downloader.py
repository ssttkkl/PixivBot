import os
import typing as T
from pathlib import Path

from PIL import Image

from utils import settings, launch, log
from .pixiv_api import papi

compress: bool = settings["illust"]["compress"]
compress_size: int = settings["illust"]["compress_size"]
compress_quantity: int = settings["illust"]["compress_quantity"]
download_quantity: str = settings["illust"]["download_quantity"]
download_dir: str = settings["illust"]["download_dir"]
download_replace: bool = settings["illust"]["download_replace"]
domain: T.Optional[str] = settings["illust"]["domain"]


async def cache_illust(illust: dict) -> Path:
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

    if not download_replace:
        if filepath_compressed.exists():
            return filepath_compressed
        elif filepath.exists():
            return filepath

    await launch(papi.download, url=url, path=dirpath, name=filename, replace=True)
    log.debug(f"downloaded to {filepath}")

    if not compress:
        return filepath
    else:
        await launch(compress_illust, filepath, filepath_compressed)
        # os.remove(str(filepath))
        log.debug(f"compressed to {filepath_compressed}")
        return filepath_compressed


def compress_illust(filepath: Path, filepath_compressed: Path):
    """
    压缩一个已经保存的illust
    :param filepath: 原illust保存的路径
    :param filepath_compressed: 压缩后的illust保存的路径
    """

    with Image.open(filepath) as img:
        w, h = img.size
        if w > compress_size or h > compress_size:
            ratio = min(compress_size / w, compress_size / h)
            img_cp = img.resize((int(ratio * w), int(ratio * h)), Image.ANTIALIAS)
        else:
            img_cp = img.copy()
        img_cp = img_cp.convert("RGB")

    img_cp.save(filepath_compressed, format="JPEG", optimize=True, quantity=compress_quantity)
