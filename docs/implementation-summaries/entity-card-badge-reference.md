# Entity Card Badge Reference

Quick visual reference for the new entity card badge layout.

---

## Badge Types & Placement

### Card Structure
```
┌─────────────────────────────────────────────────┐
│ HEADER                                          │
│ 👤 [Entity Name]              [Details →]      │
│     ↑ Link                     ↑ Button         │
├─────────────────────────────────────────────────┤
│ CONTENT                                         │
│ 👥 Connections: 1,450  👁 Documents: 98        │
│ ─────────────────────────────────────────────── │
│ Biography summary text here...                  │
├═════════════════════════════════════════════════┤ ← Border separator
│ FOOTER (All Badges)                             │
│ [Category Badge] 📖 Black Book ✈️ Flight Logs  │
│ ↑ Clickable      ↑ Informational badges        │
└─────────────────────────────────────────────────┘
```

---

## Badge Specifications

### 1. Category Badge (Clickable Filter)

**Purpose**: Filter entities by relationship category
**Type**: Custom button (styled badge)
**Style**: Colored background + text (from entity ontology)
**Location**: Footer (leftmost)
**Interaction**: Clickable

```tsx
<button
  onClick={(e) => {
    e.preventDefault();
    handleBadgeClick(primaryCategory.type);
  }}
  className="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold transition-all hover:opacity-80 hover:scale-105 cursor-pointer"
  style={{
    backgroundColor: primaryCategory.bg_color,
    color: primaryCategory.color,
    border: `1px solid ${primaryCategory.color}40`
  }}
  title={`Filter by ${primaryCategory.label}`}
>
  {primaryCategory.label}
</button>
```

**Examples**:
- `[Close Associate]` - Purple background
- `[Family Member]` - Blue background
- `[Victim/Survivor]` - Red background
- `[Employee]` - Green background
- `[Business Associate]` - Orange background

**Visual States**:
- Normal: Full color (bg_color, color from ontology)
- Hover: 80% opacity, 105% scale
- Focus: Ring outline (accessibility)

---

### 2. Source Badges (Informational)

**Purpose**: Show which source documents mention this entity
**Type**: Badge component (outline variant)
**Style**: Gray outline, neutral
**Location**: Footer (after category badge)
**Interaction**: Non-interactive (cursor-default)

#### Black Book Badge
```tsx
{entity.in_black_book && (
  <Badge variant="outline" className="cursor-default text-xs">
    📖 Black Book
  </Badge>
)}
```

**Displayed when**: `entity.in_black_book === true`
**Icon**: 📖 (book emoji)
**Meaning**: Entity appears in Jeffrey Epstein's "Black Book"

#### Flight Logs Badge
```tsx
{entity.sources.includes('flight_logs') && (
  <Badge variant="outline" className="cursor-default text-xs">
    ✈️ Flight Logs
  </Badge>
)}
```

**Displayed when**: `'flight_logs'` in `entity.sources` array
**Icon**: ✈️ (airplane emoji)
**Meaning**: Entity appears in flight logs

---

### 3. Feature Badges (Informational)

**Purpose**: Highlight special entity attributes
**Type**: Badge component (outline variant)
**Style**: Gray outline (or subtle colored)
**Location**: Footer (after source badges)
**Interaction**: Non-interactive (cursor-default)

#### Billionaire Badge
```tsx
{entity.is_billionaire && (
  <Badge variant="outline" className="cursor-default text-xs">
    💰 Billionaire
  </Badge>
)}
```

**Displayed when**: `entity.is_billionaire === true`
**Icon**: 💰 (money bag emoji)
**Style**: Gray outline, neutral

#### Biography Badge
```tsx
{entity.bio?.summary && (
  <Badge variant="outline" className="cursor-default text-xs bg-primary/5 border-primary/20 text-primary">
    <Sparkles className="h-3 w-3 mr-1" />
    Biography
  </Badge>
)}
```

**Displayed when**: `entity.bio.summary` exists
**Icon**: ✨ (sparkles - Lucide icon)
**Style**: Primary colored (subtle blue tint)
**Meaning**: Entity has AI-generated biography

---

## Badge Ordering

### Priority Order (Left to Right)
1. **Category Badge** (if available) - Always first
2. **Black Book Badge** (if applicable)
3. **Flight Logs Badge** (if applicable)
4. **Billionaire Badge** (if applicable)
5. **Biography Badge** (if applicable)

### Example Combinations

**High-profile individual**:
```
[Close Associate] 📖 Black Book ✈️ Flight Logs 💰 Billionaire ✨ Biography
```

**Victim/Survivor**:
```
[Victim/Survivor] 📖 Black Book ✨ Biography
```

**Business entity**:
```
[Business Associate] ✨ Biography
```

**Unknown entity (no bio)**:
```
📖 Black Book
```

---

## Responsive Behavior

### Desktop (1280px+)
```
Footer: [Category] [Black Book] [Flight Logs] [Billionaire] [Biography]
        └── All badges on one line ──────────────────────────────────┘
```

### Tablet (768px - 1279px)
```
Footer: [Category] [Black Book] [Flight Logs]
        [Billionaire] [Biography]
        └── Wraps to 2 rows ───────────────┘
```

### Mobile (< 768px)
```
Footer: [Category]
        [Black Book]
        [Flight Logs]
        [Billionaire]
        [Biography]
        └── Wraps to multiple rows ────┘
```

