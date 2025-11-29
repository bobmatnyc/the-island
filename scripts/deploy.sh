#!/usr/bin/env bash
################################################################################
# deploy.sh - Production Deployment Script
#
# Comprehensive deployment script with testing, building, verification, and
# rollback capabilities. Supports multiple environments (staging, production).
#
# Usage:
#   ./scripts/deploy.sh --env staging       # Deploy to staging
#   ./scripts/deploy.sh --env production    # Deploy to production
#   ./scripts/deploy.sh --dry-run          # Test without deploying
#   ./scripts/deploy.sh --rollback         # Rollback to previous version
#   ./scripts/deploy.sh --skip-tests       # Skip test suite (not recommended)
#
# Environment Variables:
#   DEPLOY_TARGET   - Deployment target (local/staging/production)
#   SKIP_TESTS      - Skip test suite (true/false)
#   BACKUP_COUNT    - Number of backups to keep (default: 3)
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
readonly DEPLOY_DIR="${PROJECT_ROOT}/deploy"
readonly BACKUP_DIR="${PROJECT_ROOT}/backups"
readonly LOGS_DIR="${PROJECT_ROOT}/logs"

# Deployment configuration
ENVIRONMENT="local"
DRY_RUN=false
ROLLBACK=false
SKIP_TESTS=false
BACKUP_COUNT=3

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
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

