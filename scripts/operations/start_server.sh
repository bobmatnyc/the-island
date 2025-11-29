#!/bin/bash
# Start Epstein Archive server with virtual environment

cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Start server on port 8081
python3 server/app.py 8081
