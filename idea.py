#! /usr/bin/env python3
import json
import logging

# import os
import shlex
import sys
from pathlib import Path

import click
from click_shell import shell

# from prompt_toolkit.styles.named_colors import NAMED_COLORS
from rich import box, print
from rich.console import Console
from rich.logging import RichHandler
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

# from rich.traceback import install

# install(show_locals=True, max_frames=4)

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

log = logging.getLogger("rich")


from database import (
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
from model import (
    click_log,
    edit_content_with_nvim,
    format_datetime,
    format_timedelta,
    timestamp,
)

rank_names = ["spark", "inkling", "thought", "idea"]
rank_colors = ["#6495ed", "#87CEFA", "#adff2f", "#ffff00"]
rank_pos_to_str = {pos: value for pos, value in enumerate(rank_names)}
rank_str_to_pos = {value: pos for pos, value in enumerate(rank_names)}
valid_rank = [i for i in range(len(rank_names))]

status_names = ["shelved", "nursery", "library"]
status_colors = ["#4775e6", "#ffa500", "#32CD32"]
status_pos_to_str = {pos: value for pos, value in enumerate(status_names)}
status_str_to_pos = {value: pos for pos, value in enumerate(status_names)}
valid_status = [i for i in range(len(status_names))]

console = Console()


# Define the path to the temporary JSON file
TEMP_FILE = Path(".position_to_id.json")


def save_position_to_id(position_to_id: dict):
    """Save the position_to_id mapping to a temporary JSON file."""
    with open(TEMP_FILE, "w") as f:
        json.dump(position_to_id, f)


def load_position_to_id() -> dict:
    """Load the position_to_id mapping from the temporary JSON file."""
    if TEMP_FILE.exists():
        with open(TEMP_FILE, "r") as f:
            return json.load(f)
    return {}


@shell(prompt="app> ", intro="Welcome to the idea manager shell!")
@click.option(
    "-t", "--file", type=click.Path(exists=True), help="Batch file with commands."
)
def cli(file):
    """Main entry point for the CLI."""
    if file:
        process_batch_file(file)


def process_batch_file(file_path):
    """Process commands from a batch file."""
    with open(file_path, "r") as file:
        for line in file:
            command = line.strip()
            if command:
                try:
                    print(f"Executing command: {command}")
                    # Use shlex.split to properly parse the command line
                    args = shlex.split(command)
                    ctx = cli.make_context("cli", args)
                    cli.invoke(ctx)
                except click.ClickException as e:
                    console.print(
                        f"[red]Error executing command: {e.format_message()}[/red]"
                    )
                except Exception as e:
                    console.print(f"[red]Unexpected error: {e}[/red]")
                    console.print(f"Executing command: {command = }; {args = }")
                # finally:
                #     console.print(f"Executing command: {command = }; {args = }")
                #     sys.exit()


@cli.command(short_help="Adds an idea")
@click.argument("name")
@click.option("--content", type=str, help="Content of the idea")
@click.option(
    "--rank",
    type=click.Choice([r for r in rank_names]),
    default=rank_names[0],
    help="Rank of the idea",
)
@click.option(
    "--status",
    type=click.Choice([s for s in status_names]),
    default=status_names[1],
    help="Status of the idea",
)
def add(name, content, rank, status):
    """Add a new idea with NAME, CONTENT, RANK, and STATUS."""
    print(
        f"Adding idea with name: {name}, content: {content}, rank: {rank}, status: {status}"
    )
    insert_idea(
        name,
        content,
        rank_str_to_pos[rank] if rank is not None else 0,
        status_str_to_pos[status] if status is not None else 1,
    )
    _list_all()


@cli.command(short_help="Updates data for idea")
@click.argument("position", type=int)
@click.option("--name")
@click.option("--content", type=str, help="Content of the idea")
@click.option(
    "--rank",
    type=click.Choice([r for r in rank_names]),
    default=rank_names[0],
    help="Rank of the idea",
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
    rank: int = None,
):
    """Update data for idea at POSITION."""
    # Print debug information
    click.echo(f"Update idea at position {position}")
    # Call the database function to handle the deletion
    update_idea(
        position,
        name,
        content,
        rank_str_to_pos[rank] if rank is not None else None,
        status_str_to_pos[status] if status is not None else None,
    )
    # Refresh the list to reflect changes
    _list_all()


@cli.command(short_help="Sets reviewed timestamp for idea")
@click.argument("position", type=int)
def review(position):
    """Review idea at POSITION."""
    # Print debug information
    click.echo(f"Review idea at position {position}")
    # Call the database function to handle the deletion
    review_idea(position)
    # Refresh the list to reflect changes
    _list_all()


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


@cli.command()
@click.option(
    "--status",
    type=int,
    help="i=0,1,2: only show items with status i;\ni=3,4,5: hide items with status i-3",
)
@click.option(
    "--rank",
    type=int,
    help="i=0,1,2,3: only show items with rank i;\ni=4,5,6,7: hide items with rank i-4",
)
def view(status: int = None, rank: int = None):
    """Set or restore view filters."""
    current_status, current_rank = get_view_settings()
    # Update settings based on user input
    if status is not None:
        current_status = status
    if rank is not None:
        current_rank = rank
    set_view_settings(current_status, current_rank)
    click.echo(f"View settings updated: status={current_status}, rank={current_rank}")


@cli.command(short_help="Lists ideas")
def list():
    _list_all()


def _list_all():
    """List all ideas based on the current view settings."""
    # Fetch filtered ideas
    ideas = get_ideas_from_view()
    with open("debug.log", "a") as debug_file:
        click.echo(f"ideas from view: {ideas}", file=debug_file)
    # log.info(f"{ideas}")

    # Render the table
    console.clear()
    console.print(" 💡[#87CEFA]Idea Nursery[/#87CEFA]")
    table = Table(
        show_header=True, header_style="bold blue", expand=True, box=box.HEAVY_EDGE
    )
    table.add_column("#", style="dim", min_width=1, justify="right")
    table.add_column("name", min_width=24)
    table.add_column("rank", width=7, justify="center")
    table.add_column("status", width=7, justify="center")
    table.add_column("age", width=4, justify="center")
    table.add_column("idle", width=4, justify="center")

    for idx, idea in enumerate(ideas, start=1):
        id_, name, rank, status, added_, reviewed_, position_ = idea
        table.add_row(
            str(idx),
            name,
            f"[{rank_colors[rank]}]{rank_pos_to_str[rank]}",
            f"[{status_colors[status]}]{status_pos_to_str[status]}",
            f"{format_timedelta(timestamp() - added_)}",
            f"{format_timedelta(timestamp() - reviewed_)}",
        )
    console.print(table)


@cli.command(short_help="Shows details for idea")
@click.argument("position", type=int)
def details(position):
    """Show details for idea at POSITION."""
    now = timestamp()
    console.clear()
    idea = get_idea_by_position(position)
    with open("debug.log", "a") as debug_file:
        click.echo(f"idea from position: {idea}", file=debug_file)

    if idea:
        id, name, rank, status, added, reviewed, content = idea
        rank_str = f"{rank:<14} ({rank_pos_to_str[rank]})" if rank is not None else ""
        status_str = (
            f"{status:<14} ({status_pos_to_str[status]})" if status is not None else ""
        )
        added_str = (
            f"{added:<14} ({format_timedelta(now - added, short=False)} ago at {format_datetime(added)})"
            if added is not None
            else ""
        )
        reviewed_str = (
            f"{reviewed:<14} ({format_timedelta(now - reviewed, short=False)} ago at {format_datetime(reviewed)})"
            if reviewed is not None
            else ""
        )
        meta = f"""\
name:      {name}
rank:      {rank_str}  
status:    {status_str}    
added:     {added_str}  
reviewed:  {reviewed_str}\
"""

        res = f"""\
{content}\
"""
        console.print(Panel(meta, title="data"))
        # md = Markdown(res)
        console.print(Panel(res, title="content"))
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
        id, name, rank, status, added_, reviewed_, content = idea
        new_content = edit_content_with_nvim(content)
        click_log(f"{id=}, {new_content = }")
        update_idea(id, None, new_content, None, None)


def main():
    if "-t" in sys.argv:
        try:
            idx = sys.argv.index("-t")
            batch_file = sys.argv[idx + 1]
            process_batch_file(batch_file)
            return
        except IndexError:
            console.print("[red]Error: Missing batch file after -t[/red]")
            return
    elif "--file" in sys.argv:
        try:
            idx = sys.argv.index("--file")
            batch_file = sys.argv[idx + 1]
            process_batch_file(batch_file)
            return
        except IndexError:
            console.print("[red]Error: Missing batch file after --file[/red]")
            return

    elif len(sys.argv) > 1 and sys.argv[1] == "shell":
        sys.argv.pop(1)  # Remove 'shell' argument to prevent interference
        _list_all()
        cli()
    else:
        if len(sys.argv) == 1:
            sys.argv.append("--help")
        cli.main(prog_name="app")


if __name__ == "__main__":
    main()
