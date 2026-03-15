<!--
  Sync Impact Report
  ===================
  Version change: (new) → 1.0.0
  Modified principles: N/A (initial creation)
  Added sections:
    - Core Principles (6 principles)
    - Technical Constraints
    - Development Workflow
    - Governance
  Removed sections: N/A
  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ No changes needed (generic placeholders)
    - .specify/templates/spec-template.md ✅ No changes needed (generic placeholders)
    - .specify/templates/tasks-template.md ✅ No changes needed (generic placeholders)
  Follow-up TODOs: None
-->

# Project Constitution

## Core Principles

### I. Test-First (MUST)

- TDD を必須とする: テストを書く → テストが失敗することを確認 → 実装 → テストが通ることを確認
- Red-Green-Refactor サイクルを厳守する
- テストフレームワークは pytest を使用する
- テストが通らないコードは main ブランチにマージしない
- テストカバレッジはコア機能で最低限維持する

### II. Simplicity First (MUST)

- KISS 原則を徹底する。最小限の複雑さで要件を満たす実装を選ぶ
- 過度な抽象化を避ける。3行の類似コードは早すぎる抽象化より良い
- YAGNI: 現時点で必要のない機能は実装しない
- 将来の拡張性のための設計は、明確な根拠がある場合のみ許可する

### III. Type Safety (MUST)

- 全ての Python コードに型ヒントを付与する
- mypy strict モードで型チェックを実施し、エラーゼロを維持する
- データバリデーションには Pydantic モデルを使用する
- `Any` 型の使用は明確な理由がある場合のみ許可する

### IV. API-First Design (MUST)

- API 契約（OpenAPI スキーマ）を実装前に定義する
- フロントエンド（React/Next.js）とバックエンド（FastAPI）の契約を明確にする
- API の変更は契約の更新を先に行い、その後実装を修正する
- エンドポイントのレスポンス形式は Pydantic モデルで定義する

### V. Performance Awareness (SHOULD)

- FastAPI の非同期処理（async/await）を適切に活用する
- SQLite クエリの最適化を意識する（N+1 問題の回避、インデックス設計）
- 不要な処理やデータ取得を避け、必要最小限のリソースで動作させる
- パフォーマンス劣化が疑われる場合は計測してから最適化する

### VI. Observability (SHOULD)

- 構造化ログ（structlog 等）を使用し、JSON 形式で出力する
- リクエストごとにトレースIDを付与し、追跡可能にする
- エラー発生時は十分なコンテキスト情報をログに含める
- ログレベルを適切に使い分ける（DEBUG/INFO/WARNING/ERROR）

## Technical Constraints

- **Language**: Python 3.12+
- **Backend Framework**: FastAPI
- **Frontend Framework**: React / Next.js
- **Database**: SQLite
- **Package Manager**: uv または pip
- **Linter / Formatter**: ruff
- **Test Framework**: pytest
- **Type Checker**: mypy (strict mode)
- **Deploy**: ローカル環境（当面）

## Development Workflow

- Git フローベースの開発: feature ブランチから main へ PR を作成する
- マージ条件:
  - 全テストが通過すること
  - mypy strict の型チェックが通過すること
  - ruff によるリント・フォーマットチェックが通過すること
- コミットは論理的な単位で行い、意味のあるメッセージを付ける
- 各機能は独立してテスト・デプロイ可能な単位で開発する

## Governance

- この Constitution はプロジェクトの全ての開発判断に優先する
- 原則の変更は以下の手順で行う:
  1. 変更内容と理由を文書化する
  2. 既存コードへの影響を評価する
  3. Constitution のバージョンを更新する（セマンティックバージョニング準拠）
- MUST 原則の違反は原則として許可しない。例外が必要な場合は Complexity Tracking で理由を記録する
- SHOULD 原則は推奨事項であり、合理的な理由がある場合は逸脱を許可する

**Version**: 1.0.0 | **Ratified**: 2026-03-15 | **Last Amended**: 2026-03-15
