# React + ShadCN Migration Plan

**Quick Summary**: **To**: React + ShadCN + Vite + TypeScript...

**Category**: Developer
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- 🎯 Migration Goals
- 📋 Architecture Overview
- Current Stack (Vanilla JS)

---

**Date**: 2025-11-18
**From**: Vanilla JS frontend
**To**: React + ShadCN + Vite + TypeScript
**Backend**: FastAPI (unchanged)
**Rollback Tag**: `v1.2.2-vanilla-js-stable`

---

## 🎯 Migration Goals

1. **Eliminate fragile vanilla JS**: No more global state conflicts, manual DOM manipulation
2. **Type safety**: Catch errors at build time with TypeScript
3. **Component isolation**: Each UI element encapsulated with its own state/logic
4. **Better DX**: Hot module replacement, modern dev tools
5. **Maintain all features**: No functionality loss during migration
6. **Keep FastAPI backend**: No backend changes required

---

## 📋 Architecture Overview

### Current Stack (Vanilla JS)
```
┌─────────────────────────────────────┐
│         Browser (Port 8081)         │
│  ┌───────────────────────────────┐  │
│  │   index.html                  │  │
│  │   - Inline CSS (5000+ lines)  │  │
│  │   - Includes app.js           │  │
│  │   - Includes documents.js     │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │   app.js (5300+ lines)        │  │
│  │   - Global functions          │  │
│  │   - Manual DOM updates        │  │
│  │   - Global state              │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
              ↓ HTTP
┌─────────────────────────────────────┐
│   FastAPI Backend (Port 8081)       │
│   - /api/stats                      │
│   - /api/entities                   │
│   - /api/documents                  │
│   - /api/network                    │
│   - /api/flights                    │
│   - /api/timeline                   │
└─────────────────────────────────────┘
```

### New Stack (React + ShadCN)
```
┌─────────────────────────────────────┐
│    Vite Dev Server (Port 5173)      │
│  ┌───────────────────────────────┐  │
│  │   React App                   │  │
│  │   - TypeScript                │  │
│  │   - ShadCN Components         │  │
│  │   - Tailwind CSS              │  │
│  │   - TanStack Query (API)      │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
              ↓ HTTP (CORS)
┌─────────────────────────────────────┐
│   FastAPI Backend (Port 8081)       │
│   - Same endpoints (no changes)     │
│   - Add CORS middleware             │
└─────────────────────────────────────┘
```

---

## 🗂️ New Project Structure

```
epstein/
├── server/                    # FastAPI backend (unchanged)
│   ├── app.py
│   ├── routes/
│   ├── services/
│   └── models/
│
├── frontend/                  # NEW: React frontend
│   ├── src/
│   │   ├── main.tsx          # Entry point
│   │   ├── App.tsx           # Root component
│   │   ├── components/       # React components
│   │   │   ├── ui/           # ShadCN components
│   │   │   ├── layout/       # Header, Sidebar, Layout
│   │   │   ├── entities/     # Entity-related components
│   │   │   ├── documents/    # Document-related components
│   │   │   ├── network/      # Network visualization
│   │   │   ├── timeline/     # Timeline components
│   │   │   ├── flights/      # Flight components
│   │   │   └── maps/         # Map components
│   │   ├── pages/            # Page components
│   │   │   ├── HomePage.tsx
│   │   │   ├── EntitiesPage.tsx
│   │   │   ├── DocumentsPage.tsx
│   │   │   ├── NetworkPage.tsx
│   │   │   ├── TimelinePage.tsx
│   │   │   ├── FlightsPage.tsx
│   │   │   └── MapsPage.tsx
│   │   ├── lib/              # Utilities
│   │   │   ├── api.ts        # API client
│   │   │   ├── utils.ts      # Helper functions
│   │   │   └── types.ts      # TypeScript types
│   │   ├── hooks/            # Custom React hooks
│   │   │   ├── useEntities.ts
│   │   │   ├── useDocuments.ts
│   │   │   ├── useNetwork.ts
│   │   │   └── useTimeline.ts
│   │   └── styles/           # Global styles
│   │       └── globals.css
│   ├── public/               # Static assets
│   ├── index.html            # HTML entry point
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── data/                      # Data files (unchanged)
├── scripts/                   # Python scripts (unchanged)
└── docs/                      # Documentation
```

