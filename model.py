import datetime
from enum import Enum


def format_seconds(seconds: int, short: bool = True) -> str:
    if seconds == 0:
        return "0m"
    sign = ""
    if seconds < 0:
        sign = "-"
        seconds = abs(seconds)
    until = []
    days = hours = minutes = 0
    if seconds:
        minutes = seconds // 60
        if minutes >= 60:
            hours = minutes // 60
            minutes = minutes % 60
            if short and minutes >= 30:
                hours += 1
        if hours >= 24:
            days = hours // 24
            hours = hours % 24
            if short and hours >= 12:
                days += 1
    if days:
        until.append(f"{days}d")
    if hours:
        until.append(f"{hours}h")
    if minutes:
        until.append(f"{minutes}m")
    if not until:
        until.append("0m")
    if short:
        return f"{sign}{until[0]}"
    else:
        return f"{sign}{''.join(until)}"


def timestamp() -> int:
    return round(datetime.datetime.now().timestamp())


class Rank(str, Enum):
    spark = "spark"
    inkling = "inkling"
    thought = "thought"
    idea = "idea"


class Status(str, Enum):
    deferred = "deferred"
    active = "active"
    promoted = "promoted"


class Idea:
    def __init__(
        self,
        name,
        content,
        rank=Rank.spark,
        status=Status.active,
        added=None,
        reviewed=None,
        position=None,
    ):
        self.name = name
        self.content = content
        self.rank = rank
        self.added = added if added is not None else timestamp()
        self.reviewed = reviewed if reviewed is not None else timestamp()
        self.status = (
            status if status is not None else 1
        )  # 0 = waiting,  1 = active, 2 =
        self.position = position if position is not None else None

    def __repr__(self) -> str:
        return f"({self.name}, {self.rank}, {self.added}, {self.reviewed}, {self.status}, {self.position})"
