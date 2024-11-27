import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import click

from modules.model import click_log, timestamp

from . import backup_dir, db_path, idea_home, log_dir

original_makedirs = os.makedirs


def safe_makedirs(path, *args, **kwargs):
    click_log(f"{path = }; {args = }; {kwargs = }")
    log_directory_creation(path)
    original_makedirs(path, *args, **kwargs)


os.makedirs = safe_makedirs

conn = sqlite3.connect(db_path)
c = conn.cursor()

default_rank_setting = 8
default_status_setting = 6
pos_to_id = {}


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
    # Drop the view if it already exists
    c.execute("DROP VIEW IF EXISTS idea_positions")

    # Create the SQL query dynamically
    query = """
        CREATE VIEW idea_positions AS
        SELECT 
            name,
            rank,
            status,
            added,
            reviewed,
            id,
            ROW_NUMBER() OVER (ORDER BY status, rank, reviewed, id) AS position
        FROM ideas
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
    current_status, current_stage = get_view_settings()

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
    if (
        current_status is not None and current_stage < 8
    ):  # Apply filter only if rank < 8
        if current_stage // 4 == 0:
            where_clauses.append(f"rank = {current_stage % 4}")
        elif current_stage // 4 == 1:
            where_clauses.append(f"rank != {current_stage % 4}")

    # Build the WHERE clause
    where_clause = " AND ".join(where_clauses)

    # Fetch ideas based on filters
    query = f"""
        SELECT id, name, rank, status, added, reviewed, position
        FROM idea_positions
        WHERE {where_clause}
    """
    c.execute(query)
    ideas = c.fetchall()
    # pos = 0
    # pos_to_id = {}
    # for idea in ideas:
    #     pos += 1
    #     id = idea[0]
    #     pos_to_id[pos] = id
    # click_log(f"{pos_to_id = }")
    # click_log(f"{ideas = }")

    return ideas, current_status, current_stage
    # return c.fetchall()


def get_id_from_position(position: int) -> int:
    """Get the ID of the idea at the specified position in the current view."""
    # id = pos_to_id.get(position)
    # click_log(f"{position = } -> {id = }")
    # if id:
    #     return id
    # raise ValueError(f"No id corresponding to position {position}")

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


def get_idea_by_position(position: int):
    try:
        # Get the ID from the position
        idea_id = get_id_from_position(position)
        if not idea_id:
            return None
        click_log(f"{position = }; {idea_id = }")
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
    added: Optional[int] = None,
    reviewed: Optional[int] = None,
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
    params = {"id": idea_id, "reviewed": reviewed if not None else timestamp()}

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
    if added is not None:
        updates.append("added = :added")
        params["added"] = added
    # if reviewed is not None:
    #     updates.append("reviewed = :reviewed")
    #     params["reviewed"] = reviewed

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
        click_log(f"{position = } -> {idea_id = }")
    except ValueError as e:
        click.echo(str(e))
        return

    with conn:
        c.execute(
            "UPDATE ideas SET reviewed = :reviewed WHERE id = :id",
            {"id": idea_id, "reviewed": timestamp()},
        )


def backup_with_retention(source_db: str, backup_dir: str, retention: int = 7):
    # Ensure backup directory exists
    os.makedirs(backup_dir, exist_ok=True)

    # Generate backup file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"backup_{timestamp}.db")

    # Perform the backup
    with sqlite3.connect(source_db) as conn:
        with sqlite3.connect(backup_file) as backup_conn:
            conn.backup(backup_conn)
    click_log(f"Backup created: {backup_file}")

    # Enforce retention: Delete oldest files if over retention limit
    backups = sorted(
        [
            os.path.join(backup_dir, f)
            for f in os.listdir(backup_dir)
            if f.startswith("backup_")
        ],
        key=os.path.getctime,
    )

    while len(backups) > retention:
        oldest = backups.pop(0)
        os.remove(oldest)
        print(f"Deleted old backup: {oldest}")


def get_file_last_modified(file_path: str) -> int:
    """Get the last modified timestamp of a file in seconds since the epoch."""
    return int(os.path.getmtime(file_path))


def get_current_timestamp() -> int:
    """Get the current timestamp in seconds since the epoch."""
    return int(datetime.now().timestamp())


def backup_with_conditions(
    source_db: str, backup_dir: str, retention: int = 7, backup_interval_days: int = 1
):
    """keep 'last_backup' in the column 'added' and 'next_backup' in the column 'reviewed'"""
    click_log("how now?")
    conn = sqlite3.connect(source_db)
    c = conn.cursor()

    # Get added and reviewed from row 0
    c.execute("SELECT added, reviewed FROM ideas WHERE id = 0")
    row = c.fetchone()
    added, reviewed = row if row else (None, None)

    # Get current timestamps
    current_timestamp = get_current_timestamp()
    db_last_modified = get_file_last_modified(source_db)

    click_log(
        f"Current: {current_timestamp}, DB Last Modified: {db_last_modified}, Last Backup: {added}, Next Backup: {reviewed}"
    )

    # Initialize backup settings if they are None
    if added is None or reviewed is None:
        added = db_last_modified
        reviewed = added + (backup_interval_days * 86400)  # Convert days to seconds
        c.execute(
            "UPDATE ideas SET added = ?, reviewed = ? WHERE id = 0", (added, reviewed)
        )
        conn.commit()
        print(
            f"Initialized backup settings: Last Backup: {added}, Next Backup: {reviewed}"
        )
        conn.close()
        return

    # Check if backup is needed
    if current_timestamp > reviewed and db_last_modified > added:
        print("Backup is due and the database has changed. Starting backup process...")

        # Perform the backup
        backup_with_retention(source_db, backup_dir, retention)

        # Update the backup timestamps
        added = db_last_modified
        reviewed = added + (backup_interval_days * 86400)
        c.execute(
            "UPDATE ideas SET added = ?, reviewed = ? WHERE id = 0", (added, reviewed)
        )
        conn.commit()
        print(f"Backup completed. Last Backup: {added}, Next Backup: {reviewed}")
    else:
        print("Backup not needed at this time.")

    conn.close()


# Example Usage
# source_db_path = "your_database.db"
# backup_directory = "./backups"
# backup_with_retention(source_db_path, backup_directory)
