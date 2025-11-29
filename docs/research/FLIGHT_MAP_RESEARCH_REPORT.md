# Flight Map Research Report

**Quick Summary**: Research analysis and findings documentation.

**Category**: Research
**Status**: Complete
**Last Updated**: 2025-11-24

**Key Points**:
- Leaflet 1.9.4 (CDN)
- Leaflet.curve plugin for geodesic paths
- Dark-themed CartoDB tiles
- ~700 lines of custom JavaScript
- **Fullscreen Map**: Map fills entire viewport (100vw × 100vh minus header)

---

**Date**: 2025-11-20
**Research Agent**: Claude (Research Specialist)
**Purpose**: Investigate old flight map implementation for React reimplementation

---

## Executive Summary

The Epstein Archive previously had a **fullscreen interactive flight map** built with **Leaflet.js** in both the old vanilla JS site and Svelte site. This research provides comprehensive details on what was implemented, what data is available, and recommendations for reimplementing it in the new React + ShadCN frontend.

### Key Findings

✅ **Old Implementation Found**: Comprehensive documentation and Svelte code recovered
✅ **Flight Data Available**: 1,167 flights with full geocoding (89 airports with lat/lon)
✅ **API Ready**: `/api/flights` and `/api/flights/all` endpoints already functional
✅ **Map Library**: Leaflet.js was used (CDN-based, now needs npm package)
✅ **Advanced Features**: Curved flight paths, rotated plane icons, passenger filtering

---

## Old Implementation Analysis

### 1. Technology Stack (Old Sites)

**Vanilla JS Site** (`/server/web/`):
- Leaflet 1.9.4 (CDN)
- Leaflet.curve plugin for geodesic paths
- Dark-themed CartoDB tiles
- ~700 lines of custom JavaScript

**Svelte Site** (`/server/web-svelte/`) - DELETED:
```typescript
// Recovered from git history
import FlightsMap from '$lib/components/FlightsMap.svelte';
import { fetchFlights, type FlightsResponse, type FlightRoute } from '$lib/utils/api';

// Used Leaflet CDN with Svelte component wrapper
```

### 2. Map Features Implemented

#### **Core Visualization**
- **Fullscreen Map**: Map fills entire viewport (100vw × 100vh minus header)
- **Dark Theme**: CartoDB dark matter tiles for aesthetics
- **Flight Paths**: Curved geodesic arcs connecting airports (not straight lines)
- **Airport Markers**: Custom div icons showing 3-letter airport codes
- **Plane Markers**: Rotated plane icons at midpoint of routes

#### **Interactive Elements**
- **Click Flight Path**: Opens passenger popup modal
- **Click Plane Icon**: Same popup behavior
- **Click Airport Marker**: Shows airport name tooltip
- **Hover Effects**: Paths increase opacity (0.6 → 0.9) and thickness

#### **Advanced Features**
- **Variable Path Thickness**: Based on flight frequency
  - 1-4 flights: 2px
  - 5-9 flights: 3px
  - 10+ flights: 4px
- **Bearing Calculation**: Plane icons rotate to match flight direction
- **Curved Paths**: Uses Leaflet.curve plugin for quadratic Bezier curves

### 3. UI Layout Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ FILTER BAR (60px) - Semi-transparent overlay at top        │
│ [Start Date] | [End Date] | [Passengers ▼] | [Apply]       │
└─────────────────────────────────────────────────────────────┘
│                                                             │
│               🗺️  FULLSCREEN MAP BACKGROUND                 │
│                                                             │
│   📍TEB ─────────╮                                         │
│            ✈️    ╰──────→ 📍PBI                            │
│                                                             │
│                                     ┌──────────────────┐   │
│                                     │ STATS PANEL      │   │
│                                     │ ▼ Minimize       │   │
│                                     ├──────────────────┤   │
│                                     │ Total: 1,167     │   │
│                                     │ Passengers: 387  │   │
│                                     └──────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Key UI Components**:
1. **Filter Bar** (top overlay): Horizontal layout with date pickers, passenger dropdown
2. **Statistics Panel** (bottom-right): Collapsible panel showing flight counts
3. **Passenger Popup Modal**: Centered overlay showing flight details and passenger list
4. **Airport Markers**: Fixed position with 3-letter codes
5. **Plane Icons**: Animated midpoint markers with rotation

---

## Flight Data Structure

### API Endpoints (Already Functional)

