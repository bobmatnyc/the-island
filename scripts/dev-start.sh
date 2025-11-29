#!/usr/bin/env bash
################################################################################
# dev-start.sh - Development Environment Startup Script
#
# Starts the Epstein Archive development environment with health monitoring.
# Manages both FastAPI backend (port 8000) and Vite frontend (port 5173).
#
# Usage:
#   ./scripts/dev-start.sh                    # Start both servers
#   ./scripts/dev-start.sh --backend-only     # Only backend
#   ./scripts/dev-start.sh --frontend-only    # Only frontend
#   ./scripts/dev-start.sh --status           # Check status without starting
#   ./scripts/dev-start.sh --restart          # Restart both servers
#
# Environment Variables:
#   BACKEND_PORT    - Backend port (default: 8000)
#   FRONTEND_PORT   - Frontend port (default: 5173)
#   LOG_LEVEL       - Logging level (default: INFO)
#
# Author: Epstein Archive Development Team
# Date: 2025-11-20
################################################################################

set -euo pipefail

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Symbols
readonly CHECK_MARK="✅"
readonly WARNING="⚠️ "
readonly ERROR_MARK="❌"
readonly INFO_MARK="🔵"

# Project paths
readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly VENV_PATH="${PROJECT_ROOT}/.venv"
readonly BACKEND_DIR="${PROJECT_ROOT}/server"
readonly FRONTEND_DIR="${PROJECT_ROOT}/frontend"
readonly LOGS_DIR="${PROJECT_ROOT}/logs"
readonly PID_FILE="${PROJECT_ROOT}/.dev-pids"

# Default ports
readonly BACKEND_PORT="${BACKEND_PORT:-8000}"
readonly FRONTEND_PORT="${FRONTEND_PORT:-5173}"
readonly LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Log files
readonly BACKEND_LOG="${LOGS_DIR}/backend.log"
readonly FRONTEND_LOG="${LOGS_DIR}/frontend.log"

# Parse command line arguments
BACKEND_ONLY=false
FRONTEND_ONLY=false
STATUS_ONLY=false
RESTART=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only)
            BACKEND_ONLY=true
            shift
            ;;
        --frontend-only)
            FRONTEND_ONLY=true
            shift
            ;;
        --status)
            STATUS_ONLY=true
            shift
            ;;
        --restart)
            RESTART=true
            shift
            ;;
        -h|--help)
            head -n 30 "$0" | grep "^#" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo -e "${ERROR_MARK} ${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${INFO_MARK} ${BLUE}$1${NC}"
}

log_success() {
    echo -e "${CHECK_MARK} ${GREEN}$1${NC}"
}

log_warning() {
    echo -e "${WARNING}${YELLOW}$1${NC}"
}

log_error() {
    echo -e "${ERROR_MARK} ${RED}$1${NC}"
}

# Check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :${port} -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Get process using port
get_port_process() {
    local port=$1
    lsof -Pi :${port} -sTCP:LISTEN -t 2>/dev/null || echo ""
}

# Kill process on port
kill_port_process() {
    local port=$1
    local pid=$(get_port_process "$port")

    if [[ -n "$pid" ]]; then
        log_warning "Killing process $pid on port $port"
        kill -TERM "$pid" 2>/dev/null || true
        sleep 2

        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            log_warning "Force killing process $pid"
            kill -KILL "$pid" 2>/dev/null || true
        fi

        sleep 1
        return 0
    fi
    return 1
}

# Ensure logs directory exists
ensure_logs_dir() {
    mkdir -p "${LOGS_DIR}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check virtual environment
    if [[ ! -d "${VENV_PATH}" ]]; then
        log_error "Virtual environment not found at ${VENV_PATH}"
        log_info "Run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi

    # Check backend directory
    if [[ ! -d "${BACKEND_DIR}" ]]; then
        log_error "Backend directory not found at ${BACKEND_DIR}"
        exit 1
    fi

    # Check frontend directory
    if [[ ! -d "${FRONTEND_DIR}" ]]; then
        log_error "Frontend directory not found at ${FRONTEND_DIR}"
        exit 1
    fi

    # Check frontend dependencies
    if [[ ! -d "${FRONTEND_DIR}/node_modules" ]]; then
        log_warning "Frontend dependencies not installed"
        log_info "Run: cd frontend && npm install"
        exit 1
    fi

    log_success "Prerequisites OK"
}

