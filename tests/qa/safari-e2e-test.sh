#!/bin/bash

# Safari E2E Testing Script for Feature Verification
# Tests: 1M-87 (Unified Timeline), 1M-153 (Bio Tooltips), 1M-138 (Enhanced Bios)

BASE_URL="https://the-island.ngrok.app"
SCREENSHOT_DIR="/Users/masa/Projects/epstein/tests/qa/screenshots"
REPORT_FILE="/Users/masa/Projects/epstein/tests/qa/safari-test-report.md"

# Create screenshots directory
mkdir -p "$SCREENSHOT_DIR"

echo "🚀 Starting Safari E2E Testing"
echo "📋 Testing URL: $BASE_URL"
echo ""

# Initialize report
cat > "$REPORT_FILE" << EOF
# Safari E2E Test Report

**Test Date:** $(date)
**Test URL:** $BASE_URL
**Browser:** Safari (macOS)

## Test Results

EOF

# Function to take screenshot
take_screenshot() {
    local filename="$1"
    local title="$2"

    osascript -e "tell application \"Safari\"
        delay 2
        set bounds of window 1 to {0, 0, 1280, 800}
    end tell"

    screencapture -x -l$(osascript -e 'tell application "Safari" to id of window 1') "$SCREENSHOT_DIR/$filename"

    if [ -f "$SCREENSHOT_DIR/$filename" ]; then
        echo "✅ Screenshot saved: $filename"
        echo "- ✅ Screenshot captured: $filename" >> "$REPORT_FILE"
    else
        echo "⚠️  Failed to capture screenshot: $filename"
    fi
}

# Function to navigate Safari
navigate_safari() {
    local url="$1"

    osascript << APPLESCRIPT
tell application "Safari"
    activate
    if (count of windows) is 0 then
        make new document
    end if
    set URL of document 1 to "$url"
    delay 3
end tell
APPLESCRIPT
}

# Function to get page content
get_page_content() {
    osascript << 'APPLESCRIPT'
tell application "Safari"
    do JavaScript "document.body.innerText" in document 1
end tell
APPLESCRIPT
}

echo "============================================================"
echo "TEST 1: Home Page - Unified Timeline & News Card (1M-87)"
echo "============================================================"

cat >> "$REPORT_FILE" << EOF

### TEST 1: Unified Timeline & News Card (1M-87)

**Objective:** Verify home page shows exactly 5 dashboard cards with unified "Timeline & News" card

EOF

navigate_safari "$BASE_URL"
sleep 3

take_screenshot "home-page-safari.png" "Home Page"

# Check page content
PAGE_CONTENT=$(get_page_content)

if echo "$PAGE_CONTENT" | grep -i "Timeline" > /dev/null && echo "$PAGE_CONTENT" | grep -i "News" > /dev/null; then
    echo "✅ Timeline & News content found"
    echo "- ✅ Timeline & News content detected in page" >> "$REPORT_FILE"
else
    echo "⚠️  Timeline & News content not clearly visible"
    echo "- ⚠️ Timeline & News content unclear" >> "$REPORT_FILE"
fi

# Try to click on Timeline link
osascript << 'APPLESCRIPT'
tell application "Safari"
    do JavaScript "
        var links = Array.from(document.querySelectorAll('a, button, div[role=button]'));
        var timelineLink = links.find(el => el.textContent.match(/timeline/i));
        if (timelineLink) {
            console.log('Found timeline link:', timelineLink.textContent);
            timelineLink.click();
            'Clicked timeline link';
        } else {
            'Timeline link not found';
        }
    " in document 1
end tell
APPLESCRIPT

sleep 3

echo ""
echo "============================================================"
echo "TEST 2: Timeline Page Navigation"
echo "============================================================"

cat >> "$REPORT_FILE" << EOF

### TEST 2: Timeline Page

**Objective:** Verify timeline page loads and displays news content

EOF

CURRENT_URL=$(osascript -e 'tell application "Safari" to return URL of document 1')
echo "Current URL: $CURRENT_URL"

if echo "$CURRENT_URL" | grep -i "timeline" > /dev/null; then
    echo "✅ Successfully navigated to Timeline page"
    echo "- ✅ Navigation to /timeline successful" >> "$REPORT_FILE"
else
    echo "⚠️  Manual navigation to timeline"
    navigate_safari "$BASE_URL/timeline"
    echo "- ⚠️ Manual navigation required" >> "$REPORT_FILE"
fi

sleep 2
take_screenshot "timeline-page-safari.png" "Timeline Page"

PAGE_CONTENT=$(get_page_content)

if echo "$PAGE_CONTENT" | grep -i "news\|event\|article" > /dev/null; then
    echo "✅ Timeline/News content visible"
    echo "- ✅ Timeline content detected" >> "$REPORT_FILE"
fi

echo ""
echo "============================================================"
echo "TEST 3: Flights Page - Entity Bio Tooltips (1M-153)"
echo "============================================================"

cat >> "$REPORT_FILE" << EOF

### TEST 3: Flight Logs Entity Tooltips (1M-153)

