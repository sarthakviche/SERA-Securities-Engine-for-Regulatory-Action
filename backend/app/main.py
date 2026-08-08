from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import contextlib

from app.core.config import settings
from app.core.logging import setup_logging
from app.modules.documents.router import router as documents_router
from app.pipeline.router import router as pipeline_router
from app.workers import monitor

# Setup logging before FastAPI initializes fully
logger = setup_logging()

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting up {settings.APP_NAME}")

    # Initialize LangGraph Postgres Checkpointer tables
    try:
        from app.ai.graph.checkpointer import get_checkpointer
        checkpointer = get_checkpointer()
        await checkpointer.setup()
        logger.info("LangGraph checkpointer tables ready.")
    except Exception as e:
        logger.warning(f"Checkpointer setup skipped (no DB?): {e}")

    # Configure Resend email service
    try:
        from app.modules.notifications.email_service import email_service
        email_service.configure(
            api_key=settings.RESEND_API_KEY,
            from_email=settings.RESEND_FROM_EMAIL,
            to_email=settings.NOTIFICATION_EMAIL_RECIPIENT,
            enabled=settings.EMAIL_ENABLED,
        )
        logger.info("Email notification service configured.")
    except Exception as e:
        logger.warning(f"Email service setup failed: {e}")

    # Start the overdue task checker background loop
    overdue_task = None
    try:
        from app.workers.overdue_checker import run_overdue_checker_loop
        overdue_task = asyncio.create_task(run_overdue_checker_loop(interval_seconds=3600))
        logger.info("Overdue task checker started (interval=1h).")
    except Exception as e:
        logger.warning(f"Overdue checker could not start: {e}")

    yield

    # Shutdown
    if overdue_task and not overdue_task.done():
        overdue_task.cancel()
        try:
            await overdue_task
        except asyncio.CancelledError:
            pass
    logger.info(f"Shutting down {settings.APP_NAME}")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="Backend service for SEBI Regulatory Monitoring",
        version="0.1.0",
        lifespan=lifespan
    )

    # Add CORS middleware for frontend communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    app.include_router(documents_router)
    app.include_router(pipeline_router)

    from app.modules.workflow.router import router as workflow_router
    app.include_router(workflow_router)

    from app.modules.notifications.router import router as notifications_router
    app.include_router(notifications_router)

    @app.get("/")
    async def root():
        return {"message": f"Welcome to {settings.APP_NAME}"}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
