#!/bin/bash
# Pre-release Quality Gate Script
# Runs linting, type checking, formatting checks, and tests before release
#
# Usage:
#   ./scripts/pre_release.sh              # Run all checks
#   ./scripts/pre_release.sh --fix         # Run checks and auto-fix issues
#   ./scripts/pre_release.sh --fast        # Skip slow checks (tests)
#
# Exit codes:
#   0 - All checks passed
#   1 - Linting failures
#   2 - Type checking failures
#   3 - Test failures
#   4 - Coverage below threshold

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COVERAGE_THRESHOLD=80
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Parse arguments
FIX_MODE=false
FAST_MODE=false
for arg in "$@"; do
    case $arg in
        --fix)
            FIX_MODE=true
            ;;
        --fast)
            FAST_MODE=true
            ;;
        --help)
            echo "Usage: $0 [--fix] [--fast]"
            echo "  --fix   Auto-fix linting and formatting issues"
            echo "  --fast  Skip slow checks (tests)"
            exit 0
            ;;
    esac
done

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if tools are installed
check_tools() {
    print_header "Checking Required Tools"

    MISSING_TOOLS=()

    if ! command -v ruff &> /dev/null; then
        MISSING_TOOLS+=("ruff")
    fi

    if ! command -v black &> /dev/null; then
        MISSING_TOOLS+=("black")
    fi

    if ! command -v isort &> /dev/null; then
        MISSING_TOOLS+=("isort")
    fi

    if ! command -v mypy &> /dev/null; then
        MISSING_TOOLS+=("mypy")
    fi

    if ! command -v pytest &> /dev/null; then
        MISSING_TOOLS+=("pytest")
    fi

    if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
        print_error "Missing required tools: ${MISSING_TOOLS[*]}"
        print_info "Install with: pip install ruff black isort mypy pytest pytest-cov"
        exit 1
    fi

    print_success "All required tools installed"
}

# Ruff linting
run_ruff() {
    print_header "Running Ruff Linter"

    if [ "$FIX_MODE" = true ]; then
        print_info "Running ruff with auto-fix enabled..."
        if ruff check --fix scripts/ server/; then
            print_success "Ruff check passed (with fixes applied)"
        else
            print_error "Ruff check failed"
            return 1
        fi
    else
        print_info "Running ruff check (use --fix to auto-fix issues)..."
        if ruff check scripts/ server/; then
            print_success "Ruff check passed"
        else
            print_error "Ruff check failed"
            print_warning "Run with --fix to auto-fix issues"
            return 1
        fi
    fi
}

# Black formatting
run_black() {
    print_header "Running Black Formatter"

    if [ "$FIX_MODE" = true ]; then
        print_info "Running black with auto-format..."
        if black scripts/ server/; then
            print_success "Black formatting applied"
        else
            print_error "Black formatting failed"
            return 1
        fi
    else
        print_info "Checking black formatting (use --fix to auto-format)..."
        if black --check scripts/ server/; then
            print_success "Black formatting check passed"
        else
            print_error "Black formatting check failed"
            print_warning "Run with --fix to auto-format"
            return 1
        fi
    fi
}

# isort import sorting
run_isort() {
    print_header "Running isort Import Sorter"

    if [ "$FIX_MODE" = true ]; then
        print_info "Running isort with auto-fix..."
        if isort scripts/ server/; then
            print_success "isort applied"
        else
            print_error "isort failed"
            return 1
        fi
    else
        print_info "Checking import sorting (use --fix to auto-sort)..."
        if isort --check-only scripts/ server/; then
            print_success "isort check passed"
        else
            print_error "isort check failed"
            print_warning "Run with --fix to auto-sort imports"
            return 1
        fi
    fi
}

# mypy type checking
run_mypy() {
    print_header "Running mypy Type Checker"

    print_info "Type checking scripts/ and server/..."
    if mypy scripts/ server/ --ignore-missing-imports --no-strict-optional; then
        print_success "mypy type checking passed"
    else
        print_warning "mypy type checking found issues (non-blocking)"
        print_info "Consider adding more type hints to improve type coverage"
        # Don't fail on mypy errors for now (gradual adoption)
        return 0
    fi
}

