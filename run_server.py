"""
OmniMind AI — Server Runner Entrypoint

Usage:
  python run_server.py [--port 8000] [--reload]
"""
import sys
import uvicorn
from config import settings

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
        
    print(f"Starting {settings.APP_NAME} FastAPI server on http://localhost:{port}")
    uvicorn.run(
        "omnimind.backend.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level="info",
    )
