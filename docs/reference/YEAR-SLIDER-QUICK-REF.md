# YearSlider Component - Quick Reference

## Import
```typescript
import { YearSlider } from '@/components/visualizations/YearSlider'
```

## Basic Usage
```typescript
<YearSlider
  years={[1995, 1996, ..., 2006]}
  selectedYear={2002}
  onYearChange={setYear}
/>
```

## With Activity Data
```typescript
<YearSlider
  years={years}
  selectedYear={selectedYear}
  onYearChange={setSelectedYear}
  activityData={{ 1995: 45, 1996: 78, 1997: 112 }}
/>
```

## Props
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `years` | `number[]` | ✅ Yes | Array of available years |
| `selectedYear` | `number` | ✅ Yes | Currently selected year |
| `onYearChange` | `(year: number) => void` | ✅ Yes | Callback when year changes |
| `activityData` | `Record<number, number>` | ❌ No | Optional activity counts per year |
| `className` | `string` | ❌ No | Optional additional CSS classes |

## Features
- ✅ **Visual Timeline**: Horizontal year markers with adaptive spacing
- ✅ **Activity Density**: Color-coded bars showing activity per year
- ✅ **Keyboard Navigation**: Arrow keys, Home, End
- ✅ **Mobile Touch**: 44px+ touch targets, smooth interactions
- ✅ **Accessibility**: ARIA labels, screen reader support
- ✅ **Animations**: 300ms smooth transitions
- ✅ **Performance**: Debounced drag (200ms), memoized calculations

## Keyboard Shortcuts
- **Arrow Left/Down**: Previous year
- **Arrow Right/Up**: Next year
- **Home**: First year
- **End**: Last year

## Activity Color Scale
- Gray: 0 flights
- Light Blue: 1-20% of max activity
- Medium Blue: 21-40%
- Dark Blue: 41-60%
- Darkest Blue: 61-100%

## Edge Cases
```typescript
// Single year - renders static text
<YearSlider years={[2002]} selectedYear={2002} onYearChange={() => {}} />
// Output: "2002"

// No years - renders message
<YearSlider years={[]} selectedYear={2002} onYearChange={() => {}} />
// Output: "No year data available"

// No activity data - still works
<YearSlider years={years} selectedYear={2002} onYearChange={setYear} />
// Activity bars show gray (no data)
```

## Browser Support
- ✅ Chrome 120+
- ✅ Safari 17+
- ✅ Firefox 121+
- ✅ Edge 120+

## File Location
`frontend/src/components/visualizations/YearSlider.tsx`

## Related Components
- `Slider` - Base Radix UI wrapper (`frontend/src/components/ui/slider.tsx`)
- `CalendarHeatmap` - Uses YearSlider for year selection
- `Activity` page - Main integration point

## Documentation
- Implementation: `docs/implementation-summaries/1M-154-YEAR-SLIDER-IMPLEMENTATION.md`
- Testing: `docs/linear-tickets/1M-154-TESTING-GUIDE.md`
- Deliverable: `docs/linear-tickets/1M-154-DELIVERABLE.md`

---

*Last Updated: 2025-11-24*
*Linear Ticket: 1M-154*
