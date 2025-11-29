#!/bin/bash

# Start Epstein Document Archive with Public Access
# This script ensures both the backend server and ngrok tunnel are running

PROJECT_DIR="/Users/masa/Projects/Epstein"
SERVER_DIR="$PROJECT_DIR/server/web"
NGROK_MANAGER="$PROJECT_DIR/scripts/ngrok_manager.sh"

echo "Starting Epstein Document Archive..."
echo ""

# Check if backend server is running
SERVER_PID=$(lsof -ti:8081 2>/dev/null)
if [ -n "$SERVER_PID" ]; then
    echo "✓ Backend server already running (PID: $SERVER_PID)"
else
    echo "✗ Backend server not running"
    echo "  Starting server..."
    cd "$SERVER_DIR"
    nohup python3 app.py > "$PROJECT_DIR/logs/server.log" 2>&1 &
    sleep 2
    SERVER_PID=$(lsof -ti:8081 2>/dev/null)
    if [ -n "$SERVER_PID" ]; then
        echo "✓ Backend server started (PID: $SERVER_PID)"
    else
        echo "✗ Failed to start backend server"
        echo "  Check logs: $PROJECT_DIR/logs/server.log"
        exit 1
    fi
fi

echo ""

# Start ngrok tunnel
echo "Starting ngrok tunnel..."
$NGROK_MANAGER start

echo ""
echo "=========================================="
echo "Both services are now running!"
echo "=========================================="
echo ""
echo "To stop all services:"
echo "  Backend: kill \$(lsof -ti:8081)"
echo "  Ngrok:   $NGROK_MANAGER stop"
echo ""
