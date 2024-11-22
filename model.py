import datetime
from enum import Enum


def format_timedelta(seconds: int, short: bool = True) -> str:
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


def format_datetime(seconds: int, fmt: str = "%Y-%m-%d %H:%M %Z") -> str:
    return datetime.datetime.fromtimestamp(seconds).astimezone().strftime(fmt)


def timestamp() -> int:
    return round(datetime.datetime.now().timestamp())


# class Rank(str, Enum):
#     spark = "spark"
#     inkling = "inkling"
#     thought = "thought"
#     idea = "idea"
#
#
# class Status(str, Enum):
#     deferred = "deferred"
#     active = "active"
#     promoted = "promoted"


# class Rank:
#     _valid_ranks = {1: "spark", 2: "inkling", 3: "thought", 4: "brainstorm"}
#
#     def __init__(self, value: int):
#         if value not in [1, 2, 3, 4]:
#             raise ValueError(f"{value} is not a valid Rank")
#         self.value = value
#
#     @classmethod
#     def from_int(cls, value: int):
#         """Create a Rank from an integer, validating it."""
#         return cls(value)
#
#     @classmethod
#     def display_name(cls, value: int) -> str:
#         """Get the display name for a given integer rank."""
#         return cls._valid_ranks.get(value, "Unknown")
#
#     def __str__(self):
#         return self.display_name(self.value)
#
#
# class Status:
#     _valid_statuses = {1: "deferred", 2: "active", 3: "promoted"}
#
#     def __init__(self, value: int):
#         if value not in [1, 2, 3]:
#             raise ValueError(f"{value} is not a valid Status")
#         self.value = value
#
#     @classmethod
#     def from_int(cls, value: int):
#         """Create a Status from an integer, validating it."""
#         return cls(value)
#
#     @classmethod
#     def display_name(cls, value: int) -> str:
#         """Get the display name for a given integer status."""
#         return cls._valid_statuses.get(value, "Unknown")
#
#     def __str__(self):
#         return self.display_name(self.value)
#


class Idea:
    def __init__(
        self,
        name,
        content,
        rank=1,
        status=2,
        added=None,
        reviewed=None,
        id=None,
        position=None,
    ):
        self.name = name
        self.content = content
        self.rank = rank
        self.status = status
        self.added = added if added is not None else timestamp()
        self.reviewed = reviewed if reviewed is not None else timestamp()
        self.id = id if id is not None else None
        self.position = position if position is not None else None

    def __repr__(self) -> str:
        return f"({self.name}, {self.rank}, {self.status}, {self.added}, {self.reviewed}, {self.id}, {self.position})"
