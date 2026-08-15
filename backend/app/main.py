"""
Main FastAPI application for Retinue platform.

This application orchestrates all 7 AI agents and provides a REST API
for human interaction with the agent company.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException

from app.core.config import settings
from app.api.routes import router
from app.api.agents import router as agents_router
from app.api.projects import router as projects_router
from app.api.tasks import router as tasks_router
from app.api.pm_agent import pm_agent_router
from app.api.analytics import analytics_router
from app.api.learning import learning_router
from app.api.audit import audit_router
from app.api.conversations import router as conversations_router
from app.api.websocket import router as websocket_router
from app.api.multi_agent import router as multi_agent_router
from app.api.exports_v2 import router as exports_v2_router
from app.db.database import init_db
from app.exceptions import RetinueException, InternalError
# Import all models to register them with SQLAlchemy
from app.db import models
from app.db import event_models
from app.db import conversation_models
from app.db import multi_agent_models
from app.db import knowledge_models
from app.agents import (
    CEOAgent,
    CTOAgent,
    PMAgent,
    HRAgent,
    BackendEngineerAgent,
    FrontendEngineerAgent,
    DesignerAgent,
)
# Import event-driven system integration
from app.services.event_driven_integration import (
    initialize_event_driven_system,
    start_event_driven_services,
    shutdown_event_driven_system,
    start_agent,
)
from app.agents.specialized_event_handlers import setup_specialized_handlers

# Import RAG event handlers
from app.services.rag_event_handlers import register_rag_event_handlers, unregister_rag_event_handlers
from app.services.rag_indexing_service import RAGIndexingService

# Import RAG cache service (Phase 3)
from app.services.rag_cache_service import initialize_cache_service, shutdown_cache_service

# Import RAG feedback loop service (Phase 3)
from app.services.rag_feedback_loop import initialize_feedback_loop_service, shutdown_feedback_loop_service

# Import RAG performance monitor service (Phase 3.4)
from app.services.rag_performance_monitor import initialize_performance_monitor, shutdown_performance_monitor

# Import Phase 1 Task RAG Integration
from app.services.task_rag_event_handlers import initialize_task_rag_handlers

# Import Phase 2 Multi-Entity RAG Integration
from app.services.multi_entity_rag_event_handlers import initialize_multi_entity_rag_handlers

# Import Agent Chat Monitor for background conversation monitoring
from app.services.agent_chat_monitor import start_agent_monitoring, stop_agent_monitoring

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Reduce SQLAlchemy verbosity
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)

# Reduce other noisy loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Global agent instances
agent_instances = {}
agent_tasks = {}

# Global RAG services
rag_indexing_service: Optional[RAGIndexingService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Starts all agents on application startup and gracefully shuts them down.
    """
    # Startup
    logger.info("🚀 Starting Retinue Platform...")

    try:
        # Initialize database
        logger.info("Initializing database...")
        await init_db()
        logger.info("✅ Database initialized")

        # Initialize event-driven system
        logger.info(f"Initializing event-driven system (mode: {settings.AGENT_EXECUTION_MODE})...")
        await initialize_event_driven_system()
        logger.info("✅ Event-driven system initialized")

        # Initialize all 7 agents
        logger.info("Initializing agents...")
        agent_instances["ceo"] = CEOAgent()
        agent_instances["cto"] = CTOAgent()
        agent_instances["pm"] = PMAgent()
        agent_instances["hr"] = HRAgent()
        agent_instances["backend"] = BackendEngineerAgent()
        agent_instances["frontend"] = FrontendEngineerAgent()
        agent_instances["designer"] = DesignerAgent()

        logger.info("✅ All 7 agents initialized")

        # Set up specialized event handlers for CEO, CTO, PM
        logger.info("Setting up specialized event handlers...")
        setup_specialized_handlers(
            agent_instances["ceo"],
            agent_instances["cto"],
            agent_instances["pm"]
        )
        logger.info("✅ Specialized event handlers configured")

        # Start event-driven services
        logger.info("Starting event-driven services...")
        await start_event_driven_services()
        logger.info("✅ Event-driven services started")

        # Initialize and start RAG services (Phase 2)
        if settings.RAG_ENABLED:
            logger.info("Initializing RAG services...")
            try:
                # Initialize RAG cache service (Phase 3)
                logger.info("Initializing RAG cache service...")
                await initialize_cache_service()
                logger.info("✅ RAG cache service initialized")

                # Initialize RAG feedback loop service (Phase 3)
                logger.info("Initializing RAG feedback loop service...")
                await initialize_feedback_loop_service()
                logger.info("✅ RAG feedback loop service initialized")

                # Initialize RAG performance monitor (Phase 3.4)
                logger.info("Initializing RAG performance monitor...")
                await initialize_performance_monitor()
                logger.info("✅ RAG performance monitor initialized")

                # Initialize Phase 1 Task RAG Event Handlers
                logger.info("Initializing Task RAG event handlers (Phase 1)...")
                await initialize_task_rag_handlers()
                logger.info("✅ Task RAG event handlers initialized - automatic task indexing enabled")

                # Initialize Phase 2 Multi-Entity RAG Event Handlers
                logger.info("Initializing Multi-Entity RAG event handlers (Phase 2)...")
                await initialize_multi_entity_rag_handlers()
                logger.info("✅ Multi-Entity RAG event handlers initialized - automatic project/decision/escalation indexing enabled")

                # Initialize RAG indexing service
                global rag_indexing_service
                rag_indexing_service = RAGIndexingService()
                await rag_indexing_service.start()
                logger.info("✅ RAG indexing service started")

                # Register RAG event handlers to enable automatic indexing
                from app.services.event_driven_integration import get_event_bus
                event_bus = get_event_bus()
                await register_rag_event_handlers(event_bus)
                logger.info("✅ RAG event handlers registered - automatic indexing enabled")
            except Exception as e:
                logger.warning(f"⚠️  RAG initialization failed, continuing without RAG: {e}")
                # Continue without RAG if initialization fails
        else:
            logger.info("⚠️  RAG disabled in configuration")

        # Start each agent using event-driven system
        logger.info(f"Starting agents in {settings.AGENT_EXECUTION_MODE} mode...")
        for name, agent in agent_instances.items():
            await start_agent(agent)
            logger.info(f"✅ {name.upper()} agent started")

        # Start Agent Chat Monitor for autonomous agent joining
        logger.info("Starting agent chat monitoring service...")
        await start_agent_monitoring()
        logger.info("✅ Agent chat monitor started - agents can now autonomously join conversations")

        logger.info("✨ All agents running in event-driven mode!")
        logger.info(f"🌐 API available at http://0.0.0.0:8000")
        logger.info(f"📚 API docs at http://0.0.0.0:8000/docs")
        logger.info(f"⚡ Event-driven execution enabled - agents respond in <100ms!")

    except Exception as e:
        logger.error(f"❌ Failed to start agents: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("🛑 Shutting down Retinue Platform...")

    # Shutdown Agent Chat Monitor
    logger.info("Stopping agent chat monitoring service...")
    await stop_agent_monitoring()
    logger.info("✅ Agent chat monitor stopped")

    # Shutdown RAG services
    if settings.RAG_ENABLED:
        logger.info("Shutting down RAG services...")
        try:
            # Shutdown cache service first (Phase 3)
            logger.info("Shutting down RAG cache service...")
            await shutdown_cache_service()
            logger.info("✅ RAG cache service shutdown")

            # Shutdown feedback loop service (Phase 3)
            logger.info("Shutting down RAG feedback loop service...")
            await shutdown_feedback_loop_service()
            logger.info("✅ RAG feedback loop service shutdown")

            # Shutdown performance monitor (Phase 3.4)
            logger.info("Shutting down RAG performance monitor...")
            await shutdown_performance_monitor()
            logger.info("✅ RAG performance monitor shutdown")

            if rag_indexing_service:
                await rag_indexing_service.stop()
                logger.info("✅ RAG indexing service shutdown")

            from app.services.event_driven_integration import get_event_bus
            event_bus = get_event_bus()
            await unregister_rag_event_handlers()
            logger.info("✅ RAG event handlers unregistered")
        except Exception as e:
            logger.warning(f"⚠️  Error during RAG shutdown: {e}")

    # Shutdown event-driven system
    logger.info("Shutting down event-driven system...")
    await shutdown_event_driven_system()
    logger.info("✅ Event-driven system shutdown")

    # Cancel all agent tasks (if any are still running)
    for name, task in agent_tasks.items():
        if not task.done():
            logger.info(f"Stopping {name} agent...")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    logger.info("✅ All agents stopped")
    logger.info("👋 Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    Retinue - AI Agent Company Platform

    A multi-agent AI system that operates like a real company
    """,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routes
app.include_router(router, prefix="/api/v1")
app.include_router(agents_router)
app.include_router(projects_router)
app.include_router(tasks_router)
# Phase 2 routers
app.include_router(pm_agent_router)
app.include_router(analytics_router)
app.include_router(learning_router)
app.include_router(audit_router)
# Conversation router
app.include_router(conversations_router)
# Multi-Agent Chat router
app.include_router(multi_agent_router)
# WebSocket router (must be included directly, not through prefix)
app.include_router(websocket_router)
# Export v2 API - simplified export functionality
app.include_router(exports_v2_router, prefix="/api/v2/exports")


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with system information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "agents": {
            name: {
                "name": agent.name,
                "role": agent.role,
                "status": "running" if name in agent_tasks else "stopped",
            }
            for name, agent in agent_instances.items()
        },
        "api_docs": "/docs",
        "health_check": "/health",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    from app.agents import AgentRegistry

    # Create mapping from agent_id to short name for instantiated agents
    agent_id_to_short_name = {
        "ceo_001": "ceo",
        "pm_001": "pm",
        "hr_monitor_001": "hr",
        "cto_001": "cto",
        "backend_001": "backend",
        "frontend_001": "frontend",
        "designer_001": "designer"
    }

    # Get status for all agents in the registry
    agent_status = {}
    for agent_id, config in AgentRegistry.AGENT_CATALOG.items():
        # Check if agent is instantiated and running
        short_name = agent_id_to_short_name.get(agent_id)

        if short_name and short_name in agent_instances and short_name in agent_tasks:
            status = "running" if not agent_tasks[short_name].done() else "stopped"
        elif short_name and short_name in agent_instances:
            status = "initialized"
        else:
            status = "registered"  # In registry but not instantiated

        agent_status[agent_id] = {
            "status": status,
            "name": config.get("name", ""),
            "department": config.get("department", "").value if hasattr(config.get("department", ""), "value") else str(config.get("department", ""))
        }

    # Count running agents
    running_count = sum(1 for a in agent_status.values() if a["status"] == "running")
    initialized_count = sum(1 for a in agent_status.values() if a["status"] in ["running", "initialized", "stopped"])

    return {
        "status": "healthy" if running_count > 0 else "degraded",
        "agents_count": len(AgentRegistry.AGENT_CATALOG),
        "agents_initialized": initialized_count,
        "agents_running": running_count,
        "agents": agent_status,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/info", tags=["System"])
async def system_info():
    """Get detailed system information."""
    return {
        "application": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        },
        "agents": {
            name: {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "role": agent.role,
                "department": agent.department,  # Legacy field
                "departments": agent.all_departments if hasattr(agent, 'all_departments') else [agent.department],  # Multi-department support
                "reports_to": agent.reports_to,
                "check_interval": agent.check_interval,
            }
            for name, agent in agent_instances.items()
        },
        "configuration": {
            "agent_check_interval": settings.AGENT_CHECK_INTERVAL,
            "inactive_warning_threshold": settings.AGENT_INACTIVE_WARNING_THRESHOLD,
            "inactive_critical_threshold": settings.AGENT_INACTIVE_CRITICAL_THRESHOLD,
            "task_stuck_threshold": settings.TASK_STUCK_THRESHOLD,
            "approval_timeout_threshold": settings.APPROVAL_TIMEOUT_THRESHOLD,
        },
    }


# Exception handlers
@app.exception_handler(RetinueException)
async def retinue_exception_handler(request: Request, exc: RetinueException):
    """Handle Retinue custom exceptions with consistent error format."""
    error_response = exc.error_response.to_dict()
    logger.warning(
        f"Retinue error [{exc.error_response.error_code}]: {exc.error_response.message}",
        extra={"request_id": exc.error_response.request_id}
    )
    return JSONResponse(
        status_code=exc.error_response.status_code,
        content=error_response,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions with consistent error format."""
    # Map HTTP status codes to error codes
    status_to_code = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_ERROR",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE",
        504: "TIMEOUT_ERROR",
    }

    error_code = status_to_code.get(exc.status_code, "HTTP_ERROR")
    
    # Generate a simple request ID using the request path and timestamp
    import uuid
    request_id = str(uuid.uuid4())

    error_response = {
        "error": {
            "code": error_code,
            "message": exc.detail or "An error occurred",
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "request_id": request_id,
        }
    }

    logger.warning(
        f"HTTP error [{error_code}]: {exc.detail}",
        extra={"status_code": exc.status_code, "request_id": request_id}
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with safe error message."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Create safe error response
    error_response = InternalError(
        details={"original_error_type": type(exc).__name__} if settings.DEBUG else {}
    )

    return JSONResponse(
        status_code=error_response.error_response.status_code,
        content=error_response.error_response.to_dict(),
    )


# Custom startup message
@app.on_event("startup")
async def startup_message():
    """Display startup message."""
    logger.info("=" * 60)
    logger.info(f"  {settings.APP_NAME}")
    logger.info(f"  Version: {settings.APP_VERSION}")
    logger.info(f"  Environment: {settings.ENVIRONMENT}")
    logger.info("=" * 60)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )
