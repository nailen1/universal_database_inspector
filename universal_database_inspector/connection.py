"""MySQL connection management and introspection."""

from urllib.parse import quote_plus

import mysql.connector
from mysql.connector.connection import MySQLConnection
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

def get_engine(config: dict) -> Engine:
    """Create a SQLAlchemy engine for MySQL.

    Args:
        config: Database configuration dict (from load_config).

    Returns:
        Engine: A SQLAlchemy engine instance.
    """

    url = (
        f"mysql+mysqlconnector://{quote_plus(config['user'])}:"
        f"{quote_plus(config['password'])}@"
        f"{config['host']}:{config['port']}/{config['database']}"
    )
    return create_engine(url)


def get_connection(config: dict) -> MySQLConnection:
    """Create a raw MySQL connection.

    Args:
        config: Database configuration dict (from load_config).

    Returns:
        MySQLConnection: An active connection.
    """

    return mysql.connector.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
    )


def get_list_tables(config: dict) -> list[str]:
    """Retrieve the list of tables in the database.

    Args:
        config: Database configuration dict (from load_config).

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
