import datetime
import sqlite3
from os import walk
from typing import List, Optional, Tuple

from model import timestamp

conn = sqlite3.connect("ideas.db")
c = conn.cursor()


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
            id INTEGER PRIMARY KEY,
            position INTEGER UNIQUE
        )"""
    )


create_table()


def create_view(order_by_column="id"):
    # Validate the column name to prevent SQL injection
    valid_columns = {"id", "name", "rank", "status", "added", "reviewed"}
    if order_by_column not in valid_columns:
        raise ValueError(f"Invalid column name: {order_by_column}")

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
             WHERE i2.{order_by_column} <= ideas.{order_by_column}) AS position
        FROM ideas
        ORDER BY {order_by_column};
    """
    c.execute(query)


def get_ideas_from_view() -> List[Tuple]:
    """Fetch ideas from the dynamically created view."""
    c.execute(
        "SELECT name, rank, status, added, reviewed, id, position FROM idea_positions"
    )
    return c.fetchall()


def insert_idea(
    name: str,
    content: str = "",
    rank: int = 0,
    status: int = 1,
    added: int = timestamp(),
    reviewed: int = timestamp(),
):
    """Insert a new idea into the database."""
    reviewed = (
        reviewed if reviewed is not None else added
    )  # Default reviewed to added if not provided
    with conn:
        c.execute(
            """INSERT INTO ideas (name, content, rank, status, added, reviewed)
               VALUES (:name, :content, :rank, :status, :added, :reviewed)""",
            {
                "name": name,
                "content": content,
                "rank": rank,
                "status": status,
                "added": added,
                "reviewed": reviewed,
            },
        )


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
    c.execute("SELECT MAX(position) FROM ideas")
    max_position = c.fetchone()[0]
    position = (max_position + 1) if max_position is not None else 1

    with conn:
        c.execute(
            """INSERT INTO ideas (position, name, content, rank, status, added, reviewed)
               VALUES (:position, :name, :content, :rank, :status, :added, :reviewed)""",
            {
                "position": position,
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
    c.execute(
        "SELECT name, rank, status, added, reviewed, content FROM ideas WHERE position=:position",
        {"position": position},
    )
    result = c.fetchone()
    if result:
        name, rank, status, added, reviewed, content = result
        return {
            "name": name,
            "rank": rank,
            "status": status,
            "added": added,
            "reviewed": reviewed,
            "content": content,
        }
    else:
        return None  # Return None if no matching record is found


def delete_idea(position):
    c.execute("select count(*) from ideas")
    count = c.fetchone()[0]

    with conn:
        c.execute("DELETE from ideas WHERE position=:position", {"position": position})
        for pos in range(position + 1, count):
            change_position(pos, pos - 1, False)


def change_position(old_position: int, new_position: int, commit=True):
    c.execute(
        "UPDATE ideas SET position = :position_new WHERE position = :position_old",
        {"position_old": old_position, "position_new": new_position},
    )
    if commit:
        conn.commit()


def update_idea(
    position: int,
    name: Optional[str] = None,
    content: Optional[str] = None,
    rank: Optional[int] = None,
    status: Optional[int] = None,
):
    # Build the base query and parameters
    base_query = "UPDATE ideas SET "
    updates = []
    params = {"position": position, "reviewed": timestamp()}

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
    query = f"{base_query} {', '.join(updates)}, reviewed = :reviewed WHERE position = :position"

    # Execute the query with the parameters
    with conn:
        c.execute(query, params)


def review_idea(position: int):
    with conn:
        c.execute(
            "UPDATE ideas SET reviewed = :reviewed WHERE position = :position",
            {"position": position, "reviewed": timestamp()},
        )
