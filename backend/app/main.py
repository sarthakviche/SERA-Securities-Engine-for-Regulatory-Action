from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    # Optional: We could trigger an initial background scrape here
    yield
    # Shutdown
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
    
    @app.get("/")
    async def root():
        return {"message": f"Welcome to {settings.APP_NAME}"}

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
