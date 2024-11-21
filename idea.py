import sys

import click
from click_shell import shell
from prompt_toolkit.styles.named_colors import NAMED_COLORS
from rich import box, print
from rich.color import Color
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.traceback import install

install(show_locals=True, max_frames=4)

from database import (
    delete_idea,
    get_all_ideas,
    get_idea_by_position,
    insert_idea,
    review_idea,
    update_idea,
)
from model import Idea, format_datetime, format_timedelta, timestamp

# there will be as many ranks as there are rank_names. names for display and entry, integers for the database
rank_names = ["spark", "inkling", "thought", "idea"]
rank_colors = ["#4775e6", "#7a9ca6", "#c2d14d", "#ffff00"]
rank_pos_to_str = {pos: value for pos, value in enumerate(rank_names)}
rank_str_to_pos = {value: pos for pos, value in enumerate(rank_names)}
valid_rank = [i for i in range(len(rank_names))]

# ditto rank comment above
status_names = ["shelved", "nursery", "library"]
status_colors = ["#FFDEAD", "#87CEFA", "#32CD32"]
# status_colors = ["#BDB76B", "#ADFF2F", "#FF8C00"]
status_pos_to_str = {pos: value for pos, value in enumerate(status_names)}
status_str_to_pos = {value: pos for pos, value in enumerate(status_names)}
valid_status = [i for i in range(len(status_names))]

console = Console()


@shell(prompt="app> ", intro="Welcome to the idea manager shell! Type ? for help.")
def cli():
    pass


@cli.command(short_help="Adds an idea")
@click.argument("name")
@click.option("--content", type=str, help="Content of the idea")
@click.option(
    "--rank",
    # type=click.Choice(["spark", "inkling", "thought", "idea"]),
    type=click.Choice([r for r in rank_names]),
    default=rank_names[0],
    help="Rank of the idea",
)
@click.option(
    "--status",
    # type=click.Choice(["deferred", "active", "promoted"]),
    type=click.Choice([s for s in status_names]),
    default=status_names[1],
    help="Status of the idea",
)
def add(name, content, rank, status):
    """Add a new idea with NAME, CONTENT, RANK, and STATUS."""
    print(
        f"Adding idea with name: {name}, content: {content}, rank: {rank}, status: {status}"
    )
    idea = Idea(
        name,
        content,
        rank_str_to_pos[rank] if rank is not None else None,
        status_str_to_pos[status] if status is not None else None,
    )
    print(idea)
    insert_idea(idea)
    _list_all()


@cli.command(short_help="Deletes an idea")
@click.argument("position", type=int)
def delete(position):
    """Delete an idea at POSITION."""
    print(f"Deleting idea at position {position}")
    delete_idea(position - 1)  # Adjust for zero-based index
    _list_all()


@cli.command(short_help="Updates an idea")
@click.argument("position", type=int)
@click.option("--name", default=None, help="New name for the idea")
@click.option("--content", default=None, help="New content for the idea")
@click.option(
    "--rank",
    default=None,
    type=click.Choice([f"{r}" for r in rank_names]),
    help="New rank for the idea",
)
@click.option(
    "--status",
    default=None,
    type=click.Choice([f"{s}" for s in status_names]),
    help="New status for the idea",
)
def update(position, name, content, rank, status):
    """Update an idea at POSITION with new NAME, CONTENT, RANK, and STATUS."""
    print(f"Updating idea at position {position}")
    update_idea(
        position - 1,
        name,
        content,
        rank_str_to_pos[rank] if rank is not None else None,
        status_str_to_pos[status] if status is not None else None,
    )
    _list_all()


@cli.command(short_help="Updates reviewed timestamp for an idea")
@click.argument("position", type=int)
def review(position):
    """Update the reviewed timestamp for an idea at POSITION."""
    print(f"Updating reviewed timestamp for idea at position {position}")
    review_idea(position - 1)
    _list_all()


@cli.command(short_help="Lists ideas")
def list():
    _list_all()


def _list_all(view: str = ""):
    """List all ideas."""
    now = timestamp()
    ideas = get_all_ideas()
    console.clear()
    console.print(" 💡[#87CEFA]IdeaNursery[/#87CEFA]")

    table = Table(
        show_header=True, header_style="bold blue", expand=True, box=box.HEAVY_EDGE
    )
    table.add_column("#", style="dim", min_width=1, justify="right")
    table.add_column("name", min_width=24)
    table.add_column("rank", width=7, justify="center")
    table.add_column("status", width=7, justify="center")
    table.add_column("age", min_width=3, justify="center")
    table.add_column("rev", min_width=3, justify="center")

    for idx, idea in enumerate(ideas, start=1):
        added_str = format_timedelta(now - idea.added)
        reviewed_str = format_timedelta(now - idea.reviewed)
        table.add_row(
            str(idx),
            idea.name,
            f"[{rank_colors[idea.rank]}]{rank_pos_to_str[idea.rank]}[{rank_colors[idea.rank]}]",
            f"[{status_colors[idea.status]}]{status_pos_to_str[idea.status]}[{status_colors[idea.status]}]",
            added_str,
            reviewed_str,
        )
    console.print(table)


@cli.command(short_help="Shows details for idea")
@click.argument("position", type=int)
def details(position):
    """Show details for idea at POSITION."""
    now = timestamp()
    console.clear()
    hsh = get_idea_by_position(position - 1)
    # print(hsh)

    # console.print(" 💡[bold magenta]Idea[/bold magenta]")
    if hsh:
        rank = hsh.get("rank")
        rank_str = f"{rank:<12} {rank_pos_to_str[rank]:<10}" if rank is not None else ""
        status = hsh.get("status")
        status_str = (
            f"{status:<12} {status_pos_to_str[status]:<10}"
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
        # console.print(meta)
        console.print(Panel(meta, title="metadata"))

        md = Markdown(res)
        console.print(Panel(md, title="name and content as markdown"))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "shell":
        sys.argv.pop(1)  # Remove 'shell' argument to prevent interference
        _list_all()
        cli()  # Start the interactive shell
    else:
        # If no arguments are provided, show help
        if len(sys.argv) == 1:
            sys.argv.append("--help")  # Append --help to arguments
        cli.main(prog_name="app")  # Process as a standard Click command


if __name__ == "__main__":
    main()
