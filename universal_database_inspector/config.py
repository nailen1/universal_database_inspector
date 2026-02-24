"""Database configuration loader.

Reads MySQL connection parameters from environment variables:
DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def load_db_config() -> dict:
    """Load MySQL connection configuration from environment variables.

    Required variables::

        DB_HOST
        DB_PORT
        DB_USER
        DB_PASSWORD
        DB_NAME

    Returns:
        dict with keys: host, port, user, password, database.

    Raises:
        EnvironmentError: If any required variable is missing.
    """
    required_keys = {
        "host": "DB_HOST",
        "port": "DB_PORT",
        "user": "DB_USER",
        "password": "DB_PASSWORD",
        "database": "DB_NAME",
    }

    config = {}
    missing = []

    for key, env_var in required_keys.items():
        value = os.getenv(env_var)
        if value is None:
            missing.append(env_var)
        else:
            config[key] = value

    if missing:
        raise EnvironmentError(
            f"Missing environment variables: {', '.join(missing)}"
        )

    config["port"] = int(config["port"])
    return config
