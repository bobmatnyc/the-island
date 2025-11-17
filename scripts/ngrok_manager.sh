#!/bin/bash

# Ngrok Tunnel Manager for Epstein Document Archive
# Manages ngrok tunnel for localhost:8081

NGROK_PORT=8081
NGROK_LOG="/Users/masa/Projects/Epstein/logs/ngrok.log"
NGROK_PID_FILE="/tmp/epstein_ngrok.pid"

start_tunnel() {
    # Check if ngrok is already running
    if [ -f "$NGROK_PID_FILE" ]; then
        PID=$(cat "$NGROK_PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "Ngrok tunnel is already running (PID: $PID)"
            get_url
            return
        fi
    fi

    # Start ngrok in background
    echo "Starting ngrok tunnel on port $NGROK_PORT..."
    mkdir -p "$(dirname "$NGROK_LOG")"
    nohup ngrok http $NGROK_PORT --log=stdout > "$NGROK_LOG" 2>&1 &
    NGROK_PID=$!
    echo $NGROK_PID > "$NGROK_PID_FILE"

    # Wait for ngrok to start
    echo "Waiting for ngrok to initialize..."
    sleep 3

    # Get and display URL
    get_url
}

stop_tunnel() {
    if [ -f "$NGROK_PID_FILE" ]; then
        PID=$(cat "$NGROK_PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "Stopping ngrok tunnel (PID: $PID)..."
            kill $PID
            rm "$NGROK_PID_FILE"
            echo "Tunnel stopped."
        else
            echo "Ngrok process not found. Cleaning up PID file."
            rm "$NGROK_PID_FILE"
        fi
    else
        # Try to find and kill any running ngrok processes
        PIDS=$(pgrep -f "ngrok http $NGROK_PORT")
        if [ -n "$PIDS" ]; then
            echo "Found ngrok processes: $PIDS"
            kill $PIDS
            echo "Stopped orphaned ngrok processes."
        else
            echo "No ngrok tunnel running."
        fi
    fi
}

get_url() {
    # Query ngrok API for public URL
    URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data['tunnels'] else 'Not available')" 2>/dev/null)

    if [ "$URL" = "Not available" ] || [ -z "$URL" ]; then
        echo "ERROR: Could not retrieve ngrok URL. Is ngrok running?"
        return 1
    fi

    echo ""
    echo "=========================================="
    echo "Epstein Document Archive - Public Access"
    echo "=========================================="
    echo ""
    echo "Public URL: $URL"
    echo ""
    echo "Authentication Credentials:"
    echo "  Username: epstein"
    echo "  Password: @rchiv*!2025"
    echo ""
    echo "  OR"
    echo ""
    echo "  Username: masa"
    echo "  Password: @rchiv*!2025"
    echo ""
    echo "Ngrok Web Interface: http://localhost:4040"
    echo ""
    echo "To stop tunnel: $0 stop"
    echo "=========================================="
    echo ""
}

status() {
    if [ -f "$NGROK_PID_FILE" ]; then
        PID=$(cat "$NGROK_PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "Ngrok tunnel is running (PID: $PID)"
            get_url
        else
            echo "Ngrok PID file exists but process is not running."
            rm "$NGROK_PID_FILE"
        fi
    else
        echo "Ngrok tunnel is not running."
        echo "Start with: $0 start"
    fi
}

restart_tunnel() {
    echo "Restarting ngrok tunnel..."
    stop_tunnel
    sleep 2
    start_tunnel
}

case "$1" in
    start)
        start_tunnel
        ;;
    stop)
        stop_tunnel
        ;;
    restart)
        restart_tunnel
        ;;
    status|url)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|url}"
        echo ""
        echo "Commands:"
        echo "  start   - Start ngrok tunnel"
        echo "  stop    - Stop ngrok tunnel"
        echo "  restart - Restart ngrok tunnel"
        echo "  status  - Show tunnel status and URL"
        echo "  url     - Show current public URL"
        exit 1
        ;;
esac
