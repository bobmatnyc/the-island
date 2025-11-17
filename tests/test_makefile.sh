#!/bin/bash
# Makefile Test Suite
# Tests all Makefile targets and scripts for the Epstein Document Archive

set -e

PROJECT_DIR="/Users/masa/Projects/Epstein"
cd "$PROJECT_DIR"

echo "════════════════════════════════════════════════════════════════"
echo "  Makefile Test Suite - Epstein Document Archive"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

TESTS_PASSED=0
TESTS_FAILED=0

# Test helper function
test_command() {
    local test_name="$1"
    local command="$2"

    echo -n "Testing: $test_name ... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((TESTS_FAILED++))
    fi
}

# Test helper for expected output
test_output() {
    local test_name="$1"
    local command="$2"
    local expected="$3"

    echo -n "Testing: $test_name ... "

    output=$(eval "$command" 2>&1)

    if echo "$output" | grep -q "$expected"; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  Expected: $expected"
        echo "  Got: $output"
        ((TESTS_FAILED++))
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. File Existence Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_command "Makefile exists" "test -f Makefile"
test_command "VERSION file exists" "test -f VERSION"
test_command "CHANGELOG.md exists" "test -f CHANGELOG.md"
test_command ".makerc exists" "test -f .makerc"
test_command "bump_version.py exists" "test -f scripts/bump_version.py"
test_command "update_changelog.py exists" "test -f scripts/update_changelog.py"
test_command "validate_version.py exists" "test -f scripts/validate_version.py"
test_command "git_commit_helper.py exists" "test -f scripts/git_commit_helper.py"
test_command "MAKEFILE_GUIDE.md exists" "test -f docs/MAKEFILE_GUIDE.md"
test_command "MAKEFILE_QUICKSTART.md exists" "test -f MAKEFILE_QUICKSTART.md"
test_command "MAKEFILE_SUMMARY.md exists" "test -f MAKEFILE_SUMMARY.md"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Script Executable Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_command "bump_version.py executable" "test -x scripts/bump_version.py"
test_command "update_changelog.py executable" "test -x scripts/update_changelog.py"
test_command "validate_version.py executable" "test -x scripts/validate_version.py"
test_command "git_commit_helper.py executable" "test -x scripts/git_commit_helper.py"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Makefile Target Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_output "make help" "make help" "Epstein Document Archive"
test_output "make version" "make version" "0.1.0"
test_output "make status" "make status" "Project Status"
test_command "make validate-version" "make validate-version"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Python Script Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_command "validate_version.py runs" "python3 scripts/validate_version.py"
test_output "update_changelog.py validate" \
    "python3 scripts/update_changelog.py validate" \
    "Changelog format validated"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. Version Format Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

VERSION=$(cat VERSION)
test_output "VERSION format valid" "echo $VERSION" "^[0-9]\+\.[0-9]\+\.[0-9]\+$"
test_output "CHANGELOG has version" "grep '\[0.1.0\]' CHANGELOG.md" "0.1.0"
test_output "CHANGELOG has Unreleased" "grep '\[Unreleased\]' CHANGELOG.md" "Unreleased"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. Documentation Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_output "MAKEFILE_GUIDE.md complete" \
    "grep 'Version Management' docs/MAKEFILE_GUIDE.md" \
    "Version Management"
test_output "MAKEFILE_QUICKSTART.md complete" \
    "grep 'Quick Start' MAKEFILE_QUICKSTART.md" \
    "Quick Start"
test_output "MAKEFILE_SUMMARY.md complete" \
    "grep 'Implementation Summary' MAKEFILE_SUMMARY.md" \
    "Implementation Summary"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. Configuration Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_output ".makerc has config" "grep 'PYTHON_VERSION' .makerc" "PYTHON_VERSION"
test_output ".makerc has OCR config" "grep 'OCR_WORKERS' .makerc" "OCR_WORKERS"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Test Results"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi
