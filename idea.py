import sys

import click
from click_shell import shell
from prompt_toolkit.styles.named_colors import NAMED_COLORS
from rich import box, print
from rich.color import Color
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.traceback import install

install(show_locals=True)

from database import (
    delete_idea,
    get_all_ideas,
    get_idea_by_position,
    insert_idea,
    review_idea,
    update_idea,
)
from model import Idea, format_seconds, timestamp

# valid_rank = [Rank.from_int(x) for x in range(1, 5)]
# valid_rank = [x for x in range(1, 5)]
# valid_status = [x for x in range(1, 4)]

# ranks = {1: "spark", 2: "inkling", 3: "thought", 4: "brainstorm"}
# valid_rank = [x for x in ranks.keys()]
# status = {1: "deferred", 2: "active", 3: "promoted"}
# valid_status = [x for x in status.keys()]

rank_names = ["spark", "inkling", "thought", "idea"]
rank_pos_to_str = {pos: value for pos, value in enumerate(rank_names)}
rank_str_to_pos = {value: pos for pos, value in enumerate(rank_names)}
valid_rank = [i for i in range(len(rank_names))]

status_names = ["deferred", "active", "prompted"]
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
    type=click.Choice([r for r in valid_rank]),
    default=valid_rank[0],
    help="Rank of the idea",
)
@click.option(
    "--status",
    # type=click.Choice(["deferred", "active", "promoted"]),
    type=click.Choice([s for s in valid_status]),
    default=valid_status[1],
    help="Status of the idea",
)
def add(name, content, rank, status):
    """Add a new idea with NAME, CONTENT, RANK, and STATUS."""
    print(
        f"Adding idea with name: {name}, content: {content}, rank: {rank}, status: {status}"
    )
    idea = Idea(name, content, rank, status)
    print(idea)
    insert_idea(idea)
    _show_all()


@cli.command(short_help="Deletes an idea")
@click.argument("position", type=int)
def delete(position):
    """Delete an idea at POSITION."""
    print(f"Deleting idea at position {position}")
    delete_idea(position - 1)  # Adjust for zero-based index
    _show_all()


@cli.command(short_help="Updates an idea")
@click.argument("position", type=int)
@click.option("--name", default=None, help="New name for the idea")
@click.option("--content", default=None, help="New content for the idea")
@click.option(
    "--rank",
    default=None,
    type=click.Choice([f"{r}" for r in valid_rank]),
    help="New rank for the idea",
)
@click.option(
    "--status",
    default=None,
    type=click.Choice([f"{s}" for s in valid_status]),
    help="New status for the idea",
)
def update(position, name, content, rank, status):
    """Update an idea at POSITION with new NAME, CONTENT, RANK, and STATUS."""
    print(f"Updating idea at position {position}")
    update_idea(
        position - 1,
        name,
        content,
        rank if rank else None,
        status if status else None,
    )
    _show_all()


@cli.command(short_help="Updates reviewed timestamp for an idea")
@click.argument("position", type=int)
def review(position):
    """Update the reviewed timestamp for an idea at POSITION."""
    print(f"Updating reviewed timestamp for idea at position {position}")
    review_idea(position - 1)
    _show_all()


@cli.command(short_help="Show idea content")
@click.argument("position", type=int)
def content(position):
    """Show content of the idea at POSITION."""
    hsh = get_idea_by_position(position - 1)
    if hsh:
        res = f"""\
# {hsh['name']}

{hsh['content']}
"""
        md = Markdown(res)
        console.print(md)


@cli.command(short_help="Lists all ideas")
def show():
    _show_all()


def _show_all():
    """List all ideas."""
    now = timestamp()
    ideas = get_all_ideas()
    console.clear()
    console.print(" 💡[bold magenta]Idea[/bold magenta]")

    table = Table(
        show_header=True, header_style="bold blue", expand=True, box=box.HEAVY_EDGE
    )
    table.add_column("#", style="dim", min_width=1, justify="right")
    table.add_column("Name", min_width=24)
    table.add_column("Rank", width=7, justify="center")
    table.add_column("Status", width=7, justify="center")
    table.add_column("Age", min_width=3, justify="center")
    table.add_column("Rev", min_width=3, justify="center")

    def get_rank_color(rank):
        COLORS = {
            0: NAMED_COLORS["CornflowerBlue"],
            1: NAMED_COLORS["LightSkyBlue"],
            2: NAMED_COLORS["GreenYellow"],
            3: NAMED_COLORS["Yellow"],
        }
        return COLORS.get(int(rank), "white")

    for idx, idea in enumerate(ideas, start=0):
        c = get_rank_color(idea.rank)
        added_str = format_seconds(now - idea.added)
        reviewed_str = format_seconds(now - idea.reviewed)
        table.add_row(
            str(idx),
            idea.name,
            # f"[bold {c}]{idea.rank}[/bold {c}]",
            f"[{c}]{rank_pos_to_str[idea.rank]}[/{c}]",
            status_pos_to_str[idea.status],
            added_str,
            reviewed_str,
        )
    console.print(table)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "shell":
        sys.argv.pop(1)  # Remove 'shell' argument to prevent interference
        _show_all()
        cli()  # Start the interactive shell
    else:
        cli.main(prog_name="app")  # Process as a standard Click command


if __name__ == "__main__":
    main()
