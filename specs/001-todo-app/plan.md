# Implementation Plan: TODO App

**Branch**: `001-todo-app` | **Date**: 2026-03-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-todo-app/spec.md`

## Summary

個人用の TODO 管理 Web アプリケーション。FastAPI (Python) バックエンドと React/Next.js フロントエンドで構成し、SQLite でデータを永続化する。CRUD 操作、完了/未完了トグル、ステータスフィルタリングを提供する。インライン編集と削除確認ダイアログを含む。

## Technical Context

**Language/Version**: Python 3.12+ (backend), TypeScript (frontend)
**Primary Dependencies**: FastAPI, aiosqlite, Pydantic (backend); React, Next.js (frontend)
**Storage**: SQLite (aiosqlite 経由の非同期アクセス)
**Testing**: pytest + httpx AsyncClient (backend); Jest + React Testing Library (frontend)
**Target Platform**: ローカル環境 (localhost)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: 100件 TODO で一覧表示 2秒以内、操作レスポンス 1秒以内
**Constraints**: 単一ユーザー、認証不要、ローカルデプロイ
**Scale/Scope**: 単一ユーザー、数百件程度の TODO

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Test-First (MUST) | PASS | pytest + httpx AsyncClient で TDD。テストタスクを実装タスクの前に配置 |
| II. Simplicity First (MUST) | PASS | 単一エンティティ、ORM 不使用（aiosqlite 直接）、最小限の依存 |
| III. Type Safety (MUST) | PASS | 全コードに型ヒント付与、mypy strict、Pydantic モデルでバリデーション |
| IV. API-First Design (MUST) | PASS | contracts/api.md で OpenAPI 契約を先行定義済み |
| V. Performance Awareness (SHOULD) | PASS | aiosqlite で非同期 I/O、completed カラムにインデックス |
| VI. Observability (SHOULD) | PASS | structlog で構造化ログ、リクエストトレーシングミドルウェア |

**Gate Result**: ALL PASS - Phase 0 進行可

## Project Structure

### Documentation (this feature)

```text
specs/001-todo-app/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── api.md
├── checklists/
│   └── requirements.md
└── tasks.md              # /speckit.tasks で生成
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI app, CORS, ミドルウェア
│   ├── models.py           # Pydantic schemas (request/response)
│   ├── database.py         # aiosqlite 接続管理, テーブル初期化
│   ├── routes.py           # API エンドポイント
│   └── logging_config.py   # structlog 設定
├── tests/
│   ├── conftest.py         # pytest fixtures (test DB, async client)
│   ├── test_routes.py      # API エンドポイントテスト
│   └── test_models.py      # Pydantic モデルバリデーションテスト
├── requirements.txt
├── pyproject.toml          # mypy, ruff 設定
└── todo.db                 # SQLite DB (gitignore)

frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   └── page.tsx        # メインページ
│   ├── components/
│   │   ├── TodoList.tsx     # TODO 一覧
│   │   ├── TodoItem.tsx     # 個別 TODO（インライン編集、トグル、削除）
│   │   ├── TodoForm.tsx     # 新規 TODO 入力フォーム
│   │   └── TodoFilter.tsx   # フィルタボタン群
│   └── lib/
│       └── api.ts           # FastAPI との通信クライアント
├── package.json
├── tsconfig.json
└── next.config.js
```

**Structure Decision**: Web application 構成（backend/ + frontend/）を採用。Constitution の技術スタック（FastAPI + React/Next.js）に合致し、API 契約による明確な責務分離を実現する。
