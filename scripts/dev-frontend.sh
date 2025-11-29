#!/bin/bash
# Frontend Development Server Manager

PROJECT_DIR="/Users/masa/Projects/epstein"
FRONTEND_DIR="$PROJECT_DIR/frontend"
PID_FILE="$PROJECT_DIR/.frontend-dev.pid"

case "$1" in
  start)
    # Check if already running
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      if kill -0 "$PID" 2>/dev/null; then
        echo "Frontend already running on PID $PID"
        echo "URL: http://localhost:5173"
        exit 0
      fi
    fi

    # Kill any orphaned processes
    pkill -f "vite.*frontend" 2>/dev/null

    # Create logs directory if it doesn't exist
    mkdir -p "$PROJECT_DIR/logs"

    # Start frontend
    cd "$FRONTEND_DIR"
    npm run dev > "$PROJECT_DIR/logs/frontend.log" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Frontend started on PID $(cat $PID_FILE)"
    echo "URL: http://localhost:5173"
    echo "Logs: $PROJECT_DIR/logs/frontend.log"
    ;;

  stop)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      kill "$PID" 2>/dev/null && echo "Stopped frontend (PID $PID)"
      rm -f "$PID_FILE"
    fi
    pkill -f "vite.*frontend" 2>/dev/null
    echo "All frontend processes stopped"
    ;;

  restart)
    $0 stop
    sleep 2
    $0 start
    ;;

  status)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      if kill -0 "$PID" 2>/dev/null; then
        echo "Frontend running on PID $PID"
        echo "URL: http://localhost:5173"
        exit 0
      fi
    fi
    echo "Frontend not running"
    exit 1
    ;;

  logs)
    tail -f "$PROJECT_DIR/logs/frontend.log"
    ;;

  *)
    echo "Usage: $0 {start|stop|restart|status|logs}"
    exit 1
    ;;
esac
