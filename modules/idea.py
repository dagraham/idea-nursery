#! /usr/bin/env python3
import json
import logging
import os
import shlex
import sqlite3
import sys
from pathlib import Path
from typing import List, Optional, Required, Tuple

import click
from click.testing import CliRunner
from click_shell import shell

# from prompt_toolkit.styles.named_colors import NAMED_COLORS
from rich import box, print
from rich.console import Console
from rich.logging import RichHandler
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from modules.database import (
    create_view,
    delete_idea,
    get_find,
    get_idea_by_position,
    get_ideas_from_view,
    get_view_settings,
    insert_idea,
    review_idea,
    set_find,
    set_hide_encoded,
    set_show_encoded,
    update_idea,
)
from modules.model import (
    click_log,
    edit_content_with_nvim,
    format_age_color,
    format_datetime,
    format_idle_color,
    format_timedelta,
    is_valid_path,
    timestamp,
)
from modules.model import type_colors as status_colors

from . import CONFIG_FILE, backup_dir, db_path, idea_home, log_dir, markdown_dir
from .__version__ import version

click_log(
    f"{idea_home = }; {backup_dir = }; {log_dir =}, {markdown_dir}, {db_path = }; {version = }"
)

status_names = ["inkling", "notion", "idea"]
status_pos_to_str = {pos: value for pos, value in enumerate(status_names)}
status_str_to_pos = {value: pos for pos, value in enumerate(status_names)}
valid_status = [i for i in range(len(status_names))]
status_finds = (
    [f"+{name}" for name in status_names]
    + [f"-{name}" for name in status_names]
    + ["clear"]
)
status_find_to_pos = {value: pos for pos, value in enumerate(status_finds)}
status_pos_to_find = {pos: value for pos, value in enumerate(status_finds)}

state_names = ["paused", "active"]
state_colors = ["#938856", "#c4a72f"]
state_pos_to_str = {pos: value for pos, value in enumerate(state_names)}
state_str_to_pos = {value: pos for pos, value in enumerate(state_names)}
valid_state = [i for i in range(len(state_names))]
state_finds = (
    [f"+{name}" for name in state_names]
    + [f"-{name}" for name in state_names]
    + ["clear"]
)
state_find_to_pos = {value: pos for pos, value in enumerate(state_finds)}
state_pos_to_find = {pos: value for pos, value in enumerate(state_finds)}

age_alert_seconds = 4 * 60 * 60  # 1 hour
age_notice_seconds = 2 * 60 * 60  # 30 minutes
idle_alert_seconds = 30 * 60  # 15
idle_notice_seconds = 15 * 60  # 30 minutes
alert_color = "#ff4500"
notice_color = "#ffa500"

console = Console()


@shell(prompt="app> ", intro="Welcome to the idea shell!")
def cli():
    """Idea

    Give your thoughts the care they deserve.

    """
    pass


def update_tmp_home(tmp_home: str = ""):
    """
    Save the IDEA path to the configuration file.
    """
    tmp_home = tmp_home.strip()
    if tmp_home:
        is_valid, message = is_valid_path(tmp_home)
        if is_valid:
            console.print(message)
            config = {"IDEAHOME": tmp_home}
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f)
            console.print(f"Configuration saved to {CONFIG_FILE}")
        else:
            console.print(f"[red]An unexpected error occurred: {message}[/red]")
    elif os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
        console.print(f"[green]Temporary home directory use cancelled[/green]")
    else:
        console.print(f"[yellow]Temporary home directory not in use[/yellow]")


@cli.command("batch")
@click.argument("file_path", required=True)
def process_batch_file(file_path: str):
    """Process commands from a batch file containing one command with any necessary arguments on each line."""
    runner = CliRunner()

    with open(file_path, "r") as file:
        for line in file:
            command = line.strip()
            if command:
                try:
                    print(f"Executing command: {command}")

                    # Use shlex.split to parse the command line
                    args = shlex.split(command)

                    # Pass the parsed command to the CLI runner
                    result = runner.invoke(cli, args)

                    # Check for errors in the result
                    if result.exception:
                        console.print(
                            f"[red]Error executing command: {result.exception}[/red]"
                        )
                    else:
                        console.print(f"Success executing: {command}")

                except Exception as e:
                    console.print(f"[red]Unexpected error: {e}[/red]")
                    console.print(f"Executing command: {command = }; {args = }")


