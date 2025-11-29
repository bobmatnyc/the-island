# Timeline UI - Visual Testing Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- ✅ Total height: ~60-70px (previously ~120-140px)
- ✅ Header padding: Compact but readable
- ✅ Slider visible with month labels
- ✅ 3 navigation buttons centered
- ✅ All text and controls disappear

---

## Quick Test Checklist

### 🚀 Start Testing
```bash
cd /Users/masa/Projects/epstein
./start_server.sh
# Open http://localhost:5001 in browser
# Click "Flights" tab
```

---

## ✅ Visual Inspection Checklist

### 1️⃣ Expanded State (Default)

**What You Should See:**
```
┌─────────────────────────────────────────────────────────┐
│ 📅 Flight Timeline  │  Sep 2002   │  [chevron-down]    │
│                     │  5 routes   │                     │
├─────────────────────────────────────────────────────────┤
│ ════════●══════════════════════════════════════════     │
│ Jan 02   Apr 02   Jul 02   Sep 02   Dec 02   Mar 03    │
├─────────────────────────────────────────────────────────┤
│        [< Previous]  [Latest]  [Next >]                 │
└─────────────────────────────────────────────────────────┘
```

**Measurements:**
- ✅ Total height: ~60-70px (previously ~120-140px)
- ✅ Header padding: Compact but readable
- ✅ Slider visible with month labels
- ✅ 3 navigation buttons centered

### 2️⃣ Click Chevron-Down → Collapsed State

**What You Should See:**
```
┌──────┐
│  📅  │  ← Single circular button
└──────┘
```

**Expected Changes:**
- ✅ All text and controls disappear
- ✅ Only circular calendar icon remains
- ✅ Button size: 40px × 40px (desktop) or 36px (mobile)
- ✅ Background: Blue/accent color
- ✅ Icon: White calendar symbol
- ✅ Smooth animation (300ms)

### 3️⃣ Hover Over Collapsed Icon

**Visual Feedback:**
- ✅ Background gets slightly darker
- ✅ Icon scales up ~5% (subtle zoom)
- ✅ Tooltip appears: "Expand Timeline"
- ✅ Cursor changes to pointer

### 4️⃣ Click Calendar Icon → Re-Expand

**What You Should See:**
- ✅ Button expands to full panel
- ✅ Icon changes: 📅 calendar → ⌄ chevron-down
- ✅ Tooltip changes: "Minimize Timeline"
- ✅ Same month/state as before collapse
- ✅ Smooth animation (300ms)

---

## 🎯 Functional Tests

### Test 1: Slider Functionality
1. **Drag Handle**: Click and drag the slider circle
   - ✅ Handle moves smoothly
   - ✅ Tooltip shows month as you drag
   - ✅ Map updates when you release

2. **Click Track**: Click directly on slider bar
   - ✅ Handle jumps to clicked position
   - ✅ Month updates immediately

### Test 2: Navigation Buttons
1. **Previous Button**: Click "Previous"
   - ✅ Slider moves left one month
   - ✅ Map shows previous month's flights
   - ✅ Button disables at earliest month

2. **Next Button**: Click "Next"
   - ✅ Slider moves right one month
   - ✅ Map shows next month's flights
   - ✅ Button disables at latest month

3. **Latest Button**: Click "Latest"
   - ✅ Slider jumps to most recent month
   - ✅ Map shows most recent flights

### Test 3: State Persistence
1. Select a specific month (e.g., "Jul 2002")
2. Click collapse (chevron-down)
3. Click expand (calendar icon)
   - ✅ Should return to "Jul 2002" (not reset)
   - ✅ Map should show same flights

### Test 4: Multiple Collapse/Expand Cycles
1. Expand → Collapse → Expand → Collapse (repeat 3x)
   - ✅ No visual glitches
   - ✅ Icons always change correctly
   - ✅ Animations remain smooth
   - ✅ No console errors

---

## 📱 Mobile Testing

### Resize Browser to 375px × 667px (iPhone SE)

