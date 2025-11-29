#!/bin/bash
# Epstein Archive Complete Startup Script
# Starts both server and ngrok tunnel

PROJECT_DIR="/Users/masa/Projects/epstein"
PORT="${1:-8081}"

echo "========================================="
echo "   Epstein Archive Complete Startup     "
echo "========================================="
echo ""

# Start server
echo "Step 1: Starting Epstein Archive Server..."
echo "-----------------------------------------"
$PROJECT_DIR/start_server.sh $PORT

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Server startup failed. Aborting."
    exit 1
fi

echo ""
echo "Step 2: Starting Ngrok Tunnel..."
echo "-----------------------------------------"
$PROJECT_DIR/start_ngrok.sh

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Ngrok startup failed, but server is running."
    echo "You can access the server locally at http://localhost:$PORT/"
    exit 1
fi

echo ""
echo "========================================="
echo "   All Systems Operational               "
echo "========================================="
echo ""
echo "Local Access:  http://localhost:$PORT/"
echo "Public Access: https://the-island.ngrok.app/"
echo ""
echo "Server Logs:   /tmp/epstein_${PORT}_venv.log"
echo "Ngrok Logs:    /tmp/ngrok_the-island.log"
echo "Ngrok Web UI:  http://localhost:4040"
echo ""
echo "To stop all services:"
echo "  lsof -ti:$PORT | xargs kill    # Stop server"
echo "  pkill -f 'ngrok start'         # Stop ngrok"
echo ""
