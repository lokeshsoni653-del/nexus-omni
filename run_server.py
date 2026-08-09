"""
OmniMind AI — Server Runner Entrypoint
"""
import os
import sys
import uvicorn

if __name__ == "__main__":
    port_env = os.getenv("PORT")
    if port_env and port_env.isdigit():
        port = int(port_env)
    elif len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    else:
        port = 8000

    print(f"Starting OmniMind AI FastAPI server on host 0.0.0.0:{port}")
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
