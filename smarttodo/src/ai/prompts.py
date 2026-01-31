from src.models.task import TaskResponse

SUGGESTION_SYSTEM_PROMPT = """あなたはタスク管理のアシスタントです。
ユーザーの過去のタスク履歴を分析し、次にやるべきタスクを提案してください。

提案は以下の観点で行ってください:
- 未完了タスクの優先度と期限
- 過去のタスクパターン（繰り返しのタスク、関連するタスク）
- タスクの依存関係や論理的な順序

各提案には以下を含めてください:
- タスクのタイトル
- 提案理由（簡潔に）
- 推奨優先度（high/medium/low）
"""


def build_suggestion_prompt(tasks: list[TaskResponse], limit: int = 3) -> str:
    """タスク提案用のプロンプトを構築"""
    if not tasks:
        return f"""タスク履歴がありません。
一般的なタスク管理のベストプラクティスに基づいて、{limit}件のタスクを提案してください。
新規ユーザー向けの基本的なタスクを提案してください。"""

    # タスク情報をフォーマット
    task_info = []
    for task in tasks:
        status_ja = {"pending": "未完了", "in_progress": "進行中", "completed": "完了"}.get(
            task.status.value, task.status.value
        )
        priority_ja = {"low": "低", "medium": "中", "high": "高"}.get(
            task.priority.value, task.priority.value
        )
        due_str = task.due_date.isoformat() if task.due_date else "なし"

        task_info.append(
            f"- タイトル: {task.title}\n"
            f"  説明: {task.description or 'なし'}\n"
            f"  ステータス: {status_ja}\n"
            f"  優先度: {priority_ja}\n"
            f"  期限: {due_str}"
        )

    tasks_text = "\n".join(task_info)

    return f"""以下は現在のタスク一覧です:

{tasks_text}

上記のタスク履歴を分析して、次にやるべきタスクを{limit}件提案してください。
JSON形式で以下の構造で回答してください:
{{
  "suggestions": [
    {{
      "title": "提案するタスクのタイトル",
      "reason": "提案理由",
      "priority": "high/medium/low"
    }}
  ]
}}"""
