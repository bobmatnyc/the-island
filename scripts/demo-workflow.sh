#!/usr/bin/env bash
################################################################################
# demo-workflow.sh - Demonstration of DevOps Scripts Workflow
#
# This script demonstrates the typical development workflow using the DevOps
# scripts. It's for demonstration purposes only - in real usage, you would
# run these commands manually as needed.
#
# Usage:
#   ./scripts/demo-workflow.sh
#
# Author: Epstein Archive Development Team
# Date: 2025-11-20
################################################################################

set -euo pipefail

# Color codes
readonly GREEN='\033[0;32m'
readonly BLUE='\033[0;34m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

# Project root
readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Logging
log_step() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}▶ $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

log_info() {
    echo -e "${YELLOW}$1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

pause() {
    echo ""
    log_info "Press Enter to continue..."
    read -r
}

# Main demonstration
main() {
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║       Epstein Archive DevOps Workflow Demo            ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""
    log_info "This demo will show you the typical development workflow."
    echo ""
    pause

    # Step 1: Check current status
    log_step "STEP 1: Check Current Status"
    log_info "Before starting, let's check if anything is already running..."
    echo ""
    echo "$ ./scripts/dev-status.sh --compact"
    echo ""
    "${PROJECT_ROOT}/scripts/dev-status.sh" --compact || true
    pause

    # Step 2: Start development environment
    log_step "STEP 2: Start Development Environment"
    log_info "Starting both backend and frontend servers..."
    echo ""
    echo "$ ./scripts/dev-start.sh"
    echo ""
    log_info "In real usage, this would start the servers."
    log_info "For this demo, we'll skip the actual startup."
    log_success "Servers started (simulated)"
    pause

    # Step 3: Monitor status
    log_step "STEP 3: Monitor Status"
    log_info "Check the status of running services..."
    echo ""
    echo "$ ./scripts/dev-status.sh"
    echo ""
    log_info "This would show detailed status of both services."
    pause

    # Step 4: View logs
    log_step "STEP 4: View Logs"
    log_info "View real-time logs from both servers..."
    echo ""
    echo "$ ./scripts/dev-logs.sh"
    echo ""
    log_info "This would tail logs from backend and frontend."
    log_info "You can filter with: --errors-only, --grep 'pattern', etc."
    pause

    # Step 5: Health check
    log_step "STEP 5: Health Check"
    log_info "Quick health check of all services..."
    echo ""
    echo "$ ./scripts/health-check.sh --verbose"
    echo ""
    "${PROJECT_ROOT}/scripts/health-check.sh" --verbose || true
    pause

    # Step 6: Development workflow
    log_step "STEP 6: Development Workflow"
    log_info "During development:"
    echo "  1. Make code changes"
    echo "  2. Servers auto-reload"
    echo "  3. Monitor logs: ./scripts/dev-logs.sh --errors-only"
    echo "  4. Check status: ./scripts/dev-status.sh --compact"
    echo "  5. Debug issues: ./scripts/dev-logs.sh --grep 'error'"
    pause

    # Step 7: Deployment
    log_step "STEP 7: Deployment Workflow"
    log_info "When ready to deploy:"
    echo ""
    echo "$ ./scripts/deploy.sh --dry-run"
    log_info "(Test deployment without actually deploying)"
    echo ""
    echo "$ ./scripts/deploy.sh --env staging"
    log_info "(Deploy to staging environment)"
    echo ""
    echo "$ ./scripts/deploy.sh --env production"
    log_info "(Deploy to production - requires confirmation)"
    pause

    # Step 8: Troubleshooting
    log_step "STEP 8: Troubleshooting"
    log_info "If something goes wrong:"
    echo ""
    echo "# Port already in use"
    echo "$ ./scripts/dev-stop.sh --force"
    echo ""
    echo "# View error logs"
    echo "$ ./scripts/dev-logs.sh --errors-only"
    echo ""
    echo "# Check what's wrong"
    echo "$ ./scripts/dev-status.sh --verbose"
    echo ""
    echo "# Restart everything"
    echo "$ ./scripts/dev-start.sh --restart"
    pause

    # Step 9: Stop development
    log_step "STEP 9: Stop Development Environment"
    log_info "When done developing, gracefully stop servers..."
    echo ""
    echo "$ ./scripts/dev-stop.sh"
    echo ""
    log_info "In real usage, this would stop both servers."
    log_success "Servers stopped (simulated)"
    pause

    # Summary
    log_step "SUMMARY: Available Scripts"
    echo ""
    echo "Development Scripts:"
    echo "  • dev-start.sh      - Start development servers"
    echo "  • dev-stop.sh       - Stop development servers"
    echo "  • dev-status.sh     - Check status"
    echo "  • dev-logs.sh       - View logs"
    echo ""
    echo "Monitoring Scripts:"
    echo "  • health-check.sh   - Quick health check"
    echo ""
    echo "Deployment Scripts:"
    echo "  • deploy.sh         - Production deployment"
    echo ""
    echo "Documentation:"
    echo "  • scripts/DEVOPS_README.md          - Full documentation"
    echo "  • DEVOPS_QUICK_REF.md               - Quick reference"
    echo "  • DEVOPS_VISUAL_GUIDE.md            - Visual guide"
    echo "  • DEVOPS_IMPLEMENTATION_SUMMARY.md  - Implementation report"
    echo ""
    log_success "Demo complete!"
    echo ""
    log_info "Try running the scripts yourself:"
    echo "  ./scripts/dev-start.sh"
    echo ""
}

# Run main
main
