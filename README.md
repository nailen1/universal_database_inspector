# universal_database_inspector

MySQL 데이터베이스의 스키마를 자동으로 분석하고, AI를 활용하여 컬럼 라벨링과 테이블 설명을 생성하는 Python 패키지입니다.

## Features

- **스키마 추출** — 데이터베이스의 전체 테이블·컬럼 구조를 JSON으로 저장
- **AI 컬럼 라벨링** — OpenAI 모델을 활용하여 각 컬럼의 한국어 라벨을 자동 생성
- **AI 테이블 설명** — 테이블의 목적과 용도를 한국어로 요약
- **테이블 통계** — 행 수, 컬럼 수, 날짜 범위 자동 수집
- **Table 객체** — 테이블별 구조·라벨·설명·데이터를 하나의 인터페이스로 접근

## Installation

```bash
pip install git+https://github.com/nailen1/universal_database_inspector.git
```

## Setup

`.env.example`을 참고하여 `.env` 파일을 생성합니다.

```
# MySQL Database Connection
DB_HOST=your_host
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=your_database

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key
```

## Quick Start

```python
from universal_database_inspector import init_structure, inspect_all, describe_all_tables, Table
```

### 1. 출력 폴더 초기화

```python
init_structure()
```

```
database_structure/
├── labels/
└── description/
```

### 2. 데이터베이스 구조 추출

```python
structure = inspect_all()
list(structure.keys())
# ['bond', 'currency', 'daily_price', 'index', 'index_membership', 'stock_info']
```

`database_structure/structure.json`에 전체 테이블-컬럼 매핑이 저장됩니다.

### 3. 테이블 설명 생성

```python
describe_all_tables()
```

각 테이블에 대해 AI 라벨링과 설명 파일을 일괄 생성합니다.

```
[1/6] describing: bond
[2/6] describing: currency
...
done: 6 created, 0 skipped (total 6)
```

### 4. Table 객체로 접근

```python
table = Table('bond')

table.columns       # ['code', 'date', 'open', 'high', 'low', 'close']
table.labels        # {'code': '채권 코드', 'date': '거래일자', 'open': '시가', ...}
table.description   # {'description': '...', 'first_date': '1962-01-02', 'last_date': '2026-02-20', ...}
table.df            # 원본 데이터 DataFrame
table.labeled       # 한국어 라벨이 적용된 DataFrame
```

## Output Structure

```
database_structure/
├── structure.json              # 전체 테이블-컬럼 구조
├── labels/
│   ├── bond.json               # {"code": "채권 코드", "date": "거래일자", ...}
│   ├── currency.json
│   └── ...
└── description/
    ├── bond.json               # {"description": "...", "row_count": 85376, ...}
    ├── currency.json
    └── ...
```

## CLI

```bash
python -m universal_database_inspector
python -m universal_database_inspector --overwrite
```

## Dependencies

- `mysql-connector-python` — MySQL 연결
- `sqlalchemy` — ORM 엔진
- `pandas` — 데이터 처리
- `python-dotenv` — 환경변수 로딩
- [`use_ai`](https://github.com/nailen1/use_ai) — OpenAI API 래퍼
