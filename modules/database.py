import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

import click

from modules.model import click_log, timestamp

from . import backup_dir, db_path, idea_home, log_dir

# original_makedirs = os.makedirs
#
#
# def safe_makedirs(path, *args, **kwargs):
#     click_log(f"{path = }; {args = }; {kwargs = }")
#     log_directory_creation(path)
#     original_makedirs(path, *args, **kwargs)
#
#
# os.makedirs = safe_makedirs

conn = sqlite3.connect(db_path)
c = conn.cursor()

default_status_setting = 0
default_monitor_setting = 0
pos_to_id = {}


def create_table():
    c.execute(
        """\
        CREATE TABLE IF NOT EXISTS ideas (
            name TEXT,
            content TEXT,
            status INTEGER,
            monitor INTEGER,
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
                # """INSERT INTO ideas (name, content, status, monitor, added, reviewed)
                #    VALUES ('settings', '', None, None, 0, 0)"""
                f"""INSERT INTO ideas (name, content, monitor, status, added, reviewed, id)
                   VALUES ('settings', '', {default_monitor_setting}, {default_status_setting}, 0, 0, 0)"""
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
            status,
            monitor,
            added,
            reviewed,
            id,
            ROW_NUMBER() OVER (ORDER BY monitor, status, id) AS position
        FROM ideas
    """
    c.execute(query)
    # ROW_NUMBER() OVER (ORDER BY monitor, status, reviewed, id) AS position


create_view()


# def get_view_settings() -> Tuple[int | None]:
#     """Fetch the current view settings."""
#     c.execute("SELECT monitor, status FROM ideas WHERE id = 0")
#     result = c.fetchone()
#     with open("debug.log", "a") as debug_file:
#         click.echo(f"get_view_settings: {result = }", file=debug_file)
#     # return result if result else (default_monitor_setting, default_status_setting)
#     return result if result else (6, 8)
#
#
# def set_view_settings(monitor: Optional[int] = 2, status: Optional[int] = 4):
#     """Update the current view settings."""
#     with conn:
#         c.execute(
#             "UPDATE ideas SET monitor = :monitor, status = :status WHERE id = 0",
#             {"monitor": monitor, "status": status},
#         )
#


def set_hide_encoded(lst: List[int]):
    """
    Converts list of status HIDE positions to an encoded integer representing a list of binaries where a 1's mean hide and 0's show.
    Positions correspond to 0-3: status[seed, sprout, seedling, plant], 4: monitor. In 0-3, 0/1 mean show/hide ideas with that status.
    In 4, 0/1 means show/hide items with monitor value 0 (paused). This integer is stored as "status" for item id 0.
    """
    ret = []
    for x in [0, 1, 2, 3]:
        if x in lst:
            ret.append(1)
        else:
            ret.append(0)
    encoded = encode_binary_list(ret)
    with conn:
        c.execute(
            "UPDATE ideas SET status = :status WHERE id = 0",
            {"status": encoded},
        )


def set_show_encoded(lst: List[int]):
    """
    Converts list of status SHOW positions to an encoded integer representing a list of binaries where a 1's mean hide and 0's show.
    Positions correspond to 0-3: status[seed, sprout, seedling, plant], 4: monitor. In 0-3, 0/1 mean show/hide ideas with that status.
    In 4, 0/1 means show/hide items with monitor value 0 (paused). This integer is stored as "status" for item id 0.
    """
    ret = []
    for x in [0, 1, 2, 3]:
        if x in lst:
            ret.append(0)
        else:
            ret.append(1)
    encoded = encode_binary_list(ret)
    with conn:
        c.execute(
            "UPDATE ideas SET status = :status WHERE id = 0",
            {"status": encoded},
        )


def get_view_settings() -> List[int]:
    """
    Fetch the current view settings as an encoded integer from status in idea id 0 and return the decoded list of binaries.
    """
    c.execute("SELECT status FROM ideas WHERE id = 0")
    result = c.fetchone()[0]
    click_log(f"{result = }")
    if result:
        ret = decode_to_binary_list(result)
        click_log(f"{ret = }")
        return ret
    else:
        # return [0, 0, 0, 0]
        return [1, 1, 1, 1]


def encode_binary_list(binary_list: List[int]) -> int:
    result = 0
    for bit in binary_list:
        result = (result << 1) | bit
    return result


def decode_to_binary_list(encoded_int: int, length: int = 4) -> List[int]:
    binary_list = []
    for _ in range(length):
        binary_list.append(encoded_int & 1)
        encoded_int >>= 1
    return binary_list[::-1]


def pos_from_show_binaries(lst_of_binaries: list[int]) -> list[int]:
    count = 0
    res = []
    for x in lst_of_binaries:
        if x == 1:
            res.append(count)
        count += 1
    return res


def get_ideas_from_view() -> List[Tuple]:
    """
    Fetch filtered ideas based on the current view settings.

    Returns:
        List[Tuple]: Filtered list of ideas.
    """
    global pos_to_id
    # Get current view settings
    show_binaries = get_view_settings()
    click_log(f"{show_binaries = }")
    show_list = pos_from_show_binaries(show_binaries)
    click_log(f"{show_list = }")

    # Determine filters

    # # Add monitor filter if applicable
    # if (
    #     current_monitor is not None and current_monitor < 6
    # ):  # Apply filter only if monitor < 6
    #     if current_monitor // 3 == 0:
    #         where_clauses.append(f"monitor = {current_monitor % 3}")
    #     elif current_monitor // 3 == 1:
    #         where_clauses.append(f"monitor != {current_monitor % 3}")
    #
    # # Add status filter if applicable
    # if (
    #     current_monitor is not None and current_status < 8
    # ):  # Apply filter only if status < 8
    #     if current_status // 4 == 0:
    #         where_clauses.append(f"status = {current_status % 4}")
    #     elif current_status // 4 == 1:
    #         where_clauses.append(f"status != {current_status % 4}")

    # status_list = [1, 3]  # List of integers for filtering
    where_clauses = ["id > 0"]  # Always skip row 0

    # Add the status condition
    if show_list:  # Ensure the list is not empty
        placeholders = ", ".join(["?"] * len(show_list))
        where_clauses.append(f"status IN ({placeholders})")

    # Combine all conditions into a single WHERE clause
    where_clause = " AND ".join(where_clauses)

    # Construct the full query
    query = f"""
        SELECT id, name, status, monitor, added, reviewed, position
        FROM idea_positions
        WHERE {where_clause}
    """

    # Execute the query with the parameters for the placeholders
    c.execute(query, show_list)  # Fetch ideas based on filters
    ideas = c.fetchall()
    click_log(f"{ideas = }")
    pos = 0
    for idea in ideas:
        pos += 1
        id = idea[0]
        pos_to_id[pos] = id

    click_log(f"{pos_to_id = }")
    return ideas, show_list


def get_id_from_position(position: int) -> int:
    """Get the ID of the idea at the specified position in the current view."""
    click_log(f"{pos_to_id = }")
    id = pos_to_id.get(position)
    # click_log(f"{position = } -> {id = }")
    if id:
        return id
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
    status: int,
    monitor: int,
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
            """INSERT INTO ideas (name, content, status, monitor, added, reviewed)
               VALUES (:name, :content, :status, :monitor, :added, :reviewed)""",
            {
                # "position": position,
                "name": name,
                "content": content,
                "status": status,
                "monitor": monitor,
                "added": added,
                "reviewed": reviewed,
            },
        )
        sqlite3.register_adapter


def get_idea_by_position(position: int):
    try:
        # Get the ID from the position
        click_log(f"calling get_id_from_position with {position = }")
        idea_id = get_id_from_position(position)
        if not idea_id:
            return None
        click_log(f"{position = }; {idea_id = }")
    except ValueError as e:
        click.echo(str(e))
        return

    c.execute(
        f"""SELECT id, name, status, monitor, added, reviewed, content 
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
    status: Optional[int] = None,
    monitor: Optional[int] = None,
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
    if status is not None:
        updates.append("status = :status")
        params["status"] = status
    if monitor is not None:
        updates.append("monitor = :monitor")
        params["monitor"] = monitor
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
