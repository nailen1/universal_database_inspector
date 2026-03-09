"""Database configuration loader.

Loads MySQL connection parameters from JSON (file path or JSON string/dict).
"""

import json
import os


def load_config(source: str | dict) -> dict:
    """Load database configuration from JSON.

    Args:
        source: Either:
            - Path to a JSON file
            - JSON string (e.g. '{"host":"localhost","database":"mydb",...}')
            - Dict with keys: host, port, user, password, database

    Returns:
        dict with keys: host, port, user, password, database.

    Raises:
        FileNotFoundError: If source is a path and the file does not exist.
        ValueError: If required keys are missing or JSON is invalid.
    """
    if isinstance(source, dict):
        data = source
    elif isinstance(source, str):
        if os.path.isfile(source):
            with open(source, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            try:
                data = json.loads(source)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}") from e
    else:
        raise TypeError("source must be str (path or JSON) or dict")

    required = ["host", "port", "user", "password", "database"]
    missing = [k for k in required if k not in data or data[k] is None]
    if missing:
        raise ValueError(f"Missing required config keys: {', '.join(missing)}")

    config = {
        "host": str(data["host"]),
        "port": int(data["port"]),
        "user": str(data["user"]),
        "password": str(data["password"]),
        "database": str(data["database"]),
    }
    return config


def get_output_dir(config: dict, base: str = "database_structure") -> str:
    """Get the output directory for a database (database_structure/{db_name}).

    Args:
        config: Config dict with "database" key.
        base: Base directory for all database outputs.

    Returns:
        str: Path like database_structure/mydb
    """
    return os.path.join(base, config["database"])
