"""Runs the FastAPI token server standalone."""
import sys
import os
import uvicorn

sys.path.insert(0, os.path.dirname(__file__))

from app.api.server import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
