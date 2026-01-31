# Cloud Run デプロイ手順

FastAPI バックエンドを Google Cloud Run にデプロイする手順。

## 前提条件

- Google Cloud SDK (gcloud) インストール済み
- プロジェクトが設定済み (`gcloud config set project <PROJECT_ID>`)
- Cloud Run API と Artifact Registry API が有効化済み

## 環境変数

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `USE_FIRESTORE` | Firestore を使用する場合 `true` | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS` | サービスアカウントキーのパス（ローカル用） | No |
| `OPENAI_API_KEY` | OpenAI API キー | Yes |

Cloud Run では、同一プロジェクトの Firestore に自動認証されるため `GOOGLE_APPLICATION_CREDENTIALS` は不要。

## デプロイ手順

### 1. Artifact Registry にリポジトリを作成（初回のみ）

```bash
gcloud artifacts repositories create smarttodo \
    --repository-format=docker \
    --location=asia-northeast1 \
    --description="SmartTodo Docker images"
```

### 2. Docker イメージをビルド・プッシュ

```bash
cd smarttodo

# Cloud Build でビルド（推奨）
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/<PROJECT_ID>/smarttodo/api:latest

# または、ローカルでビルドしてプッシュ
docker build -t asia-northeast1-docker.pkg.dev/<PROJECT_ID>/smarttodo/api:latest .
docker push asia-northeast1-docker.pkg.dev/<PROJECT_ID>/smarttodo/api:latest
```

### 3. Cloud Run にデプロイ

```bash
gcloud run deploy smarttodo-api \
    --image asia-northeast1-docker.pkg.dev/<PROJECT_ID>/smarttodo/api:latest \
    --region asia-northeast1 \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars "USE_FIRESTORE=true,OPENAI_API_KEY=<YOUR_API_KEY>" \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10
```

### 4. デプロイ確認

```bash
# サービス URL を取得
gcloud run services describe smarttodo-api --region asia-northeast1 --format 'value(status.url)'

# ヘルスチェック
curl <SERVICE_URL>/health
```

## Secrets Manager を使用する場合（推奨）

API キーを環境変数に直接設定するのではなく、Secrets Manager を使用する。

### 1. シークレットを作成

```bash
echo -n "<YOUR_OPENAI_API_KEY>" | gcloud secrets create openai-api-key --data-file=-
```

### 2. Cloud Run サービスアカウントに権限を付与

```bash
gcloud secrets add-iam-policy-binding openai-api-key \
    --member="serviceAccount:<PROJECT_NUMBER>-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 3. シークレットを参照してデプロイ

```bash
gcloud run deploy smarttodo-api \
    --image asia-northeast1-docker.pkg.dev/<PROJECT_ID>/smarttodo/api:latest \
    --region asia-northeast1 \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars "USE_FIRESTORE=true" \
    --set-secrets "OPENAI_API_KEY=openai-api-key:latest" \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10
```

## ローカルでの Docker テスト

```bash
cd smarttodo

# ビルド
docker build -t smarttodo-api .

# 起動（インメモリモード）
docker run -p 8080:8080 smarttodo-api

# 起動（Firestore 使用）
docker run -p 8080:8080 \
    -e USE_FIRESTORE=true \
    -e GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json \
    -e OPENAI_API_KEY=<YOUR_API_KEY> \
    -v /path/to/credentials.json:/app/credentials.json:ro \
    smarttodo-api

# ヘルスチェック
curl http://localhost:8080/health
```

## トラブルシューティング

### コンテナが起動しない

```bash
# ログを確認
gcloud run services logs read smarttodo-api --region asia-northeast1 --limit 50
```

### Firestore に接続できない

- Cloud Run サービスアカウントに Firestore への権限があるか確認
- 同一プロジェクト内であれば自動認証される

### メモリ不足

- `--memory` オプションで増やす（例: `1Gi`）
