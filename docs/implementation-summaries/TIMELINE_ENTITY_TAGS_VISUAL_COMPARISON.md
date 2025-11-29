# Timeline Entity Tags - Visual Comparison

**Feature**: Clickable Entity Tags in Timeline Events
**Date**: 2025-11-28

## Before and After

### Before: Static Badges
```tsx
{/* Non-interactive entity badges */}
{event.related_entities.map((entity, idx) => (
  <Badge key={idx} variant="secondary" className="text-xs">
    {formatEntityName(entity)}
  </Badge>
))}
```

**Behavior**:
- ❌ No hover feedback
- ❌ Not clickable
- ❌ No navigation
- ❌ Cursor: default (text cursor)

---

### After: Clickable Links
```tsx
{/* Interactive entity links with hover effects */}
{event.related_entities.map((entity, idx) => {
  const entityId = entityNameToId(entity);
  return (
    <Link
      key={idx}
      to={`/entities/${entityId}`}
      className="inline-block transition-transform hover:scale-105"
      aria-label={`View ${formatEntityName(entity)} profile`}
    >
      <Badge
        variant="secondary"
        className="text-xs cursor-pointer hover:bg-secondary/80 transition-colors"
      >
        {formatEntityName(entity)}
      </Badge>
    </Link>
  );
})}
```

**Behavior**:
- ✅ Hover: Scale up 5% + darken background
- ✅ Click: Navigate to entity detail page
- ✅ Right-click: "Open in new tab" option
- ✅ Middle-click: Open in new tab
- ✅ CMD/CTRL+click: Open in new tab
- ✅ Cursor: pointer (hand cursor)
- ✅ Accessibility: Screen reader announces link with description

---

## Interaction States

### 1. **Default State**
```
┌─────────────────┐
│ Clinton, Bill   │  <-- Normal badge appearance
└─────────────────┘
```
- Standard secondary badge styling
- Text size: xs (extra small)
- Background: secondary color

### 2. **Hover State**
```
┌──────────────────┐
│ Clinton, Bill ⬆  │  <-- Scales up 5%, darker background
└──────────────────┘
```
- Transform: `scale(1.05)` - 5% larger
- Background: `bg-secondary/80` - 80% opacity (darker)
- Cursor: pointer (hand cursor)
- Transition: smooth animation (200ms)

### 3. **Click → Navigate**
```
Timeline Event
  ↓ (click entity badge)
Entity Detail Page (/entities/clinton_bill)
  → Biography
  → Related Documents
  → Connections
  → Timeline
```

---

## User Workflows

### Workflow 1: Explore Entity from Timeline
```
User reads timeline event
  ↓
Hovers over entity badge (Clinton, Bill)
  ↓ (visual feedback: scale + color change)
Clicks badge
  ↓
Navigates to Clinton, Bill entity page
  ↓
Reads full biography, connections, documents
```

### Workflow 2: Multi-Tab Research
```
User finds interesting timeline event with 5 entities
  ↓
Right-clicks first entity → "Open in new tab"
  ↓
Right-clicks second entity → "Open in new tab"
  ↓
Right-clicks third entity → "Open in new tab"
  ↓
Switches between tabs to compare entities
```

### Workflow 3: Keyboard Navigation
```
User tabs through timeline
  ↓
Tab key focuses on entity badge
  ↓ (visual focus ring appears)
Press Enter
  ↓
Navigates to entity detail page
```

---

## Entity Name → ID Conversion Examples

| Entity Name Input      | Converted ID         | Navigation URL                    |
|------------------------|----------------------|-----------------------------------|
| Clinton, Bill          | `clinton_bill`       | `/entities/clinton_bill`          |
| Jeffrey Epstein        | `jeffrey_epstein`    | `/entities/jeffrey_epstein`       |
| Ghislaine Maxwell      | `ghislaine_maxwell`  | `/entities/ghislaine_maxwell`     |
| Prince Andrew          | `prince_andrew`      | `/entities/prince_andrew`         |
| Donald Trump           | `donald_trump`       | `/entities/donald_trump`          |
| Virginia Roberts Giuffre | `virginia_roberts_giuffre` | `/entities/virginia_roberts_giuffre` |

**Conversion Algorithm**:
1. Convert to lowercase
2. Replace all non-alphanumeric chars with underscores
3. Strip leading/trailing underscores

---

