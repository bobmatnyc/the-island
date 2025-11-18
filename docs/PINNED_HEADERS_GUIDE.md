# Pinned Headers Implementation Guide

## Overview
This document explains the pinned header pattern implemented for all secondary windows and detail views in the Epstein Document Archive application.

## Design Pattern

### Concept
Pinned (sticky) headers remain visible at the top of panels while content scrolls beneath them. This provides consistent context and navigation even when viewing long lists.

### Visual Hierarchy
```
┌─────────────────────────────────────┐
│ PANEL HEADER (Always Visible)      │ ← z-index: 101
│ Entity Name                    [×]  │
├─────────────────────────────────────┤
│ STATS SECTION (Always Visible)     │ ← z-index: 100
│ Connections: 25  Documents: 12     │
├─────────────────────────────────────┤
│ SUBHEADER (Always Visible)         │ ← z-index: 99
│ Connected Entities                  │
├─────────────────────────────────────┤
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ SCROLLABLE CONTENT              │ │
│ │ • Entity 1                      │ │
│ │ • Entity 2                      │ │
│ │ • Entity 3                      │ │
│ │ • Entity 4                      │ │
│ │ ...                             │ │
│ │ (scrolls independently)         │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Clear Selection Button]            │
└─────────────────────────────────────┘
```

## Implementation

### HTML Structure

```html
<div class="panel-name" id="panel-id">
    <!-- Sticky Header Section -->
    <div class="panel-header">
        <h4 id="entity-name">Entity Name</h4>
        <button class="close-panel-btn" onclick="closePanel()">×</button>
    </div>

    <!-- Sticky Stats Section (optional) -->
    <div class="panel-stats">
        <div class="stat-item">
            <span class="stat-label">Connections:</span>
            <span class="stat-value" id="stat-value">0</span>
        </div>
        <!-- More stats... -->
    </div>

    <!-- Sticky Subheader (optional) -->
    <div class="subheader-class">
        <h5>Section Title</h5>
    </div>

    <!-- Scrollable Content Wrapper -->
    <div class="panel-scrollable-content">
        <!-- All scrollable content goes here -->
        <div class="content-list" id="content-list">
            <!-- Dynamic content -->
        </div>
        <button>Action Button</button>
    </div>
</div>
```

### CSS Requirements

```css
/* Panel Container */
.panel-name {
    display: flex;
    flex-direction: column;
    overflow: hidden;  /* Critical: prevents content overflow */
    max-height: 500px; /* Or calc(100vh - offset) */
}

/* Sticky Header */
.panel-header {
    position: sticky;
    top: 0;
    z-index: 101;
    background: var(--bg-secondary);  /* Must match panel background */
    border-bottom: 1px solid var(--border-color);
    padding: 16px;
}

/* Sticky Stats (if applicable) */
.panel-stats {
    position: sticky;
    top: 57px;  /* Height of panel-header */
    z-index: 100;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
}

/* Sticky Subheader (if applicable) */
.subheader-class {
    position: sticky;
    top: 141px;  /* Sum of previous sticky elements */
    z-index: 99;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
}

/* Scrollable Content */
.panel-scrollable-content {
    flex: 1;  /* Takes remaining space */
    overflow-y: auto;
    overflow-x: hidden;
}

/* Custom Scrollbar */
.panel-scrollable-content::-webkit-scrollbar {
    width: 6px;
}

.panel-scrollable-content::-webkit-scrollbar-thumb {
    background: var(--scrollbar-thumb);
    border-radius: 3px;
}
```

## Current Implementations

### 1. Connected Entities Panel
**Location**: Network view → Click entity node
**File**: `/server/web/index.html` (lines 4585-4621)

**Features**:
- Entity name header
- 3-column stats grid (Connections, Documents, Billionaire)
- "Connected Entities" subheader
- Scrollable connections list

**Sticky Elements**:
1. Panel header (z-index: 101)
2. Panel stats (z-index: 100)
3. Connections list header (z-index: 99)

