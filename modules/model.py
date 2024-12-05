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

from make_examples import status

from . import backup_dir, db_path, idea_home, log_dir


def timestamp() -> int:
    return round(datetime.datetime.now().timestamp())


def format_datetime(
    seconds: int, fmt: str = "%Y-%m-%d %H:%M %Z", stage: int = 1, use_color=False
) -> str:
    if use_color:
        return f"[{get_color(stage, seconds)}]{datetime.datetime.fromtimestamp(seconds).astimezone().strftime(fmt)}"
    else:
        return f"{datetime.datetime.fromtimestamp(seconds).astimezone().strftime(fmt)}"


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


alert_color = "#ff4500"
notice_color = "#ffa500"


def hex_to_rgb(hex_color):
    """Convert a hex color (#RRGGBB) to an RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    """Convert an RGB tuple to a hex color (#RRGGBB)."""
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def interpolate_colors(color1, color2, n):
    """
    Generate a list of n colors forming a gradient between color1 and color2.
    color1, color2: Hex color strings (#RRGGBB)
    n: Number of colors to generate
    """
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)

    colors = []
    for i in range(n):
        interpolated = tuple(
            int(rgb1[j] + (rgb2[j] - rgb1[j]) * i / (n - 1)) for j in range(3)
        )
        colors.append(rgb_to_hex(interpolated))
    return colors


# Example usage
start_color = "#fcf5f2"
end_color = "#cc3300"
num_colors = 10

# gradient = interpolate_colors(start_color, end_color, num_colors)
# print(gradient)


oneperiod = 24 * 60 * 60  # seconds in one day
status_ages = [0, 2, 5, 9, 14, 20, 26, 32]  # in periods

# status_colors = [
#     #   inkling,    notion,      thought,      idea
#     ["#3399FF", "#7aaf6c", "#b5d23d", "#e8f115"],  # age/row index 0
#     ["#478fe6", "#9b9051", "#c8aa2e", "#eec210"],  # age/row index 1
#     ["#8f6b8c", "#bc7136", "#de7b1b", "#f58809"],  # age/row index 2
#     ["#cc4c40", "#de521b", "#f0530c", "#f96205"],  # age/row index 3
#     ["#ff3300", "#ff3300", "#ff3300", "#ff3300"],  # age/row index 4
# ]


type_colors = interpolate_colors("#7dbe20", "#ffff00", 4)
# click_log(f"{type_colors = }")

# status_colors = [
#     interpolate_colors("#73e600", "#FF3300", 4),
#     interpolate_colors("#7AAF6C", "#FF3300", 4),
#     interpolate_colors("#B5D23D", "#FF3300", 4),
#     interpolate_colors("#E8F115", "#FF3300", 4),
# ]

status_colors = [
    interpolate_colors(type_colors[0], "#FF3300", 4),
    interpolate_colors(type_colors[1], "#FF3300", 4),
    interpolate_colors(type_colors[2], "#FF3300", 4),
    interpolate_colors(type_colors[3], "#FF3300", 4),
]


idle_colors = interpolate_colors("#ffffff", "#ff9900", 32)

idle_ages = [x // 2 for x in range(32)]


def get_color(color_type: int, seconds: int):
    color = "#cc9900"
    pos = 0
    try:
        periods = round(seconds / oneperiod)
        if color_type in [0, 1, 2, 3]:  # colors from status_ages and colors
            pos = find_position(status_ages[color_type:], periods)
            color = (
                status_colors[color_type][pos]
                if pos <= 4
                else status_colors[color_type][-1]
            )
        elif color_type == 4:  # colors from idle_ages and colors
            pos = find_position(idle_ages, periods)
            color = idle_colors[pos] if pos <= 21 else idle_colors[-1]
            click_log(f"got {color = } for {pos = }")
        return color
    except Exception as e:
        click_log(
            f"Exception {e} raised processing {color_type = } and {seconds = } for {pos = }"
        )
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


def find_position(lst, x):
    try:
        pos = bisect.bisect_right(lst, x)
        if pos >= 0:
            return pos
        else:
            return 0
    except Exception as e:
        click_log(f"Exception {e} raised processing {lst = } and {x =}")
        return 0


s = 1
m = 60 * s
h = 60 * m
d = 24 * h
w = 7 * d
y = 52 * w
units = [s, m, h, d, w, y]
labels = ["seconds", "minutes", "hours", "days", "weeks", "years"]


def skip_show_units(seconds: int, num: int = 1):
    pos = find_position(units, seconds)
    used_labels = labels[:pos]
    show_labels = used_labels[-num:]
    round_labels = used_labels[:-num]

    return round_labels, show_labels


def format_timedelta(
    total_seconds: int, num: int = 1, color_type: int = 1, use_colors=False
) -> str:
    # if total_seconds == 0:
    #     return "0m"
    sign = ""
    if total_seconds < 0:
        sign = "-"
        total_seconds = abs(total_seconds)
    until = []
    skip, show = skip_show_units(total_seconds, num)
    click_log(f"{skip = }; {show = }")

    years = weeks = days = hours = minutes = 0
    if total_seconds:
        seconds = total_seconds
        if seconds >= 60:
            minutes = seconds // 60
            seconds = seconds % 60
            if "seconds" in skip and seconds >= 30:
                minutes += 1
        if minutes >= 60:
            hours = minutes // 60
            minutes = minutes % 60
            if "minutes" in skip and minutes >= 30:
                hours += 1
        if hours >= 24:
            days = hours // 24
            hours = hours % 24
            if "hours" in skip and hours >= 12:
                days += 1
        if days >= 7:
            weeks = days // 7
            days = days % 7
            if "days" in skip and days >= 4:
                weeks += 1
        if weeks >= 52:
            years = weeks // 52
            weeks = weeks % 52
            if "weeks" in skip and weeks >= 26:
                years += 1
    else:
        seconds = 0
    if "years" in show:
        until.append(f"{years}y")
    if "weeks" in show:
        until.append(f"{weeks}w")
    if "days" in show:
        until.append(f"{days}d")
    if "hours" in show:
        until.append(f"{hours}h")
    if "minutes" in show:
        until.append(f"{minutes}m")
    if "seconds" in show:
        until.append(f"{seconds}s")
    if not until:
        until.append("0s")
    ret = f"{sign}{''.join(until)}"
    click_log(f"{ret = }")

    if use_colors:
        color = get_color(color_type, total_seconds)
        click_log(f"{color_type = }; {seconds = }; {color = }")
        ret = f"[{color}]" + ret

    return ret


def edit_content_with_nvim(name: str, content: str):
    # Write the content to a temporary file
    temp_path = f'/tmp/f"{name}"'
    with open(temp_path, "w") as tmp_file:
        tmp_file.write(
            f"""\
{name.strip()}

{content.lstrip() if content is not None else ""}
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