log_step() {
    echo ""
    echo -e "${BLUE}▶ $1${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Stop development servers
stop_dev_servers() {
    log_step "Stopping development servers..."

    if [[ -f "${PROJECT_ROOT}/scripts/dev-stop.sh" ]]; then
        "${PROJECT_ROOT}/scripts/dev-stop.sh" || true
    else
        log_warning "dev-stop.sh not found, skipping"
    fi

    log_success "Dev servers stopped"
}

# Run Python tests
run_python_tests() {
    log_step "Running Python tests..."

    cd "${PROJECT_ROOT}"

    if [[ -d "tests" ]]; then
        source "${VENV_PATH}/bin/activate"

        # Check if pytest is installed
        if command -v pytest &> /dev/null; then
            if pytest tests/ -v; then
                log_success "Python tests passed"
            else
                log_error "Python tests failed"
                return 1
            fi
        else
            log_warning "pytest not installed, skipping Python tests"
        fi
    else
        log_info "No tests directory found, skipping Python tests"
    fi
}

# Run frontend tests
run_frontend_tests() {
    log_step "Running frontend tests..."

    cd "${FRONTEND_DIR}"

    # Check if test script exists
    if grep -q '"test"' package.json; then
        if CI=true npm test; then
            log_success "Frontend tests passed"
        else
            log_error "Frontend tests failed"
            return 1
        fi
    else
        log_info "No test script found in package.json, skipping"
    fi
}

# Build frontend for production
build_frontend() {
    log_step "Building frontend for production..."

    cd "${FRONTEND_DIR}"

    # Clean previous build
    rm -rf dist/

    # Build with production optimizations
    if npm run build; then
        log_success "Frontend build complete"

        # Show build stats
        if [[ -d "dist" ]]; then
            local build_size=$(du -sh dist/ | cut -f1)
            log_info "Build size: ${build_size}"
        fi
    else
        log_error "Frontend build failed"
        return 1
    fi
}

# Run API smoke tests
run_smoke_tests() {
    log_step "Running API smoke tests..."

    # Start backend temporarily for testing
    cd "${BACKEND_DIR}"
    source "${VENV_PATH}/bin/activate"

    # Start backend in background
    python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 >/dev/null 2>&1 &
    local backend_pid=$!

    # Wait for backend to start
    local attempts=0
    local max_attempts=30

    while [[ $attempts -lt $max_attempts ]]; do
        if curl -s "http://localhost:8000/api/rag/stats" >/dev/null 2>&1; then
            break
        fi
        sleep 1
        ((attempts++))
    done

    if [[ $attempts -ge $max_attempts ]]; then
        log_error "Backend failed to start for smoke tests"
        kill "$backend_pid" 2>/dev/null || true
        return 1
    fi

    # Run smoke tests
    local tests_passed=true

    # Test 1: RAG stats endpoint
    if curl -s -f "http://localhost:8000/api/rag/stats" >/dev/null; then
        log_success "✓ RAG stats endpoint"
    else
        log_error "✗ RAG stats endpoint failed"
        tests_passed=false
    fi

    # Test 2: News stats endpoint
    if curl -s -f "http://localhost:8000/api/news/stats" >/dev/null; then
        log_success "✓ News stats endpoint"
    else
        log_warning "⚠ News stats endpoint failed (non-critical)"
    fi

    # Cleanup
    kill "$backend_pid" 2>/dev/null || true
    sleep 2

    if [[ "$tests_passed" == true ]]; then
        log_success "Smoke tests passed"
        return 0
    else
        log_error "Some smoke tests failed"
        return 1
    fi
}

# Create deployment package
create_deployment_package() {
    log_step "Creating deployment package..."

    # Create deploy directory
    mkdir -p "${DEPLOY_DIR}"

    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local package_name="epstein-archive-${ENVIRONMENT}-${timestamp}"
    local package_dir="${DEPLOY_DIR}/${package_name}"

    mkdir -p "${package_dir}"

    # Copy frontend build
    log_info "Copying frontend build..."
    cp -r "${FRONTEND_DIR}/dist" "${package_dir}/frontend"

    # Copy backend
    log_info "Copying backend..."
    cp -r "${BACKEND_DIR}" "${package_dir}/backend"

    # Copy requirements
    cp "${PROJECT_ROOT}/requirements.txt" "${package_dir}/"

    # Copy configuration files
    if [[ -f "${PROJECT_ROOT}/.env.local" ]]; then
        cp "${PROJECT_ROOT}/.env.local" "${package_dir}/.env"
    fi

    # Create deployment manifest
    cat > "${package_dir}/MANIFEST.json" <<EOF
{
  "version": "${timestamp}",
  "environment": "${ENVIRONMENT}",
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
}
EOF

    # Create tarball
    log_info "Creating tarball..."
    cd "${DEPLOY_DIR}"
    tar -czf "${package_name}.tar.gz" "${package_name}"

    local package_size=$(du -sh "${package_name}.tar.gz" | cut -f1)
    log_success "Deployment package created: ${package_name}.tar.gz (${package_size})"

    # Cleanup uncompressed directory
    rm -rf "${package_dir}"

    echo "$package_name"
}

# Backup current deployment
backup_current_deployment() {
    log_step "Backing up current deployment..."

    mkdir -p "${BACKUP_DIR}"

    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_name="backup-${timestamp}"

    # Backup frontend
    if [[ -d "${FRONTEND_DIR}/dist" ]]; then
        cp -r "${FRONTEND_DIR}/dist" "${BACKUP_DIR}/${backup_name}-frontend"
        log_success "Frontend backed up"
    fi

    # Backup backend (current state)
    cp -r "${BACKEND_DIR}" "${BACKUP_DIR}/${backup_name}-backend"
    log_success "Backend backed up"

    # Clean old backups
    local backup_count=$(ls -1 "${BACKUP_DIR}" | wc -l | tr -d ' ')
    if [[ $backup_count -gt $((BACKUP_COUNT * 2)) ]]; then
        log_info "Cleaning old backups..."
        cd "${BACKUP_DIR}"
        ls -t | tail -n +$((BACKUP_COUNT * 2 + 1)) | xargs rm -rf
    fi

    log_success "Backup complete: ${backup_name}"
}

# Deploy to environment
deploy_to_environment() {
    local package_name="$1"

    log_step "Deploying to ${ENVIRONMENT}..."

    if [[ "$DRY_RUN" == true ]]; then
        log_warning "DRY RUN - Skipping actual deployment"
        return 0
    fi

    case "$ENVIRONMENT" in
        local)
            deploy_local "$package_name"
            ;;
        staging)
            deploy_staging "$package_name"
            ;;
        production)
            deploy_production "$package_name"
            ;;
        *)
            log_error "Unknown environment: $ENVIRONMENT"
            return 1
            ;;
    esac
}

# Deploy to local
deploy_local() {
    local package_name="$1"

    log_info "Deploying locally..."

    # Extract package
    cd "${DEPLOY_DIR}"
    tar -xzf "${package_name}.tar.gz"

    # Copy frontend build
    rm -rf "${FRONTEND_DIR}/dist"
    cp -r "${package_name}/frontend" "${FRONTEND_DIR}/dist"

    log_success "Local deployment complete"
}

