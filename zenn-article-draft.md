---
title: "AIコーディングでテストと実装のエージェントを分離したら、コード品質が劇的に上がった話"
emoji: "🧪"
type: "tech"
topics: ["claudecode", "ai", "tdd", "fastapi", "nextjs"]
published: false
---

## はじめに

[GitHub Spec Kit](https://github.com/staru09/github-spec-kit)というOSSをご存知でしょうか。Claude Codeのスキル（カスタムスラッシュコマンド）として動作する仕様駆動開発ツールで、仕様書の作成（`/speckit.specify`）→ 設計（`/speckit.plan`）→ タスク分解（`/speckit.tasks`）→ 実装（`/speckit.implement`）という流れでコード生成を自動化してくれます。

この中の実装スキル **speckit.implement** は、TDD（テスト駆動開発）での実装を謳っています。タスク定義に沿ってテストを書き、それを通す実装を生成してくれる。

でもふと思ったんですよね。

**「テストを書くのも実装するのも同じエージェントって、それ本当にTDDなの？」**

人間のTDDでは「テストが仕様を表現して、実装がそれに従う」っていう緊張関係が大事ですよね。でも同じエージェントが両方やると、テストが実装の都合に寄り添っちゃうんじゃないか、と。

そこで、**テストエージェントと実装エージェントを分けるスキル**「**spec-impl-tdd**」を自作してみました。同じTODOアプリの仕様で両方試して、どのくらい品質が変わるのか検証した結果を共有します。

## 何が違うの？

### speckit.implement（同一エージェント方式）

```
仕様書 → [エージェントA] テスト作成 → [エージェントA] 実装 → 完了
```

1つのエージェントがタスクリストを上から順に処理します。テストも実装も同じコンテキストの中で行われるので、「こう実装するつもりだから、テストはこの程度でいいかな」みたいなバイアスが入りやすい構造です。

### spec-impl-tdd（エージェント分離方式）

```
各タスクに対して:
  [Red Team]   テスト作成（実装を見れない、worktree隔離）
  [Green Team] 実装（テストコードを見れない、worktree隔離）
  → 全テストPASS → 完了
  → FAIL → [QA Agent] テスト/実装/仕様のどれが悪いか判定 → やり直し
```

3種類のエージェントが関わります。テストを書く**Red Team**は実装コードを見れず、実装する**Green Team**はテストのアサーション内容を見れません。それぞれgitのworktreeで物理的に隔離されています。テストが通らなかった場合は**QA Agent**が仕様書を正として「テストが間違っているのか、実装が間違っているのか」を判定し、該当する側をやり直させます。

人間のTDDでいう「テストファースト」の本質を、エージェントアーキテクチャのレベルで再現したイメージです。

### 比較条件

| | speckit.implement | spec-impl-tdd |
|---|---|---|
| エージェント構成 | 単一エージェント | Red / Green / QA の3エージェント |
| 入力仕様 | 同一（spec.md, plan.md, tasks.md） | 同一 |
| 技術スタック | FastAPI + Next.js | 同一 |
| コミット数 | 1 | 33+ |

同じ仕様書、同じ技術スタック、同じtasks.md。**変えたのはエージェントの分離構造だけ**です。

## レビューもAIにやってもらった

せっかくなので、比較レビューも人間じゃなくてAIにやってもらいました。Claude Codeのエージェント機能で5種類の専門レビュアーを**同時に並列起動**して、`git show`で両ブランチのコードを読み比べてもらいます。

| エージェント | 見てもらった観点 |
|---|---|
| code-reviewer | コード品質・可読性・エラーハンドリング |
| architect-reviewer | アーキテクチャ・結合度・スケーラビリティ |
| security-auditor | SQLインジェクション・CORS・XSS等 |
| performance-engineer | DB接続・API効率・レンダリング |
| qa-expert | テストカバレッジ・分離・エッジケース |

## 結果：全5観点でエージェント分離方式が勝った

| 観点 | 勝者 |
|------|------|
| コード品質 | **spec-impl-tdd** |
| アーキテクチャ | **spec-impl-tdd** |
| セキュリティ | **spec-impl-tdd**（主にテスト面） |
| パフォーマンス | **spec-impl-tdd** |
| テスト品質 | **spec-impl-tdd** |

テスト数は **20件 vs 229件**（11.5倍）。しかも数だけじゃなくて、実装コードの設計品質そのものにも大きな差が出ました。

## なぜテスト数がここまで違うのか

ここが今回の検証で一番面白かったところです。

両方とも**同じtasks.md**を使っています。tasks.mdに明示的に書かれているテストタスクはバックエンドAPIテストだけ（T012〜T016, T024〜T025）で、**フロントエンドのテストタスクはゼロ**です。

speckit.implementはtasks.mdに忠実に従ったので、指示されたテストだけを書きました。当然の結果です。

一方、spec-impl-tddは全く違う動きをしました。各タスクに対してテストエージェントが先行するので、**全ての実装タスクに対してテストが自動的に生まれた**んです。

実際のコミットを見ると一目瞭然です。

```
T006の指示: 「database.pyを実装せよ」（テストの指示はない）

speckit.implement → database.py を作って終わり
spec-impl-tdd    → test_database.py (339行) を先に作る → database.py を作ってテストを通す
```

```
T020の指示: 「TodoFormコンポーネントを作れ」（テストの指示はない）

speckit.implement → TodoForm.tsx を作って終わり
spec-impl-tdd    → TodoForm.test.tsx (409行) を先に作る → TodoForm.tsx を作ってテストを通す
```

つまり、テストエージェントを分離するというアーキテクチャ自体が、「全ての実装にテストを伴わせる」構造を自然に作り出していたんです。tasks.mdに「テストを書け」と書いてあるかどうかは関係ない。**エージェント分離 = 全タスクへのTDD適用**になる、というのは作ってみて初めて気づいた発見でした。

## コードで見る品質差

テスト数だけじゃなく、実装コードにも明確な差が出ました。具体的に見ていきます。

### テストが設計を駆動した例：DB接続管理

**speckit.implement**: テストがモジュール内部のグローバル変数を直接書き換える

```python
# conftest.py - 内部実装に依存したテスト
import app.database as db_module
db_module.DB_PATH = TEST_DB_PATH  # グローバル変数をモンキーパッチ
```

**spec-impl-tdd**: テストエージェントが公開APIとしてのインターフェースを要求

```python
# conftest.py - 公開APIだけを使うクリーンなテスト
await init_db(test_db_path)   # パスを引数で渡せるAPI
yield client
await close_db()              # 明示的なリソース解放API
```

テストエージェントは実装を知らないので、「`init_db`にパスを渡したい」「`close_db`で後片付けしたい」という使う側の視点でテストを書きます。すると実装エージェントは、そのテストを通すためにテスタブルなAPIを設計せざるを得なくなる。**テストが設計を引っ張った**わかりやすい例です。

### エッジケースの発見力

同じPydanticモデルのテストでも、カバレッジに大きな差がありました。

**speckit.implement**: 基本パターン7件

```python
class TestTodoCreate:
    def test_valid_title(self)
    def test_title_required(self)
    def test_empty_string_rejected(self)
    def test_whitespace_only_rejected(self)
    # ... 計7件
```

**spec-impl-tdd**: 境界値・型安全まで網羅した16件

```python
class TestTodoCreate:
    def test_whitespace_only_tabs_rejected(self)      # タブ文字
    def test_whitespace_only_newlines_rejected(self)   # 改行文字
    def test_title_trimmed_with_tabs(self)             # タブのトリム
    def test_title_trimmed_then_validated_length(self)  # トリム後の長さ検証
    def test_title_none_rejected(self)                  # None入力
    def test_title_non_string_rejected(self)            # 整数入力
    # ... 計16件
```

実装を知ってるエージェントなら「Pydanticが弾いてくれるから大丈夫」とスキップしそうなケースも、実装を知らないテストエージェントはちゃんと書いてくれます。この「知らないからこそ厳しい」っていうのが、エージェント分離の一番のメリットかもしれません。

### フロントエンドの設計が根本的に変わった

一番差が出たのがここでした。

**speckit.implement**: 操作のたびにAPI全件再取得

```tsx
const handleToggle = async (id: number, completed: boolean) => {
    await updateTodo(id, { completed });
    await loadTodos();  // 毎回 GET /api/todos が走る
};

const handleDelete = async (id: number) => {
    await deleteTodo(id);
    await loadTodos();  // ここでも
};
```

**spec-impl-tdd**: APIレスポンスでローカル状態を差分更新

```tsx
const handleUpdated = (updatedTodo: Todo) => {
    setTodos((prev) =>
        prev.map((t) => (t.id === updatedTodo.id ? updatedTodo : t))
    );
};

const handleDeleted = (id: number) => {
    setTodos((prev) => prev.filter((t) => t.id !== id));
};
```

1操作あたりのAPIコール数が2回 vs 1回。なぜこうなったかというと、テストエージェントがコンポーネント単体テストを先に書く過程で、`onUpdated(updatedTodo: Todo)` というコールバックを先に定義したからなんですね。テストファーストで設計すると、「更新後のTodoオブジェクトを返す」というインターフェースが自然に生まれるので、全件再取得する必要がなくなるわけです。

他にも、こんな品質向上が見られました。

- **二重送信防止**: `isSubmitting`状態でボタンを無効化
- **CSS外部化**: インラインスタイルではなく`globals.css`に分離（`:hover`/`:disabled`が使える）
- **型安全性**: `FilterStatus` union型や `TodoCreate`/`TodoUpdate` interfaceで厳密に定義
- **アクセシビリティ**: `aria-current`や`role="alert"`の適切な使用

## speckit.implementのほうが良かった点

とはいえ、全部が全部spec-impl-tddが勝ちってわけでもなくて。

**開発速度は圧倒的にspeckit.implement**です。1コミットで全機能が動く状態まで到達するので、プロトタイピングなら間違いなくこっちが正解。

他にも良い点がありました。

- **コードが簡潔**: Pydanticの `Field(min_length=1, max_length=200)` は、手書きバリデーターより意図がわかりやすい
- **リクエストログが充実**: ミドルウェアで `request_started` / `request_completed` を記録してて、観測可能性はこっちのほうが上
- **mypy統合**: `pyproject.toml` に `pydantic-mypy` プラグインがちゃんと設定されてた

## なぜエージェント分離が効くのか

人間のTDDで品質が上がる理由って、「テストと実装の間にある健全な緊張関係」だと思うんです。テストが甘ければバグを見逃すし、厳しすぎれば実装が通らない。この押し引きが良い設計を生む。

AIでも同じことが起きてました。

**同一エージェントだと**：
- テストを書く時点で「こう実装するだろうな」っていう前提が入り込む
- テストが実装の追認になって、チェック機能として弱くなる
- tasks.mdに指示されたテストしか書かない

**エージェントを分けると**：
- テストエージェントは仕様だけを見てテストを書く
- **tasks.mdに指示がなくても、全タスクに対してテストが生まれる**
- 実装エージェントはテストをパスすることに集中する
- テストが外部仕様として機能して、設計を駆動する

同一エージェントのTDDは、自分で問題を作って自分で解くようなもの。エージェントを分けることで初めて、テストが「第三者の目」として機能するんですね。

## 全レビュー結果サマリー

| 観点 | speckit.implement | spec-impl-tdd | 差 |
|------|---------|-----|---|
| コード品質 | ○ | ◎ | 中〜大 |
| アーキテクチャ | ○ | ◎ | 中〜大 |
| セキュリティ | ○ | ○+ | 小 |
| パフォーマンス | △ | ◎ | 大 |
| テスト品質 | △ | ◎ | 大 |
| **開発速度** | **◎** | △ | 大 |
| **コードの簡潔さ** | **◎** | ○ | 中 |

## 試してみたい方へ：使い方

spec-impl-tddはGitHub Spec Kitと組み合わせて使います。仕様〜タスク分解まではSpec Kitのスキルをそのまま使い、実装フェーズだけ差し替えるイメージです。

```bash
# 1. GitHub Spec Kitをセットアップ済みのプロジェクトで

# 2. 仕様書を作る
/speckit.specify 「TODOアプリを作りたい」

# 3. 設計する
/speckit.plan

# 4. タスク分解する
/speckit.tasks

# 5. ここだけ差し替え！ speckit.implement の代わりに：
/spec-impl-tdd 001-todo-app
```

ステップ1〜4はSpec Kitの標準フロー。最後の実装だけ `/spec-impl-tdd` に差し替えるだけです。spec-impl-tddはSpec Kitが生成した `spec.md`、`plan.md`、`tasks.md`、`contracts/` をそのまま読み込んで、Red/Green/QAのサイクルを回してくれます。

特定のタスクだけ実行したい場合はタスクIDを指定できます。

```bash
/spec-impl-tdd 001-todo-app T012 T013 T014
```

スキルのソースコードは `.claude/skills/spec-impl-tdd/` にあるので、自分のプロジェクトに合わせてカスタマイズもできます。

## 課題：トークン消費と実行時間

ここまでspec-impl-tddの品質面での優位性を紹介してきましたが、正直なところ課題もあります。

エージェントを分離するということは、**全タスクでテストエージェントと実装エージェントの2回分のLLM呼び出しが走る**ということです。さらに各タスクにテストが自動生成されるので、生成されるコード量自体も大幅に増えます。

speckit.implementが1セッションで全タスクを処理するのに対し、spec-impl-tddはタスクごとにエージェントを2回起動するので、単純計算でもトークン消費量はかなり多くなります。今回の検証でもコミット数が1 vs 33+と大差がついている通り、実行時間にも相当な差が出ます。

品質が上がるのは嬉しいけど、毎回この量のトークンを使うのは現実的じゃない場面もありますよね。ここは今後の改善ポイントで、たとえば以下のようなアプローチを検討しています。

- **テストエージェントの軽量化**: テスト生成にはHaikuのような高速・低コストなモデルを使い、実装にはOpusを使う
- **差分テスト生成**: 変更のあったファイルに関連するテストだけを生成・更新する
- **テスト生成のキャッシュ**: 同一仕様に対するテストを再利用する仕組み

品質とコストのバランスをどう取るかは、これから詰めていく必要があります。

## まとめ

AIコーディングツールが「TDDできます」って言うとき、**そのTDDがどういうエージェント構造で動いてるか**を見てみると面白いです。

同じ仕様書、同じtasks.mdでも、テストと実装のエージェントを分けるだけで：

- テスト数が **20件 → 229件**（11.5倍）に増えた
- tasks.mdに指示のない**テストが全タスクに自動生成**された
- テストが設計を駆動して、**実装品質そのものが向上**した
- 5つの専門レビュアー全てで**エージェント分離方式が優位**と判定された

一方で、トークン消費量と実行時間は大幅に増えるので、用途に応じた使い分けが大事です。プロトタイプならspeckit.implementの一括実装、本番品質を目指すならエージェント分離方式、というのが現時点での使い分けかなと思います。

トークン効率の改善は今後の課題ですが、AIコーディングの品質が**モデルの性能だけでなくプロセスの設計で大きく変わる**というのは、今回の一番の学びでした。

## リポジトリ

今回の検証に使ったコード・スキル・仕様書は全て公開しています。

👉 **[GitHub リポジトリ](https://github.com/your-username/test-github-spec-kit)**

- **`main`ブランチ**: spec-impl-tdd（エージェント分離方式）の実装結果
- **`001-todo-app`ブランチ**: speckit.implement（同一エージェント方式）の実装結果

両ブランチを `git diff` で比較すれば、この記事で紹介した品質差を実際のコードで確認できます。spec-impl-tddスキル本体は `.claude/skills/spec-impl-tdd/` にあります。

---

*この記事のレビュー自体も、Claude Codeの5つの専門エージェントを並列実行して生成しています。AIが書いたコードをAIが審査する、なかなかメタな実験でした。*
