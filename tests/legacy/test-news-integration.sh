#!/bin/bash

# News Integration Test Script
# Tests both backend API and frontend components

echo "=========================================="
echo "News Integration Test Suite"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Backend URL
BACKEND_URL="http://localhost:8081"

echo -e "${BLUE}[1/5] Testing Backend API Connection...${NC}"
if curl -s -f "${BACKEND_URL}/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend is not running. Please start with: python3 server/app.py 8081${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}[2/5] Testing News Statistics Endpoint...${NC}"
STATS=$(curl -s "${BACKEND_URL}/api/news/stats")
TOTAL_ARTICLES=$(echo $STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['total_articles'])" 2>/dev/null)
TOTAL_SOURCES=$(echo $STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['total_sources'])" 2>/dev/null)

if [ -n "$TOTAL_ARTICLES" ]; then
    echo -e "${GREEN}✓ News stats endpoint working${NC}"
    echo "  Total Articles: $TOTAL_ARTICLES"
    echo "  Total Sources: $TOTAL_SOURCES"
else
    echo -e "${RED}✗ News stats endpoint failed${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}[3/5] Testing Jeffrey Epstein News Articles...${NC}"
EPSTEIN_ARTICLES=$(curl -s "${BACKEND_URL}/api/news/articles?entity=jeffrey_epstein&limit=3")
EPSTEIN_COUNT=$(echo $EPSTEIN_ARTICLES | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('articles', [])))" 2>/dev/null)

if [ "$EPSTEIN_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $EPSTEIN_COUNT articles for Jeffrey Epstein${NC}"
    echo ""
    echo "Sample articles:"
    echo $EPSTEIN_ARTICLES | python3 -c "
import sys, json
data = json.load(sys.stdin)
for i, article in enumerate(data.get('articles', [])[:3], 1):
    print(f\"  {i}. {article['title'][:60]}...\")
    print(f\"     Source: {article['publication']} | Date: {article['published_date']} | Credibility: {article['credibility_score']:.2f}\")
" 2>/dev/null
else
    echo -e "${RED}✗ No articles found for Jeffrey Epstein${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}[4/5] Testing Ghislaine Maxwell News Articles...${NC}"
MAXWELL_ARTICLES=$(curl -s "${BACKEND_URL}/api/news/articles?entity=ghislaine_maxwell&limit=3")
MAXWELL_COUNT=$(echo $MAXWELL_ARTICLES | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('articles', [])))" 2>/dev/null)

if [ "$MAXWELL_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $MAXWELL_COUNT articles for Ghislaine Maxwell${NC}"
    echo ""
    echo "Sample articles:"
    echo $MAXWELL_ARTICLES | python3 -c "
import sys, json
data = json.load(sys.stdin)
for i, article in enumerate(data.get('articles', [])[:3], 1):
    print(f\"  {i}. {article['title'][:60]}...\")
    print(f\"     Source: {article['publication']} | Date: {article['published_date']} | Credibility: {article['credibility_score']:.2f}\")
" 2>/dev/null
else
    echo -e "${RED}✗ No articles found for Ghislaine Maxwell${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}[5/5] Testing Frontend Build...${NC}"
cd frontend
if npm run build > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend builds successfully${NC}"
    echo -e "${GREEN}✓ TypeScript compilation passed${NC}"
    echo -e "${GREEN}✓ All imports resolved${NC}"
else
    echo -e "${RED}✗ Frontend build failed${NC}"
    exit 1
fi
cd ..
echo ""

echo "=========================================="
echo -e "${GREEN}All Tests Passed! ✓${NC}"
echo "=========================================="
echo ""
echo "News Integration Status: COMPLETE"
echo ""
echo "Next steps:"
echo "  1. Start the frontend: cd frontend && npm run dev"
echo "  2. Visit an entity page: http://localhost:5173/entities/jeffrey_epstein"
echo "  3. Scroll to 'News Coverage' section"
echo "  4. Verify articles display correctly"
echo ""
