# Entity Multi-Select Category Filters Implementation

**Date**: 2025-11-28
**Component**: `frontend/src/pages/Entities.tsx`
**Type**: Feature Enhancement

## Overview

Upgraded the entity category filtering system from single-select to multi-select, allowing users to filter entities by multiple relationship categories simultaneously with individual removal capabilities.

## Changes Made

### 1. State Management Update

**Before (Single Select)**:
```typescript
const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
```

**After (Multi-Select)**:
```typescript
const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
```

### 2. Filter Logic Enhancement

**Before (Single Category)**:
```typescript
if (selectedCategory) {
  filteredEntities = response.entities.filter(entity =>
    entity.bio?.relationship_categories?.some(cat => cat.type === selectedCategory)
  );
}
```

**After (Multiple Categories with OR Logic)**:
```typescript
if (selectedCategories.length > 0) {
  filteredEntities = response.entities.filter(entity =>
    selectedCategories.some(selectedCat =>
      entity.bio?.relationship_categories?.some(cat => cat.type === selectedCat)
    )
  );
}
```

**Logic**: Entities match if they have ANY of the selected categories (OR operation).

### 3. Toggle Behavior

Added toggle functionality to category badge clicks:
- **First click**: Adds category to selection
- **Second click**: Removes category from selection

```typescript
const handleBadgeClick = (categoryType: string) => {
  setSelectedCategories(prev => {
    const isSelected = prev.includes(categoryType);
    const updated = isSelected
      ? prev.filter(cat => cat !== categoryType)  // Remove if selected
      : [...prev, categoryType];                   // Add if not selected

    // Update URL with comma-separated categories
    updateURLParams(updated);
    return updated;
  });
};
```

### 4. New Handler Functions

#### Individual Category Removal
```typescript
const handleRemoveCategory = (categoryType: string) => {
  setSelectedCategories(prev => {
    const updated = prev.filter(cat => cat !== categoryType);
    updateURLParams(updated);
    return updated;
  });
};
```

#### Clear All Filters
```typescript
const handleClearAllFilters = () => {
  setSelectedCategories([]);

  const newParams = new URLSearchParams(searchParams);
  newParams.delete('categories');
  setSearchParams(newParams);
};
```

### 5. Category Data Helper

Added static mapping from `entity_relationship_ontology.json`:

```typescript
const getCategoryData = (categoryType: string) => {
  const categoryMap: Record<string, { label: string; color: string; bg_color: string }> = {
    'victims': { label: 'Victims', color: '#DC2626', bg_color: '#FEE2E2' },
    'co-conspirators': { label: 'Co-Conspirators', color: '#EA580C', bg_color: '#FFEDD5' },
    'frequent_travelers': { label: 'Frequent Travelers', color: '#EAB308', bg_color: '#FEF9C3' },
    'social_contacts': { label: 'Social Contacts', color: '#84CC16', bg_color: '#ECFCCB' },
    'associates': { label: 'Associates', color: '#F59E0B', bg_color: '#FEF3C7' },
    'legal_professionals': { label: 'Legal Professionals', color: '#06B6D4', bg_color: '#CFFAFE' },
    'investigators': { label: 'Investigators', color: '#3B82F6', bg_color: '#DBEAFE' },
    'public_figures': { label: 'Public Figures', color: '#8B5CF6', bg_color: '#EDE9FE' },
    'peripheral': { label: 'Peripheral', color: '#6B7280', bg_color: '#F3F4F6' },
  };
  return categoryMap[categoryType] || { label: categoryType, color: '#6B7280', bg_color: '#F3F4F6' };
};
```

### 6. Enhanced Filter Bar UI

**Before**: Single category with "Clear Filter" button

**After**: Multi-select filter bar with individual removable badges

```tsx
{selectedCategories.length > 0 && (
  <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
    <div className="flex items-center justify-between gap-4 flex-wrap">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm font-medium">Filters:</span>

        {/* Individual removable category badges */}
        {selectedCategories.map(catType => {
          const catData = getCategoryData(catType);
          return (
            <button
              key={catType}
              onClick={() => handleRemoveCategory(catType)}
              style={{
                backgroundColor: catData.bg_color,
                color: catData.color,
                border: `1px solid ${catData.color}40`
              }}
              title={`Remove ${catData.label} filter`}
            >
              {catData.label}
              <X className="h-3.5 w-3.5" />
            </button>
          );
        })}

        {/* Count */}
        <span className="text-sm text-muted-foreground">
          ({totalEntities} {totalEntities === 1 ? 'entity' : 'entities'})
        </span>
      </div>

      {/* Clear All button */}
      <Button variant="ghost" size="sm" onClick={handleClearAllFilters}>
        <X className="h-4 w-4" />
        Clear All
      </Button>
    </div>
  </div>
)}
```

### 7. Visual Selection Indicator

Category badges in entity cards now show when they are selected:

