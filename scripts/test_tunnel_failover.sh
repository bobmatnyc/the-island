#!/bin/bash
# Test script to verify ngrok tunnel auto-restart

echo "Testing ngrok tunnel failover..."
echo ""

echo "1. Current status:"
/Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh status
echo ""

echo "2. Killing ngrok process to simulate failure..."
NGROK_PID=$(cat /tmp/ngrok.pid 2>/dev/null)
if [ -n "$NGROK_PID" ]; then
    echo "   Killing PID: $NGROK_PID"
    kill $NGROK_PID
    sleep 2
else
    echo "   No PID file found, using pkill"
    pkill ngrok
    sleep 2
fi

echo ""
echo "3. Checking if tunnel is down..."
/Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh status
echo ""

echo "4. Waiting for auto-restart (monitoring runs every 5 minutes)..."
echo "   In production, the monitor will restart the tunnel automatically."
echo "   For this test, we'll manually restart:"
echo ""

/Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh restart
sleep 3

echo ""
echo "5. Final status after restart:"
/Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh status

echo ""
echo "Test complete! Tunnel should be back up."
