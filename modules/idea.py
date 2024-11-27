#! /usr/bin/env python3
import json
import logging

# import os
import shlex
import sys

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
    get_idea_by_position,
    get_ideas_from_view,
    get_view_settings,
    insert_idea,
    review_idea,
    set_view_settings,
    update_idea,
)
from modules.model import (
    click_log,
    edit_content_with_nvim,
    format_datetime,
    format_timedelta,
    timestamp,
)

from . import backup_dir, db_path, idea_home, log_dir
from .__version__ import version

click_log(f"{idea_home = }; {backup_dir = }; {log_dir =}, {db_path = }; {version = }")
# from pathlib import Path


# from rich.traceback import install

# install(show_locals=True, max_frames=4)

stage_names = ["seed", "sprout", "seedling", "plant"]
stage_colors = ["#3e8b9b", "#7aaf6c", "#b5d23d", "#e8f115"]
stage_pos_to_str = {pos: value for pos, value in enumerate(stage_names)}
stage_str_to_pos = {value: pos for pos, value in enumerate(stage_names)}
valid_stage = [i for i in range(len(stage_names))]
stage_filters = (
    [f"+{name}" for name in stage_names]
    + [f"-{name}" for name in stage_names]
    + ["clear"]
)
stage_filter_to_pos = {value: pos for pos, value in enumerate(stage_filters)}
stage_pos_to_filter = {pos: value for pos, value in enumerate(stage_filters)}

status_names = ["paused", "active", "available"]
status_colors = ["#938856", "#c4a72f", "#f5c608"]
status_pos_to_str = {pos: value for pos, value in enumerate(status_names)}
status_str_to_pos = {value: pos for pos, value in enumerate(status_names)}
valid_status = [i for i in range(len(status_names))]
status_filters = (
    [f"+{name}" for name in status_names]
    + [f"-{name}" for name in status_names]
    + ["clear"]
)
status_filter_to_pos = {value: pos for pos, value in enumerate(status_filters)}
status_pos_to_filter = {pos: value for pos, value in enumerate(status_filters)}

age_alert_seconds = 4 * 60 * 60  # 1 hour
age_notice_seconds = 2 * 60 * 60  # 30 minutes
idle_alert_seconds = 30 * 60  # 15
idle_notice_seconds = 15 * 60  # 30 minutes
alert_color = "#ff4500"
notice_color = "#ffa500"


console = Console()


@shell(prompt="app> ", intro="Welcome to the idea manager shell!")
def cli():
    """Idea Nursery Shell"""
    pass


def process_batch_file(file_path: str):
    """Process commands from a batch file."""
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


@cli.command(short_help="Adds an idea")
@click.argument("name")
@click.option("--content", type=str, help="Content of the idea")
@click.option(
    "--stage",
    type=click.Choice([r for r in stage_names]),
    default=stage_names[0],
    help="Stage of the idea",
)
@click.option(
    "--status",
    type=click.Choice([s for s in status_names]),
    default=status_names[1],
    help="Status of the idea",
)
def add(name, content, stage, status):
    """Add a new idea with NAME, CONTENT, STAGE, and STATUS."""
    print(
        f"Adding idea with name: {name}, content: {content}, stage: {stage}, status: {status}"
    )
    insert_idea(
        name,
        content,
        stage_str_to_pos[stage] if stage is not None else 0,
        status_str_to_pos[status] if status is not None else 1,
    )
    _list_all()


@cli.command(short_help="Updates data for idea")
@click.argument("position", type=int)
@click.option("--name")
@click.option("--content", type=str, help="Content of the idea")
@click.option(
    "--stage",
    type=click.Choice([r for r in stage_names]),
    default=stage_names[0],
    help="Stage of the idea",
)
@click.option(
    "--status",
    type=click.Choice([s for s in status_names]),
    default=status_names[1],
    help="Status of the idea",
)
def update(
    position: int,
    name: str = None,
    content: str = None,
    status: int = None,
    stage: int = None,
):
    """Update NAME, CONTENT, STAGE, and/or STATUS for idea at POSITION."""
    # Print debug information
    click.echo(f"Update idea at position {position}")
    # Call the database function to handle the deletion
    update_idea(
        position,
        name,
        content,
        stage_str_to_pos[stage] if stage is not None else None,
        status_str_to_pos[status] if status is not None else None,
        None,
        None,
    )
    # Refresh the list to reflect changes
    _list_all()


@cli.command(short_help="Changes status from active to paused for idea")
@click.argument("position", type=int)
def pause(position: int):
    idea = get_idea_by_position(position)
    click_log(f"{idea = }")
    if idea:
        id, name, stage, status, added, reviewed, content_ = idea
        click_log(f"{status = }; {type(status) = }")
        if status != 1:
            console.print(
                f"[red]Only ideas whose status is {status_names[1]} can be paused![/red]"
            )
            return
        now = timestamp()
        # adjust added and reviewed to be restored when idea is activated
        new_added = now - added
        new_reviewed = now - reviewed
        click_log(
            f"{new_added = }; {added = }; {new_reviewed = }; {reviewed = }; {now = }"
        )
        update_idea(
            position,
            None,
            None,
            None,
            0,  # status 1 -> 0
            new_added,  # to restore later
            new_reviewed,  # to restore later
        )
        _list_all()

    else:
        console.print(f"[red]Idea at position {position} not found![/red]")


