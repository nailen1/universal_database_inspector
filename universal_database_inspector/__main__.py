"""CLI entrypoint for universal_database_inspector.

Usage::

    python -m universal_database_inspector --config config.json
    python -m universal_database_inspector --config config.json --overwrite
    python -m universal_database_inspector --config config.json --parallel --workers 8
    python -m universal_database_inspector -c '{"host":"localhost","port":3306,"user":"root","password":"pwd","database":"mydb"}'
"""

import argparse
import sys

from universal_database_inspector.config import load_config, get_output_dir
from universal_database_inspector.inspector import inspect_all
from universal_database_inspector.describer import describe_all_tables
from universal_database_inspector.scaffold import init_structure


def main():
    parser = argparse.ArgumentParser(
        description="Inspect database structure, generate labels and descriptions.",
    )
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        help="Config: path to JSON file or JSON string with host, port, user, password, database.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing label/description files.",
    )
    parser.add_argument(
        "--base-dir",
        default="database_structure",
        help="Base output directory (default: database_structure).",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run description generation in parallel using threads.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of parallel workers (default: 8, only used with --parallel).",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except (ValueError, FileNotFoundError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    output_dir = get_output_dir(config, base=args.base_dir)
    init_structure(base_dir=args.base_dir, db_name=config["database"])

    print(f"\ndatabase: {config['database']}")
    print(f"output: {output_dir}\n")
    print("[1/2] structure.json")
    inspect_all(config=config, output_dir=output_dir)

    print("\n[2/2] labels + descriptions")
    if args.parallel:
        from universal_database_inspector.parallel import describe_all_tables_parallel
        describe_all_tables_parallel(
            config=config,
            output_dir=output_dir,
            overwrite=args.overwrite,
            max_workers=args.workers,
        )
    else:
        describe_all_tables(config=config, output_dir=output_dir, overwrite=args.overwrite)

    print("\nall done.")


if __name__ == "__main__":
    main()
