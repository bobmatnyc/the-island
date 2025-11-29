# Flights Page - Visual Testing Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Quick Visual Reference
- Page Layout
- Timeline View - Flight Card
- Routes View

---

## Quick Visual Reference

### Page Layout

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Flight Logs                                                    ┃
┃ Explore 1,167 flight records from Nov 17, 1995 to Sep 9, 2002┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━┓ ┏━━━━━━━━━━━┓ ┏━━━━━━━━━━━┓ ┏━━━━━━━━━━━┓
┃ ✈️  Total  ┃ ┃ 📍 Routes ┃ ┃ 👥 Pax    ┃ ┃ 🏢 Airports┃
┃   1,167   ┃ ┃    234    ┃ ┃    358    ┃ ┃     45     ┃
┗━━━━━━━━━━━┛ ┗━━━━━━━━━━━┛ ┗━━━━━━━━━━━┛ ┗━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🕐 Timeline  │  📍 Routes  │  👥 Passengers                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🔍 Search flights by passenger, location, or airport...  [🔧] ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

Showing 1,167 of 1,167 flights

[Flight Cards Below...]
```

## Timeline View - Flight Card

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                                ┃
┃  📅            📍 TEB  ─────────  ✈️  ─────────  📍 PBI       ┃
┃  Nov 17, 1995  Teterboro, NJ     │     Palm Beach, FL         ┃
┃  N908JE                                                        ┃
┃                                                                ┃
┃  ─────────────────────────────────────────────────────────────┃
┃                                                                ┃
┃  👥 Passengers (3)                                             ┃
┃     [Jeffrey Epstein] [Ghislaine Maxwell] [Sarah Kellen]     ┃
┃                                                                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## Routes View

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 📈 Most Frequent Routes                                        ┃
┃                                                                ┃
┃  1  TEB → PBI  Teterboro → Palm Beach          [142 flights] ┃
┃  2  PBI → TEB  Palm Beach → Teterboro          [128 flights] ┃
┃  3  TEB → SXM  Teterboro → St Maarten           [45 flights] ┃
┃  4  SXM → TEB  St Maarten → Teterboro           [42 flights] ┃
┃  5  PBI → SXM  Palm Beach → St Maarten          [38 flights] ┃
┃  ...                                                           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 📍 Busiest Airports                                            ┃
┃                                                                ┃
┃  1  TEB  [284 flights]    2  PBI  [268 flights]               ┃
┃  3  SXM  [123 flights]    4  CMH  [89 flights]                ┃
┃  5  JFK  [67 flights]     6  LGA  [54 flights]                ┃
┃  ...                                                           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## Passengers View

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 👥 Most Frequent Passengers                                    ┃
┃                                                                ┃
┃  1  Jeffrey Epstein                            [1,001 flights]┃
┃  2  Ghislaine Maxwell                            [520 flights]┃
┃  3  Sarah Kellen                                 [312 flights]┃
┃  4  Nadia Marcinkova                             [198 flights]┃
┃  5  Bill Clinton                                  [26 flights]┃
┃  6  Prince Andrew                                 [11 flights]┃
┃  ...                                                           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ✈️ Aircraft Usage                                              ┃
┃                                                                ┃
┃  N908JE  [543 flights]          N212JE  [387 flights]         ┃
┃  N120JE  [178 flights]          N928JE   [59 flights]         ┃
┃  ...                                                           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## Filter Panel (Expanded)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Filter Flights                                                 ┃
┃                                                                ┃
┃  Passenger Name        Start Date        End Date             ┃
┃  [Enter name...]       [📅 1995-11-17]   [📅 2002-09-09]      ┃
┃                                                                ┃
┃  [Apply Filters]  [Clear All]                                 ┃
┃                                                                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## Component Hierarchy

```
<Flights>
  ├─ <Header>
  │   ├─ Title: "Flight Logs"
  │   └─ Subtitle: "Explore X flight records from DATE to DATE"
  │
  ├─ <StatisticsCards>
  │   ├─ Total Flights
  │   ├─ Unique Routes
  │   ├─ Unique Passengers
  │   └─ Airports
  │
  ├─ <ViewModeTabs>
  │   ├─ Timeline (default)
  │   ├─ Routes
  │   └─ Passengers
  │
  ├─ <Filters>
  │   ├─ Quick Search Input
  │   ├─ Filter Toggle Button
  │   └─ Advanced Filter Panel (collapsible)
  │       ├─ Passenger Name Input
  │       ├─ Start Date Picker
  │       ├─ End Date Picker
  │       └─ Action Buttons
  │
  ├─ <ResultsCount>
  │
  └─ <ViewContent>
      ├─ if viewMode === 'timeline':
      │   └─ FlightCard[] (map over filteredFlights)
      │
      ├─ if viewMode === 'routes':
      │   ├─ Most Frequent Routes Card
      │   └─ Busiest Airports Card
      │
      └─ if viewMode === 'passengers':
          ├─ Most Frequent Passengers Card
          └─ Aircraft Usage Card
```

## Color Coding

- **Primary Action**: Blue/Violet (active tab, apply button)
- **Secondary Action**: Gray (outline buttons, inactive tabs)
- **Success**: Green (badges with flight counts)
- **Info**: Blue (airport codes, dates)
- **Muted**: Gray (secondary text, icons)

## Responsive Breakpoints

### Mobile (< 768px)
- Statistics cards: 1 column
- Flight card: Stacked layout
- Filter inputs: 1 column

### Tablet (768px - 1024px)
- Statistics cards: 2 columns
- Flight card: Horizontal layout
- Filter inputs: 2 columns

### Desktop (> 1024px)
- Statistics cards: 4 columns
- Flight card: Full horizontal layout
- Filter inputs: 3 columns

## Key Interactions

1. **Tab Switching**: Click tab → content smoothly changes
2. **Search**: Type in search box → instant client-side filter
3. **Filter Toggle**: Click filter button → panel expands/collapses
4. **Apply Filters**: Click apply → loading state → new data loads
5. **Clear Filters**: Click clear → reset all inputs → reload full dataset
6. **Flight Card Hover**: Subtle shadow elevation

## Expected Behavior

### On Initial Load
1. Show loading spinner
2. Fetch flights and routes in parallel
3. Display statistics cards
4. Default to Timeline view
5. Show all flights (no filters)

### Search Interaction
1. User types in search box
2. Instant filter (no API call)
3. Results count updates
4. Flight cards filter in real-time

### Filter Interaction
1. User clicks "Filters" button
2. Panel expands with inputs
3. User fills in passenger/dates
4. Click "Apply Filters"
5. Show loading state
6. API call with parameters
7. Update flights and stats
8. Update results count

### View Switching
1. User clicks "Routes" tab
2. Tab becomes active (blue border)
3. Content area switches to routes view
4. No API call (uses cached data)

---

**Note**: All actual flight data, passenger names, and statistics shown are from the real Epstein flight logs dataset.
