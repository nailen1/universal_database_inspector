"""universal_database_inspector - Automated MySQL schema decomposition."""

from universal_database_inspector.config import load_config, get_output_dir
from universal_database_inspector.connection import (
    get_engine,
    get_connection,
    get_list_tables,
)
from universal_database_inspector.inspector import (
    load_structure,
    get_columns,
    get_structure,
    save_structure,
    inspect_all,
)
from universal_database_inspector.labeler import (
    fetch_sample_rows,
    generate_labels,
    save_labels,
    label_table,
)
from universal_database_inspector.application import (
    label_all_tables,
    load_labels,
    get_labeled_table,
)
from universal_database_inspector.describer import (
    get_table_stats,
    generate_description,
    save_description,
    describe_all_tables,
)
from universal_database_inspector.table import Table
from universal_database_inspector.scaffold import init_structure

__all__ = [
    "load_config",
    "get_output_dir",
    "get_engine",
    "get_connection",
    "get_list_tables",
    "load_structure",
    "get_columns",
    "get_structure",
    "save_structure",
    "inspect_all",
    "fetch_sample_rows",
    "generate_labels",
    "save_labels",
    "label_table",
    "label_all_tables",
    "load_labels",
    "get_labeled_table",
    "get_table_stats",
    "generate_description",
    "save_description",
    "describe_all_tables",
    "Table",
    "init_structure",
]