@cli.command("find", short_help="Find ideas by name or content.")
@click.argument("pattern", type=str)
def find(pattern: str):
    """
    Find ideas where name or content matches the given pattern.
    """
    # Build the SQL filter condition
    filter_condition = f"name LIKE '%{pattern}%' OR content LIKE '%{pattern}%'"

    set_find((f"name or content LIKE {pattern}" if pattern else None))

    # Recreate the view with the filter
    create_view(filter_condition)

    # Display the filtered rows
    conn = sqlite3.connect(db_path)
    # rows = conn.execute("SELECT * FROM idea_positions").fetchall()
    _list_all()


@cli.command("set-home")
@click.argument("home", required=False)  # Optional argument for the home directory
def set_home(home):
    """
    Set or clear a temporary home directory for IDEA_NURSERY.
    Provide a path to use as a temporary directory or
    enter nothing to stop using a temporary directory.
    """
    if home is None:
        # No argument provided, clear configuration
        update_tmp_home("")
    else:
        # Argument provided, set configuration
        update_tmp_home(home)


# @cli.command()
# def info():
#     """Display app information."""
#     console.print(
#         f"""\
# [#87CEFA]Idea[/#87CEFA]
# version: [green]{version}[/green]
# home:    [green]{idea_home}[/green]
# """
#     )
#


@cli.command("a", short_help="Alias for add")
@click.argument("name", type=str, nargs=-1)
@click.option("--content", type=str)
@click.option(
    "--status",
    type=click.Choice([r for r in status_names]),
    default=status_names[0],
    help="status of the idea",
)
@click.option(
    "--state",
    type=click.Choice([s for s in state_names]),
    default=state_names[1],
    help="state of the idea",
)
@click.option(
    "--added",
    type=int,
    default=timestamp(),
    help="added timestamp in seconds since the epoch",
)
@click.option(
    "--probed",
    type=int,
    default=timestamp(),
    help="probed timestamp in seconds since the epoch",
)
@click.pass_context
def add_alias(ctx, name, content, status, state, added, probed):
    """Shortcut for "add". Add a new idea with NAME and, optionally, CONTENT."""
    ctx.forward(add)


@cli.command(short_help="Adds an idea")
@click.argument("name", type=str, nargs=-1)
@click.option("--content", type=str)
@click.option(
    "--status",
    type=click.Choice([r for r in status_names]),
    default=status_names[0],
    help="status of the idea",
)
@click.option(
    "--state",
    type=click.Choice([s for s in state_names]),
    default=state_names[1],
    help="state of the idea",
)
@click.option(
    "--added",
    type=int,
    default=timestamp(),
    help="added timestamp in seconds since the epoch",
)
@click.option(
    "--probed",
    type=int,
    default=timestamp(),
    help="probed timestamp in seconds since the epoch",
)
def add(
    name: str,
    content: str = "",
    status: str = "inkling",
    state: str = "active",
    added: int = timestamp(),
    probed: int = timestamp(),
):
    """Add a new idea with NAME and, optionally, CONTENT."""
    print(f"Adding idea with name: {name} and content: {content}")
    full_name = " ".join(name)
    insert_idea(
        name=full_name,
        content=content,
        status=status_str_to_pos[status],
        state=state_str_to_pos[state],
        added=added,
        probed=probed,
    )
    _list_all()


def update(
    position: int,
    name: str = None,
    content: str = None,
    state: int = None,
    status: int = None,
):
    """Update NAME, CONTENT, status, and/or state for idea at POSITION."""
    # Print debug information
    # Call the database function to handle the deletion
    update_idea(
        position,
        name,
        content,
        status_str_to_pos[status] if status is not None else None,
        state_str_to_pos[state] if state is not None else None,
        None,
        timestamp(),
    )
    # Refresh the list to reflect changes
    _list_all()


@cli.command(short_help="Toggles state status between paused and active for idea")
@click.argument("position", type=int)
def pause(position: int):
    """If idea at POSITION is active then pause it else if paused then activate it. When an idea is paused the times since added and since probed are saved and then restored when/if the idea is activated again."""
    position = int(position)
    idea = get_idea_by_position(position)
    # click_log(f"{idea = }")
    if idea:
        id, name, status, state, added, probed, content_ = idea
        # click_log(f"{state = }; {type(state) = }")
        now = timestamp()
        new_added = now - added
        new_probed = now - probed
        new_state = 0 if state == 1 else 1

        # click_log(f"{new_added = }; {added = }; {new_probed = }; {probed = }; {now = }")
        update_idea(
            position,
            None,
            None,
            None,
            new_state,  # state 1 -> 0
            new_added,  # to restore later
            new_probed,  # to restore later
        )
        _list_all()
    else:
        console.print(f"[red]Idea at position {position} not found![/red]")


