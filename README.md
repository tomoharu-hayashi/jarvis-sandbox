# Taska

AI アシスト付きのシンプルなタスク管理 Web アプリ。

## 特徴

- **シンプル UI**: 余計な機能を排除した直感的なインターフェース
- **AI 分類**: タスク入力時にカテゴリ・優先度を自動判定
- **スマート提案**: 今やるべきタスクを AI が提案
- **自然言語入力**: 「明日までに報告書」で期限付きタスク作成

## 技術スタック

- **Frontend**: Next.js 16 (App Router) + TypeScript + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI + Python 3.11+
- **Database**: Firebase Firestore
- **AI**: OpenAI GPT-4
- **Infrastructure**: Vercel / Cloud Run

## ロードマップ

### Phase 1: MVP

- [x] タスク CRUD API（作成・表示・更新・削除）
- [x] Firebase Firestore による永続化
- [x] シンプルなリスト UI
- [x] 完了/未完了の切り替え

### Phase 2: AI 機能

- [x] 自然言語でタスク入力（API）
- [x] 優先度の自動判定
- [x] 次にやるべきタスクの提案 API

## 開発

```bash
make deps        # 依存インストール（全体）
make deps-api    # 依存インストール（API）
make deps-web    # 依存インストール（Web）

make run         # 開発サーバー起動（API + Web並列）
make run-api     # APIサーバー起動（ポート8000）
make run-web     # Webサーバー起動（ポート3001）

make test        # テスト実行
make lint        # リント
make build-web   # Webビルド
```

## 環境変数

**API（Cloud Run）**:

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `USE_FIRESTORE` | `true`で Firestore 使用、それ以外でインメモリ | No |
| `GOOGLE_APPLICATION_CREDENTIALS` | Firebase サービスアカウント JSON パス | Firestore 使用時 |
| `OPENAI_API_KEY` | OpenAI API キー | AI 機能使用時 |
| `CORS_ORIGINS` | 許可するオリジン（カンマ区切り） | 本番時 |

**Frontend（Vercel）**:

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `NEXT_PUBLIC_API_URL` | API のベース URL（デフォルト: <http://localhost:8000）> | 本番時 |

## デプロイ

**Frontend（Vercel）**:

1. Vercel にプロジェクトをインポート
2. ルートディレクトリを `frontend` に設定
3. 環境変数 `NEXT_PUBLIC_API_URL` に Cloud Run の API URL を設定

**API（Cloud Run）**:

1. GCP プロジェクトを作成し、Firestore を有効化
2. Cloud Run にデプロイ:

```bash
cd smarttodo
gcloud run deploy smarttodo-api \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars "USE_FIRESTORE=true,CORS_ORIGINS=https://your-app.vercel.app"
```

1. シークレットを設定（Secret Manager 推奨）:
   - `OPENAI_API_KEY`
   - `GOOGLE_APPLICATION_CREDENTIALS`

## ライセンス

MIT
