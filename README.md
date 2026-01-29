# SmartTodo

AI アシスタント機能を搭載した次世代 Todo アプリ。

## 特徴

- **AI タスク提案**: 過去のタスクパターンから次にやるべきことを提案
- **自然言語入力**: 「明日の会議の準備」と入力するだけでタスク作成
- **スマートリマインダー**: ユーザーの行動パターンを学習して最適なタイミングで通知
- **優先度自動判定**: タスクの緊急度・重要度を AI が自動判定

## 技術スタック

- **Backend**: Python (FastAPI)
- **Frontend**: React + TypeScript
- **Database**: PostgreSQL
- **AI/ML**: OpenAI API, LangChain
- **Infrastructure**: Docker, AWS

## セットアップ

```bash
# 依存関係のインストール
make deps

# 開発サーバー起動
make run

# テスト実行
make test
```

## 開発

```bash
# フォーマット
make fmt

# リント
make lint
```

## ディレクトリ構成

```
smarttodo/
├── src/
│   ├── main.py          # アプリケーションエントリポイント
│   ├── api/             # API エンドポイント
│   ├── models/          # データモデル
│   ├── services/        # ビジネスロジック
│   └── ai/              # AI 機能
├── frontend/            # React フロントエンド
├── tests/               # テストコード
└── docs/                # ドキュメント
```

## ロードマップ

- [x] 基本的な Todo CRUD
- [ ] AI タスク提案機能
- [ ] 自然言語入力
- [ ] スマートリマインダー
- [ ] モバイルアプリ対応

## ライセンス

MIT