## CSS Classes Breakdown

### Link Container
```tsx
className="inline-block transition-transform hover:scale-105"
```
- `inline-block`: Allows transform while maintaining inline flow
- `transition-transform`: Smooth animation for scale changes
- `hover:scale-105`: Scale to 105% on hover (5% larger)

### Badge Component
```tsx
className="text-xs cursor-pointer hover:bg-secondary/80 transition-colors"
```
- `text-xs`: Extra small text size
- `cursor-pointer`: Hand cursor on hover
- `hover:bg-secondary/80`: Darker background on hover (80% opacity)
- `transition-colors`: Smooth color transition

---

## Accessibility Features

### ARIA Label
```tsx
aria-label={`View ${formatEntityName(entity)} profile`}
```
- Screen reader announces: "View Clinton, Bill profile, link"
- Provides context about link destination
- Helps users understand what will happen when clicked

### Keyboard Navigation
- **Tab**: Focus on entity badge
- **Enter**: Activate link (navigate to entity page)
- **Shift+Tab**: Navigate backwards

### Focus State
- Browser default focus ring appears when tabbed to
- Meets WCAG 2.1 accessibility standards

---

## Browser Compatibility

| Feature                | Chrome | Firefox | Safari | Edge |
|------------------------|--------|---------|--------|------|
| Hover scale animation  | ✅     | ✅      | ✅     | ✅   |
| Color transitions      | ✅     | ✅      | ✅     | ✅   |
| Right-click menu       | ✅     | ✅      | ✅     | ✅   |
| Middle-click new tab   | ✅     | ✅      | ✅     | ✅   |
| CMD/CTRL+click         | ✅     | ✅      | ✅     | ✅   |
| Cursor pointer         | ✅     | ✅      | ✅     | ✅   |

---

## Performance Characteristics

- **Render Time**: No measurable impact (client-side string conversion is O(n) where n = entity name length)
- **Memory**: No additional state or caching
- **Network**: Zero additional API calls
- **Animation Performance**: Hardware-accelerated CSS transforms (smooth 60fps)

---

## Example Timeline Event

### Event Data
```json
{
  "date": "1998-09-15",
  "title": "Flight to Little St. James Island",
  "description": "Private jet flight from New York to Caribbean island",
  "category": "biographical",
  "related_entities": [
    "Jeffrey Epstein",
    "Clinton, Bill",
    "Ghislaine Maxwell",
    "Prince Andrew"
  ]
}
```

### Rendered Output (Visual Representation)

```
┌────────────────────────────────────────────────────────────────┐
│ 📅 September 15, 1998                                          │
│                                                                 │
│ Flight to Little St. James Island                              │
│ Private jet flight from New York to Caribbean island           │
│                                                                 │
│ Related Entities:                                              │
│ [Jeffrey Epstein] [Clinton, Bill] [Ghislaine Maxwell]         │
│ [Prince Andrew]                                                │
│  ↑ All badges are clickable links with hover effects          │
└────────────────────────────────────────────────────────────────┘
```

Each badge:
- Displays formatted entity name
- Has pointer cursor on hover
- Scales up 5% on hover
- Darkens background on hover
- Links to `/entities/{entity_id}`
- Supports right-click, middle-click, CMD/CTRL+click

---

## Testing Checklist

- [x] Entity badges render as clickable links
- [x] Hover effect: scale animation works
- [x] Hover effect: background color darkens
- [x] Cursor changes to pointer on hover
- [x] Click navigates to correct entity page
- [x] Right-click shows "Open in new tab" option
- [x] Middle-click opens in new tab
- [x] CMD+click (Mac) opens in new tab
- [x] CTRL+click (Windows) opens in new tab
- [x] Tab key focuses on badges
- [x] Enter key activates link when focused
- [x] Screen reader announces link with ARIA label
- [x] No TypeScript errors
- [x] Build succeeds
- [x] Visual consistency with existing UI
- [x] All entity names convert to valid IDs
- [x] No broken links or 404 errors

---

## Success Metrics

✅ **Functionality**: All entity tags are clickable and navigate correctly
✅ **UX**: Hover effects provide clear interaction feedback
✅ **Accessibility**: ARIA labels and keyboard navigation work
✅ **Performance**: No measurable performance impact
✅ **Browser Support**: Works in all modern browsers
✅ **Code Quality**: No errors, follows best practices
