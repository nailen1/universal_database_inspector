"""High-level database inspector workflows.

Combines inspector and labeler primitives into batch operations.
"""

import json
import os

import pandas as pd

from universal_database_inspector.connection import get_engine
from universal_database_inspector.inspector import load_structure
from universal_database_inspector.labeler import save_labels


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _project_root():
    return _PROJECT_ROOT


def _group_key(table_name: str) -> str | None:
    """Return the group key if the table belongs to a grouped prefix.

    Only numeric-suffix tables (e.g. ``p_ks_000020``) are grouped.
    Named variants like ``p_ks_market`` are treated individually.
    """
    if table_name.startswith("p_ks_"):
        suffix = table_name[len("p_ks_"):]
        if suffix.isdigit():
            return "p_ks"
    return None


def label_all_tables(
    output_dir: str,
    overwrite: bool = False,
) -> list[str]:
    """Generate AI labels for every table and save as JSON files.

    Tables sharing a common prefix (e.g. ``p_ks_*``) are labeled once
    using the union of their columns, saved as ``{prefix}.json``.

    Args:
        output_dir: Database output directory (e.g. database_structure/{db_name}).
        overwrite: If False, skip tables whose label file already exists.

    Returns:
        list[str]: Paths to the saved label files.
    """
    structure = load_structure(output_dir=output_dir)

    grouped_columns: dict[str, list[str]] = {}
    normal_tables: dict[str, list[str]] = {}

    for table, columns in structure.items():
        gk = _group_key(table)
        if gk is not None:
            existing = grouped_columns.get(gk, [])
            for col in columns:
                if col not in existing:
                    existing.append(col)
            grouped_columns[gk] = existing
        else:
            normal_tables[table] = columns

    resolved_dir = output_dir
    if not os.path.isabs(resolved_dir):
        resolved_dir = os.path.join(_project_root(), resolved_dir)
    labels_dir = os.path.join(resolved_dir, "labels")

    targets = {**normal_tables, **grouped_columns}
    paths = []
    created = 0
    skipped = 0
    total = len(targets)
    for i, (name, columns) in enumerate(targets.items(), 1):
        label_file = os.path.join(labels_dir, f"{name}.json")
        already_exists = os.path.exists(label_file)

        if not overwrite and already_exists:
            skipped += 1
            print(f"[{i}/{total}] skip (exists): {name}")
            paths.append(label_file)
            continue

        print(f"[{i}/{total}] labeling: {name}")
        path = save_labels(name, columns, output_dir=output_dir, overwrite=overwrite)
        paths.append(path)
        created += 1
    print(f"done: {created} created, {skipped} skipped (total {total})")
    return paths


def load_labels(
    table_name: str,
    output_dir: str,
) -> dict:
    """Load a saved label JSON file for a table.

    For grouped tables (e.g. ``p_ks_000020``), loads the shared label
    file (``p_ks.json``) instead.

    Args:
        table_name: Name of the target table.
        output_dir: Database output directory (e.g. database_structure/{db_name}).

    Returns:
        dict: ``{column_name: label}`` mapping.

    Raises:
        FileNotFoundError: If the label file does not exist.
    """
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(_project_root(), output_dir)

    lookup_name = _group_key(table_name) or table_name
    labels_path = os.path.join(output_dir, "labels", f"{lookup_name}.json")
    with open(labels_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_labeled_table(
    table_name: str,
    config: dict,
    option_label: bool = True,
    output_dir: str | None = None,
) -> pd.DataFrame:
    """Fetch a table and optionally rename columns to Korean labels.

    Args:
        table_name: Name of the target table.
        config: Database configuration dict.
        option_label: If True, rename columns using the label JSON file.
        output_dir: Database output directory for label files. Defaults to database_structure/{database}.

    Returns:
        pd.DataFrame: Table data with original or labeled column names.
    """
    if output_dir is None:
        from universal_database_inspector.config import get_output_dir
        output_dir = get_output_dir(config)
    engine = get_engine(config)
    query = f"SELECT * FROM `{table_name}`"
    df = pd.read_sql(query, engine)

    if option_label:
        labels = load_labels(table_name, output_dir=output_dir)
        rename_map = {col: labels[col] for col in df.columns if labels.get(col)}
        df = df.rename(columns=rename_map)

    return df
