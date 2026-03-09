"""Parallel version of describe_all_tables.

Uses ThreadPoolExecutor to process multiple tables concurrently,
significantly reducing total wall-clock time for large databases.
"""

import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from universal_database_inspector.inspector import load_structure
from universal_database_inspector.describer import (
    _project_root,
    _load_or_create_labels,
    get_table_stats,
    generate_description,
)

_print_lock = threading.Lock()


def _safe_print(msg: str) -> None:
    with _print_lock:
        print(msg, flush=True)


def _describe_one(
    name: str,
    actual_table: str,
    structure: dict,
    config: dict,
    output_dir: str,
    desc_dir: str,
    overwrite: bool,
    index: int,
    total: int,
) -> tuple[str, bool]:
    """Process a single table: labels -> stats -> AI description -> save.

    Returns:
        (path, created): path to the description file and whether it was newly created.
    """
    desc_file = os.path.join(desc_dir, f"{name}.json")

    if not overwrite and os.path.exists(desc_file):
        _safe_print(f"[{index}/{total}] skip (exists): {name}")
        return desc_file, False

    _safe_print(f"[{index}/{total}] describing: {name}")

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

    return desc_file, True


def describe_all_tables_parallel(
    config: dict,
    output_dir: str,
    overwrite: bool = False,
    max_workers: int = 8,
) -> list[str]:
    """Generate description files for every table using parallel workers.

    Drop-in replacement for ``describer.describe_all_tables`` with an
    additional ``max_workers`` parameter to control concurrency.

    Args:
        config: Database configuration dict.
        output_dir: Database output directory (e.g. database_structure/{db_name}).
        overwrite: If False, skip tables whose description file already exists.
        max_workers: Maximum number of concurrent threads (default 8).

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

    total = len(targets)
    print(f"parallel describe: {total} tables, max_workers={max_workers}")

    path_map: dict[int, str] = {}
    created = 0
    skipped = 0
    errors = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {}
        for i, (name, actual_table) in enumerate(targets):
            future = executor.submit(
                _describe_one,
                name=name,
                actual_table=actual_table,
                structure=structure,
                config=config,
                output_dir=output_dir,
                desc_dir=desc_dir,
                overwrite=overwrite,
                index=i + 1,
                total=total,
            )
            future_to_idx[future] = i

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                path, was_created = future.result()
                path_map[idx] = path
                if was_created:
                    created += 1
                else:
                    skipped += 1
            except Exception as exc:
                name = targets[idx][0]
                _safe_print(f"[error] {name}: {exc}")
                errors += 1

    paths = [path_map[i] for i in sorted(path_map)]
    summary = f"done: {created} created, {skipped} skipped"
    if errors:
        summary += f", {errors} errors"
    summary += f" (total {total})"
    print(summary)
    return paths
