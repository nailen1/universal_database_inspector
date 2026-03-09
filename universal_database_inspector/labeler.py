"""AI-powered column labeler.

Fetches sample rows from a database table, sends them to an LLM,
and saves the inferred column labels as a JSON file.
"""

import json
import os
import re

import pandas as pd

from universal_database_inspector.connection import get_engine
from universal_database_inspector.ai import prompt_to_model


_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _project_root():
    return _PROJECT_ROOT


SYSTEM_MESSAGE = (
    "너는 데이터베이스 스키마 분석 전문가야. "
    "테이블의 컬럼명과 샘플 데이터를 보고, 각 컬럼의 의미를 추정하여 "
    "가급적 한국어 라벨을 부여해. 반드시 JSON 형식으로만 응답해."
)


def fetch_sample_rows(
    table_name: str,
    config: dict,
    n: int = 3,
) -> pd.DataFrame:
    """Fetch the latest N rows from a table.

    Args:
        table_name: Name of the target table.
        config: Database configuration dict.
        n: Number of rows to fetch.

    Returns:
        pd.DataFrame: Sample rows.
    """
    engine = get_engine(config)
    query = f"SELECT * FROM `{table_name}` ORDER BY 1 DESC LIMIT {n}"
    return pd.read_sql(query, engine)


def _build_prompt(
    table_name: str,
    columns: list[str],
    df: pd.DataFrame | None = None,
) -> str:
    parts = [
        f"테이블명: {table_name}",
        f"컬럼 목록: {columns}",
    ]
    if df is not None and not df.empty:
        parts.append(f"\n샘플 데이터 ({len(df)}행):\n{df.to_string(index=False)}")
    parts.append(
        "\n위 테이블의 각 컬럼에 대해 적절한 라벨을 부여해줘.\n"
        "가급적 한국어로, 적절한 한국어가 없으면 영문도 허용.\n\n"
        "다음 JSON 형식으로만 응답해:\n"
        '{"컬럼명": "라벨", ...}'
    )
    return "\n".join(parts)


def _parse_labels(response: str, columns: list[str]) -> dict:
    json_match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
    if json_match:
        try:
            labels = json.loads(json_match.group())
            return {col: labels.get(col, "") for col in columns}
        except json.JSONDecodeError:
            pass
    return {col: "" for col in columns}


def generate_labels(
    table_name: str,
    columns: list[str],
) -> dict:
    """Infer column labels for a table using AI.

    Args:
        table_name: Name of the target table.
        columns: List of column names.

    Returns:
        dict: ``{column_name: label}`` mapping.
    """
    prompt = _build_prompt(table_name, columns)
    response = prompt_to_model(
        prompt=prompt,
        system_message=SYSTEM_MESSAGE,
        temperature=0.2,
    )
    return _parse_labels(response, columns)


def save_labels(
    table_name: str,
    columns: list[str],
    output_dir: str,
    overwrite: bool = False,
) -> str:
    """Generate labels via AI and save as ``labels/{table}.json``.

    Args:
        table_name: Name of the target table.
        columns: List of column names.
        output_dir: Database output directory (e.g. database_structure/{db_name}).
        overwrite: If False, skip when the file already exists.

    Returns:
        str: Path to the saved (or existing) labels file.
    """
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(_project_root(), output_dir)
    labels_dir = os.path.join(output_dir, "labels")
    os.makedirs(labels_dir, exist_ok=True)
    labels_path = os.path.join(labels_dir, f"{table_name}.json")

    if not overwrite and os.path.exists(labels_path):
        return labels_path

    labels = generate_labels(table_name, columns)
    with open(labels_path, "w", encoding="utf-8") as f:
        json.dump(labels, f, ensure_ascii=False, indent=2)

    return labels_path


def label_table(
    table_name: str,
    config: dict,
    output_dir: str,
    n: int = 3,
) -> dict:
    """Infer column labels using AI with sample data and save as JSON.

    Args:
        table_name: Name of the target table.
        config: Database configuration dict.
        output_dir: Database output directory (e.g. database_structure/{db_name}).
        n: Number of sample rows to fetch.

    Returns:
        dict: ``{column_name: label}`` mapping.
    """
    df = fetch_sample_rows(table_name, config=config, n=n)
    prompt = _build_prompt(table_name, list(df.columns), df=df)
    response = prompt_to_model(
        prompt=prompt,
        system_message=SYSTEM_MESSAGE,
        temperature=0.2,
    )
    labels = _parse_labels(response, list(df.columns))

    if not os.path.isabs(output_dir):
        output_dir = os.path.join(_project_root(), output_dir)
    labels_dir = os.path.join(output_dir, "labels")
    os.makedirs(labels_dir, exist_ok=True)
    labels_path = os.path.join(labels_dir, f"{table_name}.json")
    with open(labels_path, "w", encoding="utf-8") as f:
        json.dump(labels, f, ensure_ascii=False, indent=2)

    return labels
