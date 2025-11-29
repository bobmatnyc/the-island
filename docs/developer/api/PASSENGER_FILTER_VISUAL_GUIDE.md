# Passenger Filter - Visual Change Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- ❌ Multi-select confusing for users
- ❌ Wrong sizing (max-height: 100px)
- ❌ Had to scroll through all passengers
- ❌ No search capability
- ❌ Filter logic not implemented

---

## Before & After Comparison

### BEFORE: Multi-Select Dropdown (Non-Functional)
```
┌─────────────────────────────────────────────┐
│ Passengers ▼                                │
├─────────────────────────────────────────────┤
│ ☐ Bill Clinton                              │
│ ☐ Donald Trump                              │
│ ☐ Prince Andrew                             │
│ ☐ Ghislaine Maxwell                         │
│ ...                                         │
└─────────────────────────────────────────────┘
```
**Issues:**
- ❌ Multi-select confusing for users
- ❌ Wrong sizing (max-height: 100px)
- ❌ Had to scroll through all passengers
- ❌ No search capability
- ❌ Filter logic not implemented

---

### AFTER: Search Input (Fully Functional)
```
┌─────────────────────────────────────────┬───┐
│ Search passenger name...                │ ✕ │
└─────────────────────────────────────────┴───┘
```
**Improvements:**
- ✅ Clean text input with placeholder
- ✅ Properly sized (matches other filters)
- ✅ Type to search instantly
- ✅ Clear button (✕) for quick reset
- ✅ Enter key support
- ✅ Fully functional filter logic

---

## Complete Filter Bar Layout

### Flight Filters Section
```
┌────────────────────────────────────────────────────────────────────────────────┐
│  Start Date     End Date      Passengers                  Airport              │
├──────────────┬──────────────┬──────────────────────────┬──────────────┬────────┤
│ 2019-01-01   │ 2019-12-31   │ Search passenger name... │ TEB, PBI...  │ [Apply]│
│              │              │                       ✕  │           ✕  │ [Clear]│
└──────────────┴──────────────┴──────────────────────────┴──────────────┴────────┘
```

### Filter Input Consistency

All inputs now follow the same pattern:

**Date Inputs:**
```html
<input type="date" 
       id="flight-date-start" 
       style="padding: 0.5rem; border: 1px solid var(--border-color); ...">
```

**Passenger Input (NEW):**
```html
<input type="text" 
       id="flight-passenger-filter" 
       placeholder="Search passenger name..."
       style="padding: 0.5rem 28px 0.5rem 0.5rem; ...">
<button class="filter-clear-btn" onclick="clearFilterInput(...)">✕</button>
```

**Airport Input:**
```html
<input type="text" 
       id="flight-airport-filter" 
       placeholder="TEB, PBI..."
       style="padding: 0.5rem 28px 0.5rem 0.5rem; ...">
<button class="filter-clear-btn" onclick="clearFilterInput(...)">✕</button>
```

---

## User Interaction Flow

### Scenario 1: Search for Passenger
```
Step 1: Click in "Passengers" field
        ┌─────────────────────────────────┬───┐
        │ █                               │   │
        └─────────────────────────────────┴───┘

Step 2: Type "trump"
        ┌─────────────────────────────────┬───┐
        │ trump█                          │ ✕ │
        └─────────────────────────────────┴───┘

Step 3: Press Enter or Click "Apply"
        → Map shows only flights with "Trump" passengers

Step 4: Click ✕ to clear
        ┌─────────────────────────────────┬───┐
        │ Search passenger name...        │   │
        └─────────────────────────────────┴───┘
```

### Scenario 2: Filter by Entity Click
```
From Entity Detail Page:
┌────────────────────────────────┐
│ Donald Trump                   │
│                                │
│ [View Flights] ← Click here    │
└────────────────────────────────┘
        ↓
Flights Tab Opens:
┌─────────────────────────────────┬───┐
│ Donald Trump                    │ ✕ │ ← Auto-filled
└─────────────────────────────────┴───┘
        ↓
Filters Applied Automatically
```

