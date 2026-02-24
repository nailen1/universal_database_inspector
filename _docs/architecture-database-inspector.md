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
                                └─ description/{table}.json 저장
```

각 단계는 이전 단계의 산출물을 입력으로 사용한다.
라벨 생성 시 샘플 데이터를 참조하고, 개요 생성 시 라벨을 참조하여 정확도를 높인다.

---

## 환경 변수

`.env` 파일에 DB 접속 정보를 설정한다.

```
DB_HOST=your_host
DB_PORT=3306
DB_USER=your_user
DB_PASSWORD=your_password
DB_NAME=your_database

OPENAI_API_KEY=your_openai_api_key
```

---

## 출력 폴더 구조

`init_structure()` 또는 첫 실행 시 자동 생성된다.

```
database_structure/
├── structure.json               ← 테이블·컬럼 목록 (자동 생성)
│
├── labels/                      ← 컬럼 라벨 (AI 생성)
│   ├── {table}.json
│   └── p_ks.json                ← 그룹 테이블 공통 라벨
│
└── description/                 ← 테이블 개요·통계 (AI 생성)
    ├── {table}.json
    └── p_ks.json                ← 그룹 테이블 공통 개요
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

### description/{table}.json

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

---

## 모듈 구조

```
universal_database_inspector/
├── __init__.py          ← 패키지 public API
├── __main__.py          ← CLI 진입점
├── config.py            ← DB 설정 로드 (.env)
├── connection.py        ← MySQL 연결 관리
├── scaffold.py          ← 출력 폴더 구조 생성
├── inspector.py         ← 구조 조회·저장
├── labeler.py           ← AI 컬럼 라벨 생성
├── application.py       ← 일괄 처리·라벨 로드·라벨 적용 조회
├── describer.py         ← AI 테이블 개요·통계 생성
└── table.py             ← Table 클래스 (단일 테이블 접근)
```

| 모듈 | 역할 | 주요 API |
|------|------|----------|
| `config` | 환경 변수 기반 DB 설정 로드 | `load_db_config()` |
| `connection` | MySQL 연결 생성, 테이블 목록 조회 | `get_engine()`, `get_connection()`, `get_list_tables()` |
| `scaffold` | 출력 폴더 구조 초기화 | `init_structure()` |
| `inspector` | 테이블·컬럼 조회, structure JSON 저장 | `get_structure()`, `save_structure()`, `load_structure()`, `inspect_all()` |
| `labeler` | 샘플 데이터 기반 AI 컬럼 라벨 생성 | `generate_labels()`, `save_labels()`, `label_table()` |
| `application` | 일괄 라벨 생성, 라벨 로드, 라벨 적용 테이블 조회 | `label_all_tables()`, `load_labels()`, `get_labeled_table()` |
| `describer` | 라벨 참조 AI 개요 생성, 테이블 통계 수집 | `generate_description()`, `save_description()`, `describe_all_tables()` |
| `table` | 단일 테이블 편의 접근 (lazy-load) | `Table` 클래스 |
| `__main__` | CLI로 전체 파이프라인 실행 | `main()` |

---

## 실행 방법

```bash
# 전체 실행 (기존 파일 스킵)
python -m universal_database_inspector

# 기존 파일 덮어쓰기
python -m universal_database_inspector --overwrite
```

### Python API

```python
from universal_database_inspector import Table, init_structure

init_structure()          # 폴더 구조 초기 생성

table = Table("bond")
table.columns             # 컬럼 목록
table.labels              # AI 생성 라벨
table.description         # 테이블 개요·통계
table.df                  # 전체 데이터 (DataFrame)
table.labeled             # 한글 라벨 적용 DataFrame
table.generate()          # 라벨 + 개요 파일 생성
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
.env (DB 접속 정보)
    │
    ▼
config.py ─→ connection.py (DB 연결·쿼리)
    │
    ▼
inspector.py ──→ structure.json
    │
    ▼
labeler.py ────→ labels/*.json  (AI + 샘플 데이터)
    │
    ▼
describer.py ──→ description/*.json  (AI + 라벨 참조 + 통계)
    │
    ▼
application.py ─→ 일괄 처리 / 라벨 적용 데이터 조회
    │
    ▼
table.py ──────→ Table 클래스 (통합 접근)
```
