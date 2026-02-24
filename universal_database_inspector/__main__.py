"""CLI entrypoint for universal_database_inspector.

Usage::

    python -m universal_database_inspector
    python -m universal_database_inspector --overwrite
"""

import argparse

from universal_database_inspector.inspector import inspect_all
from universal_database_inspector.describer import describe_all_tables


def main():
    parser = argparse.ArgumentParser(
        description="Inspect database structure, generate labels and descriptions.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing label/description files.",
    )
    args = parser.parse_args()

    print("\n[1/2] structure.json")
    inspect_all()

    print("\n[2/2] labels + descriptions")
    describe_all_tables(overwrite=args.overwrite)

    print("\nall done.")


if __name__ == "__main__":
    main()
