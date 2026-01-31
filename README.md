# Taska

AI アシスト付きのシンプルなタスク管理 Web アプリ。

## 特徴

- **シンプル UI**: 余計な機能を排除した直感的なインターフェース
- **AI 分類**: タスク入力時にカテゴリ・優先度を自動判定
- **スマート提案**: 今やるべきタスクを AI が提案
- **自然言語入力**: 「明日までに報告書」で期限付きタスク作成

## 技術スタック

- **Frontend**: Next.js 15 (App Router) + TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **Backend**: Next.js API Routes
- **Database**: Neon (PostgreSQL) + Drizzle ORM
- **AI**: Vercel AI SDK + OpenAI
- **Infrastructure**: Vercel

## ロードマップ

### Phase 1: MVP

- [ ] タスク CRUD（作成・表示・更新・削除）
- [ ] シンプルなリスト UI
- [ ] 完了/未完了の切り替え

### Phase 2: AI 機能

- [ ] 自然言語でタスク入力
- [ ] カテゴリ・優先度の自動判定
- [ ] 次にやるべきタスクの提案

## 開発

```bash
make deps    # 依存インストール
make run     # 開発サーバー起動
make test    # テスト実行
make lint    # リント
```

## ライセンス

MIT
