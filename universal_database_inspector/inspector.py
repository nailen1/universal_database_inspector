"""Database structure inspector.

Connects to the database, collects table and column information,
and saves the results as JSON files.
"""

import json
import os

from universal_database_inspector.connection import get_connection, get_list_tables


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _project_root():
    return _PROJECT_ROOT


def load_structure(output_dir: str) -> dict:
    """Load a previously saved structure JSON file.

    Args:
        output_dir: Directory containing the structure file.

    Returns:
        dict: ``{table_name: [col1, col2, ...], ...}``

    Raises:
        FileNotFoundError: If the structure file does not exist.
    """
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(_project_root(), output_dir)
    structure_path = os.path.join(output_dir, "structure.json")
    with open(structure_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_columns(table_name: str, config: dict) -> list[str]:
    """Retrieve the list of column names for a given table.

    Args:
        table_name: Name of the target table.
        config: Database configuration dict.

    Returns:
        list[str]: Column names in ordinal position order.
    """
    conn = get_connection(config)
    try:
        cursor = conn.cursor()
        cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return columns
    finally:
        conn.close()


def get_structure(config: dict) -> dict:
    """Collect the full table-column structure for the database.

    Args:
        config: Database configuration dict.

    Returns:
        dict: ``{table_name: [col1, col2, ...], ...}``
    """
    tables = get_list_tables(config)
    structure = {}
    conn = get_connection(config)
    try:
        cursor = conn.cursor()
        for table in tables:
            cursor.execute(f"SHOW COLUMNS FROM `{table}`")
            structure[table] = [row[0] for row in cursor.fetchall()]
        cursor.close()
    finally:
        conn.close()
    return structure


def save_structure(
    config: dict,
    output_dir: str,
) -> str:
    """Save the table-column structure to a JSON file.

    Args:
        config: Database configuration dict.
        output_dir: Directory to write JSON files into (e.g. database_structure/{db_name}).

    Returns:
        str: Path to the saved structure file.
    """
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(_project_root(), output_dir)
    os.makedirs(output_dir, exist_ok=True)

    structure = get_structure(config)

    structure_path = os.path.join(output_dir, "structure.json")
    with open(structure_path, "w", encoding="utf-8") as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)

    return structure_path


def inspect_all(config: dict, output_dir: str) -> dict:
    """Inspect the database and save the structure JSON file.

    Args:
        config: Database configuration dict.
        output_dir: Directory to write JSON files into (e.g. database_structure/{db_name}).

    Returns:
        dict: ``{table: [columns]}``
    """
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(_project_root(), output_dir)
    os.makedirs(output_dir, exist_ok=True)

    structure = get_structure(config)

    structure_path = os.path.join(output_dir, "structure.json")
    with open(structure_path, "w", encoding="utf-8") as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)

    return structure
