# Sticky Header Fix - Quick Reference

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Desktop**: Filter bar positioned at `top: 185px` (below header)
- **Mobile**: Filter bar positioned at `top: 280px` (below taller header)
- **Content**: Added 2rem/1rem padding-top to prevent hidden content
- `server/web/index.html` (Lines 2893-2905, 4602-4613)
- ✅ Timeline View

---

## 🎯 Problem Solved
Timeline events (and Entities/Documents content) positioned below visible screen due to overlapping sticky headers.

## ✅ Solution Applied
- **Desktop**: Filter bar positioned at `top: 185px` (below header)
- **Mobile**: Filter bar positioned at `top: 280px` (below taller header)
- **Content**: Added 2rem/1rem padding-top to prevent hidden content

## 🧪 Quick Test (3 steps)
1. Open http://localhost:5002
2. Click **Timeline** tab
3. Verify: Timeline events visible without scrolling ✅

## 📏 Expected Layout

**Desktop:**
```
Page Header   (0-185px)    ← Sticky at top
Filter Bar    (185-270px)  ← Sticky below header
Content       (270px+)     ← Scrollable, starts visible
```

**Mobile:**
```
Page Header   (0-280px)    ← Sticky at top (taller)
Filter Bar    (280-400px)  ← Sticky below header
Content       (400px+)     ← Scrollable, starts visible
```

## 🔍 Browser Console Test
```javascript
fetch('/test_sticky_headers.js').then(r=>r.text()).then(eval);
```

## 📂 Files Modified
- `server/web/index.html` (Lines 2893-2905, 4602-4613)

## 🎨 Affected Views
- ✅ Timeline View
- ✅ Entities View
- ✅ Documents View

## ✅ Success Criteria
- [x] Content visible on page load (no scroll needed)
- [x] Filter bar below header (no overlap)
- [x] Sticky headers work during scroll
- [x] Responsive (mobile + desktop)
- [x] All filters functional

## 📱 Mobile Test
1. Open DevTools (F12)
2. Switch to mobile (iPhone 12: 390px)
3. Verify stats stack vertically
4. Verify content visible immediately

## 🐛 Rollback (if needed)
Remove lines 2893-2905 and 4602-4613 from `server/web/index.html`

## 📚 Full Documentation
- `STICKY_HEADER_FIX_COMPLETE.md` - Complete documentation
- `STICKY_HEADER_VISUAL_GUIDE.md` - Visual diagrams
- `test_sticky_fix.html` - Interactive test page
- `test_sticky_headers.js` - Browser validation script

---
**Status**: ✅ COMPLETE AND TESTED
**Impact**: Critical UX fix - content now immediately visible
**Risk**: Low - CSS only, no JavaScript changes
