# universal_database_inspector

MySQL 데이터베이스의 스키마를 자동으로 분석하고, AI를 활용하여 컬럼 라벨링과 테이블 설명을 생성하는 Python 패키지입니다.

## Features

- **스키마 추출** — 데이터베이스의 전체 테이블·컬럼 구조를 JSON으로 저장
- **AI 컬럼 라벨링** — OpenAI 모델을 활용하여 각 컬럼의 한국어 라벨을 자동 생성
- **AI 테이블 설명** — 테이블의 목적과 용도를 한국어로 요약
- **테이블 통계** — 행 수, 컬럼 수, 날짜 범위 자동 수집
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
# JSON 파일로 실행
python -m universal_database_inspector --config config.json

# JSON 문자열로 실행
python -m universal_database_inspector -c '{"host":"localhost","port":3306,"user":"root","password":"pwd","database":"mydb"}'

# 기존 파일 덮어쓰기
python -m universal_database_inspector --config config.json --overwrite
```

### Python API

```python
from universal_database_inspector import (
    load_config,
    get_output_dir,
    init_structure,
    inspect_all,
    describe_all_tables,
    Table,
)

config = load_config("config.json")
output_dir = get_output_dir(config)

# 폴더 초기화
init_structure(db_name=config["database"])

# 구조 추출
structure = inspect_all(config=config, output_dir=output_dir)

# 라벨·설명 생성
describe_all_tables(config=config, output_dir=output_dir)
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

## Output Structure

각 데이터베이스별로 `database_structure/{db_name}/` 하위에 결과가 저장됩니다.

> **기존 사용자**: 이전 `database_structure/` 직하위 구조를 사용 중이었다면, `database_structure/{DB_NAME}/` 폴더를 만들고 `structure.json`, `labels/`, `descriptions/`를 그 안으로 옮기세요. (예: `database_structure/market_data/`)

```
database_structure/
└── your_database/
    ├── structure.json              # 전체 테이블-컬럼 구조
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
