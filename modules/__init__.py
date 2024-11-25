import os
import sys


def process_arguments():
    """
    Process sys.argv to get the necessary parameters, like the database file location.
    """
    envhome = os.environ.get("IDEANURSERY")
    if len(sys.argv) > 1:
        idea_home = sys.argv[1]
    elif envhome:
        idea_home = envhome
    else:
        userhome = os.path.expanduser("~")
        idea_home = os.path.join(userhome, ".idea_nursery/")

    backup_dir = os.path.join(idea_home, "backup")

    db_path = os.path.join(idea_home, "ideas.db")

    return idea_home, backup_dir, db_path


# Get command-line arguments: Process the command-line arguments to get the database file location
idea_home, backup_dir, db_path = process_arguments()
