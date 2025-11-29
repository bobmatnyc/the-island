#!/bin/bash
# Start the FastAPI backend using the .venv Python environment
# This ensures SQLAlchemy and all dependencies are available

cd "$(dirname "$0")/../.."
source .venv/bin/activate
exec uvicorn server.app:app --host 0.0.0.0 --port 8081 --reload