@cli.command(short_help="Changes status from paused to active for idea")
@click.argument("position", type=int)
def activate(position: int):
    idea = get_idea_by_position(position)
    click_log(f"{idea = }")
    if idea:
        id, name, stage, status, added, reviewed, content_ = idea
        click_log(f"{status = }; {type(status) = }")
        if status != 0:
            console.print(
                f"[red]Only ideas whose status is {status_names[0]} can be activated![/red]"
            )
            return
        now = timestamp()
        # adjust added and reviewed to be restored when idea is activated
        new_added = now - added
        new_reviewed = now - reviewed
        click_log(
            f"{new_added = }; {added = }; {new_reviewed = }; {reviewed = }; {now = }"
        )
        update_idea(
            position,
            None,
            None,
            None,
            1,  # status 1 -> 0
            new_added,  # to restore later
            new_reviewed,  # to restore later
        )
        _list_all()

    else:
        console.print(f"[red]Idea at position {position} not found![/red]")


@cli.command(short_help="Updates reviewed timestamp for idea")
@click.argument("position", type=int)
def review(position):
    """Review idea at POSITION."""
    # Print debug information
    click_log(f"Review idea at position {position}")
    idea = get_idea_by_position(position)
    click_log(f"{idea = }")
    if idea:
        id, name, stage, status, added, reviewed, content_ = idea
        click_log(f"{status = }; {type(status) = }")
        if status != 1:
            console.print(
                f"[red]Only ideas whose status is {status_names[1]} can be reviewed![/red]"
            )
            return
        review_idea(position)
        # Refresh the list to reflect changes
        _list_all()
    else:
        console.print(f"[red]Idea at position {position} not found![/red]")


@cli.command(short_help="Deletes an idea")
@click.argument("position", type=int)
def delete(position):
    """Delete an idea at POSITION."""
    # Print debug information
    click.echo(f"Deleting idea at position {position}")
    # Call the database function to handle the deletion
    delete_idea(position)
    # Refresh the list to reflect changes
    _list_all()


@cli.command(short_help="Focus on ideas based on their stage and status properties")
@click.option(
    "--stage",
    type=click.Choice([r for r in stage_filters]),
    help=f"With, e.g., '+{stage_names[0]}' only show ideas with stage '{stage_names[0]}'. With '-{stage_names[0]}' only show ideas that do NOT have stage '{stage_names[0]}'. 'clear' removes the stage focus.",
)
@click.option(
    "--status",
    type=click.Choice([s for s in status_filters]),
    help=f"With, e.g., '+{status_names[0]}' only show ideas with status '{status_names[0]}'. With '-{status_names[0]}' only show ideas that do NOT have status '{status_names[0]}'. 'clear' removes the status focus.",
)
def focus(status: str = None, stage: str = None):
    """Set or clear focus."""
    current_status, current_stage = get_view_settings()
    # Update settings based on user input

    if status is not None:
        current_status = status_filter_to_pos[status]
    if stage is not None:
        current_stage = stage_filter_to_pos[stage]
    set_view_settings(current_status, current_stage)
    click.echo(f"View settings updated: status={current_status}, stage={current_stage}")
    _list_all()


@cli.command(short_help="Lists ideas")
def list():
    """List all ideas based on the current focus settings."""
    _list_all()


def _list_all():
    """List all ideas based on the current view settings."""
    # Fetch filtered ideas
    ideas, current_status, current_stage = get_ideas_from_view()
    # click_log(f"{ideas = }")

    caption_elements = []
    if int(current_status) < len(status_pos_to_filter.keys()) - 1:
        caption_elements.append(f"--status {status_pos_to_filter.get(current_status)}")
    if int(current_stage) < len(stage_pos_to_filter.keys()) - 1:
        caption_elements.append(f"--stage {stage_pos_to_filter.get(current_stage)}")

    caption = ""
    if caption_elements:
        caption = f"focus {' '.join(caption_elements)}"

    # # ideas = get_ideas_from_view()
    # with open("debug.log", "a") as debug_file:
    #     click.echo(
    #         f"ideas from view: {ideas}; {current_status = };  {current_stage = }; {caption = }",
    #         file=debug_file,
    #     )
    # log.info(f"{ideas}")

    # Render the table
    console.clear()
    console.print(" 💡[#87CEFA]Idea Nursery[/#87CEFA]")
    table = Table(
        show_header=True,
        header_style="bold blue",
        expand=True,
        box=box.HEAVY_EDGE,
        caption=caption,
    )
    table.add_column("#", style="dim", min_width=1, justify="right")
    table.add_column("name", min_width=24)
    table.add_column("stage", width=7, justify="center")
    table.add_column("status", width=7, justify="center")
    table.add_column("age", width=4, justify="center")
    table.add_column("idle", width=4, justify="center")

    for idx, idea in enumerate(ideas, start=1):
        id_, name, stage, status, added_, reviewed_, position_ = idea
        if status == 1:
            idle = format_timedelta(timestamp() - reviewed_)
            age = format_timedelta(timestamp() - added_)
            age_color = ...
        else:
            age_color = idle_color = stage_colors[stage]
            idle = "~"
            age = "~"
        table.add_row(
            str(idx),
            name,
            f"[{stage_colors[stage]}]{stage_pos_to_str[stage]}",
            f"[{status_colors[status]}]{status_pos_to_str[status]}",
            f"{age}",
            f"{idle}",
            # f"{format_timedelta(timestamp() - added_, colors=(age_notice_seconds, age_alert_seconds))}",
            # f"{format_timedelta(timestamp() - reviewed_, colors=(idle_notice_seconds, idle_alert_seconds))}",
        )
    console.print(table)