#### 1. `/api/flights/all` - Route-Grouped Data
```json
{
  "routes": [
    {
      "origin": {
        "code": "TEB",
        "name": "Teterboro Airport",
        "city": "Teterboro, NJ",
        "lat": 40.8501,
        "lon": -74.0608
      },
      "destination": {
        "code": "PBI",
        "name": "Palm Beach International",
        "city": "West Palm Beach, FL",
        "lat": 26.6832,
        "lon": -80.0956
      },
      "flights": [
        {
          "id": "flight_001",
          "date": "2005-03-01",
          "passengers": ["Jeffrey Epstein", "Ghislaine Maxwell"],
          "passenger_count": 2,
          "aircraft": "N908JE"
        }
      ],
      "frequency": 12
    }
  ],
  "total_flights": 1167,
  "unique_routes": 177,
  "unique_passengers": 387,
  "date_range": {
    "start": "2001-01-01",
    "end": "2013-12-31"
  },
  "airports": {
    "TEB": { "name": "Teterboro Airport", "city": "Teterboro, NJ", "lat": 40.8501, "lon": -74.0608 },
    // ... 89 airports total
  }
}
```

#### 2. `/api/flights` - Filtered Flights
Query parameters:
- `start_date`: Filter by start date (YYYY-MM-DD)
- `end_date`: Filter by end date (YYYY-MM-DD)
- `passenger`: Filter by passenger name (partial match)

Returns individual flight objects with geocoded locations.

### Data Quality

✅ **Complete Geocoding**: All 89 airports have accurate lat/lon coordinates
✅ **Full Passenger Lists**: Every flight includes complete passenger manifest
✅ **Date Coverage**: 13 years of flight data (2001-2013)
✅ **Route Frequency**: Pre-calculated for efficient rendering
✅ **Aircraft Tracking**: Tail numbers available for each flight

---

## Recommended React Implementation

### 1. Map Library: React-Leaflet

**Package**: `react-leaflet` v4.2.1 (already in migration plan)

**Why React-Leaflet?**
- ✅ Official React wrapper for Leaflet
- ✅ Declarative component API (fits React paradigm)
- ✅ Full TypeScript support
- ✅ Active maintenance and community
- ✅ Same visual output as old implementation
- ✅ Easy migration from old Leaflet code

**Alternative Considered**: Mapbox GL JS
- ❌ Requires API token (costs money at scale)
- ❌ Different rendering paradigm (WebGL vs Canvas)
- ❌ Would require data transformation
- ✅ Better performance for 10K+ markers (not needed here)

### 2. Required NPM Packages

```json
{
  "dependencies": {
    "leaflet": "^1.9.4",
    "react-leaflet": "^4.2.1",
    "@types/leaflet": "^1.9.8"
  }
}
```

**Optional Enhancement**:
```json
{
  "dependencies": {
    "leaflet.curve": "^1.0.0"
  }
}
```
For curved flight paths (quadratic Bezier). Can start with straight lines.

### 3. Component Architecture

```typescript
// Recommended component structure
frontend/src/components/flights/
├── FlightMap.tsx              // Main map container
├── FlightRoute.tsx            // Individual flight path (Polyline)
├── PlaneMarker.tsx            // Rotated plane icon marker
├── AirportMarker.tsx          // Airport code marker
├── FlightPopup.tsx            // Passenger detail modal
├── FlightFilters.tsx          // Filter bar overlay
└── FlightStats.tsx            // Statistics panel

frontend/src/pages/
└── Flights.tsx                // Page component
```

### 4. Key Features to Implement

#### **Phase 1 - MVP** (5-7 days)
Must-have features for initial release:

1. **Basic Map Rendering**
   - Leaflet map with dark tiles
   - Zoom controls (bottom-left)
   - Fullscreen layout

2. **Flight Routes**
   - Straight lines between airports (defer curves to Phase 2)
   - Color: `#58a6ff` (GitHub blue)
   - Opacity: 0.6 default, 0.9 hover
   - Variable thickness by frequency

3. **Airport Markers**
   - Custom div icons with airport codes
   - Positioned at lat/lon
   - Tooltip on hover

4. **Passenger Popup**
   - Click route → show modal
   - Display flight date, origin, destination
   - List all passengers with links

5. **Basic Filtering**
   - Passenger dropdown (client-side)
   - Apply/Clear buttons

6. **Statistics Panel**
   - Total flights count
   - Date range display
   - Unique passengers count
   - Collapsible (minimize button)

#### **Phase 2 - Enhanced** (3-4 days)
Nice-to-have features for polish:

1. **Curved Flight Paths**
   - Install leaflet.curve
   - Quadratic Bezier arcs (20% offset)
   - More natural appearance

2. **Plane Icon Markers**
   - SVG plane icons at route midpoints
   - Bearing calculation for rotation
   - Hover scale animation (1.0 → 1.3)