### Scenario 3: Combined Filters
```
Date Range: 2019-07-01 to 2019-07-31
Passenger:  Clinton
Airport:    PBI

Result: Shows flights in July 2019 
        with "Clinton" passengers 
        touching PBI (Palm Beach)
```

---

## Filter Logic Visualization

### AND Logic (All Filters Must Match)
```
Flight Route:
  Date: 2019-07-06
  Passengers: ["Bill Clinton", "Ghislaine Maxwell"]
  Route: TEB → PBI

Filter Check:
  ✓ Date in range (2019-07-01 to 2019-07-31)
  ✓ Passenger matches ("Clinton" in "Bill Clinton")
  ✓ Airport matches ("PBI" in destination)
  
  → RESULT: SHOW THIS FLIGHT
```

### Substring Matching Examples
```
Search: "trump"
  ✓ Matches: "Donald Trump"
  ✓ Matches: "Ivana Trump"
  ✓ Matches: "Ivanka Trump"
  ✗ No Match: "Bill Clinton"

Search: "maxwell"
  ✓ Matches: "Ghislaine Maxwell"
  ✓ Matches: "Robert Maxwell"
  ✗ No Match: "Prince Andrew"
```

---

## Keyboard Shortcuts

| Key     | Action                      | Context           |
|---------|----------------------------|-------------------|
| Enter   | Apply filters              | Any filter input  |
| Escape  | Clear current input        | Text inputs       |
| Tab     | Navigate between filters   | All inputs        |

---

## Clear Button Behavior

### Individual Clear (✕ button)
```
Click ✕ on Passenger field:
  Before: [trump  ✕]
  After:  [Search passenger name...]
  
  → Automatically re-applies filters without passenger filter
```

### Global Clear Button
```
Click "Clear" button:
  Before: Date: [2019-01-01] to [2019-12-31]
          Passenger: [trump ✕]
          Airport: [PBI ✕]
  
  After:  Date: [         ] to [         ]
          Passenger: [Search passenger name...]
          Airport: [TEB, PBI...]
  
  → Shows all flights (no filters)
```

---

## Technical Implementation Details

### HTML Structure
```html
<div class="filter-input-wrapper" style="position: relative;">
    <label>Passengers</label>
    <input type="text" 
           id="flight-passenger-filter" 
           placeholder="Search passenger name..."
           oninput="toggleClearButton(this)">
    <button class="filter-clear-btn" 
            onclick="clearFilterInput('flight-passenger-filter')"
            style="position: absolute; right: 4px; top: 28px;">
        <svg><!-- X icon --></svg>
    </button>
</div>
```

### JavaScript Filter Logic
```javascript
// Get filter values
const passenger = document.getElementById('flight-passenger-filter')
    ?.value?.toLowerCase()?.trim();

// Apply passenger filter
if (passenger) {
    const hasMatchingPassenger = route.flights.some(flight =>
        flight.passengers.some(p => 
            p.toLowerCase().includes(passenger)
        )
    );
    if (!hasMatchingPassenger) return false;
}
```

### Enter Key Handler
```javascript
function initFlightsView() {
    const inputs = [
        'flight-passenger-filter',
        'flight-airport-filter',
        'flight-date-start',
        'flight-date-end'
    ];
    
    inputs.forEach(id => {
        document.getElementById(id)?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                applyFlightFilters();
            }
        });
    });
}
```

---

## Success Indicators

When working correctly, you should see:

1. **Input Field**: Clean text input with placeholder
   - No dropdown arrow
   - Matches size of date/airport inputs
   - Clear button appears when typing

2. **Typing**: As you type, clear button (✕) appears
   - Button positioned at right edge
   - Clicking ✕ clears field immediately

3. **Filtering**: Press Enter or click Apply
   - Map updates to show matching flights
   - Toast message shows filter count
   - Routes update on map

4. **Entity Links**: Click "View Flights" from entity detail
   - Switches to Flights tab
   - Auto-fills passenger name
   - Applies filter automatically

---

**Status**: ✅ All visual and functional requirements met
**Date**: 2025-11-17
