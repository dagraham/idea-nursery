import json
import os
import sys

CONFIG_FILE = os.path.expanduser("~/.idea_home_config")

pos_to_id = {}


def process_arguments():
    """
    Process sys.argv to get the necessary parameters, like the database file location.
    """
    print(f"using {CONFIG_FILE = }")
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            idea_home = json.load(f).get("IDEAHOME")
    else:
        envhome = os.environ.get("IDEAHOME")
        print(f"got {envhome = }")
        if envhome:
            idea_home = envhome
        else:
            userhome = os.path.expanduser("~")
            idea_home = os.path.join(userhome, ".idea_home/")
    print(f"using {idea_home}")

    backup_dir = os.path.join(idea_home, "backup")
    log_dir = os.path.join(idea_home, "logs")
    markdown_dir = os.path.join(idea_home, "markdown")

    db_path = os.path.join(idea_home, "ideas.db")

    os.makedirs(idea_home, exist_ok=True)
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(markdown_dir, exist_ok=True)

    return idea_home, backup_dir, log_dir, markdown_dir, db_path


# Get command-line arguments: Process the command-line arguments to get the database file location
idea_home, backup_dir, log_dir, markdown_dir, db_path = process_arguments()