### 2. Connection Details Panel
**Location**: Network view → Click connection edge
**File**: `/server/web/app.js` (lines 1664-1706)

**Features**:
- Connection name header
- Co-occurrence count display
- Data sources list
- Navigation buttons

**Sticky Elements**:
1. Panel header (z-index: 101)

**Dynamic Generation**:
```javascript
panel.innerHTML = `
    <div class="panel-header" style="position: sticky; top: 0; ...">
        <div>
            <h3>Connection Details</h3>
            <div>${entity1} ↔ ${entity2}</div>
        </div>
        <button class="close-panel-btn">×</button>
    </div>
    <div class="panel-scrollable-content">
        <!-- Content -->
    </div>
`;
```

## Key Principles

### 1. Container Requirements
- Must use `display: flex` with `flex-direction: column`
- Must have `overflow: hidden` to enable sticky positioning
- Must have defined height (`max-height` or `height`)

### 2. Z-Index Hierarchy
- **Header**: 101 (highest priority)
- **Stats**: 100 (medium priority)
- **Subheaders**: 99 (lower priority)
- **Content**: No z-index (natural stacking)

### 3. Background Color
- Sticky elements MUST have `background` color
- Color must match panel background
- Prevents content from showing through when scrolling

### 4. Top Position
Each sticky element's `top` value must account for elements above it:
```css
.header { top: 0; }
.stats { top: 57px; }  /* Header height */
.subheader { top: 141px; }  /* Header + Stats height */
```

## Common Pitfalls

### ❌ Wrong: Missing overflow: hidden
```css
.panel {
    display: flex;
    flex-direction: column;
    /* Missing: overflow: hidden */
}
/* Result: Sticky positioning won't work */
```

### ❌ Wrong: No background color
```css
.panel-header {
    position: sticky;
    top: 0;
    /* Missing: background color */
}
/* Result: Content shows through header when scrolling */
```

### ❌ Wrong: Incorrect top positioning
```css
.panel-stats {
    position: sticky;
    top: 0;  /* Wrong! Should be top: 57px */
}
/* Result: Stats overlap with header */
```

### ✅ Correct: Complete Implementation
```css
.panel {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    max-height: 500px;
}

.panel-header {
    position: sticky;
    top: 0;
    z-index: 101;
    background: var(--bg-secondary);
}

.panel-scrollable-content {
    flex: 1;
    overflow-y: auto;
}
```

## Testing Checklist

- [ ] Header remains visible when scrolling content
- [ ] Stats section (if present) remains visible below header
- [ ] No content shows through sticky elements
- [ ] Scrollbar appears only on content area
- [ ] Z-index hierarchy prevents overlapping
- [ ] Panel height is properly constrained
- [ ] Works on different screen sizes
- [ ] Smooth scrolling performance

## Browser Compatibility

**Sticky Positioning Support**:
- ✅ Chrome 56+
- ✅ Firefox 59+
- ✅ Safari 13+
- ✅ Edge 16+

**Fallback**: For older browsers, headers will scroll normally (graceful degradation).

## Future Extensibility

This pattern can be applied to:
- Document preview modals
- Flight details panels
- Search result panels
- Any scrollable detail view

**Template**:
1. Copy HTML structure from existing implementation
2. Adjust `.panel-header` top positions based on your layout
3. Update z-index if needed (maintain hierarchy)
4. Style content area as needed
5. Test scrolling behavior

## Related Files

**CSS Classes**: `/server/web/index.html` (lines 1257-1410)
**JavaScript Generation**: `/server/web/app.js` (lines 1664-1730)
**Reference Implementation**: Timeline page (lines 4226-4303)

## Questions?

See complete implementation in:
- `TASK_COMPLETION_SUMMARY.md` - Full documentation
- `index.html` - Live CSS and HTML
- `app.js` - Dynamic panel generation

---

**Last Updated**: 2025-11-17
**Author**: Claude Code (Engineer Agent)
