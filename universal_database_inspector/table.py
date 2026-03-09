"""Convenience wrapper for a single database table.

Provides lazy-loaded properties to access structure, labels,
description, and data without repeating path arguments.
"""

import json
import os

import pandas as pd

from universal_database_inspector.connection import get_engine
from universal_database_inspector.application import _group_key


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _project_root():
    return _PROJECT_ROOT


class Table:
    """High-level accessor for a single database table.

    Usage::

        config = load_config("config.json")
        output_dir = get_output_dir(config)
        table = Table("bond", config=config, output_dir=output_dir)
        table.columns        # list of column names
        table.labels          # {column: korean_label}
        table.description     # description dict (overview, dates, counts)
        table.df              # full table as DataFrame
        table.labeled         # df with Korean column labels
        table.generate()      # create label + description files if missing
    """

    def __init__(
        self,
        table_name: str,
        config: dict,
        output_dir: str,
    ):
        self.table_name = table_name
        self._config = config
        self._output_dir = output_dir
        self._lookup_name = _group_key(table_name) or table_name

        self._resolved_dir = output_dir
        if not os.path.isabs(self._resolved_dir):
            self._resolved_dir = os.path.join(_project_root(), self._resolved_dir)

        self._columns: list[str] | None = None
        self._labels: dict | None = None
        self._description: dict | None = None

    def __repr__(self) -> str:
        return f"Table('{self.table_name}')"

    def _not_found(self, kind: str, path: str) -> FileNotFoundError:
        return FileNotFoundError(
            f"{kind} file not found: {path}\n"
            f"Run table.generate() to create it."
        )

    @property
    def columns(self) -> list[str]:
        if self._columns is not None:
            return self._columns
        structure_path = os.path.join(self._resolved_dir, "structure.json")
        if not os.path.exists(structure_path):
            raise self._not_found("Structure", structure_path)
        with open(structure_path, "r", encoding="utf-8") as f:
            structure = json.load(f)
        cols = structure.get(self.table_name)
        if cols is None:
            raise KeyError(
                f"Table '{self.table_name}' not found in {structure_path}"
            )
        self._columns = cols
        return self._columns

    @property
    def labels(self) -> dict:
        if self._labels is not None:
            return self._labels
        labels_path = os.path.join(
            self._resolved_dir, "labels", f"{self._lookup_name}.json",
        )
        if not os.path.exists(labels_path):
            raise self._not_found("Labels", labels_path)
        with open(labels_path, "r", encoding="utf-8") as f:
            self._labels = json.load(f)
        return self._labels

    @property
    def description(self) -> dict:
        if self._description is not None:
            return self._description
        desc_path = os.path.join(
            self._resolved_dir, "descriptions", f"{self._lookup_name}.json",
        )
        if not os.path.exists(desc_path):
            raise self._not_found("Description", desc_path)
        with open(desc_path, "r", encoding="utf-8") as f:
            self._description = json.load(f)
        return self._description

    @property
    def df(self) -> pd.DataFrame:
        engine = get_engine(self._config)
        return pd.read_sql(f"SELECT * FROM `{self.table_name}`", engine)

    @property
    def labeled(self) -> pd.DataFrame:
        """Table data with column names replaced by Korean labels."""
        df = self.df
        rename_map = {col: lbl for col, lbl in self.labels.items() if lbl and col in df.columns}
        return df.rename(columns=rename_map)

    def generate(self, overwrite: bool = False) -> None:
        """Generate label and description files for this table."""
        from universal_database_inspector.describer import save_description
        from universal_database_inspector.labeler import save_labels

        columns = self.columns
        save_labels(
            self._lookup_name,
            columns,
            output_dir=self._output_dir,
            overwrite=overwrite,
        )
        save_description(
            self.table_name,
            config=self._config,
            output_dir=self._output_dir,
            overwrite=overwrite,
        )
        self._labels = None
        self._description = None
        print(f"generated: labels + description for '{self._lookup_name}'")