---

## 🛠️ Tech Stack Details

### Core Dependencies
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.22.0",
    "@tanstack/react-query": "^5.28.0",
    "axios": "^1.6.7",
    "lucide-react": "^0.344.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.64",
    "@types/react-dom": "^18.2.21",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.3",
    "vite": "^5.1.5",
    "tailwindcss": "^3.4.1",
    "autoprefixer": "^10.4.18",
    "postcss": "^8.4.35"
  }
}
```

### Visualization Libraries
```json
{
  "dependencies": {
    "d3": "^7.9.0",
    "@types/d3": "^7.4.3",
    "react-flow-renderer": "^10.3.17",
    "leaflet": "^1.9.4",
    "react-leaflet": "^4.2.1",
    "@types/leaflet": "^1.9.8",
    "recharts": "^2.12.0"
  }
}
```

### ShadCN Components to Install
```bash
# Core UI components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add label
npx shadcn-ui@latest add select
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add sheet
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add avatar
npx shadcn-ui@latest add separator
npx shadcn-ui@latest add skeleton
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add tooltip
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add command
npx shadcn-ui@latest add popover
npx shadcn-ui@latest add scroll-area
npx shadcn-ui@latest add checkbox
npx shadcn-ui@latest add radio-group
npx shadcn-ui@latest add slider
npx shadcn-ui@latest add switch
npx shadcn-ui@latest add table
npx shadcn-ui@latest add pagination
```

---

## 📅 Migration Timeline

### Phase 1: Setup (Day 1-2)
**Goal**: Create React project structure and verify API connectivity

**Tasks**:
1. ✅ Tag vanilla JS version: `v1.2.2-vanilla-js-stable`
2. Create Vite + React + TypeScript project
3. Install ShadCN UI
4. Configure Tailwind CSS
5. Set up routing (React Router)
6. Create basic layout structure
7. Add CORS to FastAPI backend
8. Test API connectivity
9. Create API client with TanStack Query

**Deliverables**:
- Working React app on localhost:5173
- API calls working to localhost:8081
- ShadCN configured and tested
- Basic layout with header/sidebar

**Verification**:
- `npm run dev` starts app successfully
- Can fetch `/api/stats` and display in React
- Dark mode toggle works (ShadCN feature)

---

### Phase 2: Core Layout & Navigation (Day 3-4)
**Goal**: Build the shell of the application

**Tasks**:
1. Create Header component
2. Create Sidebar navigation
3. Create Layout wrapper
4. Implement routing for all pages
5. Create empty page components
6. Add loading states (ShadCN Skeleton)
7. Add error boundaries
8. Implement theme toggle (dark/light)

**Components to Build**:
```tsx
// Layout components
components/layout/Header.tsx
components/layout/Sidebar.tsx
components/layout/Layout.tsx
components/layout/ThemeToggle.tsx

