"""Utilities for description JSON files and table size analysis."""

import json
import os

    
def get_description_filenames(folder_path: str) -> list[str]:
    """Return list of JSON filenames in the given descriptions folder.

    Args:
        folder_path: Path to the folder containing description JSON files
            (e.g. database_structure/ehcmall/descriptions/).

    Returns:
        list[str]: Filenames of .json files in the folder (e.g. ["IF_POS_LOGOUT.json", ...]).
    """
    if not os.path.isdir(folder_path):
        return []
    return sorted(f for f in os.listdir(folder_path) if f.endswith(".json"))


def load_description_file(folder_path: str, filename: str) -> dict:
    """Load a single description JSON file and return table name and content.

    Args:
        folder_path: Path to the folder containing description JSON files.
        filename: JSON filename (e.g. "IF_POS_LOGOUT.json").

    Returns:
        dict with keys:
            - table_name: Filename without .json extension (e.g. "IF_POS_LOGOUT").
            - content: Parsed JSON as dict (description, row_count, column_count, etc.).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    table_name = filename.removesuffix(".json") if filename.endswith(".json") else filename
    file_path = os.path.join(folder_path, filename if filename.endswith(".json") else f"{filename}.json")
    with open(file_path, "r", encoding="utf-8") as f:
        content = json.load(f)
    return {"table_name": table_name, "content": content}
