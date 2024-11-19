import datetime
import sqlite3
from os import walk
from typing import List, Optional

from model import Idea, timestamp

conn = sqlite3.connect("ideas.db")
c = conn.cursor()


def create_table():
    c.execute(
        """CREATE TABLE IF NOT EXISTS ideas (
            name text,
            content text,
            rank integer,
            status integer,
            added integer,
            reviewed integer,
            position integer
            )"""
    )


create_table()


def insert_idea(idea: Idea):
    c.execute("select count(*) FROM ideas")
    count = c.fetchone()[0]
    idea.position = count if count else 0
    with conn:
        c.execute(
            "INSERT INTO ideas VALUES (:name, :content, :rank, :status, :added, :reviewed, :position)",
            {
                "name": idea.name,
                "content": idea.content,
                "rank": idea.rank,
                "status": idea.status,
                "added": idea.added,
                "reviewed": idea.added,
                "position": idea.position,
            },
        )


def get_all_ideas() -> List[Idea]:
    c.execute("select * from ideas")
    results = c.fetchall()
    ideas = []
    for result in results:
        ideas.append(Idea(*result))
    return ideas


def get_idea_by_position(position: int):
    c.execute(
        "SELECT name, content FROM ideas WHERE position=:position",
        {"position": position},
    )
    result = c.fetchone()
    if result:
        name, content = result
        return {"name": name, "content": content}
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
    rank: Optional[str] = None,
    status: Optional[str] = None,
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
