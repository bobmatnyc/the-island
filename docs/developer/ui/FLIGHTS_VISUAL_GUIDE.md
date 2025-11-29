# Flights Page - Visual Design Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Layout Overview
- Component Breakdown
- 1. Filter Bar (Top Overlay)

---

## Layout Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ MAIN HEADER (60px)                                              │
│ [Logo] [Search] [Tabs: Documents | Network | Flights | ...]    │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│ FILTER BAR (60px) - Semi-transparent overlay                    │
│ [Start Date] | [End Date] | [Passengers ▼] | [Airport] [Apply] │
└─────────────────────────────────────────────────────────────────┘
│                                                                 │
│                   🗺️  FULLSCREEN MAP BACKGROUND                 │
│                                                                 │
│       🛩️  ← Curved flight path with plane icon                 │
│                                                                 │
│   📍TEB ───────────╮                                           │
│              ✈️    ╰─────→ 📍PBI                               │
│                                                                 │
│                                                                 │
│                                           ┌──────────────────┐ │
│                                           │ STATS PANEL      │ │
│                                           │ ▼ Minimize       │ │
│                                           ├──────────────────┤ │
│                                           │ Total: 1,167     │ │
│                                           │ Range: All Time  │ │
│                                           │ Passengers: 387  │ │
│                                           └──────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
       [Zoom Controls]
       [ + ]
       [ - ]
```

## Component Breakdown

### 1. Filter Bar (Top Overlay)

**Desktop View**:
```
┌────────────────────────────────────────────────────────────────────────┐
│  START DATE        │  END DATE         │  PASSENGERS      │  AIRPORT   │
│  [2005-01-01] | [2010-12-31] | [All Passengers ▼] | [TEB, PBI] │ [Apply] │
└────────────────────────────────────────────────────────────────────────┘
```

**Mobile View** (<768px):
```
┌──────────────────────┐
│ START DATE           │
│ [2005-01-01]         │
├──────────────────────┤
│ END DATE             │
│ [2010-12-31]         │
├──────────────────────┤
│ PASSENGERS           │
│ [All Passengers ▼]   │
├──────────────────────┤
│ AIRPORT              │
│ [TEB, PBI...]        │
├──────────────────────┤
│ [Apply]  [Clear]     │
└──────────────────────┘
```

### 2. Flight Path Visualization

**Route Components**:
```
Origin Airport (📍)
       │
       │ Curved path (━━━)
       │     ✈️ Plane icon (rotated)
       │
       ▼
Destination Airport (📍)
```

**Path Thickness** (based on frequency):
```
1-4 flights:   ━━━━━━  (2px)
5-9 flights:   ━━━━━━  (3px, medium)
10+ flights:   ━━━━━━  (4px, thick)
```

**Hover States**:
```
Default:   ━━━━━━━━━  (opacity: 0.6)
Hover:     ━━━━━━━━━  (opacity: 0.9, weight +1)
```

### 3. Passenger Popup Modal

**Layout**:
```
┌─────────────────────────────────────┐
│ TEB → PBI                        ✕ │ ← Header
├─────────────────────────────────────┤
│ 📅 2005-03-01                       │ ← Flight Info
│ 🛫 Teterboro (TEB)                  │
│ 🛬 Palm Beach (PBI)                 │
├─────────────────────────────────────┤
│ PASSENGERS                          │ ← Passenger List
│ ┌─────────────────────────────────┐ │
│ │ Jeffrey Epstein              → │ │
│ ├─────────────────────────────────┤ │
│ │ Ghislaine Maxwell            → │ │
│ ├─────────────────────────────────┤ │
│ │ Sarah Kellen                 → │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**Passenger Link Hover**:
```
Default:  │ Jeffrey Epstein              → │
Hover:    │ ➜ Jeffrey Epstein              → │  (slides right 4px)
```

### 4. Statistics Panel

**Expanded State**:
```
┌────────────────────────┐
│ FLIGHT STATISTICS   ⌄  │ ← Collapsible header
├────────────────────────┤
│ Total Flights:    1167 │
├────────────────────────┤
│ Date Range: All Time   │
├────────────────────────┤
│ Unique Pass.:      387 │
└────────────────────────┘
```

**Minimized State**:
```
┌────────────────────────┐
│ FLIGHT STATISTICS   ⌃  │ ← Chevron rotated
└────────────────────────┘
```

### 5. Airport Markers

**Design**:
```
┌─────┐
│ TEB │ ← Airport code, white text on accent blue
└─────┘
  📍   ← Positioned at coordinates
```

**With Popup**:
```
┌──────────────┐
│ Teterboro    │ ← Full name
│ TEB          │ ← Code
└──────────────┘
     │
┌─────┐
│ TEB │
└─────┘
```

### 6. Plane Icon Markers

**Rotation Examples**:
```
West to East:  ✈️  (rotate 90°)
East to West:  ✈️  (rotate 270°)
North to South: ✈️  (rotate 180°)
South to North: ✈️  (rotate 0°)
NE to SW:      ✈️  (rotate 225°)
```

**Hover Effect**:
```
Default:  ✈️  (scale: 1.0, color: #58a6ff)
Hover:    ✈️  (scale: 1.3, color: brighter blue)
```

## Color Palette

### Primary Colors
```css
--accent-color: #58a6ff       /* Flight paths, icons */
--accent-hover: #79b8ff       /* Hover state */
--bg-primary: #0d1117         /* Dark background */
--bg-secondary: #161b22       /* Overlay backgrounds */
--border-color: #30363d       /* Subtle borders */
--text-primary: #c9d1d9       /* High contrast text */
--text-secondary: #8b949e     /* Labels, secondary text */
```

