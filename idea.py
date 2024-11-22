#! /usr/bin/env python3
import json

# import os
import shlex
import sys
from pathlib import Path

import click
from click_shell import shell

# from prompt_toolkit.styles.named_colors import NAMED_COLORS
from rich import box, print
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.traceback import install

install(show_locals=True, max_frames=4)

from database import (
    create_view,
    delete_idea,
    get_ideas_from_view,
    insert_idea,
    review_idea,
    update_idea,
)
from model import format_datetime, format_timedelta, timestamp

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
    # idea = Idea(
    #     name,
    #     content,
    #     rank_str_to_pos[rank] if rank is not None else None,
    #     status_str_to_pos[status] if status is not None else None,
    # )
    insert_idea(
        name,
        content,
        rank_str_to_pos[rank] if rank is not None else 0,
        status_str_to_pos[status] if status is not None else 1,
    )
    _list_all()


@cli.command(short_help="Deletes an idea")
@click.argument("position", type=int)
def delete(position):
    """Delete an idea at POSITION."""
    print(f"Deleting idea at position {position}")
    delete_idea(position - 1)
    _list_all()


@cli.command(short_help="Lists ideas")
def list():
    _list_all()


# def _list_all(view: str = "id"):
#     """List all ideas, ordered by the specified view column."""
#     # Dynamically create the view
#     create_view(order_by_column=view)
#
#     # Fetch ideas from the dynamically created view
#     ideas = get_ideas_from_view()
#
#     # Render the table
#     console.clear()
#     console.print(" 💡[#87CEFA]Ideas[/#87CEFA]")
#     table = Table(
#         show_header=True, header_style="bold blue", expand=True, box=box.HEAVY_EDGE
#     )
#     table.add_column("#", style="dim", min_width=1, justify="right")
#     table.add_column("Name", min_width=24)
#     table.add_column("Rank", width=7, justify="center")
#     table.add_column("Status", width=7, justify="center")
#
#     for idea in ideas:
#         name, rank, status, added, reviewed, id_, position = (
#             idea  # Unpack tuple from view
#         )
#         table.add_row(
#             str(position),
#             name,
#             f"[{rank_colors[rank]}]{rank_pos_to_str[rank]}",
#             f"[{status_colors[status]}]{status_pos_to_str[status]}",
#         )
#     console.print(table)
#
#     # Optionally return position-to-id mapping if needed for subsequent operations
#     return {idea[0]: idea[1] for idea in ideas}  # {position: id}
#
#
# def _list_all(view: str = "id") -> dict:
#     """List all ideas ordered by the specified column and return position-to-id mapping."""
#     create_view(order_by_column=view)  # Dynamically create the view
#     ideas = get_ideas_from_view()  # Fetch data from the view
#
#     # Create a position-to-id mapping
#     position_to_id = {idea[0]: idea[1] for idea in ideas}  # {position: id}
#
#     # Render the table
#     console.clear()
#     console.print(" 💡[#87CEFA]IdeaNursery[/#87CEFA]")
#     table = Table(
#         show_header=True, header_style="bold blue", expand=True, box=box.HEAVY_EDGE
#     )
#     table.add_column("#", style="dim", min_width=1, justify="right")
#     table.add_column("Name", min_width=24)
#     table.add_column("Rank", width=7, justify="center")
#     table.add_column("Status", width=7, justify="center")
#
#     for idea in ideas:
#         position, id_, name, rank, status, added, reviewed = idea
#         table.add_row(
#             str(position),
#             name,
#             f"[{rank_colors[rank]}]{rank_pos_to_str[rank]}",
#             f"[{status_colors[status]}]{status_pos_to_str[status]}",
#         )
#     console.print(table)
#
#     # Return the mapping for further use
#     return position_to_id


def _list_all(view: str = "id") -> dict:
    """List all ideas ordered by the specified column and save position-to-id mapping."""
    create_view(order_by_column=view)  # Dynamically create the view
    ideas = get_ideas_from_view()  # Fetch data from the view

    console.print(ideas)
    # Create and save the position-to-id mapping
    position_to_id = {idea[-1]: idea[-2] for idea in ideas}  # {position: id}
    save_position_to_id(position_to_id)
    console.print(position_to_id)
    # sys.exit()

    # Render the table
    console.clear()
    console.print(" 💡[#87CEFA]IdeaNursery[/#87CEFA]")
    table = Table(
        show_header=True, header_style="bold blue", expand=True, box=box.HEAVY_EDGE
    )
    table.add_column("#", style="dim", min_width=1, justify="right")
    table.add_column("Name", min_width=24)
    table.add_column("Rank", width=7, justify="center")
    table.add_column("Status", width=7, justify="center")

    for idea in ideas:
        name, rank, status, added, reviewed, id_, position = idea
        table.add_row(
            str(position),
            name,
            f"[{rank_colors[rank]}]{rank_pos_to_str[rank]}",
            f"[{status_colors[status]}]{status_pos_to_str[status]}",
        )
    console.print(table)

    return position_to_id


@cli.command(short_help="Shows details for idea")
@click.argument("position", type=int)
def details(position):
    """Show details for idea at POSITION."""
    now = timestamp()
    console.clear()
    hsh = get_idea_by_position(position - 1)

    if hsh:
        rank = hsh.get("rank")
        rank_str = f"{rank:<12} {rank_pos_to_str[rank]:<10}" if rank is not None else ""
        status = hsh.get("status")
        status_str = (
            f"{status:<12} {status_str_to_pos[status]:<10}"
            if status is not None
            else ""
        )
        added = hsh.get("added")
        added_str = (
            f"{added:<12} {format_timedelta(now - added, short=False):<10} {format_datetime(added)}"
            if added is not None
            else ""
        )
        reviewed = hsh.get("reviewed")
        reviewed_str = (
            f"{reviewed:<12} {format_timedelta(now - reviewed, short=False):<10} {format_datetime(reviewed)}"
            if reviewed is not None
            else ""
        )
        meta = f"""\
field        stored         presented 
rank:      {rank_str}  
status:    {status_str}    
added:     {added_str}  
reviewed:  {reviewed_str}\
"""

        res = f"""\
# {hsh['name']}

{hsh['content']}
"""
        console.print(Panel(meta, title="metadata"))
        md = Markdown(res)
        console.print(Panel(md, title="name and content as markdown"))
    else:
        console.print(f"[red]Idea at position {position} not found![/red]")


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
