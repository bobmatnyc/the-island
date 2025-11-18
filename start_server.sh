#!/bin/bash
# Epstein Archive Server Startup Script
# Ensures server runs with venv Python and all dependencies available

PROJECT_DIR="/Users/masa/Projects/epstein"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python3"
PORT="${1:-8081}"

echo "=== Epstein Archive Server Startup ==="
echo "Project: $PROJECT_DIR"
echo "Port: $PORT"

# Kill existing process on port
echo "Checking for existing processes on port $PORT..."
if lsof -ti:$PORT > /dev/null 2>&1; then
    echo "Killing existing process on port $PORT..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null
    sleep 1
fi

# Verify venv Python exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ ERROR: Virtual environment not found at $VENV_PYTHON"
    echo "Please create the virtual environment first:"
    echo "  cd $PROJECT_DIR"
    echo "  python3 -m venv .venv"
    echo "  .venv/bin/pip install -r requirements.txt"
    echo "  .venv/bin/pip install -r server/requirements.txt"
    exit 1
fi

# Start server with venv Python
echo "Starting server with venv Python..."
cd "$PROJECT_DIR/server"
$VENV_PYTHON app.py $PORT > /tmp/epstein_${PORT}_venv.log 2>&1 &

SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"

# Wait for server to be ready
echo "Waiting for server to initialize..."
sleep 3

# Check if server is responding
echo "Testing server connectivity..."
if curl -I http://localhost:$PORT/ 2>&1 | grep -q "200 OK"; then
    echo "✅ Server is running on http://localhost:$PORT/"
else
    echo "❌ Server failed to start. Check logs: /tmp/epstein_${PORT}_venv.log"
    echo ""
    echo "Last 20 lines of log:"
    tail -20 /tmp/epstein_${PORT}_venv.log
    exit 1
fi

# Check if RAG routes loaded
echo "Checking RAG system..."
if grep -q "RAG routes registered" /tmp/epstein_${PORT}_venv.log; then
    echo "✅ RAG routes loaded successfully"

    # Test RAG endpoint
    if curl -s "http://localhost:$PORT/api/rag/stats" 2>&1 | grep -q "total_documents"; then
        echo "✅ RAG system is functional"
    else
        echo "⚠️  RAG routes loaded but endpoint test failed"
    fi
else
    echo "⚠️  RAG routes may not have loaded. Check logs:"
    grep -i "rag\|chroma\|error" /tmp/epstein_${PORT}_venv.log
fi

echo ""
echo "=== Server Status ==="
echo "URL: http://localhost:$PORT/"
echo "PID: $SERVER_PID"
echo "Logs: /tmp/epstein_${PORT}_venv.log"
echo ""
echo "To view logs in real-time:"
echo "  tail -f /tmp/epstein_${PORT}_venv.log"
echo ""
echo "To stop server:"
echo "  kill $SERVER_PID"
echo "  # or"
echo "  lsof -ti:$PORT | xargs kill"
