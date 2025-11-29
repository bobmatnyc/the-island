# Entity Bio Source Attribution - Implementation Summary

**Date**: 2025-11-25
**Component**: `frontend/src/components/entity/EntityBio.tsx`
**Feature**: Add clickable source attribution links to entity biographies

## Overview

Added source attribution links to the EntityBio component to show users where biographical information came from and allow them to click through to view the source data.

## Implementation Details

### 1. Data Structure Support

The feature extracts source information from multiple data fields:

```typescript
interface SourceLink {
  type: 'flight_logs' | 'black_book' | 'documents';
  label: string;
  icon: React.ReactNode;
  url: string;
  count?: number;
}
```

Sources are detected from:
- `entity.bio.biography_metadata.source_material` (array) - e.g., `['flight_logs', 'black_book']`
- `entity.bio.document_context` (array) - References to source documents
- `entity.bio.document_sources` (object) - Document ID mappings

### 2. Source Types

**Flight Logs**
- Icon: Plane icon
- Link: `/flights?passenger={entity_id}`
- Shows when `source_material` includes `'flight_logs'`

**Black Book**
- Icon: BookOpen icon
- No link (displayed as non-clickable badge)
- Shows when `source_material` includes `'black_book'`

**Documents**
- Icon: FileText icon
- Link: `/documents?entity={entity_id}`
- Shows count: "X Documents"
- Shows when `document_context` or `document_sources` has entries

### 3. UI Design

**Location**: Below biography metadata section, above entity details

**Visual Design**:
- Small badges/pills with icons
- Clickable links use `outline` variant with hover effects
- Non-clickable sources use `secondary` variant
- Hover state: Changes border to primary color and background

**Layout**:
```tsx
<div className="mt-4 pt-4 border-t">
  <div className="text-xs font-medium text-muted-foreground mb-2">
    Information sourced from:
  </div>
  <div className="flex flex-wrap gap-2">
    {/* Source badges */}
  </div>
</div>
```

### 4. Interaction Behavior

- **Click on Flight Logs badge** → Navigate to `/flights?passenger={entity_id}` with passenger filter applied
- **Click on Documents badge** → Navigate to `/documents?entity={entity_id}` with entity filter applied
- **Black Book badge** → No action (just informational)
- **Click event** → Uses `e.stopPropagation()` to prevent triggering bio card navigation

## Code Changes

### Modified Files

1. **frontend/src/components/entity/EntityBio.tsx**
   - Added imports: `Plane`, `FileText`, `BookOpen` icons and `Link` from react-router-dom
   - Added `SourceLink` interface
   - Added `getSourceLinks()` helper function
   - Added source attribution UI section
   - Fixed TypeScript null safety checks

### New Functions

```typescript
function getSourceLinks(entity: Entity): SourceLink[]
```
- Parses entity biography data
- Extracts source information
- Returns array of source links with icons and URLs

## Example Data Flow

### Entity with Multiple Sources

```json
{
  "id": "ghislaine_maxwell",
  "bio": {
    "summary": "...",
    "biography": "...",
    "biography_metadata": {
      "source_material": ["flight_logs", "black_book"],
      "quality_score": 0.95
    },
    "document_context": [
      {"document_id": "doc123", "snippet": "..."},
      {"document_id": "doc456", "snippet": "..."}
    ]
  }
}
```

**Displayed Sources**:
- ✈️ Flight Logs (clickable → `/flights?passenger=ghislaine_maxwell`)
- 📖 Black Book (non-clickable badge)
- 📄 2 Documents (clickable → `/documents?entity=ghislaine_maxwell`)

## Testing Checklist

- [x] TypeScript compilation passes
- [ ] Sources display correctly based on data
- [ ] Clicking Flight Logs navigates to flights page with filter
- [ ] Clicking Documents navigates to documents page with filter
- [ ] Black Book shows as non-clickable badge
- [ ] Source links don't trigger bio card click
- [ ] Document count displays correctly
- [ ] Hover states work as expected
- [ ] Works with entities that have no sources
- [ ] Works with entities that have only one source type

## Browser Testing

**Test Entities**:
1. **Ghislaine Maxwell** (`ghislaine_maxwell`) - Has flight_logs, black_book, documents
2. **Bill Clinton** (`bill_clinton`) - Has flight_logs, documents
3. **Larry Morrison** (`larry_morrison`) - Has flight_logs, black_book (95 flights)
4. **Jeffrey Epstein** (`jeffrey_epstein`) - All sources

**Test Actions**:
1. Navigate to entity detail page
2. Click on biography tab
3. Scroll to "Information sourced from:" section
4. Click each source badge
5. Verify correct navigation and filtering

## Design Decisions

### Why Small Badges?
- Subtle, not overwhelming the biography content
- Clear visual hierarchy (content first, attribution second)
- Matches existing badge design system

### Why Stop Propagation?
- Prevents accidental navigation when clicking sources
- User expects source click to open source page, not trigger other actions

### Why Different Variants?
- **Outline** for clickable = indicates interactivity
- **Secondary** for non-clickable = informational only
- Consistent with application's design patterns

## Future Enhancements

1. **Black Book Page**: Create dedicated black book page/modal for non-clickable badge
2. **Hover Preview**: Show document preview on hover over document badge
3. **Source Confidence**: Add visual indicator for source reliability
4. **External Sources**: Link to external references (Wikipedia, news articles)
5. **Citation Format**: Add formal citation export (APA, MLA, etc.)

## Performance Considerations

- Source extraction happens once per render
- No additional API calls required (data already loaded)
- Minimal DOM additions (2-4 badges typically)
- No performance impact on existing biography display

## Accessibility

- Links use semantic `<Link>` component
- Badges have proper contrast ratios
- Keyboard navigation supported via native link behavior
- Screen readers announce "link" for clickable sources

## Related Files

- `frontend/src/components/entity/EntityBio.tsx` - Main implementation
- `data/metadata/entity_biographies.json` - Source data
- `frontend/src/lib/api.ts` - Entity type definitions

## Deployment Notes

- No backend changes required
- No database migrations needed
- Works with existing biography data structure
- Backward compatible (entities without sources show no badges)

---

**Implementation Status**: ✅ Complete (TypeScript compilation passing)
**Testing Status**: ⏳ Pending manual browser testing
**Documentation Status**: ✅ Complete
