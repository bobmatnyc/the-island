#!/bin/bash
# Reliable Backend Server Management Script
#
# Design Decision: Robust process management for development stability
#
# Features:
# - Process detection and cleanup (prevents port conflicts)
# - Port availability checking (detects conflicts with other services)
# - Virtual environment validation
# - Health check after startup
# - Clear status reporting
#
# Trade-offs:
# - Complexity: More checks vs. simple startup script
# - Reliability: Prevents common startup failures
# - Developer Experience: Clear messages vs. silent failures

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

BACKEND_PORT=8081
VENV_PATH=".venv"
SERVER_SCRIPT="server/app.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_status() {
    echo -e "${BLUE}[Backend]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[Backend]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[Backend]${NC} $1"
}

print_error() {
    echo -e "${RED}[Backend]${NC} $1"
}

# Check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Get process info for port
get_port_process() {
    local port=$1
    lsof -Pi :$port -sTCP:LISTEN 2>/dev/null | tail -n +2
}

# Kill backend processes
kill_backend() {
    print_status "Stopping existing backend processes..."

    # Kill by port
    if check_port $BACKEND_PORT; then
        local pid=$(lsof -ti :$BACKEND_PORT)
        if [ ! -z "$pid" ]; then
            print_status "Killing process on port $BACKEND_PORT (PID: $pid)"
            kill -9 $pid 2>/dev/null || true
            sleep 1
        fi
    fi

    # Kill by process name
    pkill -f "python3.*app.py" 2>/dev/null || true
    pkill -f "uvicorn.*app:app" 2>/dev/null || true

    sleep 1

    if check_port $BACKEND_PORT; then
        print_error "Failed to free port $BACKEND_PORT"
        print_error "Process still running:"
        get_port_process $BACKEND_PORT
        exit 1
    else
        print_success "All backend processes stopped"
    fi
}

# Check virtual environment
check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Virtual environment not found at $VENV_PATH"
        print_error "Run: python3 -m venv $VENV_PATH && source $VENV_PATH/bin/activate && pip install -r requirements.txt"
        exit 1
    fi

    if [ ! -f "$VENV_PATH/bin/activate" ]; then
        print_error "Invalid virtual environment at $VENV_PATH"
        exit 1
    fi

    print_success "Virtual environment found"
}

# Start backend server
start_backend() {
    print_status "Starting backend server on port $BACKEND_PORT..."

    # Activate virtual environment
    source "$VENV_PATH/bin/activate"

    # Start server in background
    python3 "$SERVER_SCRIPT" $BACKEND_PORT > logs/backend.log 2>&1 &
    local pid=$!

    print_status "Backend starting (PID: $pid)..."
    sleep 3

    # Check if process is still running
    if ! ps -p $pid > /dev/null 2>&1; then
        print_error "Backend failed to start"
        print_error "Last 20 lines of logs:"
        tail -20 logs/backend.log
        exit 1
    fi

    print_success "Backend process running (PID: $pid)"
}

# Health check
health_check() {
    print_status "Running health check..."

    local max_attempts=10
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
            local response=$(curl -s http://localhost:$BACKEND_PORT/health)
            print_success "Backend is healthy!"
            print_success "Response: $response"
            return 0
        fi

        print_status "Attempt $attempt/$max_attempts: Waiting for backend..."
        sleep 1
        ((attempt++))
    done

    print_error "Backend health check failed after $max_attempts attempts"
    print_error "Check logs/backend.log for details"
    return 1
}

# Main logic
case "${1:-start}" in
    start)
        print_status "Starting backend server..."

        # Check for conflicts
        if check_port $BACKEND_PORT; then
            print_warning "Port $BACKEND_PORT is already in use:"
            get_port_process $BACKEND_PORT
            print_warning ""
            read -p "Kill existing process and restart? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                kill_backend
            else
                print_error "Cannot start: port $BACKEND_PORT is in use"
                exit 1
            fi
        fi

        check_venv
        start_backend
        health_check

        print_success "================================================"
        print_success "Backend server is running!"
        print_success "================================================"
        print_success "API:     http://localhost:$BACKEND_PORT"
        print_success "Docs:    http://localhost:$BACKEND_PORT/docs"
        print_success "Health:  http://localhost:$BACKEND_PORT/health"
        print_success "Logs:    tail -f logs/backend.log"
        print_success "================================================"
        ;;

    stop)
        kill_backend
        ;;

    restart)
        kill_backend
        sleep 1
        $0 start
        ;;

    status)
        if check_port $BACKEND_PORT; then
            print_success "Backend is running on port $BACKEND_PORT"
            get_port_process $BACKEND_PORT
            echo ""
            if curl -s http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
                print_success "Health check: PASS"
                curl -s http://localhost:$BACKEND_PORT/health | python3 -m json.tool
            else
                print_error "Health check: FAIL"
            fi
        else
            print_warning "Backend is not running"
            exit 1
        fi
        ;;

    logs)
        if [ -f logs/backend.log ]; then
            tail -f logs/backend.log
        else
            print_error "No log file found at logs/backend.log"
            exit 1
        fi
        ;;

    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the backend server"
        echo "  stop     - Stop the backend server"
        echo "  restart  - Restart the backend server"
        echo "  status   - Check backend status and health"
        echo "  logs     - Tail backend logs"
        exit 1
        ;;
esac
