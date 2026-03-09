# Database Decomposition Architecture

SQL 데이터베이스를 완전 자동 분해하는 범용 방법론.

데이터베이스에 접속하여 테이블 → 컬럼 → 라벨 → 개요 순으로 정보를 계층적으로 추출하고, 모든 결과를 JSON 파일로 보존한다.

---

## 분해 파이프라인

```
DB 접속
  └─ 테이블 목록 조회 (SHOW TABLES)
       └─ 테이블별 컬럼 조회 (SHOW COLUMNS)
            └─ structure.json 저장
                 └─ AI 컬럼 라벨 생성
                      └─ labels/{table}.json 저장
                           └─ AI 테이블 개요 + 통계 생성
                                └─ descriptions/{table}.json 저장
```

각 단계는 이전 단계의 산출물을 입력으로 사용한다.
라벨 생성 시 샘플 데이터를 참조하고, 개요 생성 시 라벨을 참조하여 정확도를 높인다.

---

## 설정

### DB 접속 (JSON)

DB 접속 정보는 JSON 파일 또는 JSON 문자열로 전달한다.

```json
{
  "host": "localhost",
  "port": 3306,
  "user": "root",
  "password": "your_password",
  "database": "your_database"
}
```

- 파일 경로: `--config config.json`
- JSON 문자열: `-c '{"host":"...","database":"..."}'`

### OpenAI API Key (.env)

AI 기능 사용 시 `.env`에 `OPENAI_API_KEY`를 설정한다.

---

## 출력 폴더 구조

각 데이터베이스별로 `database_structure/{db_name}/` 하위에 결과가 저장된다.

`init_structure(db_name=...)` 또는 CLI 첫 실행 시 자동 생성된다.

```
database_structure/
└── {db_name}/                   ← DB별 폴더 (database 필드값)
    ├── structure.json            ← 테이블·컬럼 목록 (자동 생성)
    ├── size.json                 ← 테이블별 크기 통계 (sizer 생성)
    │
    ├── labels/                   ← 컬럼 라벨 (AI 생성)
    │   ├── {table}.json
    │   └── p_ks.json             ← 그룹 테이블 공통 라벨
    │
    └── descriptions/             ← 테이블 개요·통계 (AI 생성)
        ├── {table}.json
        └── p_ks.json             ← 그룹 테이블 공통 개요
```

---

## 파일 포맷

### structure.json

테이블명을 키, 컬럼명 리스트를 값으로 갖는 딕셔너리.

```json
{
  "bond": ["dt", "bond_code", "bond_name", "yield_rate"],
  "currency": ["dt", "currency_code", "exchange_rate"]
}
```

### labels/{table}.json

컬럼명을 키, 의미 라벨(한글 우선)을 값으로 갖는 딕셔너리.

```json
{
  "dt": "기준일자",
  "bond_code": "채권 코드",
  "bond_name": "채권명",
  "yield_rate": "수익률"
}
```

### descriptions/{table}.json

테이블의 목적 개요와 기본 통계를 담는 딕셔너리.

```json
{
  "description": "채권 시장의 일별 수익률 데이터를 저장하는 테이블.",
  "first_date": "2020-01-02",
  "last_date": "2026-02-24",
  "row_count": 15420,
  "column_count": 4
}
```

### size.json

`descriptions/` 내 모든 테이블의 크기 정보를 집계한 딕셔너리. `save_size_json()`으로 생성.

`size`는 `(row_count + 1) × column_count`로 산출한다 (헤더 1행 포함).

```json
{
  "bond": {
    "row_count": 15420,
    "column_count": 4,
    "size": 61684
  },
  "currency": {
    "row_count": 8500,
    "column_count": 3,
    "size": 25503
  }
}
```

---

## 모듈 구조

```
universal_database_inspector/
├── __init__.py          ← 패키지 public API
├── __main__.py          ← CLI 진입점
├── ai.py                ← OpenAI API 래퍼
├── config.py            ← DB 설정 로드 (JSON)
├── connection.py        ← MySQL 연결 관리
├── scaffold.py          ← 출력 폴더 구조 생성
├── inspector.py         ← 구조 조회·저장
├── labeler.py           ← AI 컬럼 라벨 생성
├── application.py       ← 일괄 처리·라벨 로드·라벨 적용 조회
├── describer.py         ← AI 테이블 개요·통계 생성
├── table.py             ← Table 클래스 (단일 테이블 접근)
├── utils.py             ← description 파일 조회·로드 유틸리티
├── sizer.py             ← 테이블 사이즈 산출·저장
└── parallel/
    ├── __init__.py      ← parallel 서브패키지 진입점
    └── describer.py     ← 병렬 테이블 설명 생성
```

| 모듈 | 역할 | 주요 API |
|------|------|----------|
| `config` | JSON 기반 DB 설정 로드 | `load_config()`, `get_output_dir()` |
| `connection` | MySQL 연결 생성, 테이블 목록 조회 | `get_engine()`, `get_connection()`, `get_list_tables()` |
| `scaffold` | 출력 폴더 구조 초기화 | `init_structure()` |
| `inspector` | 테이블·컬럼 조회, structure JSON 저장 | `get_structure()`, `save_structure()`, `load_structure()`, `inspect_all()` |
| `ai` | OpenAI API 호출 (모델 호환성 자동 처리) | `prompt_to_model()` |
| `labeler` | 샘플 데이터 기반 AI 컬럼 라벨 생성 | `generate_labels()`, `save_labels()`, `label_table()` |
| `application` | 일괄 라벨 생성, 라벨 로드, 라벨 적용 테이블 조회 | `label_all_tables()`, `load_labels()`, `get_labeled_table()` |
| `describer` | 라벨 참조 AI 개요 생성, 테이블 통계 수집 | `generate_description()`, `save_description()`, `describe_all_tables()` |
| `table` | 단일 테이블 편의 접근 (lazy-load) | `Table` 클래스 |
| `utils` | description JSON 파일 조회·로드 | `get_description_filenames()`, `load_description_file()` |
| `sizer` | description 기반 테이블 크기 산출 | `get_table_dimensions()`, `save_size_json()` |
| `parallel.describer` | ThreadPoolExecutor 기반 병렬 설명 생성 | `describe_all_tables_parallel()` |
| `__main__` | CLI로 전체 파이프라인 실행 | `main()` |

