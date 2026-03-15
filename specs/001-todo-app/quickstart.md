# Quickstart: TODO App

## Prerequisites

- Python 3.12+
- Node.js 20+
- uv (Python package manager)

## Setup

### Backend

```bash
cd backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Run

### Backend (API server)

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs (Swagger UI)

### Frontend (Next.js dev server)

```bash
cd frontend
npm run dev
```

App: http://localhost:3000

## Test

### Backend

```bash
cd backend
pytest -v
```

### Type check

```bash
cd backend
mypy . --strict
```

### Lint

```bash
cd backend
ruff check .
ruff format --check .
```

## Verify

1. http://localhost:3000 にアクセス
2. TODO を作成し、一覧に表示されることを確認
3. タイトルをクリックしてインライン編集できることを確認
4. チェックボックスで完了/未完了を切り替えられることを確認
5. フィルタで絞り込みができることを確認
6. 削除ボタンで確認ダイアログ後に削除されることを確認
7. ページをリロードしてデータが保持されていることを確認
