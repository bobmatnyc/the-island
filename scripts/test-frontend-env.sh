#!/bin/bash

# Quick Frontend Environment Test
# Usage: ./scripts/test-frontend-env.sh

EXPECTED_URL="https://the-island.ngrok.app"
OLD_URL="e25a8b2fa7a5"

echo "🔍 Quick Frontend Environment Check"
echo ""

# Test 1: .env file
if grep -q "VITE_API_BASE_URL=$EXPECTED_URL" frontend/.env 2>/dev/null; then
    echo "✅ .env configured correctly"
else
    echo "❌ .env configuration issue"
    grep "VITE_API_BASE_URL" frontend/.env 2>/dev/null || echo "File not found"
    exit 1
fi

# Test 2: Old URL check
if curl -s http://localhost:5173/ 2>/dev/null | grep -q "$OLD_URL"; then
    echo "❌ Old URL still in served content - run cache clear!"
    exit 1
else
    echo "✅ Old URL not found"
fi

# Test 3: Frontend running
if curl -s http://localhost:5173/ > /dev/null 2>&1; then
    echo "✅ Frontend serving on :5173"
else
    echo "❌ Frontend not running"
    exit 1
fi

# Test 4: Backend accessible
if curl -s "$EXPECTED_URL/api/v2/stats" > /dev/null 2>&1; then
    echo "✅ Backend accessible at $EXPECTED_URL"
else
    echo "❌ Backend not responding"
    exit 1
fi

echo ""
echo "🎉 All checks passed!"
echo "   Frontend: http://localhost:5173/"
echo "   Backend:  $EXPECTED_URL"
echo ""
echo "💡 Next: Open browser and verify API calls in Network tab"

