# テンプレートマージ

dev-tools テンプレートの更新をプロジェクトにマージする。

## 背景

- **dev-tools**: AI設定・プロンプトを一元管理するテンプレートリポジトリ
- **`.devtools/`**: `setup.sh -i` でコピーされたテンプレート原本（参照用、直接編集しない）

## 自動判定ルール

| 条件 | コピー方式 |
|------|-----------|
| `**/base/*` にマッチ | 削除同期（setup.sh -i で自動処理） |
| `.ruff_cache/` 配下 | 除外（キャッシュ） |
| 上記以外 | マージ対象（このコマンドで処理） |

## 対象ファイル

### 削除同期（setup.sh -i で自動処理）

- `.prompts/commands/base/`, `.prompts/agents/base/`, `.prompts/skills/base/`
- `.claude/hooks/base/`, `.cursor/hooks/base/`
- `.shared/base/`
- `scripts/base/`

### マージ対象（このコマンドで処理）

| ファイル | 方式 |
|----------|------|
| `Makefile` | マーカー方式（`BASE`/`LOCAL` セクション） |
| `pyproject.toml` | マーカー方式（存在時） |
| `.claude/settings.json` | JSON 差分マージ |
| `.cursor/hooks.json` | JSON 差分マージ |
| `.vscode/tasks.json` | 差分表示 → 確認 |
| `scripts/*.sh`（base/ 外） | 差分表示 → 確認 |

## 手順

### 1. マージ対象ファイルの検出

```bash
# マージ対象ファイルを自動検出（base/ 以外、キャッシュ除外）
find .devtools -type f \
  -not -path '**/base/*' \
  -not -path '.devtools/.prompts/*' \
  -not -path '.devtools/.ruff_cache/*' \
  2>/dev/null
```

### 2. 差分確認・報告

各マージ対象ファイルについて差分を確認:

```bash
# 各ファイルの差分
diff .devtools/<file> <file> 2>/dev/null
```

報告フォーマット:

```markdown
## マージ対象ファイルの差分

### マーカー方式

#### Makefile
- BASE セクションの変更点

#### pyproject.toml（存在時）
- BASE セクションの変更点

### JSON ファイル

#### .claude/settings.json
- 変更点の要約（hooks パスの更新など）

#### .cursor/hooks.json
- 変更点の要約

### その他

#### .vscode/tasks.json
- 差分の要約
```

### 3. マージ実行

**マーカー方式** (Makefile, pyproject.toml):

- `BASE` セクション（`# ==== BASE ====` 〜 `# ==== LOCAL ====`）のみマージ
- `LOCAL` セクションは保持

**JSON ファイル** (.claude/settings.json, .cursor/hooks.json):

1. 差分を表示
2. ユーザーに確認
3. 承認されたら `.devtools/` から上書き

**その他のファイル**:

1. 差分を表示
2. ユーザーに確認
3. 承認されたら `.devtools/` から上書き、または手動マージ

### 4. sync_rules 実行

マージ完了後、各AIツールに反映:

```bash
bash <(gh api repos/thayashi-naruse/dev-tools/contents/setup.sh --jq '.content' | base64 -d) -s
```

または:

```bash
./setup.sh -s
```

## 注意

- `.devtools/` は直接編集しない（`setup.sh -i` で上書きされる）
- カスタマイズは各ファイルの適切な場所で行う:
  - `Makefile`: `LOCAL` セクション
  - `.prompts/`: `base/` 外のファイル
  - `.claude/hooks/`: `base/` 外のスクリプト
- `AGENTS.local.md` はプロジェクト固有ルール用（テンプレートに含まれない）
