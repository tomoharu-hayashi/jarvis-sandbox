## コーディングにおけるコメントについて

- 必要箇所のみ、日本語でコメントを行う (英語が適切な場合を除く)

## 環境変数と秘密情報

- `make env-local` / `env-prod` — プロジェクト固有
- `make env-global` — 横断シークレット（bws global）
- CI 用は GitHub Secrets

## GitHub = SSOT（唯一の情報源）

プロジェクト管理において GitHub が唯一の信頼できる情報源である。

- タスク・進捗・決定事項は GitHub Issue/PR に残す
- ローカル状態ファイルは使わない
- どのセッションでも Issue を見れば続きが分かる状態を維持

### 情報の使い分け

- GitHub Issues/Projects — タスク、進捗、コンテキスト、一時的な手順
- GitHub Release — リリース内容・結果
- README/Makefile — 安定した使い方のみ（最小限に）
- MCP Brain — 学び、知見、再利用可能な経験
