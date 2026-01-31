# Taska

AI アシスト付きのシンプルなタスク管理 Web アプリ。

## 特徴

- **シンプル UI**: 余計な機能を排除した直感的なインターフェース
- **AI 分類**: タスク入力時にカテゴリ・優先度を自動判定
- **スマート提案**: 今やるべきタスクを AI が提案
- **自然言語入力**: 「明日までに報告書」で期限付きタスク作成

## 技術スタック

- **Backend**: FastAPI + Python 3.11+
- **Database**: Firebase Firestore
- **AI**: OpenAI GPT-4
- **Infrastructure**: Vercel / Cloud Run

## ロードマップ

### Phase 1: MVP

- [x] タスク CRUD API（作成・表示・更新・削除）
- [x] Firebase Firestore による永続化
- [ ] シンプルなリスト UI
- [ ] 完了/未完了の切り替え

### Phase 2: AI 機能

- [x] 自然言語でタスク入力（API）
- [x] 優先度の自動判定
- [x] 次にやるべきタスクの提案 API

## 開発

```bash
make deps    # 依存インストール
make run     # 開発サーバー起動
make test    # テスト実行
make lint    # リント
```

## 環境変数

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `USE_FIRESTORE` | `true`で Firestore 使用、それ以外でインメモリ | No |
| `GOOGLE_APPLICATION_CREDENTIALS` | Firebase サービスアカウント JSON パス | Firestore 使用時 |
| `OPENAI_API_KEY` | OpenAI API キー | AI 機能使用時 |

## ライセンス

MIT
