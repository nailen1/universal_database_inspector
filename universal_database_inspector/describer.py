"""AI-powered table describer.

Generates description metadata for database tables including
AI-inferred purpose, date range, and row/column counts.
"""

import json
import os

from universal_database_inspector.connection import get_connection
from universal_database_inspector.inspector import load_structure
from universal_database_inspector.labeler import save_labels
from universal_database_inspector.ai import prompt_to_model


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _project_root():
    return _PROJECT_ROOT


_DATE_PATTERNS = ("dt", "date", "created_at", "updated_at", "last_updated")

SYSTEM_MESSAGE = (
    "너는 데이터베이스 스키마 분석 전문가야. "
    "테이블의 이름과 컬럼 구조를 보고, 이 테이블의 목적을 "
    "한국어로 간결하게 한두 문장으로 설명해. "
    "반드시 순수 텍스트로만 응답해 (JSON이나 마크다운 없이)."
)


def _find_date_column(columns: list[str]) -> str | None:
    """Find the most likely date column from a list of column names."""
    for col in columns:
        if col.lower() in _DATE_PATTERNS:
            return col
    for col in columns:
        for pattern in _DATE_PATTERNS:
            if pattern in col.lower():
                return col
    return None


def get_table_stats(table_name: str, config: dict) -> dict:
    """Collect basic statistics for a table.

    Args:
        table_name: Name of the target table.
        config: Database configuration dict.

    Returns:
        dict with keys: row_count, column_count, first_date, last_date.
    """
    conn = get_connection(config)
    try:
        cursor = conn.cursor()

        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        row_count = cursor.fetchone()[0]

        cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
        columns = [row[0] for row in cursor.fetchall()]
        column_count = len(columns)

        date_col = _find_date_column(columns)
        first_date = None
        last_date = None
        if date_col:
            cursor.execute(
                f"SELECT MIN(`{date_col}`), MAX(`{date_col}`) FROM `{table_name}`"
            )
            row = cursor.fetchone()
            if row[0] is not None:
                first_date = str(row[0])
                last_date = str(row[1])

        cursor.close()
    finally:
        conn.close()

    return {
        "row_count": row_count,
        "column_count": column_count,
        "first_date": first_date,
        "last_date": last_date,
    }


def generate_description(
    table_name: str,
    columns: list[str],
    labels: dict | None = None,
) -> str:
    """Infer a table's purpose using AI.

    Args:
        table_name: Name of the target table.
        columns: List of column names.
        labels: Optional ``{column: label}`` mapping for richer context.

    Returns:
        str: A short Korean description of the table's purpose.
    """
    parts = [
        f"테이블명: {table_name}",
        f"컬럼 목록: {columns}",
    ]
    if labels:
        parts.append(f"\n컬럼별 의미:\n{json.dumps(labels, ensure_ascii=False)}")
    parts.append(
        "\n이 테이블이 어떤 데이터를 저장하고 있는지 한두 문장으로 설명해줘."
    )
    return prompt_to_model(
        prompt="\n".join(parts),
        system_message=SYSTEM_MESSAGE,
        temperature=0.2,
    ).strip()


def _load_or_create_labels(
    name: str,
    columns: list[str],
    output_dir: str,
) -> dict:
    """Load existing labels or create them if missing."""
    resolved = output_dir
    if not os.path.isabs(resolved):
        resolved = os.path.join(_project_root(), resolved)
    labels_path = os.path.join(resolved, "labels", f"{name}.json")
    if os.path.exists(labels_path):
        with open(labels_path, "r", encoding="utf-8") as f:
            return json.load(f)
    save_labels(name, columns, output_dir=output_dir)
    with open(labels_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_description(
    table_name: str,
    config: dict,
    output_dir: str,
    overwrite: bool = False,
) -> str:
    """Generate description metadata and save as JSON.

    Args:
        table_name: Name of the target table.
        config: Database configuration dict.
        output_dir: Database output directory (e.g. database_structure/{db_name}).
        overwrite: If False, skip when the file already exists.

    Returns:
        str: Path to the saved (or existing) description file.
    """
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(_project_root(), output_dir)
    desc_dir = os.path.join(output_dir, "descriptions")
    os.makedirs(desc_dir, exist_ok=True)
    desc_path = os.path.join(desc_dir, f"{table_name}.json")

    if not overwrite and os.path.exists(desc_path):
        return desc_path

    structure = load_structure(output_dir=output_dir)
    columns = structure.get(table_name, [])

    labels = _load_or_create_labels(table_name, columns, output_dir)
    stats = get_table_stats(table_name, config)
    description = generate_description(table_name, columns, labels=labels)

    result = {
        "description": description,
        "first_date": stats["first_date"],
        "last_date": stats["last_date"],
        "row_count": stats["row_count"],
        "column_count": stats["column_count"],
    }

    with open(desc_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return desc_path


def describe_all_tables(
    config: dict,
    output_dir: str,
    overwrite: bool = False,
) -> list[str]:
    """Generate description files for every table.

    For grouped tables (e.g. ``p_ks_*``), uses one representative
    table for stats and creates a single shared description file.

    Args:
        config: Database configuration dict.
        output_dir: Database output directory (e.g. database_structure/{db_name}).
        overwrite: If False, skip tables whose description file already exists.

    Returns:
        list[str]: Paths to the saved description files.
    """
    from universal_database_inspector.application import _group_key

    structure = load_structure(output_dir=output_dir)

    grouped_representative: dict[str, str] = {}
    normal_tables: list[str] = []

    for table in structure:
        gk = _group_key(table)
        if gk is not None:
            if gk not in grouped_representative:
                grouped_representative[gk] = table
        else:
            normal_tables.append(table)

    resolved_dir = output_dir
    if not os.path.isabs(resolved_dir):
        resolved_dir = os.path.join(_project_root(), resolved_dir)
    desc_dir = os.path.join(resolved_dir, "descriptions")
    os.makedirs(desc_dir, exist_ok=True)

    targets = [(t, t) for t in normal_tables]
    for gk, representative in grouped_representative.items():
        targets.append((gk, representative))

    paths = []
    created = 0
    skipped = 0
    total = len(targets)

    for i, (name, actual_table) in enumerate(targets, 1):
        desc_file = os.path.join(desc_dir, f"{name}.json")

        if not overwrite and os.path.exists(desc_file):
            skipped += 1
            print(f"[{i}/{total}] skip (exists): {name}")
            paths.append(desc_file)
            continue

        print(f"[{i}/{total}] describing: {name}")
        columns = structure.get(actual_table, [])
        labels = _load_or_create_labels(name, columns, output_dir)
        stats = get_table_stats(actual_table, config)
        description = generate_description(name, columns, labels=labels)

        result = {
            "description": description,
            "first_date": stats["first_date"],
            "last_date": stats["last_date"],
            "row_count": stats["row_count"],
            "column_count": stats["column_count"],
        }

        with open(desc_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        paths.append(desc_file)
        created += 1

    print(f"done: {created} created, {skipped} skipped (total {total})")
    return paths
