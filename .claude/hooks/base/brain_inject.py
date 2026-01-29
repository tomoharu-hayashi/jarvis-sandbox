#!/usr/bin/env python3
"""beforeSubmitPrompt Hook: Brain自動コンテキスト注入（Lazy Loading版）"""

import json
import os
import sys
from pathlib import Path


def _configure_pycache_prefix() -> None:
    dev_tools_path = os.environ.get("DEV_TOOLS_PATH", "~/pj/my/dev-tools")
    sys.pycache_prefix = str(Path(dev_tools_path).expanduser() / ".cache" / "pycache")


def main() -> None:
    _configure_pycache_prefix()
    from brain_client import detect_project, search_summaries

    data = json.load(sys.stdin)
    prompt = data.get("prompt", "")

    project = detect_project()
    summaries = search_summaries(prompt, project=project, limit=3)
    if not summaries:
        return

    lines = ["[System:Knowledge]", "関連する過去の知識（参考情報。関連性が低ければ無視してよい）:"]
    for s in summaries:
        score_pct = int(s["score"] * 100) if s["score"] else 0
        desc = s["description"] or "(説明なし)"
        lines.append(f"- **{s['name']}** ({score_pct}%): {desc}")

    lines.append("")
    lines.append("有用な場合のみ `mcp__brain__get(name)` で詳細を取得。不要なら無視。")

    sys.stdout.write("\n".join(lines))


if __name__ == "__main__":
    main()
