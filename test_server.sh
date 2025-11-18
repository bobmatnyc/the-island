#!/bin/bash
# Comprehensive test of Epstein Archive server

echo "========================================="
echo "  EPSTEIN ARCHIVE COMPREHENSIVE TEST"
echo "========================================="
echo ""

PASS=0
FAIL=0

# Helper functions
pass() {
    echo "✅ PASS: $1"
    ((PASS++))
}

fail() {
    echo "❌ FAIL: $1"
    ((FAIL++))
}

# Test 1: Server responds
echo "Test 1: Server responding on port 8081..."
if curl -s -I http://localhost:8081/ | grep -q "200 OK"; then
    pass "Server is responding"
else
    fail "Server is not responding"
fi

# Test 2: RAG search endpoint
echo "Test 2: RAG search endpoint..."
RESULT=$(curl -s "http://localhost:8081/api/rag/search?query=test&limit=1" 2>&1)
if echo "$RESULT" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
    pass "RAG search endpoint returns valid JSON"
else
    fail "RAG search endpoint error"
fi

# Test 3: RAG stats endpoint
echo "Test 3: RAG stats endpoint..."
STATS=$(curl -s "http://localhost:8081/api/rag/stats" 2>&1)
if echo "$STATS" | python3 -c "import sys, json; d=json.load(sys.stdin); exit(0 if d.get('total_documents', 0) > 0 else 1)" 2>/dev/null; then
    DOC_COUNT=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_documents'])")
    pass "RAG stats shows $DOC_COUNT documents"
else
    fail "RAG stats endpoint error"
fi

# Test 4: No ChromaDB warnings
echo "Test 4: Checking for ChromaDB warnings..."
if grep -q "ChromaDB dependencies may not be installed" /tmp/epstein_8081_venv.log 2>/dev/null; then
    fail "ChromaDB warning found in logs"
else
    pass "No ChromaDB warnings"
fi

# Test 5: RAG routes loaded
echo "Test 5: RAG routes loaded..."
if grep -q "RAG routes registered" /tmp/epstein_8081_venv.log 2>/dev/null; then
    pass "RAG routes successfully registered"
else
    fail "RAG routes not found in logs"
fi

# Test 6: Ngrok tunnel active
echo "Test 6: Ngrok tunnel..."
if curl -s http://localhost:4040/api/tunnels 2>&1 | python3 -c "import sys, json; exit(0 if json.load(sys.stdin).get('tunnels') else 1)" 2>/dev/null; then
    TUNNEL=$(curl -s http://localhost:4040/api/tunnels 2>&1 | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])")
    pass "Ngrok tunnel active at $TUNNEL"
else
    fail "Ngrok tunnel not active"
fi

# Test 7: Ngrok public access
echo "Test 7: Ngrok public access..."
if curl -s -I https://the-island.ngrok.app/ 2>&1 | grep -q "200"; then
    pass "Public access via ngrok working"
else
    fail "Public access via ngrok failed"
fi

# Test 8: Process check
echo "Test 8: Server process..."
if ps aux | grep -q "[a]pp.py 8081"; then
    pass "Server process running on correct port"
else
    fail "Server process not found"
fi

# Summary
echo ""
echo "========================================="
echo "           TEST SUMMARY"
echo "========================================="
echo "Passed: $PASS"
echo "Failed: $FAIL"
echo "Total:  $((PASS + FAIL))"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "✅ ALL TESTS PASSED"
    exit 0
else
    echo "❌ SOME TESTS FAILED"
    exit 1
fi
