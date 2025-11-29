#!/usr/bin/env bash
################################################################################
# dev-logs.sh - Development Log Viewer
#
# Tail and display logs from backend and frontend servers with color coding.
# Provides filtering and search capabilities for easier debugging.
#
# Usage:
#   ./scripts/dev-logs.sh                   # Follow both servers
#   ./scripts/dev-logs.sh --backend-only    # Only backend logs
#   ./scripts/dev-logs.sh --frontend-only   # Only frontend logs
#   ./scripts/dev-logs.sh --last 50         # Last 50 lines from each
#   ./scripts/dev-logs.sh --errors-only     # Only error messages
#   ./scripts/dev-logs.sh --grep "keyword"  # Filter by keyword
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
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Project paths
readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly LOGS_DIR="${PROJECT_ROOT}/logs"
readonly BACKEND_LOG="${LOGS_DIR}/backend.log"
readonly FRONTEND_LOG="${LOGS_DIR}/frontend.log"

# Parse command line arguments
BACKEND_ONLY=false
FRONTEND_ONLY=false
FOLLOW=true
NUM_LINES=20
ERRORS_ONLY=false
GREP_PATTERN=""

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
        --last)
            FOLLOW=false
            NUM_LINES="$2"
            shift 2
            ;;
        --errors-only)
            ERRORS_ONLY=true
            shift
            ;;
        --grep)
            GREP_PATTERN="$2"
            shift 2
            ;;
        --no-follow)
            FOLLOW=false
            shift
            ;;
        -h|--help)
            head -n 25 "$0" | grep "^#" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Check if log files exist
check_log_files() {
    local files_exist=true

    if [[ "$FRONTEND_ONLY" != true ]] && [[ ! -f "$BACKEND_LOG" ]]; then
        echo -e "${RED}Backend log file not found: $BACKEND_LOG${NC}"
        files_exist=false
    fi

    if [[ "$BACKEND_ONLY" != true ]] && [[ ! -f "$FRONTEND_LOG" ]]; then
        echo -e "${RED}Frontend log file not found: $FRONTEND_LOG${NC}"
        files_exist=false
    fi

    if [[ "$files_exist" != true ]]; then
        echo -e "${YELLOW}Hint: Start the dev servers with ./scripts/dev-start.sh${NC}"
        exit 1
    fi
}

# Colorize log line based on content
colorize_line() {
    local line="$1"
    local service="$2"

    # Service prefix
    local prefix=""
    if [[ "$service" == "backend" ]]; then
        prefix="${BLUE}[BACKEND]${NC} "
    else
        prefix="${GREEN}[FRONTEND]${NC} "
    fi

    # Color based on log level
    if echo "$line" | grep -qi "error\|exception\|failed\|fatal"; then
        echo -e "${prefix}${RED}${line}${NC}"
    elif echo "$line" | grep -qi "warn\|warning"; then
        echo -e "${prefix}${YELLOW}${line}${NC}"
    elif echo "$line" | grep -qi "info\|started\|listening"; then
        echo -e "${prefix}${CYAN}${line}${NC}"
    else
        echo -e "${prefix}${line}"
    fi
}

# Process log line with filters
process_line() {
    local line="$1"
    local service="$2"

    # Apply error filter
    if [[ "$ERRORS_ONLY" == true ]]; then
        if ! echo "$line" | grep -qi "error\|exception\|failed\|fatal\|warn"; then
            return
        fi
    fi

    # Apply grep filter
    if [[ -n "$GREP_PATTERN" ]]; then
        if ! echo "$line" | grep -qi "$GREP_PATTERN"; then
            return
        fi
    fi

    # Colorize and output
    colorize_line "$line" "$service"
}

# Tail logs (follow mode)
tail_logs_follow() {
    echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           Following Development Logs                  ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""

    # Build tail command based on options
    if [[ "$BACKEND_ONLY" == true ]]; then
        tail -f "$BACKEND_LOG" | while IFS= read -r line; do
            process_line "$line" "backend"
        done
    elif [[ "$FRONTEND_ONLY" == true ]]; then
        tail -f "$FRONTEND_LOG" | while IFS= read -r line; do
            process_line "$line" "frontend"
        done
    else
        # Follow both logs with labels
        (tail -f "$BACKEND_LOG" | while IFS= read -r line; do
            process_line "$line" "backend"
        done) &

        (tail -f "$FRONTEND_LOG" | while IFS= read -r line; do
            process_line "$line" "frontend"
        done) &

        # Wait for both background processes
        wait
    fi
}

# Show last N lines
show_last_lines() {
    echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║            Recent Development Logs                     ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""

    if [[ "$FRONTEND_ONLY" != true ]]; then
        echo -e "${BLUE}━━━ Backend Logs (Last ${NUM_LINES} lines) ━━━${NC}"
        echo ""
        tail -n "$NUM_LINES" "$BACKEND_LOG" | while IFS= read -r line; do
            process_line "$line" "backend"
        done
        echo ""
    fi

    if [[ "$BACKEND_ONLY" != true ]]; then
        echo -e "${GREEN}━━━ Frontend Logs (Last ${NUM_LINES} lines) ━━━${NC}"
        echo ""
        tail -n "$NUM_LINES" "$FRONTEND_LOG" | while IFS= read -r line; do
            process_line "$line" "frontend"
        done
        echo ""
    fi
}

# Main execution
main() {
    # Check log files exist
    check_log_files

    # Show logs based on mode
    if [[ "$FOLLOW" == true ]]; then
        tail_logs_follow
    else
        show_last_lines
    fi
}

# Run main function
main
