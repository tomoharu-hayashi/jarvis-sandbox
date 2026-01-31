#!/usr/bin/env bash
# bws global プロジェクトからシークレットを環境変数として注入
# 用途: CLAUDE_OAUTH_TOKEN など、プロジェクト横断で使う値
# プレフィックスなしで全シークレットを環境変数として export
set -euo pipefail

if [[ "${1:-}" == "--" ]]; then
  shift
fi
if [[ "$#" -eq 0 ]]; then
  echo "CMD is required. e.g. make env-global CMD='echo \$CLAUDE_OAUTH_TOKEN'" >&2
  exit 1
fi

project_name="global"

project_id="$(bws project list --output json | python3 -c 'import json, sys; name=sys.argv[1]; data=json.load(sys.stdin); items=data.get("data") if isinstance(data, dict) else data; items=items if isinstance(items, list) else []; print(next((p.get("id","") for p in items if p.get("name")==name), ""), end="")' "$project_name")" || {
  echo "bws project list failed" >&2
  exit 1
}

if [[ -z "$project_id" ]]; then
  echo "bws project not found: $project_name" >&2
  exit 1
fi

# シークレットを取得（なければスキップ）
secrets_output=$(bws secret list "$project_id" --output env 2>/dev/null) || {
  # シークレットがない場合は警告を出してそのまま続行
  echo "⚠️ bws global: シークレットなし（スキップ）" >&2
  exec "$@"
}

# プレフィックスなしで全シークレットを環境変数として export
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  # export KEY="VALUE" 形式を KEY=VALUE に変換
  if [[ "$line" =~ ^export\ (.+)$ ]]; then
    line="${BASH_REMATCH[1]}"
  fi
  # シェルの変数として export
  export "$line"
done <<< "$secrets_output"

exec "$@"