# pytest test suite
run_tests() {
    if [ "$FAST_MODE" = true ]; then
        print_info "Skipping tests (--fast mode)"
        return 0
    fi

    print_header "Running pytest Test Suite"

    # Check if tests directory exists
    if [ ! -d "tests" ]; then
        print_warning "No tests/ directory found"
        print_info "Create tests/ directory and add test files"
        print_info "Skipping test execution"
        return 0
    fi

    # Count test files
    TEST_COUNT=$(find tests -name "test_*.py" -o -name "*_test.py" | wc -l | tr -d ' ')

    if [ "$TEST_COUNT" -eq 0 ]; then
        print_warning "No test files found in tests/"
        print_info "Add test files matching pattern: test_*.py or *_test.py"
        print_info "Skipping test execution"
        return 0
    fi

    print_info "Running $TEST_COUNT test file(s)..."

    if pytest --cov=scripts --cov=server --cov-report=term-missing --cov-fail-under=$COVERAGE_THRESHOLD; then
        print_success "All tests passed with coverage ≥ ${COVERAGE_THRESHOLD}%"
    else
        print_error "Tests failed or coverage below ${COVERAGE_THRESHOLD}%"
        return 3
    fi
}

# Roadmap validation
validate_roadmap() {
    print_header "Validating Roadmap"

    ROADMAP_FILE="ROADMAP.md"

    # Check if roadmap exists
    if [ ! -f "$ROADMAP_FILE" ]; then
        print_error "ROADMAP.md not found"
        return 1
    fi

    # Check if roadmap is non-empty
    if [ ! -s "$ROADMAP_FILE" ]; then
        print_error "ROADMAP.md is empty"
        return 1
    fi

    print_success "ROADMAP.md exists and is non-empty"

    # Check for required sections
    REQUIRED_SECTIONS=("Completed Recently" "Current Sprint" "Next Up" "Future Enhancements")
    MISSING_SECTIONS=()

    for section in "${REQUIRED_SECTIONS[@]}"; do
        if ! grep -q "## $section" "$ROADMAP_FILE"; then
            MISSING_SECTIONS+=("$section")
        fi
    done

    if [ ${#MISSING_SECTIONS[@]} -gt 0 ]; then
        print_error "Missing required sections: ${MISSING_SECTIONS[*]}"
        return 1
    fi

    print_success "All required sections present"

    # Check for TODO/FIXME comments
    TODO_COUNT=$(grep -c "TODO\|FIXME" "$ROADMAP_FILE" || true)
    if [ "$TODO_COUNT" -gt 0 ]; then
        print_warning "Found $TODO_COUNT TODO/FIXME comment(s) in roadmap"
        grep -n "TODO\|FIXME" "$ROADMAP_FILE" || true
    else
        print_success "No TODO/FIXME comments found"
    fi

    # Validate date format in "Last Updated" field
    if grep -q "Last Updated.*: [0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}" "$ROADMAP_FILE"; then
        print_success "Last Updated date format valid (YYYY-MM-DD)"
    else
        print_warning "Last Updated date format may be invalid"
    fi

    # Check for broken internal links (markdown anchors)
    print_info "Checking internal links..."
    BROKEN_LINKS=0

    # Extract all internal links [text](#anchor)
    while IFS= read -r link; do
        # Extract anchor from (#anchor) format
        anchor=$(echo "$link" | sed -n 's/.*(\(#[^)]*\)).*/\1/p')
        if [ -n "$anchor" ]; then
            # Convert anchor to header format (remove #, replace - with space, etc.)
            header=$(echo "$anchor" | sed 's/#//g' | sed 's/-/ /g')
            # Check if corresponding header exists (case-insensitive grep)
            if ! grep -qi "^## $header\|^### $header" "$ROADMAP_FILE"; then
                print_warning "Potentially broken link: $link"
                BROKEN_LINKS=$((BROKEN_LINKS + 1))
            fi
        fi
    done < <(grep -o '\[.*\](#[^)]*)' "$ROADMAP_FILE" || true)

    if [ "$BROKEN_LINKS" -eq 0 ]; then
        print_success "All internal links appear valid"
    else
        print_warning "Found $BROKEN_LINKS potentially broken internal link(s)"
    fi

    print_success "Roadmap validation passed"
    return 0
}

# Semantic versioning suggestion
suggest_version_bump() {
    print_header "Analyzing Version Bump"

    CURRENT_VERSION=$(grep -m 1 'version = ' pyproject.toml | sed 's/.*"\(.*\)".*/\1/')
    print_info "Current version: $CURRENT_VERSION"

    # Parse version
    MAJOR=$(echo "$CURRENT_VERSION" | cut -d. -f1)
    MINOR=$(echo "$CURRENT_VERSION" | cut -d. -f2)
    PATCH=$(echo "$CURRENT_VERSION" | cut -d. -f3)

    # Analyze ROADMAP.md for completed features
    ROADMAP_FILE="ROADMAP.md"

    # Check for breaking changes
    BREAKING_KEYWORDS=("breaking change" "incompatible" "removed" "deprecated")
    BREAKING_COUNT=0
    for keyword in "${BREAKING_KEYWORDS[@]}"; do
        count=$(grep -ci "$keyword" "$ROADMAP_FILE" 2>/dev/null || echo "0")
        count=$(echo "$count" | tr -d '[:space:]')
        BREAKING_COUNT=$((BREAKING_COUNT + count))
    done

    # Check for new features
    FEATURE_KEYWORDS=("new feature" "added" "implemented")
    FEATURE_COUNT=0
    for keyword in "${FEATURE_KEYWORDS[@]}"; do
        count=$(grep -ci "$keyword" "$ROADMAP_FILE" 2>/dev/null || echo "0")
        count=$(echo "$count" | tr -d '[:space:]')
        FEATURE_COUNT=$((FEATURE_COUNT + count))
    done

    # Check for bug fixes
    BUGFIX_KEYWORDS=("fixed" "bug fix" "patched" "corrected")
    BUGFIX_COUNT=0
    for keyword in "${BUGFIX_KEYWORDS[@]}"; do
        count=$(grep -ci "$keyword" "$ROADMAP_FILE" 2>/dev/null || echo "0")
        count=$(echo "$count" | tr -d '[:space:]')
        BUGFIX_COUNT=$((BUGFIX_COUNT + count))
    done

    # Suggest version bump
    echo ""
    print_info "Change Analysis:"
    echo "  - Breaking changes: $BREAKING_COUNT"
    echo "  - New features: $FEATURE_COUNT"
    echo "  - Bug fixes: $BUGFIX_COUNT"
    echo ""

    if [ "$BREAKING_COUNT" -gt 0 ]; then
        NEW_MAJOR=$((MAJOR + 1))
        SUGGESTED_VERSION="${NEW_MAJOR}.0.0"
        print_warning "Suggested version: $SUGGESTED_VERSION (MAJOR bump - breaking changes detected)"
    elif [ "$FEATURE_COUNT" -gt 5 ]; then
        NEW_MINOR=$((MINOR + 1))
        SUGGESTED_VERSION="${MAJOR}.${NEW_MINOR}.0"
        print_info "Suggested version: $SUGGESTED_VERSION (MINOR bump - new features detected)"
    elif [ "$BUGFIX_COUNT" -gt 0 ] || [ "$FEATURE_COUNT" -gt 0 ]; then
        NEW_PATCH=$((PATCH + 1))
        SUGGESTED_VERSION="${MAJOR}.${MINOR}.${NEW_PATCH}"
        print_info "Suggested version: $SUGGESTED_VERSION (PATCH bump - fixes/small features detected)"
    else
        print_info "No version bump needed (no significant changes detected)"
        return 0
    fi

    echo ""
    print_info "To update version, run:"
    echo "  sed -i '' 's/version = \"$CURRENT_VERSION\"/version = \"$SUGGESTED_VERSION\"/' pyproject.toml"
    echo ""

    return 0
}

# Update CHANGELOG.md from ROADMAP.md
update_changelog() {
    print_header "Updating CHANGELOG.md"

    CHANGELOG_FILE="CHANGELOG.md"
    ROADMAP_FILE="ROADMAP.md"

    if [ ! -f "$CHANGELOG_FILE" ]; then
        print_warning "CHANGELOG.md not found, skipping update"
        return 0
    fi

    if [ ! -f "$ROADMAP_FILE" ]; then
        print_warning "ROADMAP.md not found, skipping update"
        return 0
    fi

    # Extract completed items from roadmap
    print_info "Extracting completed items from roadmap..."

    # Count completed items in "Completed Recently" section
    COMPLETED_COUNT=$(sed -n '/## Completed Recently/,/^## /p' "$ROADMAP_FILE" | grep -c "^- \*\*" || true)

    if [ "$COMPLETED_COUNT" -eq 0 ]; then
        print_info "No new completed items found in roadmap"
        return 0
    fi

    print_success "Found $COMPLETED_COUNT completed item(s) in roadmap"
    print_info "Consider updating CHANGELOG.md with these items"

    # Note: We don't auto-update CHANGELOG to avoid conflicts
    # This is a suggestion only
    print_warning "Manual CHANGELOG update recommended before release"

    return 0
}

# Generate linting report
generate_report() {
    print_header "Generating Linting Report"

    REPORT_FILE="linting_report.txt"

    {
        echo "Epstein Document Archive - Linting Report"
        echo "Generated: $(date)"
        echo "=========================================="
        echo ""

        echo "Ruff Violations:"
        ruff check scripts/ server/ || true
        echo ""

        echo "Black Formatting Issues:"
        black --check scripts/ server/ 2>&1 || true
        echo ""

        echo "isort Import Sorting Issues:"
        isort --check-only scripts/ server/ 2>&1 || true
        echo ""

        echo "mypy Type Checking:"
        mypy scripts/ server/ --ignore-missing-imports --no-strict-optional 2>&1 || true
        echo ""
    } > "$REPORT_FILE"

    print_success "Linting report saved to: $REPORT_FILE"
}

# Main execution
main() {
    print_header "Epstein Archive Pre-Release Quality Gate"

    if [ "$FIX_MODE" = true ]; then
        print_info "Running in FIX mode - auto-fixing issues"
    fi

    if [ "$FAST_MODE" = true ]; then
        print_info "Running in FAST mode - skipping tests"
    fi

    # Track failures
    FAILED_CHECKS=()

    # Run checks
    check_tools

    if ! run_ruff; then
        FAILED_CHECKS+=("ruff")
    fi

    if ! run_black; then
        FAILED_CHECKS+=("black")
    fi

    if ! run_isort; then
        FAILED_CHECKS+=("isort")
    fi

    if ! run_mypy; then
        # mypy warnings are non-blocking
        :
    fi

    if ! run_tests; then
        FAILED_CHECKS+=("tests")
    fi

    # Roadmap validation
    if ! validate_roadmap; then
        FAILED_CHECKS+=("roadmap")
    fi

    # Generate report
    generate_report

    # Semantic versioning analysis (non-blocking)
    suggest_version_bump

    # CHANGELOG update check (non-blocking)
    update_changelog

    # Summary
    print_header "Summary"

    if [ ${#FAILED_CHECKS[@]} -eq 0 ]; then
        print_success "All checks passed! ✓"
        echo ""
        echo -e "${GREEN}┌─────────────────────────────────────┐${NC}"
        echo -e "${GREEN}│  READY FOR RELEASE                  │${NC}"
        echo -e "${GREEN}└─────────────────────────────────────┘${NC}"
        echo ""
        exit 0
    else
        print_error "Failed checks: ${FAILED_CHECKS[*]}"
        echo ""
        echo -e "${RED}┌─────────────────────────────────────┐${NC}"
        echo -e "${RED}│  NOT READY FOR RELEASE              │${NC}"
        echo -e "${RED}└─────────────────────────────────────┘${NC}"
        echo ""

        if [ "$FIX_MODE" != true ]; then
            print_info "Tip: Run with --fix to auto-fix linting and formatting issues"
        fi

        # Determine exit code
        if [[ " ${FAILED_CHECKS[*]} " =~ " tests " ]]; then
            exit 3  # Test failures
        elif [[ " ${FAILED_CHECKS[*]} " =~ " mypy " ]]; then
            exit 2  # Type checking failures
        else
            exit 1  # Linting failures
        fi
    fi
}

# Run main
main