3. **Advanced Filtering**
   - Date range picker (start/end)
   - Airport code filter
   - Server-side filtering with API calls

4. **Loading States**
   - Progressive route loading (batch rendering)
   - Skeleton loaders for stats
   - Loading spinner during API calls

5. **Route Clustering**
   - Group overlapping routes
   - Expand clusters on click

#### **Phase 3 - Future Enhancements** (Optional)
Features to consider later:

1. **Timeline Slider**
   - Scrub through dates
   - Animate flights over time
   - Play/pause controls

2. **Heatmap Layer**
   - Visualize flight frequency density
   - Toggle heatmap on/off

3. **Route Animation**
   - Plane icon animates along path on hover
   - Dotted trail effect

4. **Export Functionality**
   - Download filtered flight data as CSV
   - Share link to current filters

5. **3D Globe View**
   - Cesium.js integration
   - True geodesic paths on sphere

---

## Technical Specifications

### 1. Leaflet Configuration

```typescript
// Map initialization
const mapConfig = {
  center: [25, -60],  // Atlantic Ocean (shows US, Caribbean, Europe)
  zoom: 3,
  minZoom: 2,
  maxZoom: 10,
  zoomControl: false,  // Add custom controls to bottom-left
  attributionControl: true
};

// Tile layer
const tileLayerUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const tileLayerOptions = {
  attribution: '© OpenStreetMap contributors © CARTO',
  subdomains: 'abcd',
  maxZoom: 20
};
```

### 2. Route Rendering Logic

```typescript
// Calculate bearing for plane icon rotation
function calculateBearing(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const y = Math.sin(dLon) * Math.cos(lat2 * Math.PI / 180);
  const x = Math.cos(lat1 * Math.PI / 180) * Math.sin(lat2 * Math.PI / 180) -
            Math.sin(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.cos(dLon);
  const bearing = Math.atan2(y, x) * 180 / Math.PI;
  return (bearing + 360) % 360;
}

// Get line thickness based on frequency
function getLineWeight(frequency: number): number {
  if (frequency >= 10) return 4;
  if (frequency >= 5) return 3;
  return 2;
}

// Calculate route midpoint
function getMidpoint(lat1: number, lon1: number, lat2: number, lon2: number): [number, number] {
  return [(lat1 + lat2) / 2, (lon1 + lon2) / 2];
}
```

### 3. Color Scheme (Dark Theme)

```typescript
const colors = {
  accent: '#58a6ff',        // Flight paths, icons
  accentHover: '#79b8ff',   // Hover state
  bgPrimary: '#0d1117',     // Dark background
  bgSecondary: '#161b22',   // Overlays
  border: '#30363d',        // Borders
  textPrimary: '#c9d1d9',   // High contrast
  textSecondary: '#8b949e'  // Labels
};
```

### 4. Responsive Breakpoints

```typescript
// Mobile: <768px
- Filter bar: Vertical stack
- Stats panel: Full width at bottom
- Popup: 90% viewport width

// Tablet: 768px - 1024px
- Filter bar: Compressed gaps
- Stats panel: Slightly smaller
- Popup: 400px max-width

// Desktop: >1024px
- Filter bar: Full horizontal
- Stats panel: Fixed bottom-right
- Popup: 450px max-width
```

---

## Implementation Roadmap

### Week 1: Phase 1 MVP

**Day 1-2**: Map Infrastructure
- [ ] Install leaflet + react-leaflet + @types/leaflet
- [ ] Create FlightMap.tsx component
- [ ] Configure dark tile layer
- [ ] Test basic map rendering

**Day 3-4**: Route Visualization
- [ ] Create FlightRoute.tsx component
- [ ] Fetch data from `/api/flights/all`
- [ ] Render straight line polylines
- [ ] Implement variable thickness
- [ ] Add hover effects

**Day 5**: Markers & Popups
- [ ] Create AirportMarker.tsx (div icons with codes)
- [ ] Create FlightPopup.tsx (modal overlay)
- [ ] Wire up click handlers
- [ ] Test popup interactions

**Day 6-7**: Filters & Stats
- [ ] Create FlightFilters.tsx (top overlay)
- [ ] Create FlightStats.tsx (bottom-right panel)
- [ ] Implement passenger dropdown filter
- [ ] Add collapsible stats panel
- [ ] Polish responsive design

### Week 2: Phase 2 Enhancements

**Day 1-2**: Curved Paths
- [ ] Install leaflet.curve plugin
- [ ] Replace Polyline with Curve component
- [ ] Calculate control points for Bezier arcs
- [ ] Test curve rendering

