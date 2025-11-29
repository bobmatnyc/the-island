#!/usr/bin/env bash
################################################################################
# dev-status.sh - Development Environment Status Monitor
#
# Checks health and status of Epstein Archive development servers.
# Provides detailed diagnostics including process status, port availability,
# health checks, memory usage, and recent logs.
#
# Usage:
#   ./scripts/dev-status.sh              # Full status report
#   ./scripts/dev-status.sh --compact    # Compact output
#   ./scripts/dev-status.sh --json       # JSON output
#
# Exit Codes:
#   0 - All services healthy
#   1 - One or more services have issues
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
readonly LOGS_DIR="${PROJECT_ROOT}/logs"
readonly BACKEND_LOG="${LOGS_DIR}/backend.log"
readonly FRONTEND_LOG="${LOGS_DIR}/frontend.log"

# Default ports
readonly BACKEND_PORT=8000
readonly FRONTEND_PORT=5173

# Parse command line arguments
COMPACT=false
JSON_OUTPUT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --compact)
            COMPACT=true
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        -h|--help)
            head -n 25 "$0" | grep "^#" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo -e "${ERROR_MARK} ${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Logging functions (only used in non-JSON mode)
log_info() {
    if [[ "$JSON_OUTPUT" != true ]]; then
        echo -e "${INFO_MARK} ${BLUE}$1${NC}"
    fi
}

log_success() {
    if [[ "$JSON_OUTPUT" != true ]]; then
        echo -e "${CHECK_MARK} ${GREEN}$1${NC}"
    fi
}

log_warning() {
    if [[ "$JSON_OUTPUT" != true ]]; then
        echo -e "${WARNING}${YELLOW}$1${NC}"
    fi
}

log_error() {
    if [[ "$JSON_OUTPUT" != true ]]; then
        echo -e "${ERROR_MARK} ${RED}$1${NC}"
    fi
}

# Check if process is running
check_process() {
    local pid=$1
    if kill -0 "$pid" 2>/dev/null; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

# Get process uptime
get_uptime() {
    local pid=$1

    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS
        local start_time=$(ps -p "$pid" -o lstart= 2>/dev/null || echo "")
        if [[ -z "$start_time" ]]; then
            echo "N/A"
            return
        fi

        local start_epoch=$(date -j -f "%a %b %d %T %Y" "$start_time" +%s 2>/dev/null || echo "0")
        local now_epoch=$(date +%s)
        local uptime_seconds=$((now_epoch - start_epoch))
    else
        # Linux
        local start_seconds=$(ps -p "$pid" -o etimes= 2>/dev/null | tr -d ' ' || echo "0")
        local uptime_seconds=$start_seconds
    fi

    # Format uptime
    local hours=$((uptime_seconds / 3600))
    local minutes=$(((uptime_seconds % 3600) / 60))

    if [[ $hours -gt 0 ]]; then
        echo "${hours}h ${minutes}m"
    else
        echo "${minutes}m"
    fi
}

# Get process memory usage (in MB)
get_memory_usage() {
    local pid=$1

    if [[ "$(uname)" == "Darwin" ]]; then
        # macOS - RSS in KB
        local mem_kb=$(ps -p "$pid" -o rss= 2>/dev/null | tr -d ' ' || echo "0")
        local mem_mb=$((mem_kb / 1024))
    else
        # Linux - RSS in KB
        local mem_kb=$(ps -p "$pid" -o rss= 2>/dev/null | tr -d ' ' || echo "0")
        local mem_mb=$((mem_kb / 1024))
    fi

    echo "${mem_mb} MB"
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

# Health check backend
health_check_backend() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${BACKEND_PORT}/api/rag/stats" 2>/dev/null || echo "000")

    if [[ "$response" == "200" ]]; then
        # Get actual stats
        local stats=$(curl -s "http://localhost:${BACKEND_PORT}/api/rag/stats" 2>/dev/null || echo "{}")
        echo "$stats"
        return 0
    else
        echo "{\"error\": \"HTTP $response\"}"
        return 1
    fi
}

# Health check frontend
health_check_frontend() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${FRONTEND_PORT}" 2>/dev/null || echo "000")

    if [[ "$response" == "200" ]]; then
        echo "{\"status\": \"ok\"}"
        return 0
    else
        echo "{\"error\": \"HTTP $response\"}"
        return 1
    fi
}

# Get recent logs
get_recent_logs() {
    local log_file=$1
    local num_lines=${2:-10}

    if [[ -f "$log_file" ]]; then
        tail -n "$num_lines" "$log_file" 2>/dev/null | sed 's/^/  /'
    else
        echo "  (No log file found)"
    fi
}

# Get backend status
get_backend_status() {
    local status="stopped"
    local pid="N/A"
    local uptime="N/A"
    local memory="N/A"
    local health="N/A"
    local health_data="{}"

    if [[ -f "${BACKEND_PID_FILE}" ]]; then
        pid=$(cat "${BACKEND_PID_FILE}")

        if check_process "$pid"; then
            status="running"
            uptime=$(get_uptime "$pid")
            memory=$(get_memory_usage "$pid")

            # Health check
            if health_data=$(health_check_backend); then
                health="ok"
            else
                health="error"
            fi
        fi
    fi

    # Return as JSON
    cat <<EOF
{
  "status": "$status",
  "pid": "$pid",
  "port": $BACKEND_PORT,
  "uptime": "$uptime",
  "memory": "$memory",
  "health": "$health",
  "health_data": $health_data
}
EOF
}

