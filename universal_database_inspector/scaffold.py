"""Output folder scaffold generator.

Creates the directory structure for database inspection results.
"""

import os

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def init_structure(output_dir: str = "database_structure") -> str:
    """Create the output folder structure for inspection results.

    Creates::

        database_structure/
        ├── labels/
        └── description/

    Args:
        output_dir: Root output directory path.

    Returns:
        str: Absolute path to the created output directory.
    """
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(_PROJECT_ROOT, output_dir)

    dirs = [
        output_dir,
        os.path.join(output_dir, "labels"),
        os.path.join(output_dir, "description"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    print(f"initialized: {output_dir}")
    print(f"  ├── labels/")
    print(f"  └── description/")

    return output_dir
