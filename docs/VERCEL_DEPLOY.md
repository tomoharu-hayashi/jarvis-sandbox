# Vercel デプロイガイド

フロントエンド（Next.js 16）をVercelにデプロイする手順。

## 前提条件

- Vercelアカウント
- GitHubリポジトリへのアクセス権

## 初回セットアップ

### 1. Vercelプロジェクトの作成

1. [Vercel Dashboard](https://vercel.com/dashboard) にアクセス
2. 「Add New...」 > 「Project」をクリック
3. GitHubリポジトリを選択
4. 以下を設定:
   - **Framework Preset**: Next.js（自動検出）
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`（デフォルト）
   - **Install Command**: `npm install`（デフォルト）

### 2. 環境変数の設定

Vercel Dashboard > Project Settings > Environment Variables で以下を設定。

| 変数名 | 説明 | Production | Preview | Development |
|--------|------|:----------:|:-------:|:-----------:|
| `NEXT_PUBLIC_API_URL` | バックエンドAPIのURL | 必須 | 必須 | 任意 |

#### 設定例

**Production環境:**

```
NEXT_PUBLIC_API_URL=https://api.example.com
```

**Preview環境（PRプレビュー用）:**

```
NEXT_PUBLIC_API_URL=https://api-staging.example.com
```

#### 環境変数の追加手順

1. Vercel Dashboard でプロジェクトを開く
2. 「Settings」タブ > 「Environment Variables」
3. 「Add New」をクリック
4. Key/Valueを入力
5. 対象環境（Production/Preview/Development）を選択
6. 「Save」をクリック

> **注意**: `NEXT_PUBLIC_` プレフィックスの変数はクライアントサイドに公開されます。機密情報は含めないでください。

## デプロイ方法

### 自動デプロイ（推奨）

GitHubリポジトリ連携後、以下が自動で行われる:

- **Production**: `main`ブランチへのpushで自動デプロイ
- **Preview**: PRごとにプレビュー環境が自動作成

### 手動デプロイ

Vercel CLIを使用:

```bash
# Vercel CLIのインストール
npm i -g vercel

# ログイン
vercel login

# プレビューデプロイ
cd frontend
vercel

# 本番デプロイ
vercel --prod
```

## PRプレビューデプロイ

PRを作成すると自動的にプレビュー環境がデプロイされる。

- PRのコメントにプレビューURLが投稿される
- 例: `https://taska-git-feature-xxx-team.vercel.app`
- PRを更新するたびにプレビューも更新される

### プレビューデプロイの確認

1. PRページでVercel botのコメントを確認
2. 「Visit Preview」リンクをクリック
3. 動作確認後、マージ

## トラブルシューティング

### ビルドエラー

```bash
# ローカルでビルド確認
cd frontend
npm run build
```

### 環境変数が反映されない

1. Vercel Dashboardで変数が正しく設定されているか確認
2. 変数名が`NEXT_PUBLIC_`で始まっているか確認（クライアント側で使用する場合）
3. 再デプロイを実行

### API接続エラー

- `NEXT_PUBLIC_API_URL`が正しいか確認
- CORS設定がバックエンドで許可されているか確認
