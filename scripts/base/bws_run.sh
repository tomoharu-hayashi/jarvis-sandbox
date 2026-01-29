#!/usr/bin/env bash
set -euo pipefail

env="${1:-}"
if [[ "$env" != "local" && "$env" != "prod" ]]; then
  echo "usage: bws_run.sh <local|prod> -- <cmd>" >&2
  exit 1
fi
shift
if [[ "${1:-}" == "--" ]]; then
  shift
fi
if [[ "$#" -eq 0 ]]; then
  echo "CMD is required. e.g. make env-local CMD='node app.js'" >&2
  exit 1
fi

project_name="global"
repo_root="$(git rev-parse --show-toplevel 2>/dev/null)"
if [[ -z "$repo_root" ]]; then
  echo "git repo not found" >&2
  exit 1
fi
repo_key="$(basename "$repo_root" | tr '[:lower:]' '[:upper:]' | sed 's/[^A-Z0-9]/_/g')"

case "$env" in
  local)
    prefix="${repo_key}__LOCAL__"
    env_files=(.env.local .env)
    ;;
  prod)
    prefix="${repo_key}__PROD__"
    env_files=(.env.prod .env)
    ;;
esac

project_id="$(bws project list --output json | python3 -c 'import json, sys; name=sys.argv[1]; data=json.load(sys.stdin); items=data.get("data") if isinstance(data, dict) else data; items=items if isinstance(items, list) else []; print(next((p.get("id","") for p in items if p.get("name")==name), ""), end="")' "$project_name")" || {
  echo "bws project list failed" >&2
  exit 1
}

if [[ -z "$project_id" ]]; then
  echo "bws project not found: $project_name" >&2
  exit 1
fi

if ! bws secret list "$project_id" --output env >/dev/null; then
  echo "bws secret list failed" >&2
  exit 1
fi

bws_env_args=()
while IFS= read -r entry; do
  [[ -z "$entry" ]] && continue
  bws_env_args+=("-e" "$entry")
done < <(bws secret list "$project_id" --output env | python3 -c 'import shlex, sys; prefix=sys.argv[1]; 
for line in sys.stdin:
    line=line.strip()
    if not line:
        continue
    if line.startswith("export "):
        line=line[7:]
    try:
        parts=shlex.split(line, posix=True)
    except ValueError:
        continue
    if not parts:
        continue
    assign=parts[0]
    if "=" not in assign:
        continue
    key, val = assign.split("=", 1)
    if not key.startswith(prefix):
        continue
    print(f"{key[len(prefix):]}={val}")
' "$prefix")

dotenvx run "${bws_env_args[@]}" -f "${env_files[@]}" -- "$@"
