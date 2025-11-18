#!/bin/bash
# Epstein Archive Ngrok Tunnel Startup Script
# Starts ngrok tunnel for the-island domain

TUNNEL_NAME="the-island"
EXPECTED_DOMAIN="the-island.ngrok.app"

echo "=== Epstein Archive Ngrok Tunnel Startup ==="
echo "Tunnel: $TUNNEL_NAME"
echo "Domain: $EXPECTED_DOMAIN"

# Kill existing ngrok processes
echo "Checking for existing ngrok processes..."
if pgrep -f "ngrok start" > /dev/null 2>&1; then
    echo "Killing existing ngrok processes..."
    pkill -f "ngrok start"
    sleep 1
fi

# Start ngrok tunnel
echo "Starting ngrok tunnel..."
ngrok start $TUNNEL_NAME > /tmp/ngrok_${TUNNEL_NAME}.log 2>&1 &

NGROK_PID=$!
echo "Ngrok started with PID: $NGROK_PID"

# Wait for ngrok to initialize
echo "Waiting for ngrok to initialize..."
sleep 3

# Check if ngrok API is responding
echo "Testing ngrok API..."
if curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
    echo "✅ Ngrok API is responding"
else
    echo "❌ Ngrok API not responding. Check if ngrok started correctly."
    echo "Log file: /tmp/ngrok_${TUNNEL_NAME}.log"
    exit 1
fi

# Get tunnel URL
echo "Retrieving tunnel URL..."
TUNNEL_URL=$(curl -s http://localhost:4040/api/tunnels 2>&1 | python3 -c "import sys, json; data = json.load(sys.stdin); tunnels = data.get('tunnels', []); print(tunnels[0]['public_url'] if tunnels else 'No tunnels')" 2>/dev/null)

if [ "$TUNNEL_URL" = "No tunnels" ] || [ -z "$TUNNEL_URL" ]; then
    echo "❌ No tunnels found. Check ngrok configuration and logs."
    echo "Log file: /tmp/ngrok_${TUNNEL_NAME}.log"
    exit 1
fi

echo "✅ Tunnel is active: $TUNNEL_URL"

# Test tunnel connectivity
echo "Testing tunnel connectivity..."
if curl -I "$TUNNEL_URL" 2>&1 | grep -q "200 OK"; then
    echo "✅ Tunnel is accessible and working"
else
    echo "⚠️  Tunnel URL is active but connectivity test failed"
    echo "This may be normal if the server hasn't started yet."
fi

echo ""
echo "=== Ngrok Status ==="
echo "Tunnel URL: $TUNNEL_URL"
echo "PID: $NGROK_PID"
echo "Logs: /tmp/ngrok_${TUNNEL_NAME}.log"
echo "Web UI: http://localhost:4040"
echo ""
echo "To view logs in real-time:"
echo "  tail -f /tmp/ngrok_${TUNNEL_NAME}.log"
echo ""
echo "To stop ngrok:"
echo "  kill $NGROK_PID"
echo "  # or"
echo "  pkill -f 'ngrok start'"
