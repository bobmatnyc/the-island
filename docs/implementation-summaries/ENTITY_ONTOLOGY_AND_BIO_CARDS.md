# Entity Relationship Ontology & Biography Cards Implementation Plan

**Status**: Planning
**Created**: 2025-11-27
**Priority**: High

---

## 🎯 Objectives

### Primary Goals
1. **Entity Relationship Ontology**: Categorize all 634 entities by their relationship to Jeffrey Epstein
2. **Biography Summaries on Cards**: Display bio summaries directly on entity grid cards
3. **Relationship Tags**: Show visual tags/badges indicating relationship categories
4. **Category Filtering**: Allow users to filter entities by relationship type

### User Impact
- **Better Understanding**: Users can immediately see how each person relates to Epstein
- **Faster Navigation**: Quick visual cues for relationship types via color-coded tags
- **Contextual Information**: Biography summaries provide context without clicking through
- **Research Efficiency**: Filter by relationship type to focus on specific groups

---

## 📊 Ontology Structure

### Primary Relationship Categories

1. **Victims** 🔴 (Priority 1)
   - Color: `#DC2626` / Background: `#FEE2E2`
   - Description: Confirmed or alleged victims
   - Sources: Court documents, unsealed documents, depositions

2. **Co-Conspirators** 🟠 (Priority 2)
   - Color: `#EA580C` / Background: `#FFEDD5`
   - Description: Individuals implicated in facilitating crimes
   - Sources: Court documents, unsealed documents, indictments

3. **Associates** 🟡 (Priority 3)
   - Color: `#F59E0B` / Background: `#FEF3C7`
   - Description: Close personal or business associates
   - Criteria: 5+ connections, appears in black book + flight logs

4. **Frequent Travelers** 🟢 (Priority 4)
   - Color: `#EAB308` / Background: `#FEF9C3`
   - Description: Flew on Epstein's aircraft 5+ times
   - Sources: Flight logs

5. **Social Contacts** 🟢 (Priority 5)
   - Color: `#84CC16` / Background: `#ECFCCB`
   - Description: Listed in address book, limited other connections
   - Criteria: ≤2 connections, black book only

6. **Legal Professionals** 🔵 (Priority 6)
   - Color: `#06B6D4` / Background: `#CFFAFE`
   - Description: Attorneys, prosecutors, law enforcement
   - Keywords: attorney, lawyer, prosecutor, detective, agent

7. **Investigators** 🔵 (Priority 7)
   - Color: `#3B82F6` / Background: `#DBEAFE`
   - Description: Journalists, investigators, researchers
   - Keywords: journalist, reporter, investigator, researcher, author

8. **Public Figures** 🟣 (Priority 8)
   - Color: `#8B5CF6` / Background: `#EDE9FE`
   - Description: Politicians, celebrities, business leaders
   - Keywords: president, prince, senator, CEO, actor, model

9. **Peripheral** ⚪ (Priority 9)
   - Color: `#6B7280` / Background: `#F3F4F6`
   - Description: Minimal documented connections
   - Criteria: ≤1 connection

### Secondary Attributes

**Document Appearance**:
- Flight Logs Only
- Address Book Only
- Court Documents Only
- Multiple Sources (2+)

**Connection Strength**:
- High (10+ connections)
- Medium (3-9 connections)
- Low (1-2 connections)

---

## 🗂️ Data Structure Changes

### Entity Biography JSON Update

```json
{
  "entities": {
    "entity_id": {
      "id": "entity_id",
      "display_name": "Name",
      "biography": "Full biography text...",
      "biography_summary": "2-3 sentence summary for cards",  // NEW
      "relationship_categories": [  // NEW
        {
          "type": "frequent_travelers",
          "label": "Frequent Travelers",
          "color": "#EAB308",
          "bg_color": "#FEF9C3",
          "priority": 4,
          "confidence": "high"  // high|medium|low
        }
      ],
      "secondary_attributes": {  // NEW
        "document_appearance": ["flight_logs_only"],
        "connection_strength": "low"
      },
      "source_material": ["flight_logs"],
      "word_count": 265,
      "quality_score": 0.95
    }
  }
}
```

