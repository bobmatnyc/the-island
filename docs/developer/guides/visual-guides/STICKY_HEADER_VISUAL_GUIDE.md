# Sticky Header Fix - Visual Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Before & After Comparison
- BEFORE (Broken Layout)
- AFTER (Fixed Layout)

---

## Before & After Comparison

### BEFORE (Broken Layout)
```
┌─────────────────────────────────────────┐
│ 🏠 MAIN HEADER (fixed)                  │
├─────────────────────────────────────────┤
│                                          │
│  📊 PAGE HEADER (sticky, top: 0)        │
│  Timeline of Events                      │
│  [Stats: 150 | 80 | 45 | 25]           │
│                                          │
├─────────────────────────────────────────┤ ← Both at top: 0
│                                          │
│  🔍 FILTER BAR (sticky, top: 0)         │
│  [All][Case][Life] [Search...]          │
│                                          │
├─────────────────────────────────────────┤
│                                          │
│  OVERLAPPING CAUSES CONTENT TO           │
│  BE PUSHED DOWN...                       │
│                                          │
│  ... Content starts here (BELOW         │
│  visible screen)                         │
│                                          │
│  ❌ USER SEES BLANK PAGE                │
│  ❌ MUST SCROLL TO SEE EVENTS           │
└─────────────────────────────────────────┘
```

### AFTER (Fixed Layout)
```
┌─────────────────────────────────────────┐
│ 🏠 MAIN HEADER (fixed)                  │
├─────────────────────────────────────────┤
│                                          │
│  📊 PAGE HEADER (sticky, top: 0)        │
│  Timeline of Events                      │
│  [Stats: 150 | 80 | 45 | 25]           │
│  Height: ~185px                          │
├─────────────────────────────────────────┤
│                                          │
│  🔍 FILTER BAR (sticky, top: 185px)     │
│  [All][Case][Life] [Search...]          │
│  Height: ~85px                           │
├─────────────────────────────────────────┤
│  ┌────────────────────────────────┐     │
│  │ 📅 2008-03-15                  │     │
│  │ Case Event: Investigation...   │     │
│  └────────────────────────────────┘     │
│                                          │
│  ✅ CONTENT VISIBLE IMMEDIATELY          │
│  ✅ NO SCROLLING NEEDED                 │
│  ✅ PROPER SPACING                      │
└─────────────────────────────────────────┘
```

## Layout Dimensions

### Desktop Layout (>768px)

```
Header Stack:
┌──────────────────────────────────────┐ ←── Viewport Top
│                                      │
│  Page Header (185px tall)            │
│  - Title: 2rem padding               │
│  - Subtitle                           │
│  - 4 Stats in row                    │
│                                      │
├──────────────────────────────────────┤ ←── 185px from top
│                                      │
│  Filter Bar (85px tall)              │
│  - Filters in horizontal row         │
│  - Search input                      │
│                                      │
├──────────────────────────────────────┤ ←── 270px from top
│                                      │
│  Content Area                        │
│  - padding-top: 2rem (32px)          │
│  - First item at: ~302px             │
│                                      │
│  [Timeline events, entity cards,     │
│   document grid, etc.]               │
│                                      │
```

### Mobile Layout (≤768px)

```
Header Stack:
┌──────────────────────────────────────┐ ←── Viewport Top
│                                      │
│  Page Header (280px tall)            │
│  - Title: 1rem padding               │
│  - Subtitle                           │
│  - 4 Stats STACKED vertically        │
│    (takes more vertical space)       │
│                                      │
│                                      │
├──────────────────────────────────────┤ ←── 280px from top
│                                      │
│  Filter Bar (120px tall)             │
│  - Filters STACKED vertically        │
│  - Search input (full width)         │
│                                      │
├──────────────────────────────────────┤ ←── 400px from top
│                                      │
│  Content Area                        │
│  - padding-top: 1rem (16px)          │
│  - First item at: ~416px             │
│                                      │
│  [Responsive content]                │
│                                      │
```

## CSS Implementation

### Desktop Rules
```css
/* Position filter bar below page header */
#timeline-view .sticky-filter-bar,
#entities-view .sticky-filter-bar,
#documents-view .sticky-filter-bar {
    top: 185px; /* Height of sticky page header */
}

/* Add extra padding to content */
#timeline-view .page-content,
#entities-view .page-content,
#documents-view .page-content {
    padding-top: 2rem; /* 32px spacing */
}
```

### Mobile Rules (≤768px)
```css
@media (max-width: 768px) {
    /* Adjust for taller header (stats stack) */
    #timeline-view .sticky-filter-bar,
    #entities-view .sticky-filter-bar,
    #documents-view .sticky-filter-bar {
        top: 280px; /* Taller due to vertical layout */
    }

    /* Reduce content padding on mobile */
    #timeline-view .page-content,
    #entities-view .page-content,
    #documents-view .page-content {
        padding-top: 1rem; /* 16px spacing */
    }
}
```

