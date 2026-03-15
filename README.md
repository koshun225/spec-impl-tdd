# spec-impl-tdd: AI TDD with Agent Separation

AIコーディングにおけるTDD（テスト駆動開発）で、**テストエージェントと実装エージェントを分離**することでコード品質が向上するかを検証したリポジトリです。

## 背景

[GitHub Spec Kit](https://github.com/staru09/github-spec-kit) の `speckit.implement` はTDDでの実装を謳っていますが、テストと実装を同じエージェントが担当します。同一エージェントだとテストが実装の都合に寄り添いやすく、「自分で問題を作って自分で解く」構造になりがちです。

そこで、テスト作成・実装・品質判定をそれぞれ独立したエージェントが担当するスキル **spec-impl-tdd** を開発し、同一仕様のTODOアプリで品質を比較しました。

## spec-impl-tdd のアーキテクチャ

```
各タスクに対して:
  [Red Team]   テスト作成（実装を見れない、worktree隔離）
  [Green Team] 実装（テストコードを見れない、worktree隔離）
  → 全テストPASS → 完了
  → FAIL → [QA Agent] テスト/実装/仕様のどれが悪いか判定 → やり直し
```

- **Red Team**: 仕様書だけを見てテストを作成。worktreeで隔離され、実装コードにアクセスできない
- **Green Team**: 仕様書とフィルタされたテスト結果を見て実装。テストのアサーション内容は見れない
- **QA Agent**: テスト失敗時に仕様書を正として、テスト・実装・仕様のどれに問題があるか判定

## ブランチ構成

| ブランチ | 実装手法 | 説明 |
|---------|---------|------|
| `main` | **spec-impl-tdd**（エージェント分離方式） | 33+コミット、229テスト |
| `001-todo-app` | speckit.implement（同一エージェント方式） | 1コミット、20テスト |

```bash
# 両ブランチの差分を確認
git diff 001-todo-app..main -- backend/ frontend/src/
```

## 検証結果

5つの専門AIエージェント（code-reviewer, architect-reviewer, security-auditor, performance-engineer, qa-expert）による並列レビューの結果、**全5観点でエージェント分離方式が優位**と判定されました。

| 観点 | speckit.implement | spec-impl-tdd |
|------|:-:|:-:|
| コード品質 | ○ | **◎** |
| アーキテクチャ | ○ | **◎** |
| セキュリティ | ○ | **◎** |
| パフォーマンス | △ | **◎** |
| テスト品質 | △ | **◎** |
| 開発速度 | **◎** | △ |

詳細な比較レポートは [`review-comparison-report.md`](./review-comparison-report.md) を参照してください。

## 使い方

### 前提条件

- [Claude Code](https://claude.ai/claude-code) がインストール済み
- [GitHub Spec Kit](https://github.com/staru09/github-spec-kit) でプロジェクトが初期化済み

### セットアップ

このリポジトリの `.claude/skills/spec-impl-tdd/` を自分のプロジェクトにコピーします。

```bash
cp -r path/to/this-repo/.claude/skills/spec-impl-tdd your-project/.claude/skills/
```

### 実行

仕様〜タスク分解まではSpec Kitの標準フロー。実装フェーズだけ差し替えます。

```bash
# 1. 仕様書を作る
/speckit.specify 「機能の説明」

# 2. 設計する
/speckit.plan

# 3. タスク分解する
/speckit.tasks

# 4. 実装（ここだけ差し替え）
/spec-impl-tdd <feature-name>
```

特定のタスクだけ実行する場合：

```bash
/spec-impl-tdd 001-todo-app T012 T013 T014
```

## リポジトリ構成

```
.claude/
├── commands/           # GitHub Spec Kit のスキル群
│   ├── speckit.implement.md
│   ├── speckit.specify.md
│   └── ...
├── skills/
│   └── spec-impl-tdd/  # エージェント分離TDDスキル
│       ├── SKILL.md
│       └── references/
│           ├── red-team-agent.md
│           ├── green-team-agent.md
│           └── qa-agent.md
└── agents/             # 比較レビュー用エージェント
    ├── code-reviewer.md
    ├── architect-reviewer.md
    ├── security-auditor.md
    ├── performance-engineer.md
    └── qa-expert.md

specs/001-todo-app/     # TODOアプリの仕様書群
├── spec.md
├── plan.md
├── tasks.md
├── data-model.md
├── contracts/api.md
└── quickstart.md

backend/                # FastAPI + aiosqlite
frontend/               # Next.js + React
```

## 関連記事

- [AIコーディングでテストと実装のエージェントを分離したら、コード品質が劇的に上がった話](https://zenn.dev/) (Zenn)

## License

MIT
