#!/bin/bash
# Epstein Archive Server Starter
# Usage: ./start.sh [port]

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-8081}"

echo "======================================================================"
echo "EPSTEIN DOCUMENT ARCHIVE - SERVER STARTUP"
echo "======================================================================"

# Activate venv
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$PROJECT_ROOT/.venv"
fi

source "$PROJECT_ROOT/.venv/bin/activate"

# Install dependencies
echo "Installing dependencies..."
pip install -q fastapi 'uvicorn[standard]' python-multipart

# Check for credentials file
if [ ! -f "$PROJECT_ROOT/server/.credentials" ]; then
    echo "WARNING: No .credentials file found. Creating default..."
    echo "epstein:archive2025" > "$PROJECT_ROOT/server/.credentials"
fi

# Start server
cd "$PROJECT_ROOT/server"
echo ""
echo "Starting server on port $PORT..."
echo "Credentials: See server/.credentials"
echo ""

python3 app.py $PORT
