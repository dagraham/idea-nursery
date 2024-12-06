#! /usr/bin/env python3
import bisect
import os
import random
import sys
import time
from datetime import datetime, timedelta
from typing import Union

import lorem


def find_position(times, x):
    pos = bisect.bisect_right(times, x) - 1
    if pos >= 0:
        return random.choice(times[pos:])
    else:
        return 0


# from etm.model import parse

num_items = 9
onehour = 60 * 60  # in seconds
oneday = 24 * onehour  # in seconds
# now = round(datetime.now().timestamp())
# times = [x for x in range(oneday, 10 * oneday, onehour)]
max_days = 10


# def probed(times, added):
#     pos = bisect.bisect_right(times, added) - 1
#     if pos >= 0:
#         return random.choice(times[pos:])
#     else:
#         return now


def added_probed():
    now = round(datetime.now().timestamp())
    larger = random.choice([x for x in range(oneday, max_days * oneday, onehour)])
    smaller = random.choice([x for x in range(0, larger // 3, 60)])
    return now - larger, now - smaller


def name():
    # drop the ending period
    s = lorem.sentence()[:-1]
    num = random.choice([3, 4, 5])
    words = s.split(" ")[:num]
    return " ".join(words).rstrip()


def status():
    return random.choice(
        [
            "inkling",
            "inkling",
            "inkling",
            "inkling",
            "notion",
            "notion",
            "notion",
            "idea",
            "idea",
        ]
    )


def content():
    return f"{lorem.sentence()}"


def make_examples(egfile: str, num_items: int = num_items):
    examples = []

    for _ in range(num_items):
        added, probed = added_probed()
        examples.append(
            f"add '{name()}' --content '{content()}' --status {status()} --added {added} --probed {probed}"
        )

    if egfile:
        with open(egfile, "w") as fo:
            fo.writelines("\n".join(examples))

    return examples


if __name__ == "__main__":
    if len(sys.argv) > 1:
        egfile = sys.argv.pop(1)
    else:
        egfile = None

    res = make_examples(egfile)
    for _ in res:
        print(_)
