# Python Package Development Workflow

로컬 Python 패키지를 처음부터 만들고 테스트하기까지의 작업 흐름.

---

## Step 1. 프로젝트 폴더 생성

```bash
mkdir ~/dev/my_package
cd ~/dev/my_package
```

---

## Step 2. 가상환경 생성

```bash
python3 -m venv env-my_package
```

---

## Step 3. 패키지 구조 작성

```
my_package/
├── .env                     ← 환경변수 (git 제외)
├── .env.example             ← 환경변수 템플릿
├── .gitignore
├── pyproject.toml           ← 패키지 메타데이터 + 의존성
├── requirements.txt         ← 의존성 목록
├── my_package/
│   ├── __init__.py          ← public API
│   └── ...                  ← 모듈 파일들
├── docs/
│   └── ...
└── notebooks/
    └── ...
```

### pyproject.toml 최소 구성

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "my_package"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "pandas>=2.0.0",
]
```

---

## Step 4. 의존성 설치

```bash
./env-my_package/bin/pip install -r requirements.txt
```

---

## Step 5. 패키지를 editable 모드로 설치

```bash
./env-my_package/bin/pip install -e .
```

`-e` (editable) 모드로 설치하면 소스 코드 수정이 즉시 반영된다.

---

## Step 6. Jupyter 커널 등록

```bash
./env-my_package/bin/pip install ipykernel
```

노트북에서 커널 선택 시 해당 가상환경이 표시된다.

---

## Step 7. 노트북으로 테스트

```bash
notebooks/test-init.ipynb
```

```python
from my_package import some_function

some_function()
```

커널을 `env-my_package`로 선택하고 실행하여 동작을 확인한다.

---

## Step 8. Git 초기화 및 커밋

```bash
git init
git add .
git commit -m "init: initialize package"
```

---

## Step 9. GitHub 원격 저장소 연결

```bash
git remote add origin https://github.com/user/my_package.git
git push -u origin main
```

---

## 요약

| 단계 | 명령 | 결과 |
|------|------|------|
| 1 | `mkdir` | 프로젝트 폴더 |
| 2 | `python3 -m venv` | 가상환경 |
| 3 | 파일 작성 | pyproject.toml + 모듈 코드 |
| 4 | `pip install -r requirements.txt` | 의존성 설치 |
| 5 | `pip install -e .` | 패키지 editable 설치 |
| 6 | `pip install ipykernel` | Jupyter 커널 등록 |
| 7 | 노트북 실행 | 동작 확인 |
| 8 | `git init && commit` | 버전 관리 |
| 9 | `git remote add && push` | 원격 저장소 |