```tsx
<button
  className={`inline-flex items-center ... ${
    selectedCategories.includes(primaryCategory.type) ? 'ring-2 ring-offset-2' : ''
  }`}
  style={{
    border: selectedCategories.includes(primaryCategory.type)
      ? `2px solid ${primaryCategory.color}`
      : `1px solid ${primaryCategory.color}40`
  }}
>
  {primaryCategory.label}
  {selectedCategories.includes(primaryCategory.type) && (
    <span className="ml-1 text-xs">✓</span>
  )}
</button>
```

**Indicators**:
- ✓ Checkmark appears next to selected categories
- Thicker border (2px vs 1px)
- Ring styling on focus

### 8. URL Parameter Format

**Before**: `?category=social_contacts`
**After**: `?categories=social_contacts,frequent_travelers,associates`

URL parameter handling:
```typescript
// Initialize from URL on mount
useEffect(() => {
  const categoriesParam = searchParams.get('categories');
  if (categoriesParam) {
    setSelectedCategories(categoriesParam.split(',').filter(Boolean));
  }
}, []);

// Update URL when filters change
const updateURLParams = (categories: string[]) => {
  const newParams = new URLSearchParams(searchParams);
  if (categories.length > 0) {
    newParams.set('categories', categories.join(','));
  } else {
    newParams.delete('categories');
  }
  setSearchParams(newParams);
};
```

## User Experience Flow

1. **Select Multiple Categories**:
   - Click category badges on entity cards
   - Each click adds category to filter (if not selected) or removes it (if already selected)
   - Selected badges show checkmark and thicker border

2. **View Active Filters**:
   - Filter bar appears at top showing all selected categories
   - Each category displayed as removable badge with X icon
   - Entity count updates to show filtered results

3. **Remove Individual Filters**:
   - Click X on any filter badge to remove just that category
   - Click category badge in card to toggle it off
   - Remaining filters stay active

4. **Clear All Filters**:
   - Click "Clear All" button to remove all categories at once
   - Filter bar disappears
   - Full entity list restored

5. **URL Persistence**:
   - Filter state persists in URL as comma-separated values
   - Share URLs with specific filter combinations
   - Browser back/forward maintains filter state

## Testing

Comprehensive Playwright test suite created: `tests/qa/entity-multi-select-category-filters.spec.ts`

**Test Coverage**:
- ✅ Multi-select by clicking multiple category badges
- ✅ Show selected categories as removable badges
- ✅ Remove individual categories via X button
- ✅ Clear all filters with "Clear All" button
- ✅ Visual indication on selected badges
- ✅ URL parameter with comma-separated categories
- ✅ Toggle behavior (click to remove when selected)
- ✅ OR logic filtering (match ANY selected category)
- ✅ Entity count display in filter bar

## Technical Details

**Performance**:
- Client-side filtering applied after server response
- No additional API calls required
- Efficient array operations for filter logic

**Accessibility**:
- All filter badges are keyboard accessible
- Focus rings on interactive elements
- Descriptive title attributes for screen readers
- Clear visual feedback for all states

**Browser Compatibility**:
- Uses standard React hooks and modern CSS
- No browser-specific features required
- Tested with modern browsers (Chrome, Firefox, Safari, Edge)

## Success Criteria

All requirements met:

✅ **Multi-select functionality**: Users can select multiple categories
✅ **Individual removal**: Each filter badge has X button for removal
✅ **Clear all option**: Single button to remove all filters
✅ **Visual feedback**: Selected badges show checkmark and styling
✅ **URL persistence**: Comma-separated categories in URL parameter
✅ **OR logic**: Entities match if they have ANY selected category
✅ **No TypeScript errors**: Clean compilation
✅ **Comprehensive tests**: Full Playwright test suite

## Future Enhancements

Potential improvements for future iterations:

1. **AND Logic Option**: Toggle between OR/AND filtering modes
2. **Category Count Preview**: Show entity count for each category before selection
3. **Keyboard Shortcuts**: Hotkeys for common filter operations
4. **Filter Presets**: Save and load favorite filter combinations
5. **Dynamic Category Loading**: Load category data from API instead of static mapping
6. **Filter History**: Remember recently used filter combinations
7. **Export Filtered Results**: Download filtered entity list as CSV/JSON

## Related Files

- **Component**: `frontend/src/pages/Entities.tsx`
- **Test Suite**: `tests/qa/entity-multi-select-category-filters.spec.ts`
- **Ontology Data**: `data/metadata/entity_relationship_ontology.json`
- **UI Components**:
  - `frontend/src/components/ui/badge.tsx`
  - `frontend/src/components/ui/button.tsx`

## Notes

- Filter logic uses OR operation: entities appear if they match ANY selected category
- Category data is currently hardcoded but matches ontology structure
- URL parameter name changed from `category` (singular) to `categories` (plural)
- All selected categories are preserved in URL for shareable links
- Filter bar only appears when at least one category is selected
