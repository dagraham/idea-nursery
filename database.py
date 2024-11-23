import datetime
import sqlite3
from os import walk
from typing import List, Optional, Tuple

import click

from model import click_log, timestamp

conn = sqlite3.connect("ideas.db")
c = conn.cursor()

default_rank_setting = 8
default_status_setting = 6


def create_table():
    c.execute(
        """\
        CREATE TABLE IF NOT EXISTS ideas (
            name TEXT,
            content TEXT,
            rank INTEGER,
            status INTEGER,
            added INTEGER,
            reviewed INTEGER,
            id INTEGER PRIMARY KEY
        )"""
    )


create_table()


def initialize_settings():
    """Ensure row 0 exists for storing view settings."""
    c.execute("SELECT COUNT(*) FROM ideas WHERE id = 0")
    # ts = timestamp()
    if c.fetchone()[0] == 0:
        with conn:
            c.execute(
                # """INSERT INTO ideas (name, content, rank, status, added, reviewed)
                #    VALUES ('settings', '', None, None, 0, 0)"""
                f"""INSERT INTO ideas (name, content, status, rank, added, reviewed, id)
                   VALUES ('settings', '', {default_status_setting}, {default_rank_setting}, 0, 0, 0)"""
            )


initialize_settings()


def create_view():
    # Validate the column name to prevent SQL injection
    # Drop the view if it already exists
    c.execute("DROP VIEW IF EXISTS idea_positions")

    # Create the SQL query dynamically
    query = f"""
        CREATE VIEW idea_positions AS
        SELECT 
            name,
            rank,
            status,
            added,
            reviewed,
            id,
            (SELECT COUNT(*)
             FROM ideas AS i2
             WHERE i2.id < ideas.id) AS position
        FROM ideas
        ORDER BY status, rank, reviewed, id
    """
    c.execute(query)


create_view()


def get_view_settings() -> Tuple[int | None]:
    """Fetch the current view settings."""
    c.execute("SELECT status, rank FROM ideas WHERE id = 0")
    result = c.fetchone()
    with open("debug.log", "a") as debug_file:
        click.echo(f"get_view_settings: {result = }", file=debug_file)
    # return result if result else (default_status_setting, default_rank_setting)
    return result if result else (6, 8)


def set_view_settings(status: Optional[int] = 6, rank: Optional[int] = 8):
    """Update the current view settings."""
    with conn:
        c.execute(
            "UPDATE ideas SET status = :status, rank = :rank WHERE id = 0",
            {"status": status, "rank": rank},
        )


def get_ideas_from_view() -> List[Tuple]:
    """
    Fetch filtered ideas based on the current view settings.

    Returns:
        List[Tuple]: Filtered list of ideas.
    """
    # Get current view settings
    current_status, current_rank = get_view_settings()

    # Determine filters
    where_clauses = ["id > 0"]  # Always skip row 0

    # Add status filter if applicable
    if (
        current_status is not None and current_status < 6
    ):  # Apply filter only if status < 6
        if current_status // 3 == 0:
            where_clauses.append(f"status = {current_status % 3}")
        elif current_status // 3 == 1:
            where_clauses.append(f"status != {current_status % 3}")

    # Add rank filter if applicable
    if current_status is not None and current_rank < 8:  # Apply filter only if rank < 8
        if current_rank // 4 == 0:
            where_clauses.append(f"rank = {current_rank % 4}")
        elif current_rank // 4 == 1:
            where_clauses.append(f"rank != {current_rank % 4}")

    # Build the WHERE clause
    where_clause = " AND ".join(where_clauses)

    # Fetch ideas based on filters
    query = f"""
        SELECT id, name, rank, status, added, reviewed, position
        FROM idea_positions
        WHERE {where_clause}
    """
    c.execute(query)
    return c.fetchall()


# def get_id_from_position(position: int) -> int:
#     """Get the ID of the idea at the specified position in the current view."""
#     # Query the view for the corresponding ID
#     c.execute(
#         "SELECT id FROM idea_positions WHERE position = :position",
#         {"position": position},
#     )
#     result = c.fetchone()
#     print(f"{result = }")
#     if result:
#         return result[0]  # Return the ID
#     raise ValueError(f"No idea found at position {position}.")


