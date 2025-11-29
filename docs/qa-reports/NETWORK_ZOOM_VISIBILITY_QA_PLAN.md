# QA Test Plan: Network Graph Zoom-Based Edge Visibility

**Date**: 2025-11-26
**Feature**: Zoom-based automatic edge filtering (progressive disclosure)
**Implementation**: `/frontend/src/pages/Network.tsx` lines 713-753
**Test Suite**: `/tests/qa/network-zoom-edge-visibility.spec.ts`

---

## Overview

This QA plan validates the zoom-based edge visibility feature that automatically adjusts edge filtering based on zoom level, implementing a progressive disclosure pattern for network visualization.

---

## Feature Requirements

### Functional Requirements

1. **Automatic Edge Filtering**
   - When zoomed out (globalScale < 1.5): Enforce minimum edge weight of 3
   - When zoomed in (globalScale ≥ 1.5): User's filter has full control
   - Seamless transition at zoom threshold (1.5)

2. **User Filter Respect**
   - User's minEdgeWeight filter always takes precedence if higher
   - No interference with manual edge weight slider
   - Works in conjunction with existing static filter

3. **Performance**
   - Weak edges skip rendering entirely (early exit)
   - No additional React state required
   - Graph updates < 1 second after zoom change

4. **Visual Quality**
   - No flickering during zoom transitions
   - Smooth edge appearance/disappearance
   - Highlighting preserved during zoom

### Expected Impact Metrics

**Network Data**: 255 nodes, 1,482 edges

| Zoom State | Effective Min Weight | Edges Visible | Reduction |
|------------|---------------------|---------------|-----------|
| Zoomed out (< 1.5) | Auto: 3 | 311 edges | **79.0%** |
| Zoomed in (≥ 1.5, filter: 0) | 0 | 1,482 edges | 0% (full detail) |
| Zoomed in (≥ 1.5, filter: 10) | 10 | 109 edges | 92.6% (user choice) |

---

## Test Suite Structure

### Test Categories

**Total Tests**: 13 comprehensive automated tests

1. **Core Functionality** (Tests 1-3)
   - Edge count changes with zoom level
   - Transition at zoom threshold (1.5)
   - Expected reduction metrics validation

2. **User Filter Interaction** (Tests 4-5)
   - User filter respected when zoomed out
   - User filter respected when zoomed in
   - Multi-filter combination scenarios (Test 9)

3. **Performance** (Test 8)
   - Graph updates < 1s requirement
   - Rapid zoom changes without errors (Test 10)

4. **Visual Quality** (Tests 6, 11, 12)
   - Smooth zoom transitions
   - No flickering
   - Edge highlighting preservation (Test 7)

5. **Edge Cases** (Tests 10, 13)
   - Rapid zoom changes
   - Expected impact metrics

---

## Test Cases

### Test 1: Fewer Edges When Zoomed Out
**Purpose**: Verify automatic filtering reduces edge count at overview level

**Steps**:
1. Load network graph
2. Set zoom to 1.0 (globalScale = 1.0)
3. Count edge pixels on canvas

**Expected Result**:
- Edge count > 0 (baseline measurement)
- Fewer edges than when zoomed in

**Success Criteria**: ✅ Edge pixels counted successfully

---

### Test 2: More Edges When Zoomed In
**Purpose**: Verify full detail available when zoomed in

**Steps**:
1. Load network graph
2. Set zoom to 2.0 (globalScale = 2.0)
3. Count edge pixels on canvas

**Expected Result**:
- Edge count > 0
- More edges than when zoomed out

**Success Criteria**: ✅ Edge pixel count higher than Test 1

---

### Test 3: Edge Transition at Zoom Threshold
**Purpose**: Verify edge count changes at threshold (1.5)

**Steps**:
1. Set zoom to 1.4 (just below threshold)
2. Count edge pixels
3. Set zoom to 1.6 (just above threshold)
4. Count edge pixels

**Expected Result**:
- Edge count at 1.6 > edge count at 1.4
- Clear transition detected at threshold

**Success Criteria**: ✅ Edge count increases above threshold

---

### Test 4: User Filter Respected When Zoomed Out
**Purpose**: Verify user's filter takes precedence over auto threshold

**Steps**:
1. Set minEdgeWeight slider to 10
2. Zoom out to 1.0
3. Count edge pixels

**Expected Result**:
- Edge filtering uses max(10, 3) = 10
- Shows ~109 edges (based on filter value 10, not auto value 3)

**Success Criteria**: ✅ User filter honored when higher than auto threshold

---

### Test 5: User Filter Respected When Zoomed In
**Purpose**: Verify user has full control when zoomed in

**Steps**:
1. Set minEdgeWeight slider to 0
2. Zoom in to 2.0
3. Count edge pixels

