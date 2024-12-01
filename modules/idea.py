#! /usr/bin/env python3
import json
import logging
import os
import shlex
import sys
from pathlib import Path

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
    is_valid_path,
    timestamp,
)

from . import CONFIG_FILE, backup_dir, db_path, idea_home, log_dir, markdown_dir
from .__version__ import version

click_log(
    f"{idea_home = }; {backup_dir = }; {log_dir =}, {markdown_dir}, {db_path = }; {version = }"
)

# stage_names = ["seed", "sprout", "seedling", "plant"]
stage_names = ["inkling", "notion", "thought", "idea"]
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

# status_names = ["paused", "active", "available"]
status_names = ["paused", "active"]
# status_colors = ["#938856", "#c4a72f", "#f5c608"]
status_colors = ["#938856", "#c4a72f"]
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


@shell(prompt="app> ", intro="Welcome to the idea nursery shell!")
def cli():
    """Idea Nursery

    Give your thoughts the care they deserve.

    """
    pass


def update_tmp_home(tmp_home: str = ""):
    """
    Save the IDEA_NURSERY path to the configuration file.
    """
    tmp_home = tmp_home.strip()
    if tmp_home:
        is_valid, message = is_valid_path(tmp_home)
        if is_valid:
            console.print(message)
            config = {"IDEANURSERY": tmp_home}
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


@cli.command()
def info():
    """Display app information."""
    console.print(
        f"""\
[#87CEFA]Idea Nursery[/#87CEFA]
version: [green]{version}[/green]
home:    [green]{idea_home}[/green]
"""
    )


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
@click.option(
    "--added",
    type=int,
    default=timestamp(),
    help="Added timestamp in seconds since the epoch",
)
@click.option(
    "--reviewed",
    type=int,
    default=timestamp(),
    help="Reviewed timestamp in seconds since the epoch",
)
def add(name, content, stage, status, added, reviewed):
    """Add a new idea with NAME, CONTENT, STAGE, and STATUS."""
    print(
        f"Adding idea with name: {name}, content: {content}, stage: {stage}, status: {status}, added: {added}, reviewed: {reviewed}"
    )
    insert_idea(
        name,
        content,
        stage_str_to_pos[stage] if stage is not None else 0,
        status_str_to_pos[status] if status is not None else 1,
        added,
        reviewed,
    )
    _list_all()


@cli.command(short_help="Updates data for idea")
@click.argument("position", type=int)
@click.option("--name")
@click.option("--content", type=str, help="Content of the idea")
@click.option(
    "--stage",
    type=click.Choice([r for r in stage_names]),
    default=None,
    help="Stage of the idea",
)
@click.option(
    "--status",
    type=click.Choice([s for s in status_names]),
    default=None,
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
        timestamp(),
    )
    # Refresh the list to reflect changes
    _list_all()


@cli.command(short_help="Toggles status between active and paused for idea")
@click.argument("position", type=int)
def toggle(position: int):
    """If idea at POSITION is active then pause it else if paused then activate it."""
    idea = get_idea_by_position(position)
    click_log(f"{idea = }")
    if idea:
        id, name, stage, status, added, reviewed, content_ = idea
        click_log(f"{status = }; {type(status) = }")
        now = timestamp()
        new_added = now - added
        new_reviewed = now - reviewed
        new_status = 0 if status == 1 else 1

        click_log(
            f"{new_added = }; {added = }; {new_reviewed = }; {reviewed = }; {now = }"
        )
        update_idea(
            position,
            None,
            None,
            None,
            new_status,  # status 1 -> 0
            new_added,  # to restore later
            new_reviewed,  # to restore later
        )
        _list_all()
    else:
        console.print(f"[red]Idea at position {position} not found![/red]")


@cli.command(short_help="Deletes an idea")
            position,
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
    """List all ideas based on the current focus settings.
    The POSITION number in the first column is used to specify an idea in commands,
    e.g., "details 3" to see the details of an idea at POSITION 3. The age and idle
    columns refer to how long ago the idea was, repectively, added or last reviewed/modified.
    """
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
    console.print(f" 💡[#87CEFA]Idea Nursery[/#87CEFA]")
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
    # table.add_column("status", width=6, justify="center")
    table.add_column("stage", width=6, justify="center")
    table.add_column("age", width=4, justify="center")
    table.add_column("idle", width=4, justify="center")

    for idx, idea in enumerate(ideas, start=1):
        id_, name, stage, status, added_, reviewed_, position_ = idea
        if status == 1:
            age = f"{format_timedelta(timestamp() - added_, short=True, stage=stage, use_colors=True)}"
            idle = (
                f"{format_timedelta(timestamp() - reviewed_, short=True, stage=stage)}"
            )
        else:
            idle = "~"
            age = "~"
        table.add_row(
            str(idx),
            name,
            # f"[{status_colors[status]}]{status_pos_to_str[status]}",
            f"[{stage_colors[stage]}]{stage_pos_to_str[stage]}",
            f"{age}",
            f"{idle}",
            # f"{format_timedelta(timestamp() - added_, short=True, stage=stage, use_colors=True)}",
            # f"{format_timedelta(timestamp() - reviewed_, short=True, stage=stage)}",
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


@cli.command(short_help="Review and edit name and content for idea in nvim")
@click.argument("position", type=int)
def review(position):
    """Review/Edit name and content for idea at POSITION."""
    console.clear()
    idea = get_idea_by_position(position)
    click_log(f"starting with {idea = }")
    if idea:
        id, name, stage, status, added_, reviewed_, content = idea
        new_name, new_content = edit_content_with_nvim(name, content)
        click_log(f"{position = }; {id = }; {new_name = }; {new_content = }")
        update_idea(position, new_name, new_content, None, None, None, timestamp())
        _list_all()


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
        console.print(f"[red]An unexpected error occurred: {e}[/red]")


if __name__ == "__main__":
    main()
