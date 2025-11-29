# Standard Page Template Documentation

**Quick Summary**: This document defines the standardized template structure for all main navigation pages in the Epstein Document Archive web application.  Following this template ensures consistency in layout, behavior, and user experience across the entire application.

**Category**: Developer
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Overview
- Design Principles
- Standard Page Structure
- HTML Template

---

## Overview

This document defines the standardized template structure for all main navigation pages in the Epstein Document Archive web application. Following this template ensures consistency in layout, behavior, and user experience across the entire application.

## Design Principles

1. **Sticky Headers**: Page title and stats remain visible during scroll
2. **Sticky Filters**: Filter/search controls stay accessible at all times
3. **Scrollable Content**: Main content area scrolls independently
4. **Consistent Spacing**: Uniform padding and margins across all pages
5. **Responsive Design**: Adapts to different screen sizes
6. **Clear Visual Hierarchy**: Title → Description → Stats → Filters → Content

## Standard Page Structure

### HTML Template

```html
<!-- Page Container -->
<div class="view" id="[page-name]-view">

  <!-- SECTION 1: Page Header (Sticky) -->
  <div class="page-header sticky-page-header">
    <!-- Page Title -->
    <h2 class="page-title">[Page Name]</h2>

    <!-- Page Description -->
    <p class="page-subtitle">[1-2 sentence description of this page's purpose]</p>

    <!-- Statistics Display -->
    <div class="page-stats">
      <div class="stat-item">
        <div class="stat-value" id="[page]-stat-1">0</div>
        <div class="stat-label">[Stat Label 1]</div>
      </div>
      <div class="stat-item">
        <div class="stat-value" id="[page]-stat-2">0</div>
        <div class="stat-label">[Stat Label 2]</div>
      </div>
      <!-- Add more stat items as needed -->
    </div>
  </div>

  <!-- SECTION 2: Filter/Search Bar (Sticky) -->
  <div class="[page]-filters sticky-filter-bar">
    <!-- Filter Controls -->
    <select id="[page]-filter-1" onchange="filter[Page]Data()">
      <option value="">All [Items]</option>
      <!-- Dynamically populated options -->
    </select>

    <!-- Search Input with Clear Button -->
    <div class="filter-input-wrapper">
      <input type="text"
             id="[page]-search-input"
             placeholder="Search [items]..."
             oninput="filter[Page]BySearch(this.value); toggleClearButton(this)">
      <button class="filter-clear-btn"
              onclick="clearFilterInput('[page]-search-input')"
              title="Clear search">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>
  </div>

  <!-- SECTION 3: Content Area (Scrollable) -->
  <div class="page-content">
    <!-- Page-specific content goes here -->
    <!-- Tables, cards, graphs, lists, etc. -->
  </div>
</div>
```

## CSS Classes

### Required Standard Classes

```css
/* Page Container */
.view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* Sticky Page Header */
.sticky-page-header {
  position: sticky;
  top: 0;
  z-index: 101;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  padding: 2rem;
  box-shadow: 0 2px 4px var(--shadow-color);
}

/* Page Title */
.page-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

/* Page Description */
.page-subtitle {
  font-size: 1rem;
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
}

/* Statistics Row */
.page-stats {
  display: flex;
  gap: 2rem;
  margin-top: 1rem;
  flex-wrap: wrap;
}

.page-stats .stat-item {
  display: flex;
  flex-direction: column;
}

.page-stats .stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--accent-blue);
}

.page-stats .stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
}

/* Sticky Filter Bar */
.sticky-filter-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
  padding: 1rem 2rem;
  box-shadow: 0 2px 4px var(--shadow-color);
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

/* Filter Input Wrapper (for search with clear button) */
.filter-input-wrapper {
  position: relative;
  min-width: 300px;
  flex: 1;
}

.filter-input-wrapper input {
  width: 100%;
  padding: 0.75rem 2.5rem 0.75rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  background: var(--input-bg);
  color: var(--text-primary);
  font-size: 14px;
}

/* Clear Button */
.filter-clear-btn {
  position: absolute;
  right: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.25rem;
  display: none;
  width: 20px;
  height: 20px;
}

.filter-clear-btn:hover {
  color: var(--text-primary);
}

.filter-input-wrapper:has(input:not(:placeholder-shown)) .filter-clear-btn {
  display: block;
}

/* Scrollable Content Area */
.page-content {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}
```

