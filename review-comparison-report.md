# 実装手法比較レビュー: speckit.implement vs TDD

同一仕様のTODOアプリを2つの手法で実装し、5つの専門エージェントで比較レビューした結果をまとめる。

## 実装手法の違い

| | `001-todo-app` | `spec-impl-tdd` |
|---|---|---|
| 手法 | `speckit.implement`（一括実装） | TDD（テスト駆動、段階的実装） |
| コミット数 | 1 | 33+ |
| テスト総数 | 20件 | **229件** |

---

## 5エージェントによる評価サマリー

### 1. コード品質 (code-reviewer)

| カテゴリ | 勝者 | 差 |
|---------|------|---|
| コード構成・モジュール分割 | spec-impl-tdd | 中 |
| 可読性・保守性 | spec-impl-tdd | 中 |
| エラーハンドリング | spec-impl-tdd | **大** |
| 型安全性 | spec-impl-tdd | **大** |
| API設計 | spec-impl-tdd | 中 |
| CSS・スタイリング | spec-impl-tdd | **大** |
| 状態管理 | spec-impl-tdd | 中 |
| テストカバレッジ・品質 | spec-impl-tdd | **大** |

**主要差異:**
- `spec-impl-tdd` はDB接続の永続化+shutdown時の`close_db()`、`isSubmitting`による二重送信防止、`try/finally`でのコンテキストクリア等、防御的プログラミングが徹底
- `001-todo-app` は全コンポーネントにインラインスタイルを使用し、`:hover`/`:disabled`擬似クラスが利用不可
- `spec-impl-tdd` は `FilterStatus` union型、`TodoCreate`/`TodoUpdate` interface等で型安全性が高い

---

### 2. アーキテクチャ (architect-reviewer)

| カテゴリ | 勝者 | 差 |
|---------|------|---|
| データベース層 | spec-impl-tdd | 中 |
| API層 | 引き分け | 小 |
| フロントエンド | spec-impl-tdd | **大** |
| 依存関係管理 | spec-impl-tdd | 中 |
| 設定管理 | 引き分け | - |
| スケーラビリティ | spec-impl-tdd | **大** |
| 結合度/凝集度 | spec-impl-tdd | 中 |

**主要差異:**
- `001-todo-app`: `page.tsx`が全API呼び出しを集中管理 → 「神コンポーネント」化リスク
- `spec-impl-tdd`: 各コンポーネントが自律的にAPIを呼び出し、楽観的更新を実現
- `001-todo-app`: `conftest.py`がモジュール内部の`DB_PATH`を直接書き換え（強結合）
- `spec-impl-tdd`: 公開API（`init_db(path)`, `close_db()`）のみを使用（カプセル化を尊重）

---

### 3. セキュリティ (security-auditor)

| カテゴリ | 勝者 | 差 |
|---------|------|---|
| SQLインジェクション防止 | 引き分け | - |
| 入力バリデーション | 引き分け | - |
| CORS設定 | spec-impl-tdd | 小 |
| エラー情報漏洩 | 引き分け | - |
| データベースセキュリティ | spec-impl-tdd | 小 |
| XSS防止 | 引き分け | - |
| APIセキュリティ | spec-impl-tdd | 小 |

**主要差異:**
- 実装コード自体のセキュリティ水準はほぼ同等（同一仕様に基づくため）
- `spec-impl-tdd`はCORS設定・ミドルウェア・スキーマ制約のテスト検証が充実
- 両ブランチ共通の改善点: `status`パラメータのEnum化、セキュリティヘッダー追加、CORS設定の外部化

---

### 4. パフォーマンス (performance-engineer)

| カテゴリ | 勝者 | 差 |
|---------|------|---|
| DB接続管理 | spec-impl-tdd | **大** |
| WALモード | spec-impl-tdd | 中 |
| クエリ効率 (update) | spec-impl-tdd | 中 |
| 状態更新方式 | spec-impl-tdd | **大** |
| APIコール数 (toggle/edit/delete) | spec-impl-tdd | **大** |
| CSSアプローチ | spec-impl-tdd | 中 |
| structlogキャッシュ | 001-todo-app | 小 |

**主要差異（最も影響の大きい3点）:**
1. **DB接続**: `001-todo-app`は毎リクエスト接続/切断、`spec-impl-tdd`は永続接続
2. **フロントエンド更新**: `001-todo-app`は操作後に毎回全件再取得（2 APIコール/操作）、`spec-impl-tdd`はローカル差分更新（1 APIコール/操作）
3. **インラインスタイル**: `001-todo-app`は毎レンダリングでスタイルオブジェクトを再生成

---

### 5. テスト品質 (qa-expert)

| カテゴリ | 勝者 | 差 |
|---------|------|---|
| テストカバレッジの広さ | spec-impl-tdd | **大** |
| テスト構造と整理 | spec-impl-tdd | 中 |
| テスト分離 | spec-impl-tdd | **大** |
| エッジケースカバレッジ | spec-impl-tdd | **大** |
| フロントエンドテスト | spec-impl-tdd | **大** |
| テスト可読性 | spec-impl-tdd | 中 |
| テスト信頼性 | spec-impl-tdd | 中 |
| 統合/ユニットバランス | spec-impl-tdd | 中 |

**主要差異:**
- テストケース数: 20件 vs **229件**（11.5倍）
- `001-todo-app`: フロントエンドテスト **ゼロ**、DB層・ミドルウェアテスト **ゼロ**
- `spec-impl-tdd`: 仕様番号（`US1-AC1`等）へのトレーサビリティ、全テストにdocstring
- `001-todo-app`: 固定パス`"test_todo.db"`で並列実行時に競合リスク
- `spec-impl-tdd`: pytest `tmp_path`で完全分離、`test_conftest.py`で分離自体をテスト

---

## `001-todo-app` が優れている点

少数だが明確な強みもある:

1. **コードの簡潔さ**: 一括実装のため全体のコード量が少なく、初期理解コストが低い
2. **Pydanticの宣言的バリデーション**: `Field(min_length=1, max_length=200)` は `@field_validator` の手動実装より意図が明確
3. **`pydantic-mypy`プラグイン設定**: `init_forbid_extra`, `init_typed` 等の適切なmypy統合
4. **`uvicorn[standard]`**: extras指定でuvloop等の高性能依存を明示
5. **`useCallback`によるメモ化**: React的に正統なパターン（ただしAPI再フェッチの根本問題は解決しない）
6. **リクエストログ出力**: ミドルウェアでstart/completeを記録し観測可能性が高い

---

## 総合結論

| 観点 | 勝者 |
|------|------|
| コード品質 | **spec-impl-tdd** |
| アーキテクチャ | **spec-impl-tdd** |
| セキュリティ | **spec-impl-tdd**（主にテスト面） |
| パフォーマンス | **spec-impl-tdd** |
| テスト品質 | **spec-impl-tdd** |

**`spec-impl-tdd`（TDDアプローチ）が全5観点で優位**。特にテスト品質・パフォーマンス・フロントエンド設計において差が顕著。

TDDの段階的開発プロセスにより、テスタブルなAPIの設計、防御的プログラミング、エッジケースへの対処が自然に組み込まれた結果と考えられる。一方、`001-todo-app`（一括実装）はコードの簡潔さと読みやすさで優位だが、本番品質としては不十分な部分（フロントエンドテストの欠如、毎回全件再取得、インラインスタイル等）が残る。