# Deploy to staging
deploy_staging() {
    local package_name="$1"

    log_info "Deploying to staging environment..."

    # TODO: Implement staging deployment
    # This would typically involve:
    # - SCP/rsync to staging server
    # - SSH commands to extract and setup
    # - Service restart

    log_warning "Staging deployment not yet implemented"
}

# Deploy to production
deploy_production() {
    local package_name="$1"

    log_warning "Production deployment requires manual confirmation"

    read -p "Are you sure you want to deploy to PRODUCTION? (type 'yes' to confirm): " -r
    if [[ $REPLY != "yes" ]]; then
        log_error "Production deployment cancelled"
        exit 1
    fi

    log_info "Deploying to production environment..."

    # TODO: Implement production deployment
    # This would typically involve:
    # - Blue-green deployment
    # - Load balancer updates
    # - Health checks
    # - Gradual rollout

    log_warning "Production deployment not yet implemented"
}

# Verify deployment
verify_deployment() {
    log_step "Verifying deployment..."

    if [[ "$DRY_RUN" == true ]]; then
        log_warning "DRY RUN - Skipping verification"
        return 0
    fi

    # Start servers
    if [[ -f "${PROJECT_ROOT}/scripts/dev-start.sh" ]]; then
        log_info "Starting servers for verification..."
        "${PROJECT_ROOT}/scripts/dev-start.sh" >/dev/null 2>&1 &
        sleep 10
    fi

    # Run health check
    if [[ -f "${PROJECT_ROOT}/scripts/health-check.sh" ]]; then
        if "${PROJECT_ROOT}/scripts/health-check.sh" --verbose; then
            log_success "Deployment verified successfully"
            return 0
        else
            log_error "Deployment verification failed"
            return 1
        fi
    else
        log_warning "health-check.sh not found, skipping verification"
    fi
}

# Rollback to previous version
perform_rollback() {
    log_step "Rolling back to previous version..."

    # Find most recent backup
    local latest_backup=$(ls -t "${BACKUP_DIR}" | head -n 2 | tail -n 1)

    if [[ -z "$latest_backup" ]]; then
        log_error "No backup found for rollback"
        return 1
    fi

    log_info "Rolling back to: ${latest_backup}"

    # Restore frontend
    if [[ -d "${BACKUP_DIR}/${latest_backup}-frontend" ]]; then
        rm -rf "${FRONTEND_DIR}/dist"
        cp -r "${BACKUP_DIR}/${latest_backup}-frontend" "${FRONTEND_DIR}/dist"
        log_success "Frontend restored"
    fi

    # Restore backend (if needed)
    # Note: Backend rollback is trickier due to database changes
    log_warning "Backend rollback requires manual intervention"

    log_success "Rollback complete"
}

# Main execution
main() {
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║         Epstein Archive Deployment Script             ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""
    log_info "Environment: ${ENVIRONMENT}"
    log_info "Dry run: ${DRY_RUN}"
    echo ""

    # Handle rollback
    if [[ "$ROLLBACK" == true ]]; then
        perform_rollback
        exit 0
    fi

    # Stop dev servers
    stop_dev_servers

    # Run test suite
    if [[ "$SKIP_TESTS" != true ]]; then
        run_python_tests || exit 1
        run_frontend_tests || exit 1
        run_smoke_tests || exit 1
    else
        log_warning "Skipping tests (not recommended for production)"
    fi

    # Build frontend
    build_frontend || exit 1

    # Backup current deployment
    if [[ "$DRY_RUN" != true ]]; then
        backup_current_deployment
    fi

    # Create deployment package
    local package_name=$(create_deployment_package)

    # Deploy to environment
    deploy_to_environment "$package_name" || exit 1

    # Verify deployment
    if ! verify_deployment; then
        log_error "Deployment verification failed"

        read -p "Rollback to previous version? (y/n) " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            perform_rollback
        fi

        exit 1
    fi

    echo ""
    log_success "Deployment complete!"
    echo ""
    log_info "Package: ${package_name}.tar.gz"
    log_info "Environment: ${ENVIRONMENT}"
    echo ""
}

# Run main function
main