@cli.command(short_help="Updates the value of status for idea")
@click.argument("position", type=int)  # Second required argument
@click.argument(
    "status",
    type=click.Choice([r for r in status_names]),  # Constrain "status" to valid choices
)
def status(position: int, status: str):
    """Set the value of status for idea at POSITION."""
    idea = get_idea_by_position(position)
    if idea:
        # click_log(f"{idea = }")
        id, name, old_status, state, added, probed, content_ = idea
        new_status = status_str_to_pos[status]
        if new_status == old_status:
            console.print(
                f"[red]The selected value of status, {status}, is unchanged from the current value.[/red]"
            )
            return

        # click_log(f"{status = }")

        update_idea(
            position,
            None,
            None,
            new_status,
            None,  # state 1 -> 0
            None,  # to restore later
            timestamp(),  # to restore later
        )
        _list_all()
    else:
        console.print(f"[red]Idea at position {position} not found![/red]")


@cli.command(short_help="Deletes idea at POSITION")
@click.argument("position", type=int)
def delete(position):
    """Delete an idea at POSITION."""
    # Print debug information
    # Call the database function to handle the deletion
    delete_idea(position)
    # Refresh the list to reflect changes
    _list_all()


@cli.command(short_help="Show ideas based on their status names")
@click.argument(
    "types",
    type=str,
    required=False,
)
def show(types: str):
    """Show only ideas with specified status names."""
    if types is None:
        types = ""
    type_lst = types.split()
    show_positions = []
    for s in type_lst:
        if s not in status_names:
            console.print(
                f"[red]'{s}' is unrecognized.\nOnly status names in: ({', '.join(status_names)}) can be used.[/red]"
            )
            return
        show_positions.append(status_str_to_pos[s])
    set_hide_encoded(show_positions)
    _list_all()


@cli.command(short_help="Hide ideas based on their status names")
@click.argument(
    "types",
    type=str,
    required=False,
)
def hide(types: str):
    """Hide specific ideas based on their status names."""
    if types is None:
        types = ""
    type_lst = types.split()
    hide_positions = []
    for s in type_lst:
        if s not in status_names:
            console.print(
                f"[red]'{s}' is unrecognized.\nOnly status names in ({', '.join(status_names)}) can be used.[/red]"
            )
            return
        hide_positions.append(status_str_to_pos[s])
    set_show_encoded(hide_positions)
    _list_all()


@cli.command("l", short_help="Alias for list")
def list_alias(short_help="Lists aliases"):
    """Alias for "list". Lists all ideas satisfying the current find and show settings."""
    _list_all()


@cli.command(short_help="Lists ideas")
def list():
    """List all ideas satisfying the current find and show settings.
    The POSITION number in the first column is used to specify an idea in commands,
    e.g., "details 3" to see the details of an idea at POSITION 3. The age and idle
    columns refer to how long ago the idea was, repectively, added or last probed/modified.
    """
    _list_all()


def _list_all():
    """List all ideas based on the current view settings."""
    # Fetch filtered ideas
    ideas, show_list = get_ideas_from_view()
    # click_log(f"{ideas = }; {show_list = }")

    hide = []

    if show_list:
        hidden = [x for x in [0, 1, 2] if x not in show_list]
        for pos in hidden:
            hide.append(f"{status_names[pos]}")

    if len(hide) >= 3:
        hide_str = f"{', '.join(hide[:-1])} or {hide[-1]}"
    elif len(hide) >= 2:
        hide_str = f"{' or '.join(hide)}"
    elif hide:
        hide_str = f"{hide[0]}"
    else:
        hide_str = ""

    hiding = f"hiding ideas with status {hide_str}" if hide_str else ""

    find = get_find()
    showing = f"showing ideas with {find}" if find else ""

    # click_log(f"showing = '{showing}'; hiding = '{hiding}'")

    if showing and hiding:
        caption = f"{showing} but {hiding}"
    elif showing:
        caption = showing
    elif hide_str:
        caption = hiding
    else:
        caption = ""

    # Render the table
    console.clear()
    console.print(f" 💡[#87CEFA]Idea[/#87CEFA]")
    table = Table(
        show_header=True,
        # header_style="bold blue",
        header_style="#87CEFA",
        expand=True,
        box=box.HEAVY_EDGE,
        caption=caption,
    )
    table.add_column("#", style="dim", min_width=1, justify="right")
    table.add_column("name", min_width=24)
    # table.add_column("state", width=6, justify="center")
    table.add_column("status", width=6, justify="center")
    table.add_column("added", width=6, justify="center")
    table.add_column("probed", width=6, justify="center")

    for idx, idea in enumerate(ideas, start=1):
        # click_log(f"{idx = }; {idea = }; {type(idea) = }")
        id_, name, status, state, added_, probed_, position_ = idea
        # click_log(f"{id_ = }; {name = }; {status = }")
        if state == 1:
            age = f"{format_age_color(timestamp() - added_, num=2, color_type=status)}"
            idle = (
                f"{format_idle_color(timestamp() - probed_, num=2, color_type=status)}"
            )
        else:
            idle = "~"
            age = "~"
        table.add_row(
            str(idx),
            f"[{status_colors[status]}]{name}",
            # f"[{state_colors[state]}]{state_pos_to_str[state]}",
            f"[{status_colors[status]}]{status_pos_to_str[status]}",
            f"{age}",
            f"{idle}",
        )
    console.print(table)


