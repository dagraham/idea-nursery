import bisect
import datetime
import inspect
import os
import subprocess
import tempfile
from enum import Enum
from pathlib import Path
from typing import Tuple

import click

from . import backup_dir, db_path, idea_home, log_dir

alert_color = "#ff4500"
notice_color = "#ffa500"


oneperiod = 24 * 60 * 60  # seconds in one day
ages = [0, 2, 5, 9, 14, 20, 26, 32]  # in periods

colors = [
    #    seed,        sprout,     seedling,     plant
    ["#3e8b9b", "#7aaf6c", "#b5d23d", "#e8f115"],  # age/row index 0
    ["#78716c", "#9b9051", "#c8aa2e", "#eec210"],  # age/row index 1
    ["#b2563e", "#bc7136", "#de7b1b", "#f58809"],  # age/row index 2
    ["#b2563e", "#de521b", "#f0530c", "#f96205"],  # age/row index 3
    ["#ff3300", "#ff3300", "#ff3300", "#ff3300"],  # age/row index 4
]


def find_position(lst, x):
    pos = bisect.bisect_right(lst, x) - 1
    if pos >= 0:
        return min(4, pos)
    else:
        return 0
        # No element in the list is less than or equal to x


def get_color(stage: int, seconds: int):
    periods = round(seconds / oneperiod)
    pos = find_position(ages[stage:], periods)
    color = colors[pos][stage]
    return color


def is_valid_path(path):
    """
    Check if a given path is a valid directory.
    """
    path = Path(path).expanduser()

    # Check if the path exists and is a directory
    if path.exists():
        if path.is_dir():
            if os.access(path, os.W_OK):  # Check if writable
                return True, f"{path} is a valid and writable directory."
            else:
                return False, f"{path} is not writable."
        else:
            return False, f"{path} exists but is not a directory."
    else:
        # Try to create the directory
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True, f"{path} did not exist but has been created."
        except OSError as e:
            return False, f"Cannot create directory at {path}: {e}"


# TODO: add optional log level to click_log?
def click_log(msg: str):
    # Get the name of the calling function
    caller_name = inspect.stack()[1].function
    ts = timestamp()
    log_name = format_datetime(ts, "%Y-%m-%d.log")

    # Format the log message
    with open(os.path.join(log_dir, log_name), "a") as debug_file:
        msg = f"\nclick_log {format_datetime(timestamp())} [{caller_name}]\n{msg}"
        click.echo(
            msg,
            file=debug_file,
        )


def format_timedelta(
    seconds: int, short: bool = True, stage: int = 1, use_colors=False
) -> str:
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
        ret = f"{sign}{until[0]}"
    else:
        ret = f"{sign}{''.join(until)}"

    if use_colors:
        color = get_color(stage, seconds)
        click_log(f"{stage = }; {seconds = }; {color = }")
        ret = f"[{color}]" + ret

    return ret


def format_datetime(
    seconds: int, fmt: str = "%Y-%m-%d %H:%M %Z", stage: int = 1, use_color=False
) -> str:
    if use_color:
        return f"[{get_color(stage, seconds)}]{datetime.datetime.fromtimestamp(seconds).astimezone().strftime(fmt)}"
    else:
        return f"{datetime.datetime.fromtimestamp(seconds).astimezone().strftime(fmt)}"


def timestamp() -> int:
    return round(datetime.datetime.now().timestamp())


def edit_content_with_nvim(name: str, content: str):
    # Write the content to a temporary file
    temp_path = f'/tmp/f"{name}"'
    with open(temp_path, "w") as tmp_file:
        tmp_file.write(
            f"""\
{name.strip()}

{content.lstrip()}
"""
        )

    # Open the file in nvim
    subprocess.call(["nvim", temp_path])

    # Read the updated content
    with open(temp_path, "r") as tmp_file:
        name_and_content = tmp_file.read()
        lines = name_and_content.splitlines()
        new_name = lines.pop(0).strip()
        new_content = "\n".join(lines)

    # Cleanup
    os.unlink(temp_path)

    click_log(f"{new_name}; {new_content = }")

    return new_name, new_content
