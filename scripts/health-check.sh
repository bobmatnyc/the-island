#!/usr/bin/env bash
################################################################################
# health-check.sh - Quick Health Check for Monitoring Systems
#
# Fast health check script for monitoring systems (Nagios, Datadog, etc.).
# Completes in under 2 seconds and returns appropriate exit codes.
#
# Exit Codes:
#   0 - All critical services healthy
#   1 - One or more critical services down
#   2 - Partial failure (non-critical issues)
#
# Usage:
#   ./scripts/health-check.sh           # Quick health check
#   ./scripts/health-check.sh --verbose # Show details
#   ./scripts/health-check.sh --timeout 5  # Custom timeout (seconds)
#
# Author: Epstein Archive Development Team
# Date: 2025-11-20
################################################################################

set -euo pipefail

# Default configuration
readonly BACKEND_PORT="${BACKEND_PORT:-8000}"
readonly FRONTEND_PORT="${FRONTEND_PORT:-5173}"
DEFAULT_TIMEOUT=2
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --timeout|-t)
            DEFAULT_TIMEOUT="$2"
            shift 2
            ;;
        -h|--help)
            head -n 25 "$0" | grep "^#" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Logging functions
log() {
    if [[ "$VERBOSE" == true ]]; then
        echo "$1"
    fi
}

log_error() {
    echo "ERROR: $1" >&2
}

# Check endpoint with timeout
check_endpoint() {
    local url="$1"
    local timeout="$2"

    local response=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$timeout" "$url" 2>/dev/null || echo "000")

    if [[ "$response" == "200" ]]; then
        return 0
    else
        return 1
    fi
}

# Check backend health
check_backend() {
    log "Checking backend (port ${BACKEND_PORT})..."

    # Check /api/rag/stats endpoint
    if check_endpoint "http://localhost:${BACKEND_PORT}/api/rag/stats" "$DEFAULT_TIMEOUT"; then
        log "✓ Backend healthy"
        return 0
    else
        log_error "Backend not responding"
        return 1
    fi
}

# Check frontend health
check_frontend() {
    log "Checking frontend (port ${FRONTEND_PORT})..."

    # Check root endpoint
    if check_endpoint "http://localhost:${FRONTEND_PORT}" "$DEFAULT_TIMEOUT"; then
        log "✓ Frontend healthy"
        return 0
    else
        log_error "Frontend not responding"
        return 1
    fi
}

# Check vector store (if applicable)
check_vector_store() {
    log "Checking vector store accessibility..."

    # Try to get news stats (lightweight endpoint)
    if check_endpoint "http://localhost:${BACKEND_PORT}/api/news/stats" "$DEFAULT_TIMEOUT"; then
        log "✓ Vector store accessible"
        return 0
    else
        log "⚠ Vector store may not be accessible (non-critical)"
        return 2  # Non-critical warning
    fi
}

# Main health check
main() {
    local exit_code=0
    local failed_services=()

    # Check backend (critical)
    if ! check_backend; then
        failed_services+=("backend")
        exit_code=1
    fi

    # Check frontend (critical)
    if ! check_frontend; then
        failed_services+=("frontend")
        exit_code=1
    fi

    # Check vector store (non-critical)
    vector_status=0
    check_vector_store || vector_status=$?

    if [[ $vector_status -eq 2 ]] && [[ $exit_code -eq 0 ]]; then
        # Only vector store has issues
        exit_code=2
    fi

    # Output results
    if [[ $exit_code -eq 0 ]]; then
        if [[ "$VERBOSE" == true ]]; then
            echo "OK - All services healthy"
        fi
        exit 0
    elif [[ $exit_code -eq 1 ]]; then
        echo "CRITICAL - Failed services: ${failed_services[*]}"
        exit 1
    else
        echo "WARNING - Non-critical issues detected"
        exit 2
    fi
}

# Run main function
main