---

## 🛠️ Implementation Phases

### Phase 1: Data Enhancement (Backend)

**File**: `scripts/analysis/categorize_entities.py`

**Tasks**:
1. Load entity biographies and ontology
2. Load network data (connections, flights) from master index
3. Categorize each entity based on:
   - Source materials
   - Connection count
   - Flight frequency
   - Biography keywords
4. Generate biography summaries (first 2-3 sentences)
5. Calculate confidence scores
6. Update entity_biographies.json with new fields

**Algorithm**:
```python
def categorize_entity(entity, network_data, ontology):
    categories = []

    # Check source materials
    sources = set(entity.get('source_material', []))

    # Check network stats
    connections = network_data.get(entity['id'], {}).get('connections', 0)
    flights = network_data.get(entity['id'], {}).get('flights', 0)

    # Apply ontology rules in priority order
    for cat_type, cat_def in sorted(ontology['primary_relationships'].items(),
                                    key=lambda x: x[1]['priority']):
        confidence = calculate_confidence(entity, cat_def, sources, connections, flights)

        if confidence > 0.5:
            categories.append({
                'type': cat_type,
                'label': cat_def['label'],
                'color': cat_def['color'],
                'bg_color': cat_def['bg_color'],
                'priority': cat_def['priority'],
                'confidence': 'high' if confidence > 0.8 else 'medium' if confidence > 0.65 else 'low'
            })

    return categories
```

### Phase 2: API Enhancement (Backend)

**File**: `server/app.py`

**Changes**:
1. Update `/api/entities` endpoint to include new fields
2. Add `/api/ontology` endpoint to serve relationship categories
3. Add `/api/entities/categories` endpoint for filtering

**New Endpoints**:
```python
@app.route('/api/ontology')
def get_ontology():
    """Return entity relationship ontology"""
    with open('data/metadata/entity_relationship_ontology.json') as f:
        return jsonify(json.load(f))

@app.route('/api/entities/categories/<category>')
def get_entities_by_category(category):
    """Get entities filtered by relationship category"""
    # Filter entities by relationship_categories.type
    pass
```

### Phase 3: UI Components (Frontend)

**Component 1**: `BiographySummary.tsx`
Location: `frontend/src/components/entities/BiographySummary.tsx`

```typescript
interface BiographySummaryProps {
  biography: string;
  maxLength?: number;
  showExpandButton?: boolean;
}

// Displays truncated biography with "Read more" expansion
```

**Component 2**: `RelationshipBadge.tsx`
Location: `frontend/src/components/entities/RelationshipBadge.tsx`

```typescript
interface RelationshipBadgeProps {
  category: {
    type: string;
    label: string;
    color: string;
    bg_color: string;
    priority: number;
    confidence: 'high' | 'medium' | 'low';
  };
  size?: 'sm' | 'md' | 'lg';
}

// Visual badge with color coding and tooltip
```

**Component 3**: `CategoryFilter.tsx`
Location: `frontend/src/components/filters/CategoryFilter.tsx`

```typescript
interface CategoryFilterProps {
  selectedCategories: string[];
  onCategoryChange: (categories: string[]) => void;
  entityCounts: Record<string, number>;
}

// Multi-select filter with color-coded checkboxes
```

### Phase 4: Grid Card Updates (Frontend)

**File**: `frontend/src/pages/Entities.tsx`

**Changes to Entity Cards**:
1. Add biography summary below entity name
2. Add relationship badges (show top 2 categories)
3. Update card height to accommodate new content
4. Add hover state to show full category list

