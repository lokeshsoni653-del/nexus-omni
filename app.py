"""
OmniMind AI — Root Application Entrypoint for Cloud Deployments (Render / Railway / Vercel)
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("omnimind.root")

# Ensure project root is in sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from omnimind.backend.api.main import app, create_app
    logger.info("Successfully imported FastAPI app from omnimind.backend.api.main")
except Exception as err:
    logger.error(f"Failed to import core app: {err}. Initializing standalone fallback app.")
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(
        title="OmniMind AI Fallback Engine",
        version="0.5.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        return {"app_name": "OmniMind AI", "status": "online", "mode": "standalone_fallback"}

    @app.get("/health")
    async def health():
        return {"status": "healthy", "mode": "standalone_fallback"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