// Page skeletons
pages/HomePage.tsx
pages/EntitiesPage.tsx
pages/DocumentsPage.tsx
pages/NetworkPage.tsx
pages/TimelinePage.tsx
pages/FlightsPage.tsx
pages/MapsPage.tsx
```

**Deliverables**:
- Complete navigation structure
- All pages accessible via routing
- Responsive layout (mobile + desktop)
- Theme switching working

---

### Phase 3: Entities Page (Day 5-7)
**Goal**: Fully migrate Entities functionality

**Tasks**:
1. Create TypeScript types for entities
2. Build API hook: `useEntities()`
3. Create EntityCard component
4. Create EntityGrid component
5. Implement entity filtering
6. Implement entity search
7. Create EntityDetailSheet (ShadCN Sheet)
8. Add biography display
9. Add entity tags
10. Add entity statistics
11. Implement connections view
12. Add pagination

**Components**:
```tsx
components/entities/EntityCard.tsx
components/entities/EntityGrid.tsx
components/entities/EntityFilters.tsx
components/entities/EntitySearch.tsx
components/entities/EntityDetailSheet.tsx
components/entities/EntityBio.tsx
components/entities/EntityStats.tsx
components/entities/EntityConnections.tsx
```

**Deliverables**:
- Complete entities page functionality
- Entity cards with Bio button
- Entity detail view with all sections
- Filtering and search working
- 100% feature parity with vanilla JS

---

### Phase 4: Documents Page (Day 8-10)
**Goal**: Migrate Documents functionality

**Tasks**:
1. Create TypeScript types for documents
2. Build API hook: `useDocuments()`
3. Create DocumentCard component
4. Create DocumentGrid component
5. Implement document filtering
6. Implement document search
7. Create DocumentViewer component
8. Add document metadata display
9. Add document download
10. Implement pagination

**Components**:
```tsx
components/documents/DocumentCard.tsx
components/documents/DocumentGrid.tsx
components/documents/DocumentFilters.tsx
components/documents/DocumentSearch.tsx
components/documents/DocumentViewer.tsx
components/documents/DocumentMetadata.tsx
```

**Deliverables**:
- Grid-only document view
- Full-size document viewer
- No "Content not available" messages
- Filtering by type, date, entities
- Search functionality

---

### Phase 5: Network Page (Day 11-13)
**Goal**: Migrate Network visualization

**Tasks**:
1. Create TypeScript types for network data
2. Build API hook: `useNetwork()`
3. Integrate React Flow or D3 + React
4. Create NetworkGraph component
5. Implement node selection
6. Implement edge highlighting
7. Add network filters
8. Add layout algorithms
9. Add zoom/pan controls
10. Add entity highlighting

**Components**:
```tsx
components/network/NetworkGraph.tsx
components/network/NetworkControls.tsx
components/network/NetworkFilters.tsx
components/network/NodeDetail.tsx
```

**Deliverables**:
- Interactive network graph
- Node selection and detail view
- Filtering by connection type
- Zoom and pan controls
- Layout options

---

### Phase 6: Timeline Page (Day 14-16)
**Goal**: Migrate Timeline functionality

**Tasks**:
1. Create TypeScript types for timeline events
2. Build API hook: `useTimeline()`
3. Create TimelineEvent component
4. Create TimelineView component
5. Implement date range filtering
6. Implement event type filtering
7. Add timeline slider (date range selector)
8. Add event detail view
9. Implement sorting

**Components**:
```tsx
components/timeline/TimelineEvent.tsx
components/timeline/TimelineView.tsx
components/timeline/TimelineFilters.tsx
components/timeline/TimelineSlider.tsx
components/timeline/EventDetail.tsx
```

**Deliverables**:
- Complete timeline view
- Date range filtering
- Event detail modal
- Responsive layout
- No blank page issues

---

### Phase 7: Flights Page (Day 17-19)
**Goal**: Migrate Flights functionality

**Tasks**:
1. Create TypeScript types for flight data
2. Build API hook: `useFlights()`
3. Create FlightCard component
4. Create FlightList component
5. Implement flight filtering
6. Implement flight search
7. Create FlightDetail component
8. Add route visualization
9. Add passenger list

**Components**:
```tsx
components/flights/FlightCard.tsx
components/flights/FlightList.tsx
components/flights/FlightFilters.tsx
components/flights/FlightSearch.tsx
components/flights/FlightDetail.tsx
components/flights/RouteVisualization.tsx
```

**Deliverables**:
- Complete flights view
- Filtering by route, date, passengers
- Flight detail view
- Route visualization

---

### Phase 8: Maps Page (Day 20-22)
**Goal**: Migrate Maps functionality

**Tasks**:
1. Create TypeScript types for location data
2. Build API hook: `useLocations()`
3. Integrate React Leaflet
4. Create Map component
5. Add location markers
6. Add flight routes (curved lines)
7. Implement map filters
8. Add location popups
9. Add map controls

**Components**:
```tsx
components/maps/Map.tsx
components/maps/LocationMarker.tsx
components/maps/FlightRoute.tsx
components/maps/MapControls.tsx
components/maps/MapFilters.tsx
```

**Deliverables**:
- Interactive map
- Location markers
- Flight route visualization
- Filtering options

---

### Phase 9: Testing & QA (Day 23-25)
**Goal**: Comprehensive testing and bug fixes

**Tasks**:
1. Test all pages on desktop
2. Test all pages on mobile
3. Test all filters and search
4. Test API error handling
5. Test loading states
6. Test dark mode
7. Performance testing
8. Accessibility audit
9. Cross-browser testing
10. Bug fixes

**Tools**:
- React Testing Library
- Playwright (E2E tests)
- Lighthouse (performance)
- axe DevTools (accessibility)

**Deliverables**:
- 100% feature parity with vanilla JS
- All tests passing
- Performance metrics > vanilla JS
- Accessibility score > 90

---

### Phase 10: Deployment (Day 26-28)
**Goal**: Deploy to production

**Tasks**:
1. Build production bundle
2. Optimize bundle size
3. Configure FastAPI to serve React build
4. Update nginx/deployment config
5. Deploy to staging
6. QA testing on staging
7. Deploy to production
8. Monitor for errors

**Commands**:
```bash
# Build React app
cd frontend
npm run build

