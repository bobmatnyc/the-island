# React Migration - Quick Start Guide

**Status**: Phase 1 Complete (90%) - Ready for Phase 2
**Last Updated**: 2025-11-19

---

## 🚀 Start Development

### 1. Start Backend Server
```bash
cd /Users/masa/Projects/epstein
source .venv/bin/activate
.venv/bin/uvicorn server.app:app --host 0.0.0.0 --port 8081 --reload
```

### 2. Start React Dev Server
```bash
cd /Users/masa/Projects/epstein/frontend
npm run dev
```

**URLs**:
- Frontend: http://localhost:5174 (or 5173)
- Backend API: http://localhost:8081
- Old Vanilla JS: http://localhost:8081/ (when backend running)

---

## ✅ Configuration Complete

All ShadCN configuration files are in place:
- ✅ `components.json` - ShadCN config
- ✅ `src/lib/utils.ts` - Utilities
- ✅ `src/index.css` - Tailwind + theme
- ✅ `tsconfig.app.json` - TypeScript paths
- ✅ `vite.config.ts` - Vite aliases
- ✅ 8 ShadCN components installed
- ✅ React Router configured
- ✅ CORS enabled on backend

---

## ⚠️ Known Issues (3 TypeScript Errors)

### Fix Before Phase 2:

**1. AdjacencyMatrix.tsx:290**
```typescript
// Line 290: Remove unused variable 'i'
.map((_, i) => { ... })
// Change to:
.map(() => { ... })
```

**2-3. Flights.tsx:50 and 71**
```typescript
// Add missing property to FlightStats
setStats({
  total_flights: 0,  // ADD THIS LINE
  unique_routes: data.unique_routes,
  // ... rest of properties
})
```

---

## 📦 What's Installed

### React Ecosystem
- React 19.2.0 (latest)
- React Router 7.9.6
- Vite 7.2.2

### UI Framework
- Tailwind CSS 3.4.18
- ShadCN/Radix UI (8 components)
- Lucide React (icons)

### Visualizations
- React Force Graph 2D
- React Heat Map
- D3 Force

**Total**: 206 packages, 0 vulnerabilities

---

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/              # ShadCN components (8)
│   │   ├── layout/          # Header, Layout
│   │   ├── chat/            # Chat UI
│   │   ├── documents/       # Document viewer
│   │   └── visualizations/  # Graphs, charts
│   ├── pages/               # Page components (8)
│   ├── lib/                 # Utilities
│   ├── App.tsx              # Router setup
│   └── main.tsx             # Entry point
├── components.json          # ShadCN config
├── tailwind.config.js       # Tailwind
├── vite.config.ts           # Vite + aliases
└── package.json             # Dependencies
```

---

## 🧪 Quick Tests

### Test Backend API
```bash
curl http://localhost:8081/api/stats
```

### Test Frontend Build
```bash
cd frontend
npm run build
# Fix TypeScript errors first!
```

### Test CORS (Browser Console)
```javascript
fetch('http://localhost:8081/api/stats')
  .then(r => r.json())
  .then(console.log)
```

---

## 📋 Next Steps

### Immediate (10 minutes)
1. Fix 3 TypeScript errors
2. Start backend server
3. Test API connectivity
4. Verify production build

### Phase 2 (Begin After Fixes)
1. Migrate Dashboard page
2. Implement data fetching
3. Test user interactions
4. Add loading states

---

## 🆘 Quick Commands

### Install New ShadCN Component
```bash
cd frontend
npx shadcn-ui@latest add [component-name]
```

### Add New Page
```typescript
// 1. Create: src/pages/NewPage.tsx
export function NewPage() {
  return <div>New Page</div>
}

// 2. Add route in App.tsx
<Route path="new-page" element={<NewPage />} />
```

### Add New Dependency
```bash
cd frontend
npm install [package-name]
```

---

## 🔧 Troubleshooting

### Port 5173 in use
```bash
# Vite automatically tries 5174, 5175, etc.
# Or kill existing process:
lsof -ti:5173 | xargs kill -9
```

### Backend not responding
```bash
# Check if running:
lsof -i :8081

# Start if needed:
cd /Users/masa/Projects/epstein
source .venv/bin/activate
.venv/bin/uvicorn server.app:app --host 0.0.0.0 --port 8081 --reload
```

### TypeScript errors in VS Code
```bash
# Restart TypeScript server:
# CMD + Shift + P → "TypeScript: Restart TS Server"
```

---

## 📖 Documentation

- Full Configuration: `SHADCN_CONFIGURATION_COMPLETE.md`
- Migration Plan: `/Users/masa/Projects/epstein/REACT_MIGRATION_PLAN.md`
- Session Resume: `.claude-mpm/sessions/session-resume-2025-11-19-react-migration.md`

---

**Status**: Ready for Phase 2 (after fixing 3 TS errors)
**Estimated Time to Phase 2**: 10 minutes