# Handle port conflicts
handle_port_conflict() {
    local port=$1
    local service=$2

    if check_port "$port"; then
        local pid=$(get_port_process "$port")
        log_warning "Port $port is already in use by process $pid"

        read -p "Kill existing process? (y/n) " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kill_port_process "$port"
            log_success "Port $port freed"
        else
            log_error "Cannot start $service - port $port is occupied"
            exit 1
        fi
    fi
}

# Start backend server
start_backend() {
    log_info "Starting backend server on port ${BACKEND_PORT}..."

    # Activate virtual environment and start server
    cd "${PROJECT_ROOT}"

    # Start backend in background with logging
    (
        source "${VENV_PATH}/bin/activate"
        cd "${BACKEND_DIR}"
        python3 -m uvicorn app:app \
            --host 0.0.0.0 \
            --port "${BACKEND_PORT}" \
            --log-level "${LOG_LEVEL,,}" \
            --reload \
            2>&1 | tee -a "${BACKEND_LOG}"
    ) &

    local backend_pid=$!

    # Wait for backend to start
    log_info "Waiting for backend to start (PID: ${backend_pid})..."
    local attempts=0
    local max_attempts=30

    while [[ $attempts -lt $max_attempts ]]; do
        if curl -s "http://localhost:${BACKEND_PORT}/api/rag/stats" >/dev/null 2>&1; then
            log_success "Backend started successfully (PID: ${backend_pid})"

            # Save PID to file
            local started_at=$(date -u +"%Y-%m-%dT%H:%M:%S")
            echo "$backend_pid" > "${PROJECT_ROOT}/.backend.pid"

            return 0
        fi

        # Check if process is still running
        if ! kill -0 "$backend_pid" 2>/dev/null; then
            log_error "Backend process died during startup"
            log_info "Check logs at: ${BACKEND_LOG}"
            exit 1
        fi

        sleep 1
        ((attempts++))
    done

    log_error "Backend failed to start within ${max_attempts} seconds"
    log_info "Check logs at: ${BACKEND_LOG}"
    kill "$backend_pid" 2>/dev/null || true
    exit 1
}

# Start frontend server
start_frontend() {
    log_info "Starting frontend dev server on port ${FRONTEND_PORT}..."

    cd "${FRONTEND_DIR}"

    # Start frontend in background with logging
    npm run dev -- --port "${FRONTEND_PORT}" 2>&1 | tee -a "${FRONTEND_LOG}" &

    local frontend_pid=$!

    # Wait for frontend to start
    log_info "Waiting for frontend to start (PID: ${frontend_pid})..."
    local attempts=0
    local max_attempts=30

    while [[ $attempts -lt $max_attempts ]]; do
        if curl -s "http://localhost:${FRONTEND_PORT}" >/dev/null 2>&1; then
            log_success "Frontend started successfully (PID: ${frontend_pid})"

            # Save PID to file
            echo "$frontend_pid" > "${PROJECT_ROOT}/.frontend.pid"

            return 0
        fi

        # Check if process is still running
        if ! kill -0 "$frontend_pid" 2>/dev/null; then
            log_error "Frontend process died during startup"
            log_info "Check logs at: ${FRONTEND_LOG}"
            exit 1
        fi

        sleep 1
        ((attempts++))
    done

    log_error "Frontend failed to start within ${max_attempts} seconds"
    log_info "Check logs at: ${FRONTEND_LOG}"
    kill "$frontend_pid" 2>/dev/null || true
    exit 1
}

# Save PIDs to JSON file
save_pids() {
    local backend_pid=""
    local frontend_pid=""

    if [[ -f "${PROJECT_ROOT}/.backend.pid" ]]; then
        backend_pid=$(cat "${PROJECT_ROOT}/.backend.pid")
    fi

    if [[ -f "${PROJECT_ROOT}/.frontend.pid" ]]; then
        frontend_pid=$(cat "${PROJECT_ROOT}/.frontend.pid")
    fi

    local started_at=$(date -u +"%Y-%m-%dT%H:%M:%S")

    cat > "${PID_FILE}" <<EOF
{
  "backend": {
    "pid": ${backend_pid:-null},
    "port": ${BACKEND_PORT},
    "started_at": "${started_at}",
    "log_file": "${BACKEND_LOG}"
  },
  "frontend": {
    "pid": ${frontend_pid:-null},
    "port": ${FRONTEND_PORT},
    "started_at": "${started_at}",
    "log_file": "${FRONTEND_LOG}"
  }
}
EOF

    log_success "PIDs saved to ${PID_FILE}"
}

