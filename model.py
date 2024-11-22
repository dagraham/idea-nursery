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
