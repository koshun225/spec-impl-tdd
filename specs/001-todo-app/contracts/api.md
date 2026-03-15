# API Contract: TODO App

**Base URL**: `http://localhost:8000/api`
**Format**: REST JSON API

## Endpoints

### GET /todos

TODO 一覧を取得する。

**Query Parameters**:

| Parameter | Type   | Required | Description                                     |
|-----------|--------|----------|-------------------------------------------------|
| status    | string | No       | フィルタ: `all` (default), `completed`, `active` |

**Response** `200 OK`:
```json
{
  "todos": [
    {
      "id": 1,
      "title": "買い物に行く",
      "completed": false,
      "created_at": "2026-03-15T10:00:00Z",
      "updated_at": "2026-03-15T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

### POST /todos

新しい TODO を作成する。

**Request Body**:
```json
{
  "title": "買い物に行く"
}
```

**Validation**:
- `title`: 必須、1-200文字（トリム後）

**Response** `201 Created`:
```json
{
  "id": 1,
  "title": "買い物に行く",
  "completed": false,
  "created_at": "2026-03-15T10:00:00Z",
  "updated_at": "2026-03-15T10:00:00Z"
}
```

**Error** `422 Unprocessable Entity`:
```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "タイトルは1文字以上200文字以下で入力してください",
      "type": "value_error"
    }
  ]
}
```

---

### PATCH /todos/{id}

TODO を更新する（タイトル変更または完了トグル）。

**Path Parameters**:
- `id` (integer): TODO の ID

**Request Body** (partial update):
```json
{
  "title": "更新されたタイトル",
  "completed": true
}
```

- `title` と `completed` はいずれも optional（片方のみの更新可）

**Response** `200 OK`:
```json
{
  "id": 1,
  "title": "更新されたタイトル",
  "completed": true,
  "created_at": "2026-03-15T10:00:00Z",
  "updated_at": "2026-03-15T11:00:00Z"
}
```

**Error** `404 Not Found`:
```json
{
  "detail": "TODO not found"
}
```

---

### DELETE /todos/{id}

TODO を削除する。

**Path Parameters**:
- `id` (integer): TODO の ID

**Response** `204 No Content`

**Error** `404 Not Found`:
```json
{
  "detail": "TODO not found"
}
```
