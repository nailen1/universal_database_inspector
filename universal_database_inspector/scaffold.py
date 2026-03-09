"""Output folder scaffold generator.

Creates the directory structure for database inspection results.
"""

import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def init_structure(
    base_dir: str = "database_structure",
    db_name: str | None = None,
) -> str:
    """Create the output folder structure for inspection results.

    Creates::

        database_structure/
        └── {db_name}/
            ├── labels/
            └── descriptions/

    Args:
        base_dir: Root output directory (default: database_structure).
        db_name: Database name for the subfolder. Required for multi-db support.

    Returns:
        str: Absolute path to the created database-specific directory.
    """
    if db_name is None:
        raise ValueError("db_name is required for init_structure")
    if not os.path.isabs(base_dir):
        base_dir = os.path.join(_PROJECT_ROOT, base_dir)
    output_dir = os.path.join(base_dir, db_name)

    dirs = [
        output_dir,
        os.path.join(output_dir, "labels"),
        os.path.join(output_dir, "descriptions"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    print(f"initialized: {output_dir}")
    print(f"  ├── labels/")
    print(f"  └── descriptions/")


    return output_dir
