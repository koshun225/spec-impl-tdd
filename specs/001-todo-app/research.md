# Research: TODO App

**Feature Branch**: `001-todo-app`
**Date**: 2026-03-15

## R1: FastAPI + SQLite の非同期アクセスパターン

**Decision**: aiosqlite を使用した非同期 SQLite アクセス

**Rationale**: FastAPI は非同期フレームワークであり、同期的な SQLite アクセスはイベントループをブロックする。aiosqlite は sqlite3 のラッパーとして軽量かつ信頼性が高い。Constitution の Performance Awareness 原則（async/await 活用）に合致する。

**Alternatives considered**:
- SQLAlchemy async + aiosqlite: ORM は過剰。単一エンティティ（TODO）のみの MVP では不要な複雑さを追加する（Constitution: Simplicity First に違反）
- 同期的 sqlite3 + run_in_executor: 動作するが、aiosqlite のほうがコードがシンプル
- Tortoise ORM: 依存が大きく、MVP には不釣り合い

---

## R2: フロントエンド・バックエンド間の通信パターン

**Decision**: Next.js から FastAPI の REST API を呼び出す。CORS 設定で localhost 間通信を許可する。

**Rationale**: Constitution の API-First Design 原則に準拠。OpenAPI スキーマを FastAPI が自動生成し、フロントエンドはそれに基づいて通信する。

**Alternatives considered**:
- Next.js API Routes でバックエンドを兼ねる: Python/FastAPI の Constitution 制約に反する
- GraphQL: 単一エンティティの CRUD には過剰（Simplicity First 違反）
- tRPC: TypeScript 同士の通信向けで FastAPI と組み合わせ不可

---

## R3: プロジェクト構成パターン

**Decision**: モノレポ構成（backend/ + frontend/ を同一リポジトリに配置）

**Rationale**: 個人開発で単一リポジトリの方が管理が容易。API 契約の変更をフロントエンド・バックエンド同時に追跡できる。

**Alternatives considered**:
- 別リポジトリ: 個人開発では管理オーバーヘッドが不要に増える
- 単一ディレクトリ: Python と Node.js の依存管理が混在し複雑化する

---

## R4: テスト戦略

**Decision**: バックエンドは pytest + httpx（AsyncClient）でテスト。フロントエンドは Jest + React Testing Library。

**Rationale**: Constitution の Test-First 原則に準拠。httpx の AsyncClient は FastAPI の公式推奨テスト手法。TDD サイクル（Red-Green-Refactor）に適している。

**Alternatives considered**:
- unittest: pytest のほうがシンプルで fixture が強力
- requests + TestClient（同期）: 非同期エンドポイントのテストには AsyncClient が適切

---

## R5: 構造化ログの実装方針

**Decision**: structlog を使用し、JSON 形式でログ出力。リクエストごとに request_id を付与する FastAPI ミドルウェアを実装。

**Rationale**: Constitution の Observability 原則に準拠。structlog は Python エコシステムで広く使われ、FastAPI との統合が容易。

**Alternatives considered**:
- 標準 logging: 構造化ログのサポートが弱い
- loguru: 構造化ログは可能だが、structlog のほうが JSON 出力のカスタマイズが柔軟