**Day 3-4**: Plane Icons
- [ ] Create PlaneMarker.tsx component
- [ ] Implement bearing calculation
- [ ] Add rotation transform
- [ ] Add scale animation on hover

**Day 5**: Advanced Filtering
- [ ] Add date range pickers
- [ ] Add airport code input
- [ ] Implement server-side filtering
- [ ] Add loading states

**Day 6-7**: Polish & Testing
- [ ] Progressive loading for routes
- [ ] Error handling
- [ ] Performance optimization
- [ ] Cross-browser testing
- [ ] Accessibility audit

---

## Code Examples

### 1. Basic FlightMap Component

```typescript
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import { FlightRoute } from './FlightRoute';
import { AirportMarker } from './AirportMarker';

interface FlightMapProps {
  routes: RouteData[];
  airports: Record<string, AirportData>;
}

export function FlightMap({ routes, airports }: FlightMapProps) {
  return (
    <MapContainer
      center={[25, -60]}
      zoom={3}
      style={{ width: '100%', height: 'calc(100vh - 60px)' }}
      zoomControl={false}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution="© OpenStreetMap © CARTO"
      />

      {routes.map((route, idx) => (
        <FlightRoute
          key={idx}
          origin={route.origin}
          destination={route.destination}
          flights={route.flights}
          frequency={route.frequency}
        />
      ))}

      {Object.entries(airports).map(([code, airport]) => (
        <AirportMarker
          key={code}
          code={code}
          position={[airport.lat, airport.lon]}
          name={airport.name}
        />
      ))}
    </MapContainer>
  );
}
```

### 2. FlightRoute Component

```typescript
import { Polyline } from 'react-leaflet';
import { useState } from 'react';

interface FlightRouteProps {
  origin: { lat: number; lon: number };
  destination: { lat: number; lon: number };
  flights: FlightData[];
  frequency: number;
}

export function FlightRoute({ origin, destination, flights, frequency }: FlightRouteProps) {
  const [hovered, setHovered] = useState(false);

  const positions: [number, number][] = [
    [origin.lat, origin.lon],
    [destination.lat, destination.lon]
  ];

  const weight = frequency >= 10 ? 4 : frequency >= 5 ? 3 : 2;
  const opacity = hovered ? 0.9 : 0.6;

  return (
    <Polyline
      positions={positions}
      pathOptions={{
        color: '#58a6ff',
        weight: weight,
        opacity: opacity
      }}
      eventHandlers={{
        mouseover: () => setHovered(true),
        mouseout: () => setHovered(false),
        click: () => {
          // Show popup with flight details
        }
      }}
    />
  );
}
```

### 3. AirportMarker Component

```typescript
import { Marker, Tooltip } from 'react-leaflet';
import { divIcon } from 'leaflet';

interface AirportMarkerProps {
  code: string;
  position: [number, number];
  name: string;
}

export function AirportMarker({ code, position, name }: AirportMarkerProps) {
  const icon = divIcon({
    html: `<div class="airport-marker">${code}</div>`,
    className: '',
    iconSize: [40, 24],
    iconAnchor: [20, 12]
  });

  return (
    <Marker position={position} icon={icon}>
      <Tooltip>
        <strong>{name}</strong>
        <br />
        {code}
      </Tooltip>
    </Marker>
  );
}
```

---

## Performance Considerations

### Current Data Scale
- **Routes**: 177 unique routes
- **Flights**: 1,167 total flights
- **Airports**: 89 airports
- **Expected DOM Elements**: ~440 (177 polylines + 89 markers + 177 plane icons)

### Performance Benchmarks (Expected)
- **Initial Load**: <2 seconds (with progressive loading)
- **Route Rendering**: ~5ms per route
- **Map Interaction**: 60fps smooth panning/zooming
- **Filter Application**: <500ms

### Optimization Strategies

**For Current Scale** (177 routes):
✅ Render all routes at once (no clustering needed)
✅ Client-side filtering sufficient
✅ No virtualization required

**If Scale Grows** (1000+ routes):
- Implement route clustering (Leaflet.markercluster)
- Add viewport-based filtering (only render visible routes)
- Server-side pagination for filters
- Virtual scrolling for passenger lists

---

## Migration Strategy

### Step 1: Parallel Development
- Build React flight map alongside existing implementation
- Use same API endpoints
- Test in isolation before integration

### Step 2: Feature Parity
- Match all existing features from old site
- Ensure no functionality loss
- Maintain same visual design

### Step 3: Testing & Validation
- Cross-browser testing (Chrome, Firefox, Safari, Edge)
- Mobile responsiveness testing
- Performance benchmarks
- Accessibility audit