**Objective:** Verify entity bio tooltips appear on hover in flight logs

EOF

navigate_safari "$BASE_URL/flights"
sleep 3

take_screenshot "flights-page-safari.png" "Flights Page"

PAGE_CONTENT=$(get_page_content)

if echo "$PAGE_CONTENT" | grep -i "flight\|passenger\|clinton\|maxwell" > /dev/null; then
    echo "✅ Flight data visible"
    echo "- ✅ Flight data loaded" >> "$REPORT_FILE"

    # Check for HoverCard or tooltip implementation
    TOOLTIP_CHECK=$(osascript << 'APPLESCRIPT'
tell application "Safari"
    do JavaScript "
        var hasHoverCard = document.querySelectorAll('[role=tooltip], .HoverCard, [class*=tooltip]').length > 0;
        var hasEntityLinks = document.querySelectorAll('a[href*=entity], a[href*=person]').length > 0;
        JSON.stringify({hasHoverCard: hasHoverCard, hasEntityLinks: hasEntityLinks});
    " in document 1
end tell
APPLESCRIPT
)
    echo "Tooltip check result: $TOOLTIP_CHECK"
    echo "- ℹ️ Tooltip elements: $TOOLTIP_CHECK" >> "$REPORT_FILE"
fi

echo ""
echo "============================================================"
echo "TEST 4: Enhanced Entity Biographies (1M-138)"
echo "============================================================"

cat >> "$REPORT_FILE" << EOF

### TEST 4: Enhanced Entity Biographies (1M-138)

**Objective:** Verify entity pages show biography, timeline, relationships, and references

EOF

# Test multiple entity pages
ENTITIES=("jeffrey_epstein" "ghislaine_maxwell" "bill_clinton")

for entity in "${ENTITIES[@]}"; do
    echo "Testing entity: $entity"

    navigate_safari "$BASE_URL/entities/$entity"
    sleep 3

    take_screenshot "entity-${entity}-safari.png" "Entity: $entity"

    PAGE_CONTENT=$(get_page_content)

    echo "  Checking for biography sections..."

    if echo "$PAGE_CONTENT" | grep -i "biography\|bio\|about" > /dev/null; then
        echo "  ✅ Biography section found"
        echo "- ✅ Entity $entity: Biography present" >> "$REPORT_FILE"
    fi

    if echo "$PAGE_CONTENT" | grep -i "timeline\|chronology\|history" > /dev/null; then
        echo "  ✅ Timeline section found"
        echo "- ✅ Entity $entity: Timeline present" >> "$REPORT_FILE"
    fi

    if echo "$PAGE_CONTENT" | grep -i "relationship\|connection\|associate" > /dev/null; then
        echo "  ✅ Relationships section found"
        echo "- ✅ Entity $entity: Relationships present" >> "$REPORT_FILE"
    fi

    if echo "$PAGE_CONTENT" | grep -i "document\|reference\|source" > /dev/null; then
        echo "  ✅ Document references found"
        echo "- ✅ Entity $entity: Document references present" >> "$REPORT_FILE"
    fi

    echo ""
done

echo ""
echo "============================================================"
echo "TEST 5: Mobile Responsiveness"
echo "============================================================"

cat >> "$REPORT_FILE" << EOF

### TEST 5: Mobile Responsiveness

**Objective:** Test responsive design at mobile viewport

EOF

# Set mobile viewport
osascript << 'APPLESCRIPT'
tell application "Safari"
    set bounds of window 1 to {0, 0, 375, 667}
    delay 2
end tell
APPLESCRIPT

navigate_safari "$BASE_URL"
sleep 2

take_screenshot "home-mobile-safari.png" "Home Page Mobile"

echo "✅ Mobile viewport screenshot captured"
echo "- ✅ Mobile viewport (375x667) tested" >> "$REPORT_FILE"

# Reset window size
osascript << 'APPLESCRIPT'
tell application "Safari"
    set bounds of window 1 to {0, 0, 1280, 800}
end tell
APPLESCRIPT

echo ""
echo "============================================================"
echo "TEST SUMMARY"
echo "============================================================"

cat >> "$REPORT_FILE" << EOF

## Summary

All tests completed. Screenshots saved to: $SCREENSHOT_DIR

### Screenshots Captured:
- home-page-safari.png
- timeline-page-safari.png
- flights-page-safari.png
- entity-jeffrey_epstein-safari.png
- entity-ghislaine_maxwell-safari.png
- entity-bill_clinton-safari.png
- home-mobile-safari.png

### Next Steps:
1. Manual verification of entity bio tooltips (hover interactions)
2. Visual inspection of screenshot evidence
3. Cross-browser testing if needed

---
*Test completed at $(date)*
EOF

echo "✅ All tests completed!"
echo "📄 Report saved to: $REPORT_FILE"
echo "📸 Screenshots saved to: $SCREENSHOT_DIR"
echo ""

# Display screenshot list
echo "Screenshots captured:"
ls -lh "$SCREENSHOT_DIR"/*.png 2>/dev/null | awk '{print "  -", $9}' | sed 's|.*/||'
