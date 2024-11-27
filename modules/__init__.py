import os
import sys


def process_arguments():
    """
    Process sys.argv to get the necessary parameters, like the database file location.
    """
    envhome = os.environ.get("IDEANURSERY")
    if envhome:
        idea_home = envhome
    else:
        userhome = os.path.expanduser("~")
        idea_home = os.path.join(userhome, ".idea_nursery/")

    backup_dir = os.path.join(idea_home, "backup")
    log_dir = os.path.join(idea_home, "logs")

    db_path = os.path.join(idea_home, "ideas.db")

    os.makedirs(idea_home, exist_ok=True)
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    return idea_home, backup_dir, log_dir, db_path


# Get command-line arguments: Process the command-line arguments to get the database file location
idea_home, backup_dir, log_dir, db_path = process_arguments()
