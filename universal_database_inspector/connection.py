"""MySQL connection management and introspection."""

from typing import Optional
from urllib.parse import quote_plus

import mysql.connector
from mysql.connector.connection import MySQLConnection
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from universal_database_inspector.config import load_db_config


def get_engine(config: Optional[dict] = None) -> Engine:
    """Create a SQLAlchemy engine for MySQL.

    Args:
        config: Database configuration dict. Loaded from env if omitted.

    Returns:
        Engine: A SQLAlchemy engine instance.
    """
    if config is None:
        config = load_db_config()

    url = (
        f"mysql+mysqlconnector://{quote_plus(config['user'])}:"
        f"{quote_plus(config['password'])}@"
        f"{config['host']}:{config['port']}/{config['database']}"
    )
    return create_engine(url)


def get_connection(config: Optional[dict] = None) -> MySQLConnection:
    """Create a raw MySQL connection.

    Args:
        config: Database configuration dict. Loaded from env if omitted.

    Returns:
        MySQLConnection: An active connection.
    """
    if config is None:
        config = load_db_config()

    return mysql.connector.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
    )


def get_list_tables(config: Optional[dict] = None) -> list[str]:
    """Retrieve the list of tables in the database.

    Args:
        config: Database configuration dict. Loaded from env if omitted.

    Returns:
        list[str]: Sorted table names.
    """
    conn = get_connection(config=config)
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = sorted(row[0] for row in cursor.fetchall())
        cursor.close()
        return tables
    finally:
        conn.close()
