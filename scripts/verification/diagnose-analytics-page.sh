#!/bin/bash

# Analytics Page Diagnostic Script
# Run this to diagnose why Analytics page might show blank screen
#
# Usage: ./diagnose-analytics-page.sh

echo "================================================"
echo "Analytics Page Diagnostic Tool"
echo "Linear Ticket: 1M-107"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
PASS=0
FAIL=0
WARN=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $2"
        ((FAIL++))
    fi
}

test_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARN++))
}

# 1. Check if backend is running
echo "1. Checking Backend Server..."
if curl -s http://localhost:8081/api/v2/stats > /dev/null 2>&1; then
    test_result 0 "Backend server is running on port 8081"

    # Check response
    RESPONSE=$(curl -s http://localhost:8081/api/v2/stats)
    if echo "$RESPONSE" | grep -q '"status"'; then
        test_result 0 "API returns valid JSON"
    else
        test_result 1 "API response is not valid JSON"
    fi
else
    test_result 1 "Backend server is NOT running on port 8081"
    echo "   → Start backend with: cd server && python app.py"
fi
echo ""

# 2. Check if frontend is running
echo "2. Checking Frontend Server..."
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    test_result 0 "Frontend server is running on port 5173"
else
    test_result 1 "Frontend server is NOT running on port 5173"
    echo "   → Start frontend with: cd frontend && npm run dev"
fi
echo ""

# 3. Check Analytics route
echo "3. Checking Analytics Route..."
ANALYTICS_HTML=$(curl -s http://localhost:5173/analytics)
if echo "$ANALYTICS_HTML" | grep -q "Analytics"; then
    test_result 0 "Analytics route is accessible"
else
    test_result 1 "Analytics route is NOT accessible"
fi
echo ""

# 4. Check API endpoints
echo "4. Checking API Endpoints..."

# Stats endpoint
if curl -s http://localhost:8081/api/v2/stats | grep -q '"data"'; then
    test_result 0 "/api/v2/stats endpoint working"
else
    test_result 1 "/api/v2/stats endpoint failing"
fi

# Entities endpoint
if curl -s http://localhost:8081/api/entities | grep -q '{'; then
    test_result 0 "/api/entities endpoint working"
else
    test_result 1 "/api/entities endpoint failing"
fi

# Timeline mentions endpoint
if curl -s http://localhost:8081/api/v2/analytics/timeline-mentions | grep -q 'timeline'; then
    test_result 0 "/api/v2/analytics/timeline-mentions endpoint working"
else
    test_result 1 "/api/v2/analytics/timeline-mentions endpoint failing"
fi
echo ""

# 5. Check data files
echo "5. Checking Data Files..."

if [ -f "data/metadata/entity_statistics.json" ]; then
    test_result 0 "entity_statistics.json exists"
else
    test_result 1 "entity_statistics.json is missing"
fi

if [ -f "data/metadata/entity_network.json" ]; then
    test_result 0 "entity_network.json exists"
else
    test_result 1 "entity_network.json is missing"
fi

if [ -f "data/metadata/news_articles_index.json" ]; then
    test_result 0 "news_articles_index.json exists"
else
    test_result 1 "news_articles_index.json is missing"
fi
echo ""

# 6. Check ngrok (if applicable)
echo "6. Checking Ngrok Tunnel..."
if pgrep -x "ngrok" > /dev/null; then
    test_result 0 "Ngrok process is running"

    # Get ngrok URL
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o 'https://[^"]*ngrok[^"]*' | head -1)
    if [ ! -z "$NGROK_URL" ]; then
        echo "   Current ngrok URL: $NGROK_URL"
    fi
else
    test_warn "Ngrok is not running (only needed for remote access)"
fi
echo ""

# 7. Check environment variables
echo "7. Checking Environment..."

if [ -f "frontend/.env" ]; then
    test_result 0 "Frontend .env file exists"

    API_URL=$(grep VITE_API_BASE_URL frontend/.env | cut -d'=' -f2)
    if [ ! -z "$API_URL" ]; then
        echo "   VITE_API_BASE_URL: $API_URL"
    fi
else
    test_warn "Frontend .env file not found (will use defaults)"
fi
echo ""

# 8. Check node_modules
echo "8. Checking Dependencies..."

if [ -d "frontend/node_modules" ]; then
    test_result 0 "Frontend dependencies installed"
else
    test_result 1 "Frontend dependencies NOT installed"
    echo "   → Run: cd frontend && npm install"
fi

# Check for recharts
if [ -d "frontend/node_modules/recharts" ]; then
    test_result 0 "Recharts library installed (required for charts)"
else
    test_result 1 "Recharts library NOT installed"
fi
echo ""

# Summary
echo "================================================"
echo "DIAGNOSTIC SUMMARY"
echo "================================================"
echo -e "${GREEN}Passed:${NC} $PASS"
echo -e "${RED}Failed:${NC} $FAIL"
echo -e "${YELLOW}Warnings:${NC} $WARN"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All critical tests passed!${NC}"
    echo ""
    echo "Analytics page should be working at:"
    echo "  → http://localhost:5173/analytics"
    echo ""
    echo "If you still see a blank screen:"
    echo "  1. Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R)"
    echo "  2. Clear browser cache"
    echo "  3. Try incognito/private mode"
    echo "  4. Check browser console for errors (F12)"
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    echo "Fix the failed tests above, then:"
    echo "  1. Restart backend: cd server && python app.py"
    echo "  2. Restart frontend: cd frontend && npm run dev"
    echo "  3. Try accessing: http://localhost:5173/analytics"
fi

echo ""
echo "For detailed troubleshooting, see:"
echo "  → USER_TROUBLESHOOTING_GUIDE.md"
echo "================================================"
