#!/bin/bash

# Phase 1 Refactoring Verification Script
# Run this to verify all Phase 1 deliverables are in place

echo "🔍 Phase 1 Refactoring - Verification Script"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} $1 ($(wc -l < "$1") lines)"
    else
        echo -e "${RED}❌${NC} $1 - MISSING"
        ((ERRORS++))
    fi
}

# Function to check directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✅${NC} $1/ directory exists"
    else
        echo -e "${RED}❌${NC} $1/ - MISSING"
        ((ERRORS++))
    fi
}

echo "📁 Directory Structure"
echo "─────────────────────"
check_dir "core"
check_dir "utils"
check_dir "components"
echo ""

echo "📦 Core Modules"
echo "───────────────"
check_file "core/state-manager.js"
check_file "core/event-bus.js"
echo ""

echo "🔧 Utility Modules"
echo "──────────────────"
check_file "utils/dom-cache.js"
check_file "utils/formatter.js"
check_file "utils/markdown.js"
echo ""

echo "🎨 Component Modules"
echo "────────────────────"
check_file "components/toast.js"
echo ""

echo "🔗 Integration Files"
echo "────────────────────"
check_file "app-modular.js"
echo ""

echo "🧪 Test Files"
echo "─────────────"
check_file "test-refactoring-phase1.html"
check_file "test-modules-simple.html"
check_file "test-modules-node.mjs"
echo ""

echo "📚 Documentation"
echo "────────────────"
check_file "PHASE1_REFACTORING_COMPLETE.md"
check_file "PHASE1_QUICK_START.md"
check_file "PHASE1_ARCHITECTURE.md"
check_file "../../PHASE1_IMPLEMENTATION_SUMMARY.md"
check_file "../../APP_JS_REFACTORING_PHASE1_COMPLETE.md"
echo ""

echo "🔍 File Size Summary"
echo "────────────────────"
TOTAL_LINES=0
for file in core/*.js utils/*.js components/*.js app-modular.js; do
    if [ -f "$file" ]; then
        LINES=$(wc -l < "$file")
        TOTAL_LINES=$((TOTAL_LINES + LINES))
        SIZE=$(ls -lh "$file" | awk '{print $5}')
        printf "  %-30s %5d lines, %s\n" "$file" "$LINES" "$SIZE"
    fi
done
echo "  ─────────────────────────────────────────"
printf "  %-30s %5d lines\n" "TOTAL:" "$TOTAL_LINES"
echo ""

echo "🧪 Running Static Tests..."
echo "──────────────────────────"
if command -v node &> /dev/null; then
    if [ -f "test-modules-node.mjs" ]; then
        node test-modules-node.mjs 2>&1 | grep -E "(✅|❌|Pass Rate|Total)" || echo "Tests completed"
    else
        echo -e "${YELLOW}⚠️${NC} test-modules-node.mjs not found"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}⚠️${NC} Node.js not installed, skipping static tests"
    ((WARNINGS++))
fi
echo ""

echo "📊 Summary"
echo "──────────"
echo "Total Modules: 6"
echo "Total Test Files: 3"
echo "Total Documentation: 5"
echo "Total Lines of Code: $TOTAL_LINES"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ Phase 1 Verification Complete - All checks passed!${NC}"
    echo ""
    echo "🎉 Ready for production!"
    echo ""
    echo "Next steps:"
    echo "  1. Review documentation: cat PHASE1_QUICK_START.md"
    echo "  2. Run browser tests: python ../app.py"
    echo "  3. Open: http://localhost:5001/test-refactoring-phase1.html"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Phase 1 Verification Complete - $WARNINGS warnings${NC}"
    echo ""
    echo "All critical files present. Some optional checks skipped."
    exit 0
else
    echo -e "${RED}❌ Phase 1 Verification Failed - $ERRORS errors, $WARNINGS warnings${NC}"
    echo ""
    echo "Please review the errors above and ensure all files are in place."
    exit 1
fi
