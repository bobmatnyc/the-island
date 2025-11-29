# Homepage Visual Guide - Expected Layout

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Grid**: 3 columns
- **Card Width**: ~33% of container width (minus gaps)
- **Card Height**: 160px minimum (all cards equal)
- **Gap**: 24px (gap-6)
- **Padding**: 24px inside each card (p-6)

---

## Navigation Bar (Top)
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Epstein Archive                                                             │
│                                                                              │
│    Home  Timeline  News  Entities  Flights  Documents  Visualizations ▼     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Hero Section
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  The Epstein Archive                                                         │
│  A comprehensive digital archive documenting Jeffrey Epstein's network       │
│  through public records                                                      │
│                                                                              │
│  [1,234 Entities] [567 Flight Logs] [890 Documents] [456 Network Nodes]     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Dashboard Cards Section (Main Focus)
```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │ 🕐 Timeline         │  │ 📰 News             │  │ 👥 Entities         │ │
│  │                     │  │                     │  │                     │ │
│  │      5,678          │  │      7,890          │  │      9,012          │ │
│  │                     │  │                     │  │                     │ │
│  │ Explore chrono-     │  │ Search and browse   │  │ View people and     │ │
│  │ logical events,     │  │ news articles       │  │ organizations in    │ │
│  │ flights, and news   │  │ about the case      │  │ the network         │ │
│  │ coverage            │  │                     │  │                     │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘ │
│                                                                               │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │ ✈️  Flights         │  │ 📄 Documents        │  │ 🌐 Visualizations   │ │
│  │                     │  │                     │  │                     │ │
│  │      3,456          │  │      1,234          │  │      2,345          │ │
│  │                     │  │                     │  │                     │ │
│  │ Analyze flight logs │  │ Access court        │  │ Interactive charts  │ │
│  │ and passenger       │  │ documents and legal │  │ and network graphs  │ │
│  │ manifests           │  │ filings             │  │                     │ │
│  │                     │  │                     │  │                     │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘ │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Expected Card Dimensions

### Desktop (≥ 1024px)
- **Grid**: 3 columns
- **Card Width**: ~33% of container width (minus gaps)
- **Card Height**: 160px minimum (all cards equal)
- **Gap**: 24px (gap-6)
- **Padding**: 24px inside each card (p-6)

### Tablet (768px - 1023px)
- **Grid**: 2 columns
- **Card Width**: ~50% of container width (minus gaps)
- **Card Height**: 160px minimum (all cards equal)
- **Gap**: 24px (gap-6)
- **Padding**: 24px inside each card (p-6)

### Mobile (< 768px)
- **Grid**: 1 column
- **Card Width**: Full width (minus container padding)
- **Card Height**: 160px minimum (all cards equal)
- **Gap**: 24px (gap-6)
- **Padding**: 24px inside each card (p-6)

## Card Content Layout (Vertical Distribution)

```
┌─────────────────────────────┐
│ Icon Label  ← Top           │  ← flex-start
│                             │
│        Count  ← Middle      │  ← flex space-between
│                             │
│ Description  ← Bottom       │  ← flex-end
└─────────────────────────────┘
```

### Spacing Details
- Icon size: 24x24px (h-6 w-6)
- Icon-Label gap: 12px (gap-3)
- Label font: text-sm (14px)
- Count font: text-3xl (30px), font-bold
- Description font: text-xs (12px), text-muted-foreground
- Vertical gap between sections: 12px (gap-3)

## Visual Verification Checklist

When viewing the homepage, verify:

### Navigation
- [ ] Navigation order: Home, Timeline, News, Entities, Flights, Documents, Visualizations
- [ ] No "Search" link visible
- [ ] Visualizations has dropdown arrow
- [ ] All links have hover effect (text color changes)

### Cards Layout
- [ ] 6 cards total
- [ ] Cards displayed in 3 columns on desktop
- [ ] All cards have exactly the same height
- [ ] Equal spacing between all cards
- [ ] Cards arranged in 2 rows of 3

### Card Order (Left to Right, Top to Bottom)
- [ ] Row 1, Col 1: Timeline (🕐)
- [ ] Row 1, Col 2: News (📰)
- [ ] Row 1, Col 3: Entities (👥)
- [ ] Row 2, Col 1: Flights (✈️)
- [ ] Row 2, Col 2: Documents (📄)
- [ ] Row 2, Col 3: Visualizations (🌐)

### Card Content
Each card should have:
- [ ] Icon in correct color (Timeline: green, News: red, Entities: purple, Flights: orange, Documents: blue, Visualizations: cyan)
- [ ] Label text next to icon
- [ ] Large number in center
- [ ] Description text at bottom
- [ ] Description is complete and not truncated

### Card Descriptions (Exact Text)
- [ ] Timeline: "Explore chronological events, flights, and news coverage"
- [ ] News: "Search and browse news articles about the case"
- [ ] Entities: "View people and organizations in the network"
- [ ] Flights: "Analyze flight logs and passenger manifests"
- [ ] Documents: "Access court documents and legal filings"
- [ ] Visualizations: "Interactive charts and network graphs"

### Hover Effects
- [ ] Card scales up slightly on hover (scale-[1.02])
- [ ] Card gets shadow on hover (hover:shadow-lg)
- [ ] Transition is smooth (duration-200)
- [ ] Cursor changes to pointer

### Responsive Behavior
Test at these widths:
- [ ] 375px (mobile): Cards in 1 column, 6 rows
- [ ] 768px (tablet): Cards in 2 columns, 3 rows
- [ ] 1024px (desktop): Cards in 3 columns, 2 rows
- [ ] 1440px (large desktop): Cards in 3 columns, 2 rows

### Accessibility
- [ ] Each card has proper aria-label
- [ ] Cards are keyboard navigable (Tab key)
- [ ] Focus indicators visible when tabbing
- [ ] Links are properly structured

### Dark Mode
- [ ] Cards visible in dark mode
- [ ] Text readable in dark mode
- [ ] Icons have proper dark mode colors
- [ ] Hover effects work in dark mode

## Color Scheme Reference

### Card Icon Colors
- **Timeline**: `text-green-600 dark:text-green-400`
- **News**: `text-red-600 dark:text-red-400`
- **Entities**: `text-purple-600 dark:text-purple-400`
- **Flights**: `text-orange-600 dark:text-orange-400`
- **Documents**: `text-blue-600 dark:text-blue-400`
- **Visualizations**: `text-cyan-600 dark:text-cyan-400`

### Text Colors
- **Card Label**: `text-muted-foreground` (gray)
- **Card Count**: Default foreground (high contrast)
- **Card Description**: `text-muted-foreground` (gray, lighter than label)

### Background Colors
- **Card Background**: `bg-card` (theme-aware)
- **Card Border**: `border` (theme-aware)
- **Hover Shadow**: `hover:shadow-lg`

## Screenshot Comparison Points

When taking screenshots for verification:

1. **Full Page Screenshot**: Shows entire homepage with navigation and all cards
2. **Cards Section**: Close-up of just the 6 cards
3. **Single Card**: Detail view of one card showing icon, count, and description
4. **Mobile View**: Screenshot at 375px width
5. **Tablet View**: Screenshot at 768px width
6. **Desktop View**: Screenshot at 1280px width

## Common Issues to Watch For

- ❌ Cards not aligned (different heights)
- ❌ Descriptions truncated or wrapped awkwardly
- ❌ Wrong card order (doesn't match navigation)
- ❌ Missing descriptions
- ❌ Inconsistent spacing
- ❌ Icons not colored correctly
- ❌ Hover effects not working
- ❌ Cards overflow container on mobile

## Success Criteria

The implementation is correct if:
- ✅ Navigation matches specification exactly
- ✅ All 6 cards present in correct order
- ✅ All descriptions present and complete
- ✅ All cards have equal height
- ✅ Grid responsive on all screen sizes
- ✅ No visual regressions
- ✅ Hover and focus effects working

---

**Expected Result**: Clean, organized homepage with logical navigation order and informative, equally-sized cards that guide users to different sections of the archive.