def get_id_from_position(position: int) -> int:
    """Get the ID of the idea at the specified position in the current view."""
    c.execute(
        "SELECT position, id FROM idea_positions WHERE position = :position",
        {"position": position},
    )
    result = c.fetchone()

    # Log the mapping for debugging
    with open("debug.log", "a") as debug_file:
        click.echo(f"Looking up position: {position}", file=debug_file)
        c.execute("SELECT position, id FROM idea_positions")
        rows = c.fetchall()
        for row in rows:
            click.echo(f"View Row - Position: {row[0]}, ID: {row[1]}", file=debug_file)

    if result:
        return result[1]  # Return the ID
    raise ValueError(f"No idea found at position {position}.")


def insert_idea(
    name: str,
    content: str,
    rank: int,
    status: int,
    added: int = timestamp(),
    reviewed: int = timestamp(),
):
    """Insert a new idea into the database."""
    reviewed = reviewed if reviewed is not None else added

    # Determine the next position
    # c.execute("SELECT MAX(position) FROM ideas")
    # max_position = c.fetchone()[0]
    # position = (max_position + 1) if max_position is not None else 1

    with conn:
        c.execute(
            """INSERT INTO ideas (name, content, rank, status, added, reviewed)
               VALUES (:name, :content, :rank, :status, :added, :reviewed)""",
            {
                # "position": position,
                "name": name,
                "content": content,
                "rank": rank,
                "status": status,
                "added": added,
                "reviewed": reviewed,
            },
        )


# def get_all_ideas() -> List[Idea]:
#     c.execute("select * from ideas")
#     results = c.fetchall()
#     ideas = []
#     for result in results:
#         ideas.append(Idea(*result))
#     return ideas
#


def get_idea_by_position(position: int):
    try:
        # Get the ID from the position
        idea_id = get_id_from_position(position)
    except ValueError as e:
        click.echo(str(e))
        return

    c.execute(
        f"""SELECT id, name, rank, status, added, reviewed, content 
        FROM ideas 
        WHERE id={idea_id}"""
    )
    return c.fetchone()


def delete_idea(position: int):
    """Delete an idea by its position in the current view."""
    try:
        # Get the ID from the position
        idea_id = get_id_from_position(position)
    except ValueError as e:
        click.echo(str(e))
        return

    # Delete the idea by ID
    with conn:
        c.execute("DELETE FROM ideas WHERE id = :id", {"id": idea_id})


def update_idea(
    position: int,
    name: Optional[str] = None,
    content: Optional[str] = None,
    rank: Optional[int] = None,
    status: Optional[int] = None,
):
    try:
        # Get the ID from the position
        idea_id = get_id_from_position(position)
    except ValueError as e:
        click.echo(str(e))
        return
    # Build the base query and parameters
    base_query = "UPDATE ideas SET "
    updates = ["reviewed = :reviewed"]
    params = {"id": idea_id, "reviewed": timestamp()}

    # Append non-None fields to the updates list and params dict
    if name is not None:
        updates.append("name = :name")
        params["name"] = name
    if content is not None:
        updates.append("content = :content")
        params["content"] = content
    if rank is not None:
        updates.append("rank = :rank")
        params["rank"] = rank
    if status is not None:
        updates.append("status = :status")
        params["status"] = status

    # Join updates to form the full query and add the WHERE clause
    query = f"{base_query} {', '.join(updates)} WHERE id = :id"

    # Execute the query with the parameters
    click_log(f"{query =}; {params = }")
    with conn:
        c.execute(query, params)


def review_idea(position: int):
    try:
        # Get the ID from the position
        idea_id = get_id_from_position(position)
    except ValueError as e:
        click.echo(str(e))
        return

    with conn:
        c.execute(
            "UPDATE ideas SET reviewed = :reviewed WHERE id = :id",
            {"id": idea_id, "reviewed": timestamp()},
        )
