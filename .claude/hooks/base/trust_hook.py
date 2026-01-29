#!/usr/bin/env python3
"""UserPromptSubmit Hook: Trust score update + info injection."""

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

# チェックポイント定義（JARVIS.md 仕様）
CHECKPOINTS = {
    "Junior": [
        "Issue作成前",
        "PR作成前",
        "マージ前",
        "リリース前",
        "外部発信前",
        "仕様修正/削除前",
    ],
    "Senior": ["マージ前", "リリース前", "外部発信前", "仕様修正/削除前"],
    "Lead": ["リリース前", "外部発信前", "仕様修正/削除前"],
    "Principal": ["外部発信前", "仕様修正/削除前"],
}

# パターンマッチ（承認/介入検出）
APPROVE_PATTERN = re.compile(r"続けて|OK|いいね|進めて|LGTM", re.IGNORECASE)
REJECT_PATTERN = re.compile(r"違う|やり直|ダメ|待って|やめ")
PROMOTE_PATTERN = re.compile(r"/jarvis\s+promote", re.IGNORECASE)
DENY_PATTERN = re.compile(r"/jarvis\s+deny", re.IGNORECASE)

STATE_FILE = Path(".prompts/jarvis-state.local.md")


def get_level(trust: int) -> str:
    """信頼スコアからレベルを算出."""
    if trust >= 75:
        return "Principal"
    if trust >= 50:
        return "Lead"
    if trust >= 30:
        return "Senior"
    return "Junior"


LEVELS = ["Junior", "Senior", "Lead", "Principal"]


def get_level_index(level: str) -> int:
    """レベルのインデックスを返す."""
    try:
        return LEVELS.index(level)
    except ValueError:
        return 0


def get_next_level(current_level: str) -> str | None:
    """次のレベルを返す. Principal なら None."""
    idx = get_level_index(current_level)
    return LEVELS[idx + 1] if idx < len(LEVELS) - 1 else None


def read_frontmatter(path: Path) -> dict:
    """状態ファイルの frontmatter を読み取り."""
    content = path.read_text()
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if match:
        return yaml.safe_load(match.group(1)) or {}
    return {}


def write_frontmatter(path: Path, fm: dict) -> None:
    """状態ファイルの frontmatter を更新."""
    content = path.read_text()
    match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    body = match.group(2) if match else content
    new_fm = yaml.dump(
        fm, allow_unicode=True, default_flow_style=False, sort_keys=False
    )
    path.write_text(f"---\n{new_fm}---\n{body}")


def calculate_audit_decay(last_touch: str | None) -> int:
    """未監査減衰を計算. 24h超で -1/日."""
    if not last_touch:
        return 0
    try:
        last_dt = datetime.fromisoformat(last_touch.replace("Z", "+00:00"))
        now = datetime.now(UTC)
        hours = (now - last_dt).total_seconds() / 3600
        if hours > 24:
            return int((hours - 24) // 24) + 1
        return 0
    except (ValueError, TypeError):
        return 0


def main() -> None:
    if not STATE_FILE.exists():
        return

    # stdin から payload を読み取り
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        payload = {}
    user_prompt = payload.get("prompt", "")

    fm = read_frontmatter(STATE_FILE)
    trust = fm.get("trust", 15)
    level = fm.get("level", get_level(trust))
    last_status = fm.get("last_status", "working")
    pending_promotion = fm.get("pending_promotion")
    last_human_touch_at = fm.get("last_human_touch_at")

    now_iso = datetime.now(UTC).isoformat()

    # 昇格コマンド処理
    if PROMOTE_PATTERN.search(user_prompt):
        if pending_promotion:
            fm["level"] = pending_promotion
            fm["pending_promotion"] = None
            fm["last_human_touch_at"] = now_iso
            write_frontmatter(STATE_FILE, fm)
            sys.stdout.write(
                f"[JARVIS Trust] 昇格承認: {level} → {pending_promotion}\n"
            )
            return
        else:
            sys.stdout.write("[JARVIS Trust] 昇格待ちがありません\n")
            return

    # 昇格却下コマンド処理
    if DENY_PATTERN.search(user_prompt):
        if pending_promotion:
            fm["pending_promotion"] = None
            fm["last_human_touch_at"] = now_iso
            write_frontmatter(STATE_FILE, fm)
            sys.stdout.write(f"[JARVIS Trust] 昇格却下: {pending_promotion}\n")
            return
        else:
            sys.stdout.write("[JARVIS Trust] 昇格待ちがありません\n")
            return

    # awaiting_human 時のみスコア更新（チェックポイント停止後の人間再開）
    if last_status == "awaiting_human":
        if APPROVE_PATTERN.search(user_prompt):
            trust = min(100, trust + 2)
        elif REJECT_PATTERN.search(user_prompt):
            trust = max(0, trust - 3)

        # 未監査減衰を適用
        decay = calculate_audit_decay(last_human_touch_at)
        if decay > 0:
            trust = max(0, trust - decay)

        # レベル変動チェック
        calculated_level = get_level(trust)
        current_idx = get_level_index(level)
        calculated_idx = get_level_index(calculated_level)

        if calculated_idx < current_idx:
            # 降格（自動）
            fm["level"] = calculated_level
        elif calculated_idx > current_idx and not pending_promotion:
            # 昇格条件達成 → pending_promotion に記録（人間承認待ち）
            fm["pending_promotion"] = calculated_level

        fm["trust"] = trust
        fm["looping"] = True
        fm["last_status"] = "working"
        fm["last_human_touch_at"] = now_iso
        write_frontmatter(STATE_FILE, fm)

    # 信頼情報を注入
    current_trust = fm.get("trust", trust)
    current_level = fm.get("level", get_level(current_trust))
    checkpoints = CHECKPOINTS.get(current_level, [])
    pending = fm.get("pending_promotion")

    output_lines = [
        "[JARVIS:Trust]",
        f"Level: {current_level} ({current_trust})",
        f"Checkpoints: {', '.join(checkpoints)}",
    ]
    if pending:
        output_lines.append(f"Pending: {pending}（/jarvis promote|deny）")

    sys.stdout.write("\n".join(output_lines))


if __name__ == "__main__":
    main()
