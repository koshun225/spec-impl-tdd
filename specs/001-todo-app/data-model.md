# Data Model: TODO App

**Feature Branch**: `001-todo-app`
**Date**: 2026-03-15

## Entities

### TODO

タスク管理の基本単位。

| Field      | Type     | Constraints                          |
|------------|----------|--------------------------------------|
| id         | integer  | Primary key, auto-increment          |
| title      | string   | Required, max 200 characters, trimmed |
| completed  | boolean  | Required, default: false             |
| created_at | datetime | Required, auto-set on creation (UTC) |
| updated_at | datetime | Required, auto-set on mutation (UTC) |

### Validation Rules

- `title` は空文字・スペースのみを許可しない（トリム後に1文字以上）
- `title` は最大 200 文字
- `completed` のデフォルト値は `false`
- `created_at` は作成時に自動設定、以降変更不可
- `updated_at` は作成時・更新時に自動設定

### State Transitions

```
[未完了] <──toggle──> [完了]
```

- TODO は作成時に「未完了」状態で開始する
- ユーザー操作により「完了」⇔「未完了」を何度でも切り替え可能
- 状態遷移時に `updated_at` が更新される

### Indexes

- `id`: PRIMARY KEY（自動）
- `completed`: フィルタリングクエリの高速化用
