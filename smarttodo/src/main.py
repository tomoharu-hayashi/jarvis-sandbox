from fastapi import FastAPI

from src.api.parser import router as parser_router
from src.api.suggestions import router as suggestions_router
from src.api.tasks import router as tasks_router

app = FastAPI(title="SmartTodo", description="AI powered todo application", version="0.1.0")

# パス優先度: parse, suggestions を先に登録（/api/tasks/{task_id}より優先）
app.include_router(parser_router, prefix="/api")
app.include_router(suggestions_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