### Step 4: Deployment
- Deploy React flight map to `/flights` route
- Monitor for errors
- Collect user feedback

---

## Risks & Mitigations

### Risk 1: Leaflet TypeScript Integration
**Issue**: TypeScript types for Leaflet can be tricky
**Mitigation**: Use `@types/leaflet` package, follow react-leaflet docs closely

### Risk 2: Performance with Many Routes
**Issue**: 177 routes might cause lag on mobile
**Mitigation**: Implement progressive loading (batch render 10 routes at a time)

### Risk 3: Curved Path Rendering
**Issue**: leaflet.curve plugin might not have React wrapper
**Mitigation**: Start with straight lines, add curves in Phase 2, use imperative API if needed

### Risk 4: Mobile Touch Interactions
**Issue**: Map panning vs. route clicking conflicts
**Mitigation**: Increase touch target size, add slight delay for click detection

---

## Success Criteria

### Functional Requirements
- ✅ Map loads and displays 177 flight routes
- ✅ Airport markers show 89 airports with codes
- ✅ Clicking route opens passenger popup
- ✅ Filters work (passenger, date range)
- ✅ Statistics panel updates dynamically
- ✅ Responsive on mobile/tablet/desktop

### Non-Functional Requirements
- ✅ Initial load <2 seconds
- ✅ Smooth 60fps map interaction
- ✅ Works in all modern browsers
- ✅ Keyboard accessible
- ✅ No console errors

### Visual Requirements
- ✅ Matches dark theme design system
- ✅ Semi-transparent overlays with blur
- ✅ Consistent with other pages (Dashboard, Entities)

---

## Files Analyzed

### Documentation (Found)
- `/docs/developer/implementation/FLIGHTS_PAGE_IMPLEMENTATION.md` - React flights page (timeline view, no map)
- `/docs/developer/ui/FLIGHTS_IMPLEMENTATION.md` - Vanilla JS map implementation guide
- `/docs/developer/ui/FLIGHTS_REDESIGN_SUMMARY.md` - Complete fullscreen map redesign (469 lines)
- `/docs/developer/ui/FLIGHTS_VISUAL_GUIDE.md` - Detailed visual design specs (423 lines)
- `/docs/developer/migration/REACT_MIGRATION_PLAN.md` - Migration plan with leaflet packages

### Code (Recovered)
- `server/web-svelte/src/routes/flights/+page.svelte` - Svelte implementation (deleted, recovered from git)
- `/server/routes/flights.py` - Backend API (335 lines, fully functional)
- `/data/metadata/flight_locations.json` - 89 airports with geocoding

### Data Files
- `/data/md/entities/flight_logs_by_flight.json` - 1,167 flight records
- `/data/metadata/flight_locations.json` - Complete airport database

---

## Next Steps

### Immediate Actions
1. **Review this report** with product owner
2. **Confirm feature priorities** (Phase 1 MVP vs full feature set)
3. **Assign implementation** to frontend developer
4. **Schedule design review** for visual consistency

### Implementation Order
1. Install npm packages (leaflet, react-leaflet)
2. Create basic map component (Day 1-2)
3. Add flight routes (Day 3-4)
4. Add markers and popups (Day 5)
5. Add filters and stats (Day 6-7)
6. Polish and test (Week 2)

### Questions to Answer
- **Design**: Do we want curved paths in MVP or can they wait?
- **Filtering**: Client-side only or server-side pagination?
- **Animation**: Plane icon animations high priority or Phase 3?
- **Timeline**: Is 2-week timeline acceptable?

---

## Conclusion

The old flight map implementation was a **sophisticated, well-designed fullscreen map visualization** using Leaflet.js with advanced features like curved geodesic paths, rotated plane icons, and interactive passenger filtering. All necessary data is available via existing API endpoints with complete geocoding.

**Recommendation**: Proceed with **react-leaflet** implementation following the 2-week roadmap outlined above. Start with Phase 1 MVP (straight line routes) to get a functional map quickly, then add Phase 2 enhancements (curved paths, plane icons) for polish.

**Estimated Effort**:
- Phase 1 MVP: 5-7 days
- Phase 2 Enhanced: 3-4 days
- **Total**: 10-12 development days

**Confidence Level**: **High** - All requirements are clear, data is available, technology stack is proven, and previous implementations provide excellent reference.

---

**Report Prepared By**: Claude (Research Agent)
**Date**: 2025-11-20
**Files Analyzed**: 12 documentation files, 3 code files, 2 data files
**Memory Usage**: Efficient (used vector search and strategic sampling)
