import datetime
import inspect
import os
import subprocess
import tempfile
from enum import Enum
from typing import Tuple

import click

alert_color = "#ff4500"
notice_color = "#ffa500"


def click_log(msg: str):
    # Get the name of the calling function
    caller_name = inspect.stack()[1].function

    # Format the log message
    with open("debug.log", "a") as debug_file:
        msg = f"\nclick_log {format_datetime(timestamp())} [{caller_name}]\n{msg}"
        click.echo(
            msg,
            file=debug_file,
        )


def format_timedelta(
    seconds: int, short: bool = True, colors: Tuple[int, int] = (0, 0)
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

    notice_seconds, alert_seconds = colors
    if alert_seconds > 0 and seconds >= alert_seconds:
        # apply alert colors
        ret = f"[{alert_color}]" + ret
    elif notice_seconds > 0 and seconds >= notice_seconds:
        ret = f"[{notice_color}]" + ret

    return ret


def format_datetime(seconds: int, fmt: str = "%Y-%m-%d %H:%M %Z") -> str:
    return datetime.datetime.fromtimestamp(seconds).astimezone().strftime(fmt)


def timestamp() -> int:
    return round(datetime.datetime.now().timestamp())


def edit_content_with_nvim(initial_content: str) -> str:
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", delete=False
        ) as tmp_file:
            file_name = tmp_file.name
            # Write the initial content
            tmp_file.write(initial_content)
            tmp_file.flush()

        # click_log(f"Temporary file created: {file_name}")

        # Open Neovim to edit the file
        subprocess_return = subprocess.call(["nvim", file_name])
        # click_log(f"Neovim subprocess finished with return code: {subprocess_return}")

        if subprocess_return != 0:
            raise RuntimeError("Neovim exited with a non-zero status.")

        # Reopen the file in read mode to get the updated content
        with open(file_name, "r") as tmp_file:
            updated_content = tmp_file.read()
            # click_log(f"Read updated content: {updated_content}")

        # Clean up the temporary file
        os.unlink(file_name)
        # click_log(f"Temporary file deleted: {file_name}")

        return updated_content

    except Exception as e:
        click_log(f"An error occurred: {e}")
        raise
