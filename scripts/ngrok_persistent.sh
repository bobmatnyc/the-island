#!/bin/bash
# Persistent ngrok tunnel manager for Epstein Archive
# Maintains tunnel at https://the-island.ngrok.app -> localhost:8081

NGROK_URL="the-island.ngrok.app"
LOCAL_PORT="8081"
LOG_FILE="/tmp/ngrok_persistent.log"
PID_FILE="/tmp/ngrok.pid"
HEALTH_CHECK_INTERVAL=300  # 5 minutes

function log_msg() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

function start_tunnel() {
    log_msg "Starting ngrok tunnel..."

    # Kill any existing ngrok processes first
    pkill -f "ngrok.*$NGROK_URL" 2>/dev/null
    sleep 1

    # Start ngrok in background
    nohup ngrok http --domain="$NGROK_URL" "$LOCAL_PORT" > /dev/null 2>&1 &
    NGROK_PID=$!
    echo $NGROK_PID > "$PID_FILE"

    # Wait for tunnel to initialize
    sleep 3

    if check_tunnel; then
        log_msg "Tunnel started successfully (PID: $NGROK_PID)"
        return 0
    else
        log_msg "ERROR: Tunnel failed to start"
        return 1
    fi
}

function check_tunnel() {
    # Check 1: Is ngrok process running?
    if [ -f "$PID_FILE" ]; then
        NGROK_PID=$(cat "$PID_FILE")
        if ! ps -p "$NGROK_PID" > /dev/null 2>&1; then
            return 1
        fi
    else
        return 1
    fi

    # Check 2: Is API responding?
    if ! curl -s http://localhost:4040/api/tunnels > /dev/null 2>&1; then
        return 1
    fi

    # Check 3: Is our tunnel listed?
    TUNNEL_CHECK=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -c "$NGROK_URL")
    if [ "$TUNNEL_CHECK" -eq 0 ]; then
        return 1
    fi

    # Check 4: Is public URL accessible? (Skip if no backend service)
    # This check is optional since the tunnel may be up even if backend is down
    # Uncomment if you want strict health checking:
    # if ! curl -s -I --max-time 5 "https://$NGROK_URL" > /dev/null 2>&1; then
    #     return 1
    # fi

    return 0
}

function stop_tunnel() {
    log_msg "Stopping ngrok tunnel..."

    if [ -f "$PID_FILE" ]; then
        NGROK_PID=$(cat "$PID_FILE")
        kill "$NGROK_PID" 2>/dev/null
        rm "$PID_FILE"
    fi

    # Force kill any remaining ngrok processes
    pkill -f "ngrok.*$NGROK_URL" 2>/dev/null

    log_msg "Tunnel stopped"
}

function restart_tunnel() {
    stop_tunnel
    sleep 2
    start_tunnel
}

function get_status() {
    if check_tunnel; then
        TUNNEL_INFO=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tunnel = data['tunnels'][0]
    print(f\"Public URL: {tunnel['public_url']}\")
    print(f\"Local Port: {tunnel['config']['addr']}\")
    print(f\"Connections: {tunnel['metrics']['conns']['count']}\")
    print(f\"HTTP Requests: {tunnel['metrics']['http']['count']}\")
except:
    pass
" 2>/dev/null)

        echo "Tunnel Status: UP"
        echo "$TUNNEL_INFO"
        echo "PID: $(cat $PID_FILE 2>/dev/null || echo 'unknown')"
        return 0
    else
        echo "Tunnel Status: DOWN"
        return 1
    fi
}

function monitor_loop() {
    log_msg "Starting tunnel monitor (checking every $HEALTH_CHECK_INTERVAL seconds)"

    # Ensure tunnel is running at start
    if ! check_tunnel; then
        log_msg "Tunnel not running, starting..."
        start_tunnel
    else
        log_msg "Tunnel already running"
    fi

    # Monitoring loop
    CONSECUTIVE_FAILURES=0
    while true; do
        sleep "$HEALTH_CHECK_INTERVAL"

        if ! check_tunnel; then
            CONSECUTIVE_FAILURES=$((CONSECUTIVE_FAILURES + 1))
            log_msg "WARNING: Tunnel check failed (failure count: $CONSECUTIVE_FAILURES)"

            # Restart immediately on first failure
            log_msg "Attempting restart..."
            restart_tunnel

            if check_tunnel; then
                log_msg "Tunnel restored successfully"
                CONSECUTIVE_FAILURES=0
            else
                log_msg "ERROR: Restart failed (will retry in $HEALTH_CHECK_INTERVAL seconds)"
            fi
        else
            if [ $CONSECUTIVE_FAILURES -gt 0 ]; then
                log_msg "Tunnel health restored"
            fi
            CONSECUTIVE_FAILURES=0
        fi
    done
}

# Main command handler
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
    monitor)
        monitor_loop
        ;;
    status)
        get_status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|monitor|status}"
        echo ""
        echo "Commands:"
        echo "  start   - Start ngrok tunnel"
        echo "  stop    - Stop ngrok tunnel"
        echo "  restart - Restart ngrok tunnel"
        echo "  monitor - Start monitoring loop (auto-restart on failure)"
        echo "  status  - Check tunnel status"
        exit 1
        ;;
esac

exit $?
