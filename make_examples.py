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

num_items = 18
onehour = 60 * 60  # in seconds
oneday = 24 * onehour  # in seconds
now = round(datetime.now().timestamp())
times = [now - x for x in range(oneday, 5 * oneday, onehour)]


def reviewed(times, added):
    pos = bisect.bisect_right(times, added) - 1
    if pos >= 0:
        return random.choice(times[pos:])
    else:
        return now


def added_reviewed():
    added = random.choice(times)
    later_times = [x for x in times if x >= added]
    return added, random.choice(later_times)


def name():
    # drop the ending period
    s = lorem.sentence()[:-1]
    num = random.choice([3, 4, 5])
    words = s.split(" ")[:num]
    return " ".join(words).rstrip()


def stage():
    return random.choice(["inkling", "notion", "thought", "idea"])


def content():
    return f"{lorem.sentence()}"


def make_examples(egfile: str = None, num_items: int = num_items, last_id=0):
    examples = []

    for _ in range(num_items):
        added, reviewed = added_reviewed()
        examples.append(
            f"add '{name()}' --content '{content()}' --stage {stage()} --added {added} --reviewed {reviewed}"
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
