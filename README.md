# jarvis-sandbox

JARVIS E2E テスト用のサンドボックスリポジトリ。

## 目的

- JARVIS システムの hooks、状態管理、自動ループをテスト
- Issue → 実装 → PR → マージの完全フローを検証
- Claude Code の `-p` モードでの動作確認

## セットアップ

```bash
# dev-tools からテンプレートを適用
bash <(gh api repos/thayashi-naruse/dev-tools/contents/setup.sh --jq '.content' | base64 -d) -i
```

## テスト実行

### 手動テスト（別ターミナル）

```bash
cd /path/to/jarvis-sandbox

# 基本的な -p モードテスト
claude -p "src/main.py の内容を説明して" --allowedTools "Read"

# JARVIS ループテスト
claude -p "/jarvis_agent Issue #1 を実装" --dangerously-skip-permissions
```

### 観察

```bash
# 状態ファイルを監視
watch -n 1 cat .prompts/jarvis-state.local.md

# hooks ログを監視
tail -f /tmp/jarvis_hook.log
```

## 構造

```
jarvis-sandbox/
├── .claude/              # Claude Code 設定 & hooks
├── .prompts/             # JARVIS 状態 & エージェントプロンプト
├── scripts/base/         # 共有スクリプト
├── src/                  # テスト用ダミーコード
│   ├── main.py
│   └── test_main.py
└── Makefile
```
