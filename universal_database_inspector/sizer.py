"""Table dimension/size metrics from description JSON files."""

import json
import os

from universal_database_inspector.utils import get_description_filenames, load_description_file


def get_table_dimensions(descriptions_folder: str) -> dict[str, dict]:
    """Compute row_count, column_count, and size for each table from description JSONs.

    Size is (row_count + 1) * column_count (header row + data rows).

    Args:
        descriptions_folder: Path to the folder containing description JSON files
            (e.g. database_structure/ehcmall/descriptions/).

    Returns:
        dict: { table_name: { "row_count", "column_count", "size" }, ... }
    """
    result = {}
    for filename in get_description_filenames(descriptions_folder):
        loaded = load_description_file(descriptions_folder, filename)
        table_name = loaded["table_name"]
        content = loaded["content"]
        row_count = content.get("row_count", 0)
        col_count = content.get("column_count", 0)
        size = (row_count + 1) * col_count
        result[table_name] = {
            "row_count": row_count,
            "column_count": col_count,
            "size": size,
        }
    return result


def save_size_json(output_dir: str) -> str:
    """Compute table dimensions from descriptions/ and save as size.json.

    size.json is written next to structure.json (same folder as output_dir).

    Args:
        output_dir: Database output folder (e.g. database_structure/ehcmall/)
            containing descriptions/ and structure.json.

    Returns:
        str: Path to the written size.json file.
    """
    descriptions_folder = os.path.join(output_dir, "descriptions")
    dimensions = get_table_dimensions(descriptions_folder)
    size_path = os.path.join(output_dir, "size.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(size_path, "w", encoding="utf-8") as f:
        json.dump(dimensions, f, ensure_ascii=False, indent=2)
    return size_path