# Get frontend status
get_frontend_status() {
    local status="stopped"
    local pid="N/A"
    local uptime="N/A"
    local memory="N/A"
    local health="N/A"

    if [[ -f "${FRONTEND_PID_FILE}" ]]; then
        pid=$(cat "${FRONTEND_PID_FILE}")

        if check_process "$pid"; then
            status="running"
            uptime=$(get_uptime "$pid")
            memory=$(get_memory_usage "$pid")

            # Health check
            if health_check_frontend >/dev/null; then
                health="ok"
            else
                health="error"
            fi
        fi
    fi

    # Return as JSON
    cat <<EOF
{
  "status": "$status",
  "pid": "$pid",
  "port": $FRONTEND_PORT,
  "uptime": "$uptime",
  "memory": "$memory",
  "health": "$health"
}
EOF
}

# Output in JSON format
output_json() {
    local backend_status=$(get_backend_status)
    local frontend_status=$(get_frontend_status)

    cat <<EOF
{
  "backend": $backend_status,
  "frontend": $frontend_status,
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
}

# Output in human-readable format
output_human() {
    local backend_status=$(get_backend_status)
    local frontend_status=$(get_frontend_status)

    # Parse JSON (using python for portability)
    local backend_running=$(echo "$backend_status" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
    local backend_pid=$(echo "$backend_status" | python3 -c "import sys, json; print(json.load(sys.stdin)['pid'])")
    local backend_uptime=$(echo "$backend_status" | python3 -c "import sys, json; print(json.load(sys.stdin)['uptime'])")
    local backend_memory=$(echo "$backend_status" | python3 -c "import sys, json; print(json.load(sys.stdin)['memory'])")
    local backend_health=$(echo "$backend_status" | python3 -c "import sys, json; print(json.load(sys.stdin)['health'])")

    local frontend_running=$(echo "$frontend_status" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
    local frontend_pid=$(echo "$frontend_status" | python3 -c "import sys, json; print(json.load(sys.stdin)['pid'])")
    local frontend_uptime=$(echo "$frontend_status" | python3 -c "import sys, json; print(json.load(sys.stdin)['uptime'])")
    local frontend_memory=$(echo "$frontend_status" | python3 -c "import sys, json; print(json.load(sys.stdin)['memory'])")
    local frontend_health=$(echo "$frontend_status" | python3 -c "import sys, json; print(json.load(sys.stdin)['health'])")

    echo "╔════════════════════════════════════════════════════════╗"
    echo "║         Epstein Archive Development Status            ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""

    # Backend status
    echo -n "Backend (Port ${BACKEND_PORT}):  "
    if [[ "$backend_running" == "running" ]]; then
        if [[ "$backend_health" == "ok" ]]; then
            log_success "Running (PID: ${backend_pid}, Uptime: ${backend_uptime})"
        else
            log_warning "Running but unhealthy (PID: ${backend_pid})"
        fi
    else
        log_error "Stopped"
    fi

    if [[ "$backend_running" == "running" ]]; then
        echo "  Health: $(if [[ "$backend_health" == "ok" ]]; then echo -e "${CHECK_MARK} OK"; else echo -e "${ERROR_MARK} Error"; fi)"
        echo "  Memory: ${backend_memory}"

        # Show health data
        if [[ "$backend_health" == "ok" ]]; then
            local doc_count=$(echo "$backend_status" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('health_data', {}).get('document_count', 'N/A'))" 2>/dev/null || echo "N/A")
            if [[ "$doc_count" != "N/A" ]]; then
                echo "  Documents: ${doc_count}"
            fi
        fi

        echo ""
    fi

    # Frontend status
    echo -n "Frontend (Port ${FRONTEND_PORT}): "
    if [[ "$frontend_running" == "running" ]]; then
        if [[ "$frontend_health" == "ok" ]]; then
            log_success "Running (PID: ${frontend_pid}, Uptime: ${frontend_uptime})"
        else
            log_warning "Running but unhealthy (PID: ${frontend_pid})"
        fi
    else
        log_error "Stopped"
    fi

    if [[ "$frontend_running" == "running" ]]; then
        echo "  Health: $(if [[ "$frontend_health" == "ok" ]]; then echo -e "${CHECK_MARK} OK"; else echo -e "${ERROR_MARK} Error"; fi)"
        echo "  Memory: ${frontend_memory}"
        echo ""
    fi

    # Show recent logs if not compact
    if [[ "$COMPACT" != true ]]; then
        if [[ "$backend_running" == "running" ]] && [[ -f "$BACKEND_LOG" ]]; then
            echo "Recent Backend Logs:"
            get_recent_logs "$BACKEND_LOG" 5
            echo ""
        fi

        if [[ "$frontend_running" == "running" ]] && [[ -f "$FRONTEND_LOG" ]]; then
            echo "Recent Frontend Logs:"
            get_recent_logs "$FRONTEND_LOG" 5
            echo ""
        fi
    fi

    # Overall status
    if [[ "$backend_running" == "running" ]] && [[ "$frontend_running" == "running" ]] && \
       [[ "$backend_health" == "ok" ]] && [[ "$frontend_health" == "ok" ]]; then
        log_success "All services healthy"
        return 0
    elif [[ "$backend_running" == "stopped" ]] && [[ "$frontend_running" == "stopped" ]]; then
        log_warning "No services running"
        return 1
    else
        log_warning "Some services have issues"
        return 1
    fi
}

# Main execution
main() {
    if [[ "$JSON_OUTPUT" == true ]]; then
        output_json
        exit 0
    else
        if output_human; then
            exit 0
        else
            exit 1
        fi
    fi
}

# Run main function
main
