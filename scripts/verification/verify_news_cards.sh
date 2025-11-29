#!/bin/bash

# News Article Cards Rendering Verification Script
# This script provides step-by-step verification instructions

echo "========================================"
echo "NEWS ARTICLE CARDS VERIFICATION"
echo "========================================"
echo ""

# Check if frontend is running
echo "Checking if frontend is running..."
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✅ Frontend is running on http://localhost:5173"
else
    echo "❌ Frontend is NOT running!"
    echo "Please start the frontend: cd frontend && npm run dev"
    exit 1
fi

echo ""
echo "========================================"
echo "OPENING BROWSER..."
echo "========================================"
echo ""

# Open Safari to the entity page
open -a Safari "http://localhost:5173/entities/jeffrey_epstein"

sleep 3

echo "========================================"
echo "MANUAL VERIFICATION INSTRUCTIONS"
echo "========================================"
echo ""

echo "1️⃣  VERIFY CONSOLE DEBUG OUTPUT"
echo "   - Open Safari Developer Tools (⌘⌥I)"
echo "   - Go to Console tab"
echo "   - Look for these debug messages:"
echo "     [EntityDetail] Rendering news cards section:"
echo "       isArray: true"
echo "       length: 100"
echo "       firstArticle: {...}"
echo ""
read -p "   Press ENTER when you've checked the console..."
echo ""

echo "2️⃣  COUNT ARTICLE CARDS IN DOM"
echo "   - In the Console tab, run this command:"
echo "     document.querySelectorAll('article').length"
echo ""
echo "   Expected result: Should show 10 or more"
echo ""
read -p "   How many article cards found? (enter number): " card_count
echo "   You reported: $card_count cards"

if [ "$card_count" -ge 10 ] 2>/dev/null; then
    echo "   ✅ PASS: Found $card_count cards"
else
    echo "   ❌ FAIL: Expected 10+, found $card_count"
fi
echo ""

echo "3️⃣  INSPECT ARTICLE CARD CONTENT"
echo "   - Scroll to the News Articles section"
echo "   - Check the first article card has:"
echo "     ✓ Article title (clickable link)"
echo "     ✓ Publication name"
echo "     ✓ Content excerpt"
echo "     ✓ Publication date"
echo "     ✓ Credibility score badge"
echo ""
read -p "   Do the cards display complete content? (y/n): " has_content

if [ "$has_content" = "y" ]; then
    echo "   ✅ PASS: Cards have complete content"
else
    echo "   ❌ FAIL: Cards missing content"
fi
echo ""

echo "4️⃣  CHECK FOR ERRORS"
echo "   - In Safari Console, check for:"
echo "     ❌ JavaScript errors (red text)"
echo "     ⚠️  Warnings (yellow text)"
echo ""
read -p "   Any errors or warnings? (y/n): " has_errors

if [ "$has_errors" = "n" ]; then
    echo "   ✅ PASS: No errors"
else
    echo "   ❌ FAIL: Errors present"
fi
echo ""

echo "5️⃣  VERIFY BADGE DISPLAY"
echo "   - Look for badge showing '100 articles'"
echo "   - Should be near the article cards section"
echo ""
read -p "   Does badge show '100 articles'? (y/n): " badge_ok

if [ "$badge_ok" = "y" ]; then
    echo "   ✅ PASS: Badge displays correctly"
else
    echo "   ❌ FAIL: Badge issue"
fi
echo ""

echo "6️⃣  TEST USER INTERACTIONS"
echo "   - Try clicking on an article card"
echo "   - Look for 'View All' button"
echo ""
read -p "   Do interactions work? (y/n): " interactions_ok

if [ "$interactions_ok" = "y" ]; then
    echo "   ✅ PASS: Interactions work"
else
    echo "   ❌ FAIL: Interaction issues"
fi
echo ""

echo "========================================"
echo "VERIFICATION SUMMARY"
echo "========================================"
echo ""

# Calculate results
passes=0
[ "$card_count" -ge 10 ] 2>/dev/null && passes=$((passes + 1))
[ "$has_content" = "y" ] && passes=$((passes + 1))
[ "$has_errors" = "n" ] && passes=$((passes + 1))
[ "$badge_ok" = "y" ] && passes=$((passes + 1))
[ "$interactions_ok" = "y" ] && passes=$((passes + 1))

echo "Results: $passes/5 checks passed"
echo ""
echo "1. Article cards in DOM: $([ "$card_count" -ge 10 ] 2>/dev/null && echo "✅ PASS ($card_count cards)" || echo "❌ FAIL")"
echo "2. Cards have content: $([ "$has_content" = "y" ] && echo "✅ PASS" || echo "❌ FAIL")"
echo "3. No errors: $([ "$has_errors" = "n" ] && echo "✅ PASS" || echo "❌ FAIL")"
echo "4. Badge displays: $([ "$badge_ok" = "y" ] && echo "✅ PASS" || echo "❌ FAIL")"
echo "5. Interactions work: $([ "$interactions_ok" = "y" ] && echo "✅ PASS" || echo "❌ FAIL")"
echo ""

if [ $passes -eq 5 ]; then
    echo "🎉 ALL CHECKS PASSED!"
    echo ""
    echo "News article cards are rendering correctly:"
    echo "- Console shows debug output"
    echo "- Cards appear in DOM"
    echo "- Content is complete"
    echo "- No errors present"
    echo "- Badge displays correctly"
    echo "- Interactions work"
else
    echo "⚠️  SOME CHECKS FAILED"
    echo ""
    echo "Please review failed checks above."
fi

echo ""
echo "========================================"
echo "EVIDENCE COLLECTION"
echo "========================================"
echo ""

echo "For documentation, please provide:"
echo "1. Screenshot of article cards section"
echo "2. Screenshot of console showing debug output"
echo "3. Copy/paste console debug messages"
echo ""
read -p "Press ENTER to finish..."

echo ""
echo "✅ Verification complete!"
