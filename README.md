# universal_database_inspector

MySQL 데이터베이스의 스키마를 자동으로 분석하고, AI를 활용하여 컬럼 라벨링과 테이블 설명을 생성하는 Python 패키지입니다.

## Features

- **스키마 추출** — 데이터베이스의 전체 테이블·컬럼 구조를 JSON으로 저장
- **AI 컬럼 라벨링** — OpenAI 모델을 활용하여 각 컬럼의 한국어 라벨을 자동 생성
- **AI 테이블 설명** — 테이블의 목적과 용도를 한국어로 요약
- **테이블 통계** — 행 수, 컬럼 수, 날짜 범위 자동 수집
- **테이블 사이즈 분석** — description 결과를 기반으로 테이블별 크기 산출 및 `size.json` 저장
- **병렬 처리** — `--parallel` 옵션으로 다수 테이블의 라벨·설명 생성을 동시 실행
- **Table 객체** — 테이블별 구조·라벨·설명·데이터를 하나의 인터페이스로 접근
- **다중 DB 지원** — DB별로 분리된 폴더 구조로 여러 데이터베이스 분석

## Installation

```bash
pip install universal-database-inspector
```

## Setup

### 1. DB 연결 설정 (JSON)

`config.example.json`을 복사하여 `config.json`을 만들고, 실제 DB 정보를 입력합니다.

```json
{
  "host": "localhost",
  "port": 3306,
  "user": "root",
  "password": "your_password",
  "database": "your_database"
}
```

### 2. OpenAI API Key (.env)

AI 기능을 위해 `.env` 파일에 API 키를 설정합니다.

```
OPENAI_API_KEY=your_openai_api_key
```

## Quick Start

### CLI

```bash
# JSON 파일로 실행 (순차 처리)
python -m universal_database_inspector --config config.json

# JSON 문자열로 실행
python -m universal_database_inspector -c '{"host":"localhost","port":3306,"user":"root","password":"pwd","database":"mydb"}'

# 기존 파일 덮어쓰기
python -m universal_database_inspector --config config.json --overwrite

# 병렬 처리 (기본 8 워커)
python -m universal_database_inspector --config config.json --parallel

# 병렬 처리 워커 수 지정
python -m universal_database_inspector --config config.json --parallel --workers 16
```

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `-c`, `--config` | DB 설정 JSON 파일 경로 또는 JSON 문자열 | (필수) |
| `--overwrite` | 기존 라벨·설명 파일 덮어쓰기 | `False` |
| `--base-dir` | 출력 기본 디렉토리 | `database_structure` |
| `--parallel` | 병렬 모드로 설명 생성 | `False` |
| `--workers` | 병렬 워커 수 (`--parallel` 사용 시) | `8` |

### Python API

```python
from universal_database_inspector import (
    load_config,
    get_output_dir,
    init_structure,
    inspect_all,
    describe_all_tables,
    describe_all_tables_parallel,
    Table,
)

config = load_config("config.json")
output_dir = get_output_dir(config)

# 폴더 초기화
init_structure(db_name=config["database"])

# 구조 추출
structure = inspect_all(config=config, output_dir=output_dir)

# 라벨·설명 생성 (순차)
describe_all_tables(config=config, output_dir=output_dir)

# 라벨·설명 생성 (병렬) — 대규모 DB에 권장
describe_all_tables_parallel(config=config, output_dir=output_dir, max_workers=8)
```

### Table 객체로 접근

```python
table = Table("bond", config=config, output_dir=output_dir)

table.columns       # ['code', 'date', 'open', 'high', 'low', 'close']
table.labels        # {'code': '채권 코드', 'date': '거래일자', 'open': '시가', ...}
table.description   # {'description': '...', 'first_date': '1962-01-02', ...}
table.df            # 원본 데이터 DataFrame
table.labeled       # 한국어 라벨이 적용된 DataFrame
```

### 유틸리티

```python
from universal_database_inspector import (
    get_description_filenames,
    load_description_file,
    get_table_dimensions,
    save_size_json,
)

# descriptions 폴더의 JSON 파일 목록
filenames = get_description_filenames("database_structure/mydb/descriptions")

# 개별 description 파일 로드
info = load_description_file("database_structure/mydb/descriptions", "bond.json")
# {'table_name': 'bond', 'content': {'description': '...', 'row_count': 15420, ...}}

# 전체 테이블 사이즈 계산
dimensions = get_table_dimensions("database_structure/mydb/descriptions")

# size.json 파일로 저장
save_size_json("database_structure/mydb")
```

## Output Structure

각 데이터베이스별로 `database_structure/{db_name}/` 하위에 결과가 저장됩니다.

> **기존 사용자**: 이전 `database_structure/` 직하위 구조를 사용 중이었다면, `database_structure/{DB_NAME}/` 폴더를 만들고 `structure.json`, `labels/`, `descriptions/`를 그 안으로 옮기세요. (예: `database_structure/market_data/`)

```
database_structure/
└── your_database/
    ├── structure.json              # 전체 테이블-컬럼 구조
    ├── size.json                   # 테이블별 row_count, column_count, size
    ├── labels/
    │   ├── bond.json               # {"code": "채권 코드", "date": "거래일자", ...}
    │   └── ...
    └── descriptions/
        ├── bond.json               # {"description": "...", "row_count": 85376, ...}
        └── ...
```

## Dependencies

- `mysql-connector-python` — MySQL 연결
- `sqlalchemy` — ORM 엔진
- `pandas` — 데이터 처리
- `python-dotenv` — 환경변수 로딩 (OPENAI_API_KEY)
- `openai` — OpenAI API 호출
