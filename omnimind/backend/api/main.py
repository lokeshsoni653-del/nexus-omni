"""
OmniMind AI — FastAPI Core Engine Application Entrypoint
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from omnimind.db.base import create_all_tables
from omnimind.backend.api.routes import upload, workflow, websocket, auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("omnimind.backend.api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler: init DB tables on startup."""
    logger.info(f"Initializing {settings.APP_NAME} v{settings.APP_VERSION}...")
    try:
        create_all_tables()
        logger.info("Database tables initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
    yield
    logger.info("OmniMind AI application shutdown cleanly.")


def create_app() -> FastAPI:
    """FastAPI Application Factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Autonomous Multi-Agent SaaS & Enterprise RAG Platform Backend Engine",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS for multi-tenant SaaS frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API Routers
    app.include_router(auth.router)
    app.include_router(upload.router)
    app.include_router(workflow.router)
    app.include_router(websocket.router)

    # Mount static files directory for local PDF report downloads
    import os
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "eager_mode": settings.CELERY_TASK_ALWAYS_EAGER,
            "cloud_storage_enabled": settings.USE_S3_STORAGE,
        }

    return app


app = create_app()
