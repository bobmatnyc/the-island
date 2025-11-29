#!/bin/bash
# Backend Stability Test Suite
#
# Design Decision: Comprehensive testing for backend stability fixes
#
# Test Coverage:
# - Health endpoint availability
# - API endpoints responsiveness
# - Error handling for invalid requests
# - CORS configuration
# - Performance under load (basic)

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKEND_URL="http://localhost:8081"
TESTS_PASSED=0
TESTS_FAILED=0

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
}

# Test 1: Health endpoint exists and returns 200
test_health_endpoint() {
    print_test "Testing /health endpoint..."

    local status=$(curl -s -o /dev/null -w "%{http_code}" $BACKEND_URL/health)

    if [ "$status" = "200" ]; then
        local response=$(curl -s $BACKEND_URL/health)
        if echo "$response" | grep -q '"status":"ok"'; then
            print_pass "Health endpoint returns 200 with valid JSON"
        else
            print_fail "Health endpoint returns 200 but invalid JSON: $response"
        fi
    else
        print_fail "Health endpoint returned status: $status"
    fi
}

# Test 2: API stats endpoint
test_stats_endpoint() {
    print_test "Testing /api/stats endpoint..."

    local status=$(curl -s -o /dev/null -w "%{http_code}" $BACKEND_URL/api/stats)

    if [ "$status" = "200" ]; then
        print_pass "Stats endpoint returns 200"
    else
        print_fail "Stats endpoint returned status: $status"
    fi
}

# Test 3: CORS headers
test_cors_headers() {
    print_test "Testing CORS configuration..."

    local cors_header=$(curl -s -I -H "Origin: http://localhost:5173" $BACKEND_URL/health | grep -i "access-control-allow-origin")

    if [ ! -z "$cors_header" ]; then
        print_pass "CORS headers present: $cors_header"
    else
        print_fail "CORS headers missing"
    fi
}

# Test 4: Error handling for non-existent endpoint
test_404_handling() {
    print_test "Testing 404 error handling..."

    local status=$(curl -s -o /dev/null -w "%{http_code}" $BACKEND_URL/api/nonexistent)

    if [ "$status" = "404" ]; then
        print_pass "404 returned for non-existent endpoint"
    else
        print_fail "Expected 404, got: $status"
    fi
}

# Test 5: JSON response format
test_json_responses() {
    print_test "Testing JSON response format..."

    local response=$(curl -s $BACKEND_URL/health)

    if echo "$response" | python3 -m json.tool > /dev/null 2>&1; then
        print_pass "Health endpoint returns valid JSON"
    else
        print_fail "Health endpoint returned invalid JSON: $response"
    fi
}

# Test 6: API endpoint exists
test_api_endpoints() {
    print_test "Testing critical API endpoints..."

    local endpoints=(
        "/health:200"
        "/api/stats:200"
        "/api/entities:200"
        "/api/documents:200"
        "/api/timeline:200"
        "/api/network:200"
    )

    for endpoint_spec in "${endpoints[@]}"; do
        IFS=':' read -r endpoint expected_status <<< "$endpoint_spec"
        local status=$(curl -s -o /dev/null -w "%{http_code}" $BACKEND_URL$endpoint)

        if [ "$status" = "$expected_status" ]; then
            print_pass "Endpoint $endpoint returns $expected_status"
        else
            print_fail "Endpoint $endpoint returned $status, expected $expected_status"
        fi
    done
}

# Test 7: Response time
test_response_time() {
    print_test "Testing response time..."

    local response_time=$(curl -s -o /dev/null -w "%{time_total}" $BACKEND_URL/health)
    local threshold=1.0

    if (( $(echo "$response_time < $threshold" | bc -l) )); then
        print_pass "Health endpoint response time: ${response_time}s (< ${threshold}s)"
    else
        print_fail "Health endpoint too slow: ${response_time}s (> ${threshold}s)"
    fi
}

# Main test execution
echo "========================================"
echo "Backend Stability Test Suite"
echo "========================================"
echo "Backend URL: $BACKEND_URL"
echo ""

# Check if backend is running
if ! curl -s $BACKEND_URL/health > /dev/null 2>&1; then
    echo -e "${RED}ERROR:${NC} Backend is not running at $BACKEND_URL"
    echo "Run: ./scripts/dev-backend.sh start"
    exit 1
fi

# Run tests
test_health_endpoint
test_stats_endpoint
test_cors_headers
test_404_handling
test_json_responses
test_api_endpoints
test_response_time

echo ""
echo "========================================"
echo "Test Results"
echo "========================================"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
echo "========================================"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
fi
