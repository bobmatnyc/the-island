#!/bin/bash
# Restart Backend Server Script
# Properly stops and restarts the FastAPI backend on port 8081

set -e

echo "🔄 Restarting Epstein Archive Backend..."

# Kill any existing backend processes
echo "  ⏹️  Stopping existing backend..."
lsof -ti:8081 | xargs kill -9 2>/dev/null || true
sleep 2

# Verify port is free
if lsof -ti:8081 >/dev/null 2>&1; then
    echo "  ❌ Error: Port 8081 is still in use"
    exit 1
fi

echo "  ✓ Port 8081 is free"

# Start backend
echo "  🚀 Starting backend on port 8081..."
cd "$(dirname "$0")"
python3 -m uvicorn server.app:app --host 0.0.0.0 --port 8081 > /tmp/epstein_backend.log 2>&1 &

# Wait for startup
echo "  ⏳ Waiting for backend to start..."
sleep 10

# Test if backend is responding
if curl -s http://localhost:8081/health > /dev/null 2>&1; then
    echo "  ✅ Backend is running successfully!"
    echo ""
    echo "📊 Server Info:"
    echo "  URL: http://localhost:8081"
    echo "  API Docs: http://localhost:8081/docs"
    echo "  Logs: /tmp/epstein_backend.log"
    echo ""
    echo "💬 Test chat endpoint:"
    echo '  curl -X POST http://localhost:8081/api/chat/enhanced -H "Content-Type: application/json" -d '"'"'{"message": "Hello", "conversation_history": []}'"'"''
else
    echo "  ❌ Backend failed to start. Check logs:"
    echo "  tail -f /tmp/epstein_backend.log"
    exit 1
fi
