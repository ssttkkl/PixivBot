import io
import json
import math
import random
import time
import typing as T


def random_illust(illusts: T.Sequence[dict], shuffle_method: str) -> dict:
    """
    从illusts随机抽选一个illust
    :param illusts: illust的列表
    :param shuffle_method: 随机抽选的方法，可选项：bookmarks_proportion, view_proportion, time_proportion, uniform
    :return: 随机抽选的一个illust
    """

    if shuffle_method == "bookmarks_proportion":
        # 概率正比于书签数
        bookmarks = list(map(lambda illust: int(illust["total_bookmarks"]) + 10, illusts))  # 加10平滑
        sum_bm = sum(bookmarks)
        probability = list(map(lambda x: x / sum_bm, bookmarks))
    elif shuffle_method == "view_proportion":
        # 概率正比于查看人数
        view = list(map(lambda illust: int(illust["total_view"]) + 10, illusts))  # 加10平滑
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
        probability = list(map(lambda x: math.exp(-x * 3e-7), delta_time))
        sum_poss = sum(probability)
        for i in range(len(probability)):
            probability[i] = probability[i] / sum_poss
    elif shuffle_method == "uniform":
        # 概率相等
        probability = 1 / len(illusts)
    else:
        raise ValueError(f"illegal shuffle_method value: {shuffle_method}")

    for i in range(1, len(probability)):
        probability[i] = probability[i] + probability[i - 1]

    ran = random.random()

    # 二分查找
    first, last = 0, len(probability) - 1
    while first < last:
        mid = (first + last) // 2
        if probability[mid] > ran:
            last = mid
        else:
            first = mid + 1
    return illusts[first]


def has_tag(illust: dict, tag: str) -> bool:
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