**Updated Card Structure**:
```typescript
<Card>
  <CardHeader>
    <div className="flex items-center justify-between">
      <h3>{entity.display_name}</h3>
      <ConnectionCount count={entity.connections} />
    </div>
    {/* NEW: Relationship badges */}
    <div className="flex flex-wrap gap-1 mt-2">
      {entity.relationship_categories.slice(0, 2).map(cat => (
        <RelationshipBadge key={cat.type} category={cat} size="sm" />
      ))}
    </div>
  </CardHeader>

  <CardContent>
    {/* NEW: Biography summary */}
    <BiographySummary
      biography={entity.biography_summary}
      maxLength={150}
    />

    {/* Existing: Source materials, stats, etc. */}
  </CardContent>
</Card>
```

### Phase 5: Filtering & Search (Frontend)

**File**: `frontend/src/pages/Entities.tsx`

**Enhancements**:
1. Add CategoryFilter to filters sidebar
2. Combine category filter with existing search/filter logic
3. Show active filter count
4. Add "Clear all filters" button

---

## 📐 Design Specifications

### Card Dimensions
- **Current**: ~200px height
- **New**: ~280px height (accommodate summary + badges)
- **Responsive**: Stack badges on mobile

### Typography
- **Entity Name**: font-semibold text-lg
- **Biography Summary**: text-sm text-gray-600 line-clamp-3
- **Badge Text**: text-xs font-medium

### Color Scheme
All colors from ontology maintain WCAG AA contrast ratio (4.5:1 minimum)

### Spacing
- Badge gap: 4px (gap-1)
- Summary margin-top: 8px (mt-2)
- Between sections: 12px (space-y-3)

---

## 🧪 Testing Requirements

### Unit Tests
- [ ] Entity categorization logic
- [ ] Biography summary generation
- [ ] Confidence score calculation

### Component Tests
- [ ] BiographySummary renders correctly
- [ ] RelationshipBadge displays proper colors
- [ ] CategoryFilter multi-select works
- [ ] Card layout handles long text

### Integration Tests
- [ ] API returns categorized entities
- [ ] Filtering by category works
- [ ] Combined filters work together
- [ ] Performance with 634 entities

### QA Checklist
- [ ] All 634 entities have categories
- [ ] Categories match source data
- [ ] Biography summaries are coherent
- [ ] Colors are accessible (contrast)
- [ ] Mobile responsive design
- [ ] Tooltips show full category info
- [ ] Loading states handled

---

## 📅 Timeline Estimate

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1 | Data categorization script | 4-6 hours |
| Phase 2 | API endpoints | 2-3 hours |
| Phase 3 | UI components | 4-6 hours |
| Phase 4 | Grid card updates | 2-3 hours |
| Phase 5 | Filtering integration | 2-3 hours |
| Testing | All test suites | 3-4 hours |
| **Total** | | **17-25 hours** |

---

## 🎓 Success Criteria

1. **Data Quality**
   - [ ] 100% of entities have at least one category
   - [ ] Categories align with source materials
   - [ ] Biography summaries are 2-3 sentences

2. **UI/UX**
   - [ ] Categories visible on all entity cards
   - [ ] Color coding is intuitive
   - [ ] Filtering reduces entity list correctly
   - [ ] Performance <100ms for filter operations

3. **Accessibility**
   - [ ] Color contrast meets WCAG AA
   - [ ] Keyboard navigation works
   - [ ] Screen readers announce categories
   - [ ] Tooltips provide context

4. **Documentation**
   - [ ] Ontology documented
   - [ ] API endpoints documented
   - [ ] Component usage examples
   - [ ] User guide updated

---

## 📝 Notes

- **Priority**: Focus on high-priority categories first (victims, co-conspirators)
- **Privacy**: Ensure victim information is handled sensitively
- **Flexibility**: Ontology should be updateable as new documents emerge
- **Performance**: Consider caching categorized data
- **Extensibility**: Design for future category additions

---

## 🔗 Related Files

- Ontology: `data/metadata/entity_relationship_ontology.json`
- Biographies: `data/metadata/entity_biographies.json`
- Master Index: `data/metadata/master_document_index.json`
- Network Data: `data/network/entities_network.json`

---

**Last Updated**: 2025-11-27
**Next Steps**: Begin Phase 1 - Data Enhancement (categorization script)