## Visual Testing Checklist

### 1. Timeline View - Desktop
```
✅ Page header visible at top
✅ Filter bar directly below header
✅ Timeline events visible without scrolling
✅ ~30px spacing between filter and content
✅ Scroll works smoothly
```

### 2. Timeline View - Mobile (390px)
```
✅ Stats stack vertically (4 rows)
✅ Filter bar below expanded header
✅ Events visible on screen
✅ No excessive white space
✅ Touch scrolling smooth
```

### 3. Entities View - Desktop
```
✅ Entity cards grid visible
✅ No cards cut off at top
✅ Search bar accessible
✅ Type filter dropdown works
```

### 4. Documents View - Desktop
```
✅ Document grid starts below filters
✅ All UI elements aligned
✅ Source/type filters visible
✅ Search input accessible
```

## Measurement Guide

### Browser DevTools Test
1. Open DevTools (F12)
2. Select element inspector
3. Click on sticky header
4. Check computed styles:
   - Position: sticky
   - Top: 0
   - Z-index: 101
   - Height: ~185px (desktop) or ~280px (mobile)

5. Click on filter bar
6. Check computed styles:
   - Position: sticky
   - Top: 185px (desktop) or 280px (mobile)
   - Z-index: 100

7. Click on page content
8. Check computed styles:
   - Padding-top: 2rem (desktop) or 1rem (mobile)

### Visual Indicators of Success
- ✅ No white space at page load
- ✅ Content starts immediately below filter bar
- ✅ Headers stay fixed during scroll
- ✅ Backdrop blur visible on headers
- ✅ Filter interactions responsive

### Visual Indicators of Problems
- ❌ Blank page on load
- ❌ Must scroll to see first item
- ❌ Headers overlap content
- ❌ Large gap between filter and content
- ❌ Content jumps during scroll

## Affected Views

### ✅ Timeline View (`#timeline-view`)
- Timeline events container
- Event cards with dates
- Filters: Type, Date Range, Search

### ✅ Entities View (`#entities-view`)
- Entity cards grid
- Filters: Search, Connection count, Type

### ✅ Documents View (`#documents-view`)
- Document grid layout
- Filters: Search, Type, Source

## Browser Compatibility

Tested on:
- ✅ Chrome 120+ (Desktop & Mobile)
- ✅ Firefox 120+ (Desktop & Mobile)
- ✅ Safari 16+ (Desktop & Mobile)
- ✅ Edge 120+ (Desktop)

Sticky positioning supported:
- ✅ All modern browsers (2023+)
- ✅ iOS Safari 13+
- ✅ Chrome Mobile 56+

## Performance Notes

- **No JavaScript changes** - Pure CSS fix
- **GPU accelerated** - Sticky positioning uses compositor
- **No layout thrashing** - Fixed calculations, no reflows
- **Smooth 60fps scrolling** - Optimized with backdrop-filter

## Scroll Behavior Visual

```
Initial State (Top of Page):
┌─────────────────────┐ ← Viewport Top
│ PAGE HEADER         │ ← Sticky (visible)
├─────────────────────┤
│ FILTER BAR          │ ← Sticky (visible)
├─────────────────────┤
│ Content Item 1      │
│ Content Item 2      │
│ Content Item 3      │
└─────────────────────┘

Scrolled Down:
┌─────────────────────┐ ← Viewport Top
│ PAGE HEADER         │ ← Sticky (stays at top)
├─────────────────────┤
│ FILTER BAR          │ ← Sticky (stays below header)
├─────────────────────┤
│ Content Item 10     │
│ Content Item 11     │
│ Content Item 12     │
└─────────────────────┘
```

## Quick Validation Commands

```javascript
// Check Timeline layout in console
const view = document.getElementById('timeline-view');
const header = view.querySelector('.sticky-page-header');
const filters = view.querySelector('.sticky-filter-bar');
console.log({
  headerHeight: header.offsetHeight,
  filterTop: getComputedStyle(filters).top,
  expected: header.offsetHeight + 'px'
});
```

## Responsive Breakpoints

| Breakpoint | Header Height | Filter Top | Content Padding |
|------------|--------------|------------|-----------------|
| Mobile (≤768px) | ~280px | 280px | 1rem |
| Tablet (769-1024px) | ~185px | 185px | 2rem |
| Desktop (>1024px) | ~185px | 185px | 2rem |

## Z-Index Stack

```
Layer 4: Main Header (z-index: auto)
Layer 3: Page Header (z-index: 101) ← Highest sticky
Layer 2: Filter Bar (z-index: 100) ← Below page header
Layer 1: Content (z-index: auto) ← Scrolls under stickies
```

## Summary

**Problem**: Double sticky headers both positioned at `top: 0` caused overlap and pushed content below viewport.

**Solution**: Position filter bar at `top: [header-height]` and add content padding.

**Result**: Content visible immediately, proper spacing, smooth scrolling, works on all devices.