# Serve from FastAPI
# Update server/app.py to serve frontend/dist
```

**Deliverables**:
- Production-ready React build
- Deployed and accessible
- Monitoring configured
- Rollback plan documented

---

## 🔧 Backend Changes Required

### 1. Add CORS Middleware
```python
# server/app.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Serve React Build (Production)
```python
# server/app.py
from fastapi.staticfiles import StaticFiles

# Serve React build
app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve React app for all routes (SPA)"""
    if full_path.startswith("api/"):
        raise HTTPException(404)
    return FileResponse("frontend/dist/index.html")
```

### 3. No API Changes
All existing endpoints remain unchanged:
- ✅ `/api/stats`
- ✅ `/api/entities`
- ✅ `/api/documents`
- ✅ `/api/network`
- ✅ `/api/flights`
- ✅ `/api/timeline`

---

## 📊 Success Metrics

### Performance
- [ ] Bundle size < 500KB (gzipped)
- [ ] First Contentful Paint < 1.5s
- [ ] Time to Interactive < 3s
- [ ] Lighthouse score > 90

### Code Quality
- [ ] TypeScript coverage > 95%
- [ ] No `any` types in production code
- [ ] ESLint: 0 errors
- [ ] Test coverage > 80%

### Functionality
- [ ] 100% feature parity with vanilla JS
- [ ] All pages working
- [ ] All filters working
- [ ] All visualizations working
- [ ] Mobile responsive

### Developer Experience
- [ ] Hot module replacement working
- [ ] Type checking in IDE
- [ ] Component library (Storybook optional)
- [ ] Clear documentation

---

## 🚨 Rollback Plan

If migration fails or critical bugs found:

```bash
# 1. Stop new React frontend
pkill -f "vite"

# 2. Revert to vanilla JS version
git checkout v1.2.2-vanilla-js-stable

# 3. Restart FastAPI server
.venv/bin/uvicorn server.app:app --host 0.0.0.0 --port 8081 --reload

# 4. Verify vanilla JS working
curl http://localhost:8081/

# 5. Remove CORS middleware from server/app.py (if added)
```

---

## 📚 Resources

### Documentation
- [React Docs](https://react.dev/)
- [ShadCN UI](https://ui.shadcn.com/)
- [Vite Docs](https://vitejs.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [TanStack Query](https://tanstack.com/query/latest)
- [Tailwind CSS](https://tailwindcss.com/)

### Component Examples
- [ShadCN Examples](https://ui.shadcn.com/examples)
- [React Flow Examples](https://reactflow.dev/examples)
- [React Leaflet Docs](https://react-leaflet.js.org/)

---

## ✅ Pre-Migration Checklist

- [x] Vanilla JS version tagged: `v1.2.2-vanilla-js-stable`
- [x] Migration plan documented
- [ ] Node.js v18+ installed
- [ ] npm or yarn installed
- [ ] Git working tree clean
- [ ] FastAPI server running on 8081
- [ ] All data files intact
- [ ] Backup created

---

## 🎯 Next Steps

1. **Review this plan** - Confirm approach and timeline
2. **Install Node.js** - Ensure v18+ installed
3. **Create React project** - Run `npm create vite@latest`
4. **Install ShadCN** - Run `npx shadcn-ui@latest init`
5. **Start Phase 1** - Begin setup tasks

---

**Migration starts**: TBD
**Expected completion**: ~4 weeks
**Rollback tag**: `v1.2.2-vanilla-js-stable`
**Status**: Ready to begin