---

## 실행 방법

### CLI

```bash
# JSON 파일로 실행 (순차 처리)
python -m universal_database_inspector --config config.json

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
from universal_database_inspector import load_config, get_output_dir, Table, init_structure

config = load_config("config.json")
output_dir = get_output_dir(config)
init_structure(db_name=config["database"])   # 폴더 구조 초기 생성

table = Table("bond", config=config, output_dir=output_dir)
table.columns             # 컬럼 목록
table.labels              # AI 생성 라벨
table.description         # 테이블 개요·통계
table.df                  # 전체 데이터 (DataFrame)
table.labeled             # 한글 라벨 적용 DataFrame
table.generate()          # 라벨 + 개요 파일 생성
```

### 병렬 처리 API

```python
from universal_database_inspector import describe_all_tables_parallel

describe_all_tables_parallel(
    config=config,
    output_dir=output_dir,
    max_workers=8,          # 동시 실행 스레드 수
)
```

`describe_all_tables()`와 동일한 결과물을 생성하되, `ThreadPoolExecutor`로 다수 테이블을 동시 처리한다.
각 워커가 독립적으로 DB 커넥션과 OpenAI API를 호출하므로 I/O 대기 시간이 중첩되어 전체 소요 시간이 크게 감소한다.

- thread-safe 출력 (`threading.Lock`)
- 개별 테이블 에러가 전체를 중단시키지 않음
- OpenAI API rate limit에 따라 `max_workers` 조절 권장 (보통 8~16)

### 유틸리티 API

```python
from universal_database_inspector import (
    get_description_filenames,
    load_description_file,
    get_table_dimensions,
    save_size_json,
)

# descriptions 폴더 내 JSON 파일 목록
filenames = get_description_filenames("database_structure/mydb/descriptions")

# 개별 description 파일 로드
info = load_description_file("database_structure/mydb/descriptions", "bond.json")

# 전체 테이블 사이즈 계산 → dict
dimensions = get_table_dimensions("database_structure/mydb/descriptions")

# size.json 으로 저장
save_size_json("database_structure/mydb")
```

---

## 그룹 테이블 규칙

동일 스키마의 종목별 테이블(예: `p_ks_000020`, `p_ks_005930`)은 하나의 그룹으로 묶어 처리한다.

| 조건 | 그룹 키 | 예시 |
|------|---------|------|
| `p_ks_` + 숫자 접미사 | `p_ks` | `p_ks_000020` → `p_ks.json` |
| `p_ks_` + 문자 접미사 | 개별 처리 | `p_ks_market` → `p_ks_market.json` |

그룹 테이블은 구성원 전체의 컬럼 합집합으로 라벨을 생성하고, 대표 테이블 1개로 통계를 수집한다.

---

## 멱등성 (Idempotency)

- 기본 동작(`overwrite=False`): 대상 파일이 이미 존재하면 생성을 스킵한다.
- `overwrite=True`: 기존 파일을 덮어쓰고 AI를 재호출한다.
- `describe_all_tables()` 실행 시 라벨 파일이 없으면 자동으로 먼저 생성한 뒤 개요를 생성한다.

---

## 의존성 흐름

```
config.json (DB 접속 정보)
    │
    ▼
config.py ─→ connection.py (DB 연결·쿼리)
    │
    ▼
inspector.py ──→ structure.json
    │
    ▼
labeler.py ────→ labels/*.json  (ai.py + 샘플 데이터)
    │
    ▼
describer.py ──→ descriptions/*.json  (ai.py + 라벨 참조 + 통계)
    │                │
    │                ├─→ parallel/describer.py  (ThreadPoolExecutor 병렬 처리)
    │                │
    │                └─→ sizer.py ──→ size.json  (description 기반 크기 산출)
    │
    ▼
application.py ─→ 일괄 처리 / 라벨 적용 데이터 조회
    │
    ▼
table.py ──────→ Table 클래스 (통합 접근)

utils.py ──────→ description 파일 조회·로드 (sizer.py 에서 사용)
```

---

## 병렬 처리 아키텍처

`parallel/describer.py`는 기존 `describer.py`의 순차 루프를 `ThreadPoolExecutor`로 대체한다.

```
describe_all_tables_parallel(max_workers=N)
    │
    ├─ ThreadPoolExecutor (N workers)
    │   ├─ worker 1: _describe_one(table_A) → labels → stats → AI → save
    │   ├─ worker 2: _describe_one(table_B) → labels → stats → AI → save
    │   ├─ worker 3: _describe_one(table_C) → labels → stats → AI → save
    │   └─ ...
    │
    └─ as_completed() → 결과 수집, 에러 개별 처리
```

- 각 워커는 독립 DB 커넥션 + OpenAI API 호출
- `threading.Lock`으로 콘솔 출력 보호
- 기존 `describer.py`는 수정하지 않음 (순차 실행 유지)
