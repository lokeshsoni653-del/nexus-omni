"""
OmniMind AI — Core Production FastAPI Application Entrypoint (app.py)
"""
import os
import sys
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("omnimind.server")

# FastAPI App Instance
app = FastAPI(
    title="OmniMind AI",
    version="0.5.0",
    description="Autonomous Multi-Agent Enterprise RAG Platform Engine",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root Welcome Endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "app_name": "OmniMind AI",
        "version": "0.5.0",
        "status": "online",
        "docs_url": "/docs",
        "health_check": "/health",
    }

# Health Check Endpoint
@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "healthy",
        "app_name": "OmniMind AI",
        "version": "0.5.0",
        "cloud_deployment": "active",
    }

# Mount OmniMind Platform Sub-Routers
try:
    from omnimind.backend.api.routes import upload, workflow, websocket, auth
    app.include_router(auth.router)
    app.include_router(upload.router)
    app.include_router(workflow.router)
    app.include_router(websocket.router)
    logger.info("OmniMind API routers mounted successfully.")
except Exception as e:
    logger.error(f"Error mounting sub-routers: {e}")

# Mount static uploads directory for document/report downloads
try:
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    os.makedirs(upload_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")
except Exception as e:
    logger.warning(f"Static uploads mount warning: {e}")