**CSS**: `flex flex-wrap gap-2` - Badges wrap naturally based on available space

---

## Styling Classes

### CardFooter Container
```tsx
<CardFooter className="flex flex-wrap gap-2 pt-4 border-t">
```

- `flex`: Flexbox layout
- `flex-wrap`: Allow badges to wrap
- `gap-2`: 0.5rem spacing between badges
- `pt-4`: Top padding
- `border-t`: Top border for separation

### Category Badge (Button)
```tsx
className="inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold transition-all hover:opacity-80 hover:scale-105 cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
```

- `inline-flex items-center`: Inline flex container
- `rounded-full`: Fully rounded corners
- `px-3 py-1`: Padding
- `text-xs font-semibold`: Typography
- `transition-all`: Smooth transitions
- `hover:opacity-80 hover:scale-105`: Hover effects
- `cursor-pointer`: Pointer cursor
- `focus:outline-none focus:ring-2`: Focus ring

### Source/Feature Badges
```tsx
className="cursor-default text-xs"
```

- `cursor-default`: Default cursor (not clickable)
- `text-xs`: Small text size

**Biography Badge (special)**:
```tsx
className="cursor-default text-xs bg-primary/5 border-primary/20 text-primary"
```

- Additional: `bg-primary/5` - Light blue background
- Additional: `border-primary/20` - Primary colored border
- Additional: `text-primary` - Primary colored text

---

## Accessibility

### Category Badge
- **Role**: `button`
- **Keyboard**: Focusable (Tab key)
- **Title**: "Filter by [Category Name]" (tooltip)
- **Focus Ring**: 2px ring on focus
- **Screen Reader**: "Button: Filter by Close Associate"

### Source/Feature Badges
- **Role**: Presentational
- **Keyboard**: Not focusable (informational only)
- **Cursor**: Default (not clickable)
- **Screen Reader**: Announces badge text

---

## Color Reference

### Category Colors (from Entity Ontology)

| Category | Background | Text Color | Border |
|----------|------------|------------|--------|
| Close Associate | `#E9D5FF` | `#7C3AED` | `#7C3AED40` |
| Family Member | `#DBEAFE` | `#2563EB` | `#2563EB40` |
| Victim/Survivor | `#FEE2E2` | `#DC2626` | `#DC262640` |
| Employee | `#D1FAE5` | `#059669` | `#05966940` |
| Business Associate | `#FED7AA` | `#EA580C` | `#EA580C40` |

*Note: Colors are defined in `data/metadata/entity_relationship_ontology.json`*

### Source/Feature Badge Colors

| Badge | Variant | Background | Border | Text |
|-------|---------|------------|--------|------|
| Black Book | `outline` | Transparent | Gray | Gray |
| Flight Logs | `outline` | Transparent | Gray | Gray |
| Billionaire | `outline` | Transparent | Gray | Gray |
| Biography | `outline` | `primary/5` | `primary/20` | `primary` |

---

## Implementation Notes

### Badge Display Logic
```tsx
// 1. Get primary category (if exists)
const primaryCategory = entity.bio?.relationship_categories?.reduce((prev, curr) =>
  curr.priority < prev.priority ? curr : prev
);

// 2. Render footer with badges
<CardFooter className="flex flex-wrap gap-2 pt-4 border-t">
  {/* Category badge - show if exists */}
  {primaryCategory && <CategoryBadge />}

  {/* Source badges - show if applicable */}
  {entity.in_black_book && <BlackBookBadge />}
  {entity.sources.includes('flight_logs') && <FlightLogsBadge />}

  {/* Feature badges - show if applicable */}
  {entity.is_billionaire && <BillionaireBadge />}
  {entity.bio?.summary && <BiographyBadge />}
</CardFooter>
```

### Category Badge Click Handler
```tsx
const handleBadgeClick = (categoryType: string) => {
  setSelectedCategory(categoryType);
  const newParams = new URLSearchParams(searchParams);
  newParams.set('category', categoryType);
  setSearchParams(newParams);
  window.scrollTo({ top: 0, behavior: 'smooth' });
};
```

**Side Effects**:
1. Updates `selectedCategory` state
2. Updates URL parameter: `?category={type}`
3. Scrolls to top of page
4. Triggers entity list re-filter
5. Shows filter indicator banner

---

## Testing Scenarios

### Visual Testing
- [ ] Category badge shows correct color
- [ ] Source badges show emoji icons
- [ ] Biography badge shows sparkles icon
- [ ] Badges wrap on small screens
- [ ] Footer border visible

### Interaction Testing
- [ ] Category badge clickable (cursor changes)
- [ ] Category badge hover effects work
- [ ] Source badges non-clickable (cursor default)
- [ ] Category badge click filters entities
- [ ] Filter URL parameter updates

### Accessibility Testing
- [ ] Category badge keyboard accessible
- [ ] Focus ring visible on category badge
- [ ] Title attribute shows tooltip
- [ ] Screen reader announces badges correctly

---

## Quick Reference

### Show Category Badge
✅ Entity has `bio.relationship_categories` array
✅ Array is not empty
✅ Badge uses primary category (lowest priority number)

### Show Black Book Badge
✅ `entity.in_black_book === true`

### Show Flight Logs Badge
✅ `'flight_logs'` in `entity.sources` array

### Show Billionaire Badge
✅ `entity.is_billionaire === true`

### Show Biography Badge
✅ `entity.bio.summary` exists (string with content)

---

**Last Updated**: 2025-11-28