@cli.command("i", short_help="Alias for info")
@click.argument("position", type=int, required=False)
@click.pass_context
def info_alias(ctx, position):
    """Alias for info. If given, show details for idea at POSITION, else application information."""
    ctx.forward(info)


@cli.command(short_help="Shows details for idea")
@click.argument("position", type=int, required=False)
def info(position):
    """If given, show details for idea at POSITION, else application information."""
    if position is None:
        console.print(
            f"""\
[#87CEFA]Idea[/#87CEFA]
version: [green]{version}[/green]
home:    [green]{idea_home}[/green]
"""
        )
        return

    now = timestamp()
    console.clear()
    idea = get_idea_by_position(position)
    # click_log(f"idea from {position = }: {idea}")

    if idea:
        id, name, status, state, added, probed, content = idea
        status_str = (
            f"{status:<14} ({status_pos_to_str[status]})" if status is not None else ""
        )
        state_str = (
            f"{state:<14} ({state_pos_to_str[state]})" if state is not None else ""
        )
        added_str = (
            f"{added:<14} ({format_timedelta(now - added, num=2)} ago at {format_datetime(added)})"
            if added is not None and state == 1
            else (
                f"{added:<14} ({format_timedelta(added, num=2)} ago at {format_datetime(now - added)})"
                if added is not None
                else ""
            )
        )
        probed_str = (
            f"{probed:<14} ({format_timedelta(now - probed, num=2)} ago at {format_datetime(probed)})"
            if probed is not None and state == 1
            else (
                f"{probed:<14} ({format_timedelta(probed, num=2)} ago at {format_datetime(now - probed)})"
                if added is not None
                else ""
            )
        )
        meta = f"""\
name:      {name}
status:    {status_str}  
state:     {state_str}    
added:     {added_str}  
probed:    {probed_str}\
"""

        res = f"""\
# {name}
{content}\
"""
        md = Markdown(res)
        console.print(Panel(md, title="content"))
        console.print(Panel(meta, title="data"))
    else:
        console.print(f"[red]Idea at position {position} not found![/red]")


@cli.command("e", short_help="Alias for edit")
@click.argument("position", type=int)
@click.pass_context
def edit_alias(ctx, position):
    """Alias for "edit". Edit name and content for idea at POSITION."""
    ctx.forward(edit)


@cli.command(short_help="Review and edit name and content for idea in nvim")
@click.argument("position", type=int)
def edit(position: int):
    """Edit name and content for idea at POSITION."""
    console.clear()
    idea = get_idea_by_position(position)
    # click_log(f"starting with {idea = }")
    if idea:
        id, name, status, state, added_, probed_, content = idea
        new_name, new_content = edit_content_with_nvim(name, content)
        # click_log(f"{position = }; {id = }; {new_name = }; {new_content = }")
        update_idea(position, new_name, new_content, None, None, None, timestamp())
        _list_all()


# @cli.command("review")
# @click.argument("position", type=int)
# def review(position):
#     """
#     Review the idea for a specific position.
#     """
#     click.echo(f"Reviewing idea at position {position}...")
#
#
# @cli.command("re")  # Shortcut for "review"
# @click.argument("position", type=int)
# @click.pass_context
# def review_shortcut(ctx, position):
#     """
#     Shortcut for the review command.
#     """
#     ctx.forward(review)
#


def main():
    try:
        # Handle 'shell' command
        if len(sys.argv) > 1 and sys.argv[1] == "shell":
            _list_all()
            sys.argv = [sys.argv[0]]  # Reset arguments to avoid conflict
            cli.main(prog_name="idea")

        # Default to Click's CLI
        else:
            cli.main(prog_name="idea")
    except Exception as e:
        console.print(f"[red]An unexpected error occurred in main: {e}[/red]")


if __name__ == "__main__":
    main()
