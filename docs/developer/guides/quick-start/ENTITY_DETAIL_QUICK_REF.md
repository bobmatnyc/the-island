# Entity Detail Redesign - Quick Reference

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Large stats grid with all information visible
- Multiple sections stacked vertically
- No clear navigation to filtered views
- 4 navigation cards with counts (Bio, Docs, Flights, Network)
- Two-state system: Links view (default) ↔ Bio view (expanded)

---

## What Changed?

**Old Design:**
- Large stats grid with all information visible
- Multiple sections stacked vertically
- No clear navigation to filtered views

**New Design:**
- 4 navigation cards with counts (Bio, Docs, Flights, Network)
- Two-state system: Links view (default) ↔ Bio view (expanded)
- Deep linking support with URL parameters

## Files Changed

### Created (408 LOC total)
```bash
frontend/src/components/entity/EntityBio.tsx       # 178 LOC
frontend/src/components/entity/EntityLinks.tsx     # 129 LOC
frontend/src/hooks/useEntityCounts.ts              # 101 LOC
```

### Modified
```bash
frontend/src/pages/EntityDetail.tsx    # Redesigned with card navigation
frontend/src/pages/Flights.tsx         # Added ?passenger= URL param support
frontend/src/pages/Documents.tsx       # Added ?entity= URL param support
frontend/src/pages/Network.tsx         # Added ?focus= URL param support
```

## Navigation URLs

```javascript
// Bio - Toggle in place (no navigation)
onClick: () => setViewMode('bio')

// Docs - Navigate with entity filter
URL: `/documents?entity=${encodeURIComponent(entityName)}`

// Flights - Navigate with passenger filter
URL: `/flights?passenger=${encodeURIComponent(entityName)}`

// Network - Navigate with focus entity
URL: `/network?focus=${encodeURIComponent(entityName)}`
```

## Component Usage

### EntityBio
```tsx
import { EntityBio } from '@/components/entity/EntityBio';

<EntityBio
  entity={entity}
  onBack={() => setViewMode('links')}
/>
```

### EntityLinks
```tsx
import { EntityLinks } from '@/components/entity/EntityLinks';

<EntityLinks
  entity={entity}
  onBioClick={() => setViewMode('bio')}
/>
```

### useEntityCounts Hook
```tsx
import { useEntityCounts } from '@/hooks/useEntityCounts';

const { counts, loading, error } = useEntityCounts(entity);
// counts: { documents: number, flights: number, connections: number }
```

## Key Features

### ✅ Zero Extra API Calls
Counts extracted directly from Entity object (no new endpoints needed)

### ✅ Deep Linking
All navigation supports URL parameters for filtering

### ✅ Responsive
2x2 grid on desktop/tablet, single column on mobile

### ✅ State Management
React state for view toggle, no complex state management needed

### ✅ Error Handling
Defensive count extraction, graceful degradation

## Testing Checklist

```bash
# 1. Start dev server
cd frontend && npm run dev

# 2. Navigate to any entity
http://localhost:5173/entities/Jeffrey%20Epstein

# 3. Verify Links View
[ ] 4 cards visible: Bio, Docs, Flights, Network
[ ] Counts displayed correctly (match entity data)
[ ] Hover effects work (border, shadow, icon scale)

# 4. Test Bio Toggle
[ ] Click "Bio" → Expanded view appears
[ ] Click "Back" → Returns to links view
[ ] Biography content displays

# 5. Test Navigation
[ ] Click "Docs" → /documents?entity=Jeffrey%20Epstein
[ ] Click "Flights" → /flights?passenger=Jeffrey%20Epstein
[ ] Click "Network" → /network?focus=Jeffrey%20Epstein

# 6. Verify Filters Applied
[ ] Documents page: Search filter pre-filled
[ ] Flights page: Passenger filter pre-filled
[ ] Network page: Node selected + centered

# 7. Test Responsive
[ ] Desktop: 2x2 grid
[ ] Mobile: Single column
[ ] Bio view: Responsive on all sizes
```

## URL Parameter Reference

