#!/bin/bash
# Test ngrok frontend serving - comprehensive verification
# Tests both local backend and ngrok tunnel

set -e

NGROK_URL="https://the-island.ngrok.app"
LOCAL_URL="http://localhost:8081"

echo "========================================="
echo "ngrok Frontend Setup Verification"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function test_endpoint() {
    local url=$1
    local test_name=$2
    local expected_pattern=$3
    local test_type=${4:-"html"} # html or json

    echo -n "Testing $test_name... "

    if [ "$test_type" = "json" ]; then
        response=$(curl -s "$url" | python3 -m json.tool 2>/dev/null | head -n 5)
    else
        response=$(curl -s "$url" | head -n 50)
    fi

    if echo "$response" | grep -q "$expected_pattern"; then
        echo -e "${GREEN}✅ PASS${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "Expected pattern: $expected_pattern"
        echo "Got: ${response:0:200}"
        return 1
    fi
}

echo "=== Testing Local Backend ($LOCAL_URL) ==="
echo ""

test_endpoint "$LOCAL_URL/" "Root route" "<title>Epstein Archive</title>" "html"
test_endpoint "$LOCAL_URL/news" "/news route (SPA)" "<title>Epstein Archive</title>" "html"
test_endpoint "$LOCAL_URL/entities" "/entities route (SPA)" "<title>Epstein Archive</title>" "html"
test_endpoint "$LOCAL_URL/news?view=timeline" "/news with query params" "<title>Epstein Archive</title>" "html"
test_endpoint "$LOCAL_URL/assets/index-DPGAGFPk.js" "JavaScript bundle" "function" "html"
test_endpoint "$LOCAL_URL/api/news/articles?limit=1" "API endpoint" '"articles"' "json"

echo ""
echo "=== Testing ngrok Tunnel ($NGROK_URL) ==="
echo ""

test_endpoint "$NGROK_URL/" "Root route" "<title>Epstein Archive</title>" "html"
test_endpoint "$NGROK_URL/news" "/news route (SPA)" "<title>Epstein Archive</title>" "html"
test_endpoint "$NGROK_URL/entities" "/entities route (SPA)" "<title>Epstein Archive</title>" "html"
test_endpoint "$NGROK_URL/news?view=timeline" "/news with query params" "<title>Epstein Archive</title>" "html"
test_endpoint "$NGROK_URL/assets/index-DPGAGFPk.js" "JavaScript bundle" "function" "html"
test_endpoint "$NGROK_URL/api/news/articles?limit=1" "API endpoint" '"articles"' "json"

echo ""
echo "=== Checking ngrok Status ==="
echo ""

/Users/masa/Projects/Epstein/scripts/ngrok_persistent.sh status

echo ""
echo "========================================="
echo -e "${GREEN}All tests passed! ✅${NC}"
echo "========================================="
echo ""
echo "Frontend is accessible at:"
echo "  - ngrok: $NGROK_URL"
echo "  - Local: $LOCAL_URL"
echo ""
echo "Test specific pages:"
echo "  - News Timeline: $NGROK_URL/news?view=timeline"
echo "  - Entities: $NGROK_URL/entities"
echo "  - Documents: $NGROK_URL/documents"
echo "  - Network: $NGROK_URL/network"
echo ""