@cli.command(short_help="Shows details for idea")
@click.argument("position", type=int)
def details(position):
    """Show details for idea at POSITION."""
    now = timestamp()
    console.clear()
    idea = get_idea_by_position(position)
    click_log(f"idea from {position = }: {idea}")

    if idea:
        id, name, stage, status, added, reviewed, content = idea
        stage_str = (
            f"{stage:<14} ({stage_pos_to_str[stage]})" if stage is not None else ""
        )
        status_str = (
            f"{status:<14} ({status_pos_to_str[status]})" if status is not None else ""
        )
        added_str = (
            f"{added:<14} ({format_timedelta(now - added, short=False)} ago at {format_datetime(added)})"
            if added is not None and status == 1
            else (
                f"{added:<14} ({format_timedelta(added, short=False)} ago at {format_datetime(now - added)})"
                if added is not None
                else ""
            )
        )
        reviewed_str = (
            f"{reviewed:<14} ({format_timedelta(now - reviewed, short=False)} ago at {format_datetime(reviewed)})"
            if reviewed is not None and status == 1
            else (
                f"{reviewed:<14} ({format_timedelta(reviewed, short=False)} ago at {format_datetime(now - reviewed)})"
                if added is not None
                else ""
            )
        )
        meta = f"""\
name:      {name}
stage:     {stage_str}  
status:    {status_str}    
added:     {added_str}  
reviewed:  {reviewed_str}\
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


@cli.command(short_help="Edit content for idea in nvim")
@click.argument("position", type=int)
def edit(position):
    """Show details for idea at POSITION."""
    now = timestamp()
    console.clear()
    idea = get_idea_by_position(position)
    click_log(f"starting with {idea = }")
    if idea:
        id, name, stage, status, added_, reviewed_, content = idea
        new_content = edit_content_with_nvim(content, f'"{name}"')
        click_log(f"{position = }; {id = }; {new_content = }")
        update_idea(position, None, new_content, None, None)


# def main():
#     if "-t" in sys.argv:
#         try:
#             idx = sys.argv.index("-t")
#             batch_file = sys.argv[idx + 1]
#             process_batch_file(batch_file)
#             return
#         except IndexError:
#             console.print("[red]Error: Missing batch file after -t[/red]")
#             return
#     elif "--file" in sys.argv:
#         try:
#             idx = sys.argv.index("--file")
#             batch_file = sys.argv[idx + 1]
#             process_batch_file(batch_file)
#             return
#         except IndexError:
#             console.print("[red]Error: Missing batch file after --file[/red]")
#             return
#
#     elif len(sys.argv) > 1 and sys.argv[1] == "shell":
#         sys.argv.pop(1)  # Remove 'shell' argument to prevent interference
#         _list_all()
#         cli()
#     else:
#         if len(sys.argv) == 1:
#             sys.argv.append("--help")
#         cli.main(prog_name="idea")


def main():
    try:
        # Handle batch processing for -t and --file options directly
        if "-t" in sys.argv or "--file" in sys.argv:
            if "-t" in sys.argv:
                idx = sys.argv.index("-t")
            elif "--file" in sys.argv:
                idx = sys.argv.index("--file")

            try:
                batch_file = sys.argv[idx + 1]
                process_batch_file(batch_file)
                return
            except IndexError:
                console.print("[red]Error: Missing batch file after -t or --file[/red]")
                return

        # Handle 'shell' command
        if len(sys.argv) > 1 and sys.argv[1] == "shell":
            _list_all()
            sys.argv = [sys.argv[0]]  # Reset arguments to avoid conflict
            cli.main(prog_name="idea")

        # Default to Click's CLI
        else:
            cli.main(prog_name="idea")
    except Exception as e:
        console.print(f"[red]An unexpected error occurred: {e}[/red]")


if __name__ == "__main__":
    main()
