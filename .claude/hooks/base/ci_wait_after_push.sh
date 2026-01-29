#!/bin/bash
# PostToolUse hook: git push 後に CI 完了を待機
# 入力: stdin から JSON（環境変数ではない）
# 出力: exit 0 で stdout 表示、exit 2 で stderr を Claude にフィードバック

set -euo pipefail

# stdin から JSON を読み取る
INPUT_JSON=$(cat)

# tool_name を確認（Bash 以外はスキップ）
TOOL_NAME=$(echo "$INPUT_JSON" | jq -r '.tool_name // empty' 2>/dev/null || true)
if [ "$TOOL_NAME" != "Bash" ]; then
    exit 0
fi

# コマンドを抽出
COMMAND=$(echo "$INPUT_JSON" | jq -r '.tool_input.command // empty' 2>/dev/null || true)

# git push を含まない場合は何もしない
if [ -z "$COMMAND" ] || ! echo "$COMMAND" | grep -q 'git push'; then
    exit 0
fi

# PR が存在するか確認
PR="$(gh pr view --json number --jq .number 2>/dev/null || true)"

if [ -z "$PR" ]; then
    # PR がない場合はスキップ
    exit 0
fi

# CI 待機を実行
WAIT="${CI_WAIT_INTERVAL:-30}"
TIMEOUT="${CI_WAIT_TIMEOUT:-600}"

echo "🔄 git push 検知。PR #$PR の CI 完了を待機..." >&2

start_time=$(date +%s)
while :; do
    now=$(date +%s)
    elapsed=$((now - start_time))
    if [ "$elapsed" -ge "$TIMEOUT" ]; then
        echo "⏰ CI 待機タイムアウト（${TIMEOUT}秒）" >&2
        exit 2
    fi

    checks_json=$(gh pr checks "$PR" --json name,bucket,link 2>/dev/null || echo '[]')
    pending=$(echo "$checks_json" | jq '[.[] | select(.bucket=="pending")] | length')
    fail=$(echo "$checks_json" | jq '[.[] | select(.bucket=="fail" or .bucket=="cancel")] | length')

    if [ "$pending" -eq 0 ]; then
        echo "---" >&2
        echo "$checks_json" | jq -r '.[] | "\(.bucket)\t\(.name)"' >&2
        echo "---" >&2
        if [ "$fail" -gt 0 ]; then
            echo "❌ CI 失敗。以下のチェックを確認して修正が必要:" >&2
            echo "$checks_json" | jq -r '.[] | select(.bucket=="fail" or .bucket=="cancel") | "- \(.name): \(.link)"' >&2
        else
            echo "✅ CI 完了。すべてのチェックが成功。" >&2
        fi
        exit 2
    fi

    echo "⏳ 保留中: $pending 件" >&2
    sleep "$WAIT"
done