## JavaScript Functions

### Required Standard Functions

```javascript
// Toggle clear button visibility
function toggleClearButton(input) {
  const wrapper = input.closest('.filter-input-wrapper');
  if (!wrapper) return;

  const clearBtn = wrapper.querySelector('.filter-clear-btn');
  if (clearBtn) {
    clearBtn.style.display = input.value.length > 0 ? 'block' : 'none';
  }
}

// Clear filter input
function clearFilterInput(inputId) {
  const input = document.getElementById(inputId);
  if (input) {
    input.value = '';
    toggleClearButton(input);
    input.dispatchEvent(new Event('input'));
  }
}
```

## Page-Specific Implementations

### 1. Overview Page

**Purpose**: Summary dashboard of the archive
**Stats**: Total Documents, Total Entities, Total Flights, Data Sources
**Filters**: None (overview only)
**Content**: Mission statement, feature cards, latest updates

### 2. Timeline Page

**Purpose**: Chronological history of events
**Stats**: Total Events, Case Events, Life Events, Documents
**Filters**: Event Type (buttons), Date Range, Search
**Content**: Timeline events with date markers

### 3. Entities Page

**Purpose**: Browse all people, organizations, and locations
**Stats**: Total Entities, Billionaires, In Black Book, Flight Passengers
**Filters**: Search by name
**Content**: Entity cards with details

### 4. Network Page

**Purpose**: Visual relationship graph
**Stats**: Nodes, Edges, Clusters, Max Connections
**Filters**: Node type, connection strength (as overlays)
**Content**: D3.js force-directed graph

### 5. Flights Page

**Purpose**: Flight logs with map visualization
**Stats**: Total Flights, Date Range, Unique Passengers
**Filters**: Date range, passengers, airports (as overlay on map)
**Content**: Leaflet.js map with flight paths

### 6. Documents Page

**Purpose**: Search and browse all documents
**Stats**: Total Documents, Classified, OCR Complete, Sources
**Filters**: Document type, source, entity, search
**Content**: Document list/grid with pagination

## Mobile Responsiveness

### Breakpoints

```css
/* Tablet and below */
@media (max-width: 768px) {
  .sticky-filter-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-input-wrapper {
    min-width: 100%;
  }

  .page-stats {
    flex-direction: column;
    gap: 1rem;
  }

  .page-header {
    padding: 1rem;
  }

  .page-content {
    padding: 1rem;
  }
}
```

## Best Practices

### DO:
- ✅ Use semantic HTML structure
- ✅ Include aria labels for accessibility
- ✅ Maintain consistent spacing (2rem header, 1rem filters)
- ✅ Update stats dynamically with data
- ✅ Show loading states for async content
- ✅ Include empty states for no results

### DON'T:
- ❌ Mix sticky positioning with absolute positioning
- ❌ Use inline styles (except for dynamic values)
- ❌ Create custom filter bars per page (use standard)
- ❌ Forget to wire up filter/search functions
- ❌ Hardcode statistics values (load from data)

## Testing Checklist

- [ ] Header remains visible when scrolling content
- [ ] Filter bar sticks below header
- [ ] Clear button appears when typing in search
- [ ] Clear button clears input and triggers search
- [ ] Statistics update with actual data
- [ ] Page is responsive on mobile (< 768px)
- [ ] All filters trigger appropriate data updates
- [ ] Empty states display when no results
- [ ] Loading states display during data fetch

## Version History

- **v1.0** (2025-11-17): Initial standardized template
- Template based on Timeline page reference implementation
- Covers 6 main navigation pages: Overview, Timeline, Entities, Network, Flights, Documents

---

**Maintainer**: Epstein Document Archive Team
**Last Updated**: 2025-11-17