# Cleanup function for Ctrl+C
cleanup() {
    echo ""
    log_warning "Received interrupt signal, shutting down..."

    if [[ -f "${PROJECT_ROOT}/.backend.pid" ]]; then
        local backend_pid=$(cat "${PROJECT_ROOT}/.backend.pid")
        if kill -0 "$backend_pid" 2>/dev/null; then
            log_info "Stopping backend (PID: ${backend_pid})..."
            kill -TERM "$backend_pid" 2>/dev/null || true
        fi
    fi

    if [[ -f "${PROJECT_ROOT}/.frontend.pid" ]]; then
        local frontend_pid=$(cat "${PROJECT_ROOT}/.frontend.pid")
        if kill -0 "$frontend_pid" 2>/dev/null; then
            log_info "Stopping frontend (PID: ${frontend_pid})..."
            kill -TERM "$frontend_pid" 2>/dev/null || true
        fi
    fi

    sleep 2
    log_success "Shutdown complete"
    exit 0
}

# Main execution
main() {
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║       Epstein Archive Development Environment         ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""

    # Register cleanup handler
    trap cleanup SIGINT SIGTERM

    # Ensure logs directory exists
    ensure_logs_dir

    # Handle restart flag
    if [[ "$RESTART" == true ]]; then
        log_info "Restarting servers..."
        if [[ -f "${PROJECT_ROOT}/scripts/dev-stop.sh" ]]; then
            "${PROJECT_ROOT}/scripts/dev-stop.sh"
            sleep 2
        fi
    fi

    # Handle status flag
    if [[ "$STATUS_ONLY" == true ]]; then
        if [[ -f "${PROJECT_ROOT}/scripts/dev-status.sh" ]]; then
            exec "${PROJECT_ROOT}/scripts/dev-status.sh"
        else
            log_error "dev-status.sh not found"
            exit 1
        fi
    fi

    # Check prerequisites
    check_prerequisites

    # Start backend
    if [[ "$FRONTEND_ONLY" != true ]]; then
        handle_port_conflict "$BACKEND_PORT" "backend"
        start_backend
    fi

    # Start frontend
    if [[ "$BACKEND_ONLY" != true ]]; then
        handle_port_conflict "$FRONTEND_PORT" "frontend"
        start_frontend
    fi

    # Save PIDs
    save_pids

    echo ""
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║                  Servers Running                       ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""

    if [[ "$FRONTEND_ONLY" != true ]]; then
        log_success "Backend:  http://localhost:${BACKEND_PORT}"
        log_info "  API:    http://localhost:${BACKEND_PORT}/api/rag/stats"
    fi

    if [[ "$BACKEND_ONLY" != true ]]; then
        log_success "Frontend: http://localhost:${FRONTEND_PORT}"
    fi

    echo ""
    log_info "Logs:"
    if [[ "$FRONTEND_ONLY" != true ]]; then
        echo "  Backend:  ${BACKEND_LOG}"
    fi
    if [[ "$BACKEND_ONLY" != true ]]; then
        echo "  Frontend: ${FRONTEND_LOG}"
    fi

    echo ""
    log_info "Press Ctrl+C to stop both servers"
    echo ""

    # Monitor processes
    while true; do
        sleep 5

        # Check backend
        if [[ "$FRONTEND_ONLY" != true ]] && [[ -f "${PROJECT_ROOT}/.backend.pid" ]]; then
            local backend_pid=$(cat "${PROJECT_ROOT}/.backend.pid")
            if ! kill -0 "$backend_pid" 2>/dev/null; then
                log_error "Backend process died unexpectedly!"
                log_info "Check logs at: ${BACKEND_LOG}"
                cleanup
            fi
        fi

        # Check frontend
        if [[ "$BACKEND_ONLY" != true ]] && [[ -f "${PROJECT_ROOT}/.frontend.pid" ]]; then
            local frontend_pid=$(cat "${PROJECT_ROOT}/.frontend.pid")
            if ! kill -0 "$frontend_pid" 2>/dev/null; then
                log_error "Frontend process died unexpectedly!"
                log_info "Check logs at: ${FRONTEND_LOG}"
                cleanup
            fi
        fi
    done
}

# Run main function
main