### Flights Page
```typescript
// Read passenger parameter
const [searchParams] = useSearchParams();
const passenger = searchParams.get('passenger');
// Sets: passengerFilter state + shows filter panel
```

### Documents Page
```typescript
// Read entity parameter
const [searchParams] = useSearchParams();
const entity = searchParams.get('entity');
// Sets: searchQuery state (uses existing search filter)
```

### Network Page
```typescript
// Read focus parameter
const [searchParams] = useSearchParams();
const focus = searchParams.get('focus');
// Sets: searchQuery filter + auto-selects node + centers camera
```

## Design Patterns Used

### Composition over Inheritance
```tsx
// Good: Composable components
<EntityLinks entity={entity} onBioClick={handleClick} />

// Not: Inheritance-based
class EntityLinks extends BaseComponent { ... }
```

### Hook-based Logic
```tsx
// Good: Reusable hook
const { counts } = useEntityCounts(entity);

// Not: Component method
this.extractCounts(entity)
```

### URL as State
```tsx
// Good: URL parameters for navigation state
navigate(`/flights?passenger=${name}`)

// Not: Global state
setGlobalFilter({ passenger: name })
```

## Performance Notes

### Count Extraction
- **Time:** Instant (direct property access)
- **Network:** Zero extra calls
- **Caching:** React state (component lifetime)

### Navigation
- **Bio Toggle:** Instant (state change)
- **Link Navigation:** Standard React Router (no delay)
- **URL Params:** Read on mount (minimal overhead)

### Network Auto-Focus
- **Delay:** 500ms (allows graph render)
- **Animation:** 1000ms (smooth camera movement)
- **Zoom:** 3x (good context visibility)

## Common Issues

### Issue: Counts show as zero
**Solution:** Check entity object has fields:
```javascript
entity.total_documents
entity.flight_count
entity.connection_count
```

### Issue: URL params not applied
**Solution:** Check useSearchParams import:
```typescript
import { useSearchParams } from 'react-router-dom';
```

### Issue: Network not centering
**Solution:** Ensure graphRef.current exists and 500ms delay:
```typescript
setTimeout(() => {
  if (graphRef.current && focusedNode) {
    graphRef.current.centerAt(focusedNode.x, focusedNode.y, 1000);
  }
}, 500);
```

### Issue: Bio not toggling
**Solution:** Check viewMode state and handler:
```typescript
const [viewMode, setViewMode] = useState<'links' | 'bio'>('links');
const handleBioClick = () => setViewMode('bio');
```

## API No Changes Required

All data comes from existing `/api/entities/{name}` endpoint:

```json
{
  "name": "Jeffrey Epstein",
  "total_documents": 45,      // ← Used for Docs count
  "flight_count": 127,         // ← Used for Flights count
  "connection_count": 89,      // ← Used for Network count
  "name_variations": [...],
  "top_connections": [...],
  // ... rest of entity data
}
```

## Future Improvements

### Short Term
- [ ] Add loading skeletons for cards
- [ ] Implement share button for filtered URLs
- [ ] Add "last updated" timestamps

### Medium Term
- [ ] Fetch real biography from external APIs
- [ ] Add activity timeline to bio view
- [ ] Implement recent documents/flights in cards

### Long Term
- [ ] Create dedicated count endpoints
- [ ] Add real-time count updates
- [ ] Implement contribution system for bios

## Documentation Links

- **Full Implementation:** `ENTITY_DETAIL_REDESIGN_SUMMARY.md`
- **Visual Guide:** `ENTITY_DETAIL_VISUAL_GUIDE.md`
- **Component Docs:** Inline in source files

## Questions?

All components include comprehensive inline documentation explaining:
- Design decisions and rationale
- Trade-offs and alternatives considered
- Future enhancement opportunities
- Error handling approaches

Check the docstrings in each file for detailed context.

---

**Status:** ✅ Complete and Ready for Testing
**LOC Impact:** +408 LOC (new components) + ~160 LOC (modifications)
**Breaking Changes:** None
**API Changes:** None

*Quick Reference for Entity Detail Page Redesign*
*November 20, 2025*