### Overlay Transparency
```css
Filter Bar:     rgba(13, 17, 23, 0.9)  + blur(10px)
Stats Panel:    rgba(22, 27, 34, 0.95) + blur(20px)
Popup Modal:    rgba(22, 27, 34, 0.98) + blur(20px)
Popup Overlay:  rgba(0, 0, 0, 0.6)     + blur(4px)
```

## Typography Scale

```
Filter Labels:     11px, 600 weight, uppercase, 0.5px spacing
Filter Inputs:     13px, 400 weight
Popup Title:       16px, 700 weight
Popup Info:        14px, 400 weight
Stats Header:      13px, 700 weight, uppercase
Stats Values:      16px, 700 weight
Passenger Links:   14px, 500 weight
```

## Spacing System

```
Filter Bar:
  - Height: 60px
  - Padding: 0 20px
  - Gap between items: 12px

Stats Panel:
  - Padding: 14px 16px (header), 12px 16px (content)
  - Gap between stats: 10px
  - Margins: 20px (bottom, right)

Popup Modal:
  - Header padding: 18px 20px
  - Content padding: 20px
  - Gap between info items: 12px
  - Max passenger list height: 240px
```

## Animation Timings

```css
Popup Modal:
  - Open/Close: 300ms cubic-bezier(0.4, 0, 0.2, 1)
  - Transform: translate + scale
  - Opacity: 0 → 1

Filter Bar:
  - None (static overlay)

Stats Panel:
  - Collapse: 300ms ease
  - Chevron rotation: 300ms ease

Hover Effects:
  - All transitions: 200ms ease
  - Plane icon scale: 300ms ease
```

## Responsive Breakpoints

### Desktop (>1024px)
- Filter bar: Full horizontal layout
- Stats panel: Fixed bottom-right
- Popup: 450px max-width

### Tablet (768px - 1024px)
- Filter bar: Compressed gaps
- Stats panel: Slightly smaller
- Popup: 400px max-width

### Mobile (<768px)
- Filter bar: Vertical stack, full width
- Stats panel: Full width at bottom
- Popup: 90% viewport width

## Interaction States

### Flight Path
```
Default → Hover → Click
━━━━━━   ━━━━━━   [POPUP]
0.6      0.9
2px      3px
```

### Plane Icon
```
Default → Hover → Click
  ✈️      ✈️      [POPUP]
scale:1  scale:1.3
```

### Passenger Link
```
Default → Hover → Click
Jeffrey  ➜Jeffrey [NETWORK VIEW]
x:0      x:4px
```

### Filter Button
```
Apply → Hover → Active
[APPLY]  [APPLY]  [APPLY]
normal   lift+glow pressed
```

## Z-Index Layers

```
1   - Map background
100 - Filter bar
100 - Stats panel
100 - Airport markers
100 - Flight paths
100 - Plane markers
199 - Popup overlay (backdrop)
200 - Popup modal
```

## Accessibility Features

### Keyboard Navigation
```
Tab Order:
1. Filter: Start Date
2. Filter: End Date
3. Filter: Passengers
4. Filter: Airport
5. Filter: Apply button
6. Filter: Clear button
7-N. Passenger links (when popup open)
Last. Close popup button
```

### ARIA Labels
```html
<button aria-label="Apply flight filters">Apply</button>
<button aria-label="Clear all filters">Clear</button>
<button aria-label="Minimize statistics panel">▼</button>
<button aria-label="Close flight details">✕</button>
<i data-lucide="plane" aria-hidden="true"></i>
```

### Focus States
```css
All interactive elements:
  outline: 2px solid var(--accent-color)
  outline-offset: 2px
```

## Loading States

### Initial Load
```
┌─────────────────────────────┐
│ FILTER BAR (visible)        │
└─────────────────────────────┘
│                             │
│   🗺️  Loading map tiles...  │
│                             │
│   [Spinner animation]       │
│                             │
└─────────────────────────────┘
```

### Route Loading
```
Map loaded → Fetch routes → Draw paths → Add markers
    ↓             ↓             ↓            ↓
  200ms         300ms         500ms       600ms
```

## Error States

### No Routes Found
```
┌─────────────────────────────┐
│ 🗺️  Map (empty)              │
│                             │
│  ℹ️  No flights match        │
│     your filters            │
│                             │
│  [Clear Filters]            │
└─────────────────────────────┘
```

### API Error
```
┌─────────────────────────────┐
│ ⚠️  Error Loading Flights   │
│                             │
│  Failed to fetch flight     │
│  data. Please try again.    │
│                             │
│  [Retry]                    │
└─────────────────────────────┘
```

---

## Implementation Checklist

- [x] Fullscreen map layout
- [x] Horizontal filter bar
- [x] Geodesic curved paths
- [x] Rotated plane icons
- [x] Passenger popup modal
- [x] Collapsible stats panel
- [x] Airport markers
- [x] Responsive design
- [x] Dark theme styling
- [x] Hover animations
- [ ] Keyboard navigation
- [ ] Screen reader support
- [ ] Loading states
- [ ] Error handling
- [ ] API integration
- [ ] Performance optimization

---

**Last Updated**: 2025-11-17
**Design System**: GitHub Dark Theme
**Framework**: Leaflet.js + Leaflet.curve