**Expected Result**:
- All edges visible (1,482 edges)
- No automatic filtering applied

**Success Criteria**: ✅ All edges visible with filter = 0

---

### Test 6: Smooth Zoom Transitions
**Purpose**: Verify edge counts increase progressively with zoom

**Steps**:
1. Test zoom levels: 1.0, 1.2, 1.4, 1.5, 1.6, 1.8, 2.0
2. Count edges at each level
3. Compare progression

**Expected Result**:
- Edge counts generally increase with zoom
- Clear transition at 1.5

**Success Criteria**: ✅ Progressive edge count increase

---

### Test 7: Edge Highlighting Preservation
**Purpose**: Verify highlighting persists during zoom changes

**Steps**:
1. Click node to highlight edges
2. Verify highlighting visible (darker edges)
3. Zoom in to 2.0
4. Verify highlighting still visible

**Expected Result**:
- Highlighting detected before zoom
- Highlighting detected after zoom

**Success Criteria**: ✅ Highlighting state preserved

---

### Test 8: Performance Requirement (< 1s)
**Purpose**: Verify graph updates quickly after zoom change

**Steps**:
1. Measure time to update edges when zooming
2. Set zoom to 1.8
3. Wait for canvas update
4. Calculate update time

**Expected Result**:
- Update time < 1000ms

**Success Criteria**: ✅ Performance meets requirement

---

### Test 9: Multi-Filter Combination
**Purpose**: Verify zoom and slider work together at all levels

**Steps**:
1. Test combinations:
   - Zoom 1.0 + Filter 3
   - Zoom 1.0 + Filter 10
   - Zoom 2.0 + Filter 0
   - Zoom 2.0 + Filter 10
2. Count edges for each combination
3. Verify all combinations work

**Expected Result**:
- All combinations show different edge counts
- Filters combine correctly via Math.max()

**Success Criteria**: ✅ All combinations functional

---

### Test 10: Rapid Zoom Changes
**Purpose**: Verify no errors during rapid zoom adjustments

**Steps**:
1. Rapidly change zoom: 1.0, 2.0, 0.8, 1.5, 1.2, 1.8, 1.0
2. Wait 100ms between changes
3. Check for console errors

**Expected Result**:
- No console errors
- Graph remains responsive

**Success Criteria**: ✅ No errors in console

---

### Test 11: No Flickering During Transitions
**Purpose**: Verify smooth visual transitions (visual regression)

**Steps**:
1. Take screenshot at zoom 1.0
2. Take screenshot at zoom 1.5
3. Take screenshot at zoom 2.0
4. Save for visual inspection

**Expected Result**:
- Screenshots saved successfully
- Visual inspection required

**Success Criteria**: ✅ Screenshots generated for manual review

---

### Test 12: Expected Edge Reduction Metrics
**Purpose**: Verify actual impact matches implementation summary

**Steps**:
1. Zoom out to 1.0, set filter to 0
2. Count edges (should be ~311 for auto threshold 3)
3. Zoom in to 2.0, keep filter at 0
4. Count edges (should be ~1,482 for all edges)
5. Calculate reduction ratio

**Expected Result**:
- Zoomed out: ~311 edges (79% reduction)
- Zoomed in: ~1,482 edges (0% reduction)
- Reduction ratio validates expected impact

**Success Criteria**: ✅ Reduction ratio matches expected ~21% (311/1482)

---

## Automation Strategy

### Playwright E2E Testing

**Test Framework**: Playwright
**Test File**: `/tests/qa/network-zoom-edge-visibility.spec.ts`
**Execution**: `npx playwright test tests/qa/network-zoom-edge-visibility.spec.ts`

**Helper Function**: `getEdgePixelCount(page)`
- Counts gray pixels on canvas (edges)
- RGB range: 80-120 (edge color)
- Returns pixel count as proxy for edge count

### Limitations

**Canvas Pixel Counting**:
- Approximate method (counts pixels, not actual edges)
- Visual regression (Test 11) requires manual inspection
- Actual edge count verification requires DOM inspection

**Manual Testing Required**:
- Visual quality assessment
- Smoothness of transitions
- User experience validation

---

## Success Criteria

### Automated Tests

**Pass Threshold**: ≥ 80% (10/13 tests)
**Target**: ≥ 90% (12/13 tests)

**Core Functionality**: MUST PASS
- Test 1: Zoomed out edge count
- Test 2: Zoomed in edge count
- Test 3: Threshold transition
- Test 4: User filter (zoomed out)
- Test 5: User filter (zoomed in)

**Performance**: MUST PASS
- Test 8: < 1s update time

**Quality**: SHOULD PASS
- Test 6: Smooth transitions
- Test 7: Highlighting preserved
- Test 9: Multi-filter combinations
- Test 10: No errors

**Edge Cases**: NICE TO HAVE
- Test 11: Visual regression (manual)
- Test 12: Expected metrics

