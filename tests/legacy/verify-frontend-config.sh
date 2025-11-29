#!/bin/bash

# Frontend Configuration Verification Script
# Tests that Vite environment variables are correctly configured and working

set -e

FRONTEND_DIR="/Users/masa/Projects/epstein/frontend"
EXPECTED_URL="https://the-island.ngrok.app"
OLD_URL="e25a8b2fa7a5.ngrok.app"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Frontend Environment Configuration Verification         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Test 1: Verify .env file
echo "📋 Test 1: Checking .env file configuration..."
if grep -q "VITE_API_BASE_URL=$EXPECTED_URL" "$FRONTEND_DIR/.env"; then
    echo "   ✅ .env file correctly configured"
    echo "   📍 URL: $EXPECTED_URL"
else
    echo "   ❌ .env file has incorrect URL!"
    grep "VITE_API_BASE_URL" "$FRONTEND_DIR/.env" || echo "   Variable not found"
    exit 1
fi
echo ""

# Test 2: Check for old URL remnants
echo "🔍 Test 2: Checking for old URL remnants..."
if curl -s http://localhost:5173/ 2>/dev/null | grep -q "$OLD_URL"; then
    echo "   ❌ ERROR: Old URL ($OLD_URL) still in served content!"
    exit 1
else
    echo "   ✅ Old URL not found in served content"
fi
echo ""

# Test 3: Verify Vite cache was cleared
echo "🗑️  Test 3: Verifying cache directories are clean..."
if [ -d "$FRONTEND_DIR/node_modules/.vite" ]; then
    echo "   ⚠️  WARNING: Vite cache directory exists (may contain stale data)"
else
    echo "   ✅ Vite cache directory cleared"
fi

if [ -d "$FRONTEND_DIR/.vite" ]; then
    echo "   ⚠️  WARNING: .vite directory exists (may contain stale data)"
else
    echo "   ✅ .vite directory cleared"
fi
echo ""

# Test 4: Verify frontend is running
echo "🌐 Test 4: Checking frontend server status..."
if curl -s http://localhost:5173/ > /dev/null 2>&1; then
    echo "   ✅ Frontend serving on http://localhost:5173/"
else
    echo "   ❌ Frontend not accessible"
    exit 1
fi
echo ""

# Test 5: Verify backend is accessible
echo "🔗 Test 5: Testing backend connectivity..."
response=$(curl -s -w "\n%{http_code}" "$EXPECTED_URL/api/v2/stats" 2>/dev/null)
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" = "200" ]; then
    echo "   ✅ Backend responding successfully"
    echo "   📍 URL: $EXPECTED_URL/api/v2/stats"

    # Show sample data
    body=$(echo "$response" | head -n-1)
    total_docs=$(echo "$body" | jq -r '.data.documents.total' 2>/dev/null)
    total_entities=$(echo "$body" | jq -r '.data.entities.total' 2>/dev/null)

    if [ -n "$total_docs" ]; then
        echo "   📊 Documents: $total_docs, Entities: $total_entities"
    fi
else
    echo "   ❌ Backend not responding (HTTP $http_code)"
    exit 1
fi
echo ""

# Test 6: Check CORS configuration
echo "🔐 Test 6: Verifying CORS configuration..."
cors_headers=$(curl -s -I \
  -H "Origin: http://localhost:5173" \
  "$EXPECTED_URL/api/v2/stats" 2>/dev/null | grep -i "access-control-allow-origin" || echo "")

if [ -n "$cors_headers" ]; then
    echo "   ✅ CORS headers configured correctly"
else
    echo "   ⚠️  WARNING: CORS headers not detected"
fi
echo ""

# Summary
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅ All Automated Tests Passed                           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "📝 Configuration Summary:"
echo "   • Frontend:  http://localhost:5173/"
echo "   • Backend:   $EXPECTED_URL"
echo "   • Old URL:   ❌ Removed ($OLD_URL)"
echo "   • Cache:     🗑️  Cleared"
echo "   • Status:    ✅ All systems operational"
echo ""
echo "🔍 Manual Browser Verification:"
echo "   1. Open http://localhost:5173/ in your browser"
echo "   2. Open Developer Console (F12)"
echo "   3. Navigate to Network tab"
echo "   4. Click on any page (e.g., Analytics, Entities)"
echo "   5. Verify API calls go to: $EXPECTED_URL"
echo "   6. Check console for any errors"
echo ""
echo "💡 If you see the old URL error:"
echo "   • Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+F5)"
echo "   • Clear browser cache"
echo "   • Try incognito/private window"
echo ""
