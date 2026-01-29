from fastapi import FastAPI

from src.api.tasks import router as tasks_router

app = FastAPI(title="SmartTodo", description="AI powered todo application", version="0.1.0")

app.include_router(tasks_router, prefix="/api")