### Production Readiness Checklist

- [ ] Core functionality: 100% pass rate (Tests 1-5)
- [ ] Performance requirement: < 1s (Test 8)
- [ ] User filter interaction: Validated (Tests 4-5, 9)
- [ ] No console errors: Confirmed (Test 10)
- [ ] Edge highlighting: Preserved (Test 7)
- [ ] Visual quality: Manually validated (Test 11)
- [ ] Expected impact: Verified (Test 12)
- [ ] Overall pass rate: ≥ 80%

---

## Known Issues / Test Adjustments

### Potential Test Failures

1. **Canvas Pixel Counting Variability**
   - **Issue**: Pixel counts may vary slightly between runs
   - **Mitigation**: Use relative comparisons, not absolute values
   - **Example**: "edgesZoomedIn > edgesZoomedOut" instead of exact counts

2. **Visual Regression (Test 11)**
   - **Issue**: Automated visual comparison not implemented
   - **Mitigation**: Manual screenshot review required
   - **Action**: Visual inspection of /tmp/zoom_*.png files

3. **Browser Rendering Differences**
   - **Issue**: Canvas rendering may differ across browsers
   - **Mitigation**: Test in primary browser (Chrome) first
   - **Action**: Cross-browser testing as secondary phase

### Test Environment Requirements

**Prerequisites**:
- Frontend running on http://localhost:5173
- Network page accessible at /network route
- Canvas element loaded with graph data
- Playwright installed (`npm install @playwright/test`)

**Dependencies**:
- React Force Graph 2D library
- Network graph data (255 nodes, 1,482 edges)
- Zoom controls functional

---

## Execution Instructions

### Run All Tests

```bash
npx playwright test tests/qa/network-zoom-edge-visibility.spec.ts --reporter=list
```

### Run Specific Test

```bash
npx playwright test tests/qa/network-zoom-edge-visibility.spec.ts -g "should show fewer edges when zoomed out"
```

### Debug Mode

```bash
npx playwright test tests/qa/network-zoom-edge-visibility.spec.ts --debug
```

### Visual Regression Review

```bash
# Screenshots saved to /tmp/zoom_*.png
open /tmp/zoom_1.0.png
open /tmp/zoom_1.5.png
open /tmp/zoom_2.0.png
```

---

## Reporting

### Test Results Format

**Expected Output**:
```
✓ should show fewer edges when zoomed out (zoom < 1.5) (1.2s)
✓ should show more edges when zoomed in (zoom >= 1.5) (1.1s)
✓ should transition edge count at zoom threshold (1.5) (1.5s)
✓ should respect user filter when zoomed out (1.3s)
✓ should respect user filter when zoomed in (1.2s)
✓ should maintain smooth zoom transitions (2.8s)
✓ should preserve edge highlighting when zooming (1.4s)
✓ should update edges within 1 second of zoom change (0.8s)
✓ should work with edge weight slider at all zoom levels (2.2s)
✓ should handle rapid zoom changes without errors (1.5s)
⚠ should not flicker during zoom transitions (manual review required) (1.1s)
✓ should show expected edge reduction metrics (1.6s)

12 passed (18.7s)
1 manual review required
```

### QA Report Template

**After test execution, create**:
`/docs/qa-reports/NETWORK_ZOOM_VISIBILITY_QA_REPORT.md`

**Include**:
- Test execution summary (pass/fail counts)
- Performance metrics (update times)
- Edge count measurements at different zoom levels
- Screenshots for visual regression
- Issues found (if any)
- Production readiness recommendation

---

## Timeline

**Estimated Time**: 2-3 hours

1. **Test Execution** (30 minutes)
   - Run automated test suite
   - Collect results and screenshots

2. **Manual Validation** (1 hour)
   - Visual quality inspection
   - User experience testing
   - Cross-browser verification

3. **Issue Analysis** (30 minutes)
   - Investigate any failures
   - Document edge cases

4. **QA Report** (1 hour)
   - Compile test results
   - Write production readiness assessment
   - Document recommendations

---

## Next Steps

1. **Execute test suite**: Run Playwright tests
2. **Review results**: Analyze pass/fail metrics
3. **Manual validation**: Visual quality check
4. **Create QA report**: Document findings
5. **Production decision**: Approve or request fixes

---

## Sign-Off

**QA Plan Status**: ✅ **COMPLETE**
**Test Suite Status**: ✅ **READY FOR EXECUTION**
**Automation Coverage**: 92% (12/13 automated, 1 manual)
**Estimated Execution Time**: 20-30 minutes (automated portion)

This QA plan provides comprehensive validation of the zoom-based edge visibility feature, ensuring it meets functional requirements, performance standards, and quality expectations before production deployment.

**Ready to execute test suite and generate QA report.**