**Visual Differences:**
- ✅ Timeline spans full width (10px margins)
- ✅ Buttons smaller: 10px font, 4px padding
- ✅ Controls gap: 6px (vs 8px desktop)
- ✅ Collapsed icon: 36px (vs 40px desktop)

**Touch Testing:**
1. **Tap Buttons**: All buttons easily tappable
2. **Drag Slider**: Touch drag works smoothly
3. **Tap Collapsed Icon**: Easy to tap and expand

---

## 🐛 Common Issues to Check

### ❌ Visual Problems

**Issue**: Panel not half height
- Check: CSS changes applied? (padding, margins)
- Expected: ~60-70px total height

**Issue**: Icon doesn't change on collapse
- Check: JavaScript console for errors
- Check: lucide library loaded?
- Expected: chevron-down → calendar

**Issue**: Collapsed button not circular
- Check: CSS for `.minimized .timeline-toggle-btn`
- Expected: 40px × 40px, border-radius: 50%

**Issue**: Transition not smooth
- Check: CSS transition property present
- Expected: 0.3s cubic-bezier animation

### ❌ Functional Problems

**Issue**: Slider doesn't work after expand
- Check: noUiSlider still initialized?
- Expected: Slider functional in all states

**Issue**: Map doesn't update on month change
- Check: JavaScript console for errors
- Check: Network tab for API calls
- Expected: Map updates on slider change

**Issue**: Buttons don't disable at edges
- Check: updateNavigationButtons() being called
- Expected: Previous disabled at start, Next disabled at end

---

## 🎨 Design Quality Checks

### Spacing & Alignment
- ✅ Header elements evenly spaced
- ✅ Buttons aligned center in controls row
- ✅ Slider centered in container
- ✅ Icon centered in collapsed button

### Colors & Contrast
- ✅ Text readable against background
- ✅ Slider handle visible and distinct
- ✅ Buttons have clear hover states
- ✅ Collapsed icon high contrast (white on blue)

### Typography
- ✅ Font sizes appropriate for content
- ✅ Month label legible
- ✅ Button text readable
- ✅ Slider tooltips clear

### Animations
- ✅ Collapse/expand smooth (no jank)
- ✅ Hover effects subtle but noticeable
- ✅ No layout shift during animation
- ✅ Timing feels natural (not too fast/slow)

---

## 📊 Comparison: Before vs After

### Height Comparison
| Component | Before | After | Reduction |
|-----------|--------|-------|-----------|
| Header | 14px + 16px | 10px + 14px | 28% |
| Slider Container | 20px + 24px | 10px + 20px | 50% |
| Controls | 14px | 10px | 28% |
| Slider Height | 8px | 6px | 25% |
| **Total Height** | **~120-140px** | **~60-70px** | **~50%** |

### Collapsed State
| Feature | Before | After |
|---------|--------|-------|
| Visible Content | Header with title + month | Calendar icon only |
| Width | Full panel width | 40px × 40px |
| Space Used | ~40% of screen width | ~2% of screen width |
| Visual Impact | Medium | Minimal |

---

## ✅ Final Acceptance Criteria

**All must pass:**
1. ✅ Timeline height reduced by ~50% when expanded
2. ✅ Collapsed state shows only circular calendar icon
3. ✅ Icon changes between chevron-down and calendar
4. ✅ Smooth transitions (300ms) on collapse/expand
5. ✅ All timeline functionality preserved
6. ✅ Slider works correctly
7. ✅ Navigation buttons functional
8. ✅ State persists across collapse/expand
9. ✅ Mobile responsive (tested at 375px width)
10. ✅ No console errors
11. ✅ No visual glitches or layout shifts
12. ✅ Accessible (tooltips, focus states)

---

## 🎬 Video Test Recording (Optional)

**Record a quick video showing:**
1. Flights tab loaded with expanded timeline
2. Drag slider to different months
3. Click Previous/Next buttons
4. Click collapse button
5. Show collapsed icon state
6. Click expand button
7. Verify same month selected
8. Test on mobile (resize browser)

**Expected Duration**: ~30 seconds

---

**Last Updated**: 2025-11-18
**Status**: Ready for User Acceptance Testing
