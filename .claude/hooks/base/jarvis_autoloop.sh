#!/bin/bash
# JARVIS 無限ループ制御（ralph-wiggum 方式）
# Stop hook で JSON を出力し、プロンプトを再投入してループを継続

set -euo pipefail

STATE_FILE="${JARVIS_STATE_FILE:-.prompts/jarvis-state.local.md}"
CANCEL_FILE=".jarvis-cancel"

# stdin からフック入力を読み取り（使用しないが、パイプを空にする）
cat > /dev/null

# 状態ファイルがなければ何もしない
[ -f "$STATE_FILE" ] || exit 0

# 必要なコマンドの確認
command -v yq &>/dev/null || { echo "⚠️  JARVIS: yq が必要です" >&2; exit 0; }
command -v jq &>/dev/null || { echo "⚠️  JARVIS: jq が必要です" >&2; exit 0; }

# YAML フロントマターから値を取得
get_fm() {
    yq --front-matter=extract ".$1 // \"$2\"" "$STATE_FILE"
}

# YAML フロントマターの値を更新
set_fm() {
    yq --front-matter=process --inplace ".$1 = $2" "$STATE_FILE"
}

# 使用率チェック（5時間制限: 待機、週間制限: 停止）
check_rate_limit() {
    # macOS Keychain から Claude OAuth トークンを取得
    local token
    token=$(security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null | jq -r '.claudeAiOauth.accessToken' 2>/dev/null) || return 0
    [ -z "$token" ] && return 0

    # 設定値を取得
    local limit_5h=$(get_fm "rate_limit_5h" "80")
    local weekly_max=$(get_fm "rate_limit_weekly_max" "70")

    # API 呼び出し
    local response
    response=$(curl -s \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json" \
        -H "anthropic-beta: oauth-2025-04-20" \
        "https://api.anthropic.com/api/oauth/usage" 2>/dev/null) || return 0

    local five_hour_util=$(echo "$response" | jq -r '.five_hour.utilization // 0')
    local five_hour_resets=$(echo "$response" | jq -r '.five_hour.resets_at // empty')
    local seven_day_util=$(echo "$response" | jq -r '.seven_day.utilization // 0')
    local seven_day_resets=$(echo "$response" | jq -r '.seven_day.resets_at // empty')

    # 数値検証
    [[ "$five_hour_util" =~ ^[0-9.]+$ ]] || return 0
    [[ "$seven_day_util" =~ ^[0-9.]+$ ]] || return 0

    local current_epoch=$(date +%s)

    # 5時間制限チェック
    if (( $(echo "$five_hour_util > $limit_5h" | bc -l) )); then
        local reset_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${five_hour_resets%%+*}" +%s 2>/dev/null) || return 0
        local wait_seconds=$((reset_epoch - current_epoch))
        if [ "$wait_seconds" -gt 0 ]; then
            echo "⏳ JARVIS: 5時間制限 ${five_hour_util}% > ${limit_5h}%。${wait_seconds}秒待機..." >&2
            sleep "$wait_seconds"
        fi
    fi

    # 週間制限チェック（ペーシング）
    local reset_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${seven_day_resets%%+*}" +%s 2>/dev/null) || return 0
    local week_start=$((reset_epoch - 7 * 24 * 3600))
    local elapsed=$((current_epoch - week_start))
    local elapsed_ratio=$(echo "scale=4; $elapsed / (7 * 24 * 3600)" | bc -l)
    local allowed=$(echo "scale=2; $elapsed_ratio * $weekly_max" | bc -l)

    echo "📊 JARVIS: 5h=${five_hour_util}%/${limit_5h}%, 7d=${seven_day_util}%/${allowed}% (max=${weekly_max}%)" >&2

    if (( $(echo "$seven_day_util > $allowed" | bc -l) )); then
        echo "🛑 JARVIS: 週間制限ペース超過。ループを停止。" >&2
        set_fm "looping" "false"
        set_fm "last_status" "\"rate_limited\""
        exit 0
    fi
}

# 状態読み込み
looping=$(get_fm "looping" "false")

# looping=false なら何もしない（通常モード）
if [ "$looping" != "true" ]; then
    exit 0
fi

# キャンセルファイルチェック
if [ -f "$CANCEL_FILE" ]; then
    rm -f "$CANCEL_FILE"
    set_fm "looping" "false"
    echo "🛑 JARVIS: キャンセルファイルを検出。ループを停止。" >&2
    exit 0
fi

# 使用率チェック（5時間制限で待機、週間制限超過で停止）
check_rate_limit

# 残りの状態読み込み
iteration=$(get_fm "iteration" "1")
max_iter=$(get_fm "max_iterations" "50")
last_status=$(get_fm "last_status" "working")

# 数値検証
if [[ ! "$iteration" =~ ^[0-9]+$ ]]; then
    echo "⚠️  JARVIS: iteration が無効な値です: '$iteration'" >&2
    exit 0
fi
if [[ ! "$max_iter" =~ ^[0-9]+$ ]]; then
    echo "⚠️  JARVIS: max_iterations が無効な値です: '$max_iter'" >&2
    exit 0
fi

# 停止条件チェック
if [ "$last_status" = "complete" ] || [ "$last_status" = "awaiting_human" ]; then
    set_fm "looping" "false"
    echo "✅ JARVIS: $last_status でループを停止。" >&2
    exit 0
fi

if [ "$iteration" -ge "$max_iter" ]; then
    set_fm "looping" "false"
    echo "🛑 JARVIS: 最大反復回数（${max_iter}）に到達。ループを停止。" >&2
    exit 0
fi

# プロンプトを抽出（フロントマター後の本文）
PROMPT_TEXT=$(awk '/^---$/{i++; next} i>=2' "$STATE_FILE")

if [ -z "$PROMPT_TEXT" ]; then
    echo "⚠️  JARVIS: 状態ファイルにプロンプトがありません" >&2
    set_fm "looping" "false"
    exit 0
fi

# iteration をインクリメント
NEXT_ITERATION=$((iteration + 1))
set_fm "iteration" "$NEXT_ITERATION"

# 作業コンテキストを取得
current_issue=$(get_fm "current_issue" "null")
current_pr=$(get_fm "current_pr" "null")

# コンテキスト情報を構築（JARVIS:Context フォーマット）
CONTEXT_LINES="[JARVIS:Context]"
CONTEXT_LINES="${CONTEXT_LINES}\nIteration: ${NEXT_ITERATION}/${max_iter}"
if [ "$current_issue" != "null" ] && [ -n "$current_issue" ]; then
    CONTEXT_LINES="${CONTEXT_LINES}\nIssue: #${current_issue}"
fi
if [ "$current_pr" != "null" ] && [ -n "$current_pr" ]; then
    CONTEXT_LINES="${CONTEXT_LINES}\nPR: #${current_pr}"
fi
CONTEXT_MSG=$(echo -e "$CONTEXT_LINES")

# 停止をブロックしてプロンプトを再投入
echo "🔄 JARVIS iteration $NEXT_ITERATION/$max_iter" >&2

jq -n \
  --arg prompt "$PROMPT_TEXT" \
  --arg ctx "$CONTEXT_MSG" \
  '{
    "decision": "block",
    "reason": $prompt,
    "systemMessage": $ctx
  }'

exit 0
