"""
OmniMind AI — Server Runner Entrypoint
"""
import os
import sys
import uvicorn
from config import settings

if __name__ == "__main__":
    port_env = os.getenv("PORT")
    if port_env and port_env.isdigit():
        port = int(port_env)
    elif len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    else:
        port = 8000

    print(f"Starting {settings.APP_NAME} FastAPI server on host 0.0.0.0:{port}")
    uvicorn.run(
        "omnimind.backend.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level="info",
    )
