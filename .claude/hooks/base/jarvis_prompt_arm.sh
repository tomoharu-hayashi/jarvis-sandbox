#!/bin/bash
# JARVIS 起動制御 (UserPromptSubmit hook)
# /jarvis で始まるコマンドで looping: true、それ以外で looping: false

set -euo pipefail

STATE_FILE="${JARVIS_STATE_FILE:-.prompts/jarvis-state.local.md}"

# 状態ファイルがなければ何もしない
[ -f "$STATE_FILE" ] || exit 0

# yq が必要
command -v yq &>/dev/null || exit 0

# stdin から入力を読み取り
INPUT=$(cat)

# プロンプトを抽出
PROMPT=$(echo "$INPUT" | jq -r '.prompt // ""' 2>/dev/null || echo "")

# /jarvis_agent から task を抽出
if [[ "$PROMPT" =~ ^/jarvis_agent[[:space:]]*(.*) ]]; then
    TASK_TEXT="${BASH_REMATCH[1]}"
    CURRENT_LOOPING=$(yq --front-matter=extract '.looping // "false"' "$STATE_FILE" 2>/dev/null || echo "false")

    if [ "$CURRENT_LOOPING" != "true" ]; then
        TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

        # task の設定（空なら null、文字列ならエスケープして設定）
        if [ -n "$TASK_TEXT" ]; then
            ESCAPED_TASK=$(echo "$TASK_TEXT" | sed 's/"/\\"/g')
            yq --front-matter=process -i "
                .looping = true |
                .iteration = 1 |
                .started_at = \"$TIMESTAMP\" |
                .last_status = \"working\" |
                .task = \"$ESCAPED_TASK\"
            " "$STATE_FILE"
            echo "🚀 JARVIS: 起動（目的達成モード）" >&2
        else
            yq --front-matter=process -i "
                .looping = true |
                .iteration = 1 |
                .started_at = \"$TIMESTAMP\" |
                .last_status = \"working\" |
                .task = null
            " "$STATE_FILE"
            echo "🚀 JARVIS: 起動（自律モード）" >&2
        fi
    fi
elif [[ "$PROMPT" =~ ^/jarvis ]]; then
    # 他の /jarvis コマンド（/jarvis_diagnose 等）は従来通り
    CURRENT_LOOPING=$(yq --front-matter=extract '.looping // "false"' "$STATE_FILE" 2>/dev/null || echo "false")

    if [ "$CURRENT_LOOPING" != "true" ]; then
        TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        yq --front-matter=process -i "
            .looping = true |
            .iteration = 1 |
            .started_at = \"$TIMESTAMP\" |
            .last_status = \"working\"
        " "$STATE_FILE"
        echo "🚀 JARVIS: 起動" >&2
    fi
else
    # 通常モード: looping を false に
    CURRENT_LOOPING=$(yq --front-matter=extract '.looping // "false"' "$STATE_FILE" 2>/dev/null || echo "false")

    if [ "$CURRENT_LOOPING" = "true" ]; then
        yq --front-matter=process -i '.looping = false' "$STATE_FILE"
        echo "⏹️  JARVIS: 停止（別コマンド検出）" >&2
    fi
fi

exit 0
