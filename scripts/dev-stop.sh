#!/usr/bin/env bash
################################################################################
# dev-stop.sh - Development Environment Shutdown Script
#
# Gracefully stops the Epstein Archive development servers.
# Reads PIDs from .dev-pids and terminates processes cleanly.
#
# Usage:
#   ./scripts/dev-stop.sh                # Stop all servers
#   ./scripts/dev-stop.sh --backend      # Stop only backend
#   ./scripts/dev-stop.sh --frontend     # Stop only frontend
#   ./scripts/dev-stop.sh --force        # Force kill if graceful fails
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
readonly PID_FILE="${PROJECT_ROOT}/.dev-pids"
readonly BACKEND_PID_FILE="${PROJECT_ROOT}/.backend.pid"
readonly FRONTEND_PID_FILE="${PROJECT_ROOT}/.frontend.pid"

# Parse command line arguments
BACKEND_ONLY=false
FRONTEND_ONLY=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend)
            BACKEND_ONLY=true
            shift
            ;;
        --frontend)
            FRONTEND_ONLY=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            head -n 20 "$0" | grep "^#" | sed 's/^# \?//'
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

# Stop process gracefully or forcefully
stop_process() {
    local pid=$1
    local name=$2
    local timeout=10

    if ! kill -0 "$pid" 2>/dev/null; then
        log_warning "$name process (PID: $pid) is not running"
        return 0
    fi

    log_info "Stopping $name (PID: $pid)..."

    # Try graceful shutdown first
    kill -TERM "$pid" 2>/dev/null || true

    # Wait for process to terminate
    local elapsed=0
    while kill -0 "$pid" 2>/dev/null; do
        if [[ $elapsed -ge $timeout ]]; then
            if [[ "$FORCE" == true ]]; then
                log_warning "Graceful shutdown timeout, force killing $name..."
                kill -KILL "$pid" 2>/dev/null || true
                sleep 1
                break
            else
                log_error "Graceful shutdown timeout for $name"
                log_info "Use --force flag to force kill"
                return 1
            fi
        fi

        sleep 1
        ((elapsed++))
    done

    if ! kill -0 "$pid" 2>/dev/null; then
        log_success "$name stopped successfully"
        return 0
    else
        log_error "Failed to stop $name"
        return 1
    fi
}

# Check if port is free
check_port_freed() {
    local port=$1
    local name=$2

    if lsof -Pi :${port} -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        log_warning "Port $port still in use after stopping $name"
        return 1
    else
        log_success "Port $port freed"
        return 0
    fi
}

# Stop backend server
stop_backend() {
    if [[ ! -f "${BACKEND_PID_FILE}" ]]; then
        log_warning "Backend PID file not found (not running?)"
        return 0
    fi

    local pid=$(cat "${BACKEND_PID_FILE}")

    if stop_process "$pid" "Backend"; then
        rm -f "${BACKEND_PID_FILE}"

        # Check if port is freed
        sleep 1
        check_port_freed 8000 "backend" || true
    fi
}

# Stop frontend server
stop_frontend() {
    if [[ ! -f "${FRONTEND_PID_FILE}" ]]; then
        log_warning "Frontend PID file not found (not running?)"
        return 0
    fi

    local pid=$(cat "${FRONTEND_PID_FILE}")

    if stop_process "$pid" "Frontend"; then
        rm -f "${FRONTEND_PID_FILE}"

        # Check if port is freed
        sleep 1
        check_port_freed 5173 "frontend" || true
    fi
}

# Cleanup PID files
cleanup_pid_files() {
    if [[ -f "${PID_FILE}" ]]; then
        rm -f "${PID_FILE}"
        log_success "Cleaned up PID file"
    fi

    if [[ -f "${BACKEND_PID_FILE}" ]]; then
        rm -f "${BACKEND_PID_FILE}"
    fi

    if [[ -f "${FRONTEND_PID_FILE}" ]]; then
        rm -f "${FRONTEND_PID_FILE}"
    fi
}

# Verify all processes stopped
verify_stopped() {
    local all_stopped=true

    if [[ "$FRONTEND_ONLY" != true ]]; then
        if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
            log_warning "Backend port 8000 still in use"
            all_stopped=false
        fi
    fi

    if [[ "$BACKEND_ONLY" != true ]]; then
        if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
            log_warning "Frontend port 5173 still in use"
            all_stopped=false
        fi
    fi

    if [[ "$all_stopped" == true ]]; then
        log_success "All services stopped cleanly"
        return 0
    else
        log_warning "Some ports may still be in use"
        return 1
    fi
}

# Main execution
main() {
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║       Stopping Epstein Archive Dev Environment        ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""

    # Check if anything is running
    if [[ ! -f "${BACKEND_PID_FILE}" ]] && [[ ! -f "${FRONTEND_PID_FILE}" ]]; then
        log_warning "No running processes found"
        cleanup_pid_files
        exit 0
    fi

    # Stop services based on flags
    if [[ "$FRONTEND_ONLY" == true ]]; then
        stop_frontend
    elif [[ "$BACKEND_ONLY" == true ]]; then
        stop_backend
    else
        # Stop both
        if [[ -f "${BACKEND_PID_FILE}" ]]; then
            stop_backend
        fi

        if [[ -f "${FRONTEND_PID_FILE}" ]]; then
            stop_frontend
        fi
    fi

    # Cleanup PID files
    if [[ "$FRONTEND_ONLY" != true ]] && [[ "$BACKEND_ONLY" != true ]]; then
        cleanup_pid_files
    fi

    echo ""

    # Verify everything stopped
    verify_stopped

    echo ""
    log_success "Shutdown complete"
}

# Run main function
main
