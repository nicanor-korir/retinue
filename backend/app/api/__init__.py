"""API package initialization."""
from app.api.routes import router
from app.api.escalations import router as escalations_router
from app.api.agents import router as agents_router
from app.api.projects import router as projects_router
from app.api.tasks import router as tasks_router

__all__ = ["router", "escalations_router", "agents_router", "projects_router", "tasks_router"]
