from fastapi import FastAPI

from src.api.suggestions import router as suggestions_router
from src.api.tasks import router as tasks_router

app = FastAPI(title="SmartTodo", description="AI powered todo application", version="0.1.0")

# suggestionsを先に登録（/api/tasks/{task_id}より/api/tasks/suggestionsを優先）
app.include_router(suggestions_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
