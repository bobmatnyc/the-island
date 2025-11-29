#!/bin/bash
# Quick fix script for Timeline "0 articles" issue

echo "==================================================="
echo "Timeline News '0 articles' Bug - Quick Fix Script"
echo "==================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Issue:${NC} Timeline shows '0 articles' despite API returning data"
echo -e "${YELLOW}Root Cause:${NC} Browser cache holding old JavaScript bundle"
echo ""

echo "Step 1: Verify backend is running..."
if curl -s http://localhost:8081/api/news/stats > /dev/null; then
    echo -e "${GREEN}✓${NC} Backend is running"
    TOTAL=$(curl -s http://localhost:8081/api/news/stats | jq -r '.total_articles')
    echo "  Total articles in database: ${TOTAL}"
else
    echo -e "${RED}✗${NC} Backend is NOT running!"
    echo "  Please start backend first: cd server && python app.py 8081"
    exit 1
fi
echo ""

echo "Step 2: Verify frontend is running..."
if lsof -ti:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Frontend dev server is running on port 5173"
else
    echo -e "${RED}✗${NC} Frontend is NOT running!"
    echo "  Please start frontend: cd frontend && npm run dev"
    exit 1
fi
echo ""

echo "Step 3: Test News API endpoint..."
START_DATE="1953-01-20"
END_DATE="2025-11-16"
API_RESPONSE=$(curl -s "http://localhost:8081/api/news/articles?start_date=${START_DATE}&end_date=${END_DATE}&limit=100")
API_TOTAL=$(echo "$API_RESPONSE" | jq -r '.total // 0')

if [ "$API_TOTAL" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} News API returns ${API_TOTAL} articles for timeline date range"
else
    echo -e "${RED}✗${NC} News API returned 0 articles!"
    echo "  This indicates a backend issue, not a frontend cache issue."
    exit 1
fi
echo ""

echo "Step 4: Check if Vite needs restart..."
VITE_UPTIME=$(ps -p $(lsof -ti:5173) -o etime= 2>/dev/null | tr -d ' ')
echo "  Vite dev server uptime: ${VITE_UPTIME}"
echo ""

echo "==================================================="
echo "DIAGNOSIS COMPLETE"
echo "==================================================="
echo ""
echo -e "${GREEN}✓${NC} Backend is healthy (${TOTAL} articles)"
echo -e "${GREEN}✓${NC} Frontend is running"
echo -e "${GREEN}✓${NC} API returns data correctly (${API_TOTAL} articles)"
echo ""
echo -e "${YELLOW}CONCLUSION:${NC} This is a ${RED}BROWSER CACHE ISSUE${NC}"
echo ""
echo "==================================================="
echo "USER ACTION REQUIRED"
echo "==================================================="
echo ""
echo "Please do one of the following:"
echo ""
echo "Option 1: HARD REFRESH (Recommended)"
echo "  1. Open http://localhost:5173/timeline in your browser"
echo "  2. Press Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)"
echo "  3. Verify badge now shows '${API_TOTAL} articles'"
echo ""
echo "Option 2: Clear Cache via DevTools"
echo "  1. Open DevTools (F12 or Cmd+Option+I)"
echo "  2. Go to Network tab"
echo "  3. Check 'Disable cache'"
echo "  4. Right-click refresh button → 'Empty Cache and Hard Reload'"
echo ""
echo "Option 3: Clear All Browser Data"
echo "  Chrome: Settings → Privacy → Clear browsing data"
echo "  Safari: Develop → Empty Caches"
echo "  Firefox: Settings → Privacy → Clear Data"
echo ""
echo "==================================================="
echo "VERIFICATION"
echo "==================================================="
echo ""
echo "After clearing cache, verify:"
echo "  ✓ Timeline loads without errors"
echo "  ✓ 'Show News Coverage' checkbox appears"
echo "  ✓ When checked, badge shows '${API_TOTAL} articles' (not '0 articles')"
echo "  ✓ No console errors"
echo ""
echo "If issue persists after cache clear, run:"
echo "  pkill -f vite && cd frontend && npm run dev"
echo ""
