# Time Slider (Year Selector) Feature

## Overview

The Time Slider is an interactive horizontal timeline component that enables users to navigate through years of flight data with visual activity density feedback. Implemented as the `YearSlider` component, it provides an intuitive, accessible interface for temporal data exploration.

## Component Location

- **Main Component**: `frontend/src/components/visualizations/YearSlider.tsx`
- **Used In**: `frontend/src/pages/Activity.tsx` (Calendar Heatmap page)
- **Tests**: `tests/qa/year-slider-comprehensive-test.spec.ts`

## Features

### Core Functionality

1. **Interactive Timeline Scrubber**
   - Horizontal slider with draggable handle
   - Clickable year marks for quick navigation
   - Real-time year selection feedback

2. **Visual Activity Density**
   - Color-coded bars beneath timeline
   - 4-tier density visualization:
     - Gray: No activity
     - Light Blue: Low activity (0-20%)
     - Medium Blue: Medium activity (20-60%)
     - Dark Blue: High activity (60%+)
   - Normalized based on peak activity year

3. **Keyboard Navigation** (Full Accessibility)
   - `←/→` or `↑/↓`: Navigate to previous/next year
   - `Home`: Jump to earliest year
   - `End`: Jump to latest year
   - Tab: Focus slider
   - All actions announced to screen readers

4. **Mobile-Friendly**
   - Touch-optimized interactions
   - Responsive sizing
   - 44px minimum touch target height

5. **Performance Optimizations**
   - Debounced drag events (200ms)
   - Memoized calculations
   - Smooth 300ms CSS transitions
   - Controlled re-renders with React.memo

### Accessibility

- Full ARIA support (`aria-label`, `aria-valuemin`, `aria-valuemax`, `aria-valuenow`)
- Screen reader announcements for year changes
- Visible focus indicators
- Semantic HTML structure
- Keyboard-only navigation support

## Usage

### Basic Integration

```tsx
import { YearSlider } from '@/components/visualizations/YearSlider'

function MyComponent() {
  const [selectedYear, setSelectedYear] = useState(2002)
  const years = [1995, 1996, ..., 2006]

  return (
    <YearSlider
      years={years}
      selectedYear={selectedYear}
      onYearChange={setSelectedYear}
    />
  )
}
```

### With Activity Data

```tsx
const activityData = {
  1999: 247,
  2000: 312,
  2001: 289,
  2002: 347, // Peak year
  2003: 198
}

<YearSlider
  years={years}
  selectedYear={selectedYear}
  onYearChange={setSelectedYear}
  activityData={activityData}
/>
```

## Props Interface

```typescript
export interface YearSliderProps {
  years: number[]              // Array of available years
  selectedYear: number         // Currently selected year
  onYearChange: (year: number) => void  // Callback when year changes
  activityData?: Record<number, number> // Optional: year -> count mapping
  className?: string           // Optional: additional CSS classes
}
```

## Design Decisions

### Why Timeline Scrubber over Dropdown?

1. **Visual Context**: Users can see the full temporal range at a glance
2. **Intuitive Navigation**: Year-to-year transitions feel natural
3. **Activity at-a-Glance**: Density visualization provides immediate insights
4. **Better UX**: More engaging than dropdown selection

### Performance Considerations

- **Debouncing**: 200ms debounce during drag prevents excessive state updates
- **Immediate Commit**: Year updates immediately on mouse/touch release
- **Memoization**: Expensive calculations (year marks, max activity) are memoized
- **React.memo**: Component only re-renders when props change

## Testing

### Test Coverage

- ✅ **Rendering**: Component renders with correct year range
- ✅ **Interaction**: Click, drag, keyboard navigation
- ✅ **State Management**: Year changes propagate correctly
- ✅ **Accessibility**: ARIA attributes, keyboard navigation
- ✅ **Edge Cases**: Single year, no years, missing activity data
- ✅ **Visual Regression**: Playwright snapshots

### Running Tests

```bash
# Run all tests
npx playwright test tests/qa/year-slider-comprehensive-test.spec.ts

# Run specific test
npx playwright test tests/qa/year-slider-comprehensive-test.spec.ts --grep "should render YearSlider"

# Debug mode with UI
npx playwright test tests/qa/year-slider-comprehensive-test.spec.ts --headed --slowMo=1000
```

## Implementation Status

### ✅ Completed (Linear Tickets)

- **1M-187**: Design time slider UI mockup ✓
- **1M-188**: Implement year slider component ✓
- **1M-189**: Connect slider to Activity.tsx state ✓
- **1M-190**: Add smooth transitions ✓
- **1M-191**: Add data density visualization ✓
- **1M-192**: Implement keyboard navigation ✓
- **1M-194**: Write comprehensive tests ✓

### 🔄 In Progress

- **1M-193**: Mobile responsive design (partially complete - touch works, needs verification)
- **1M-195**: Documentation (this document)

### 📋 Planned

- **1M-196**: Add preset range buttons (Peak Years, Recent, All Time)

## Known Limitations

1. **Year Range**: Currently hardcoded for flight data years (1995-2006)
2. **Preset Buttons**: Not yet implemented (1M-196)
3. **Mobile Optimization**: Touch gestures work but need full responsive testing

## Future Enhancements

1. **Preset Range Buttons** (1M-196)
   - "Peak Years" (1999-2002)
   - "Recent" (2003-2006)
   - "All Time" (full range)

2. **Enhanced Mobile Experience**
   - Swipe gestures for year navigation
   - Larger touch targets on small screens
   - Optimized density bar sizing

3. **Advanced Features**
   - Year range selection (start + end years)
   - Zoom in/out on timeline
   - Bookmarked years

## Related Documentation

- [Calendar Heatmap Feature](./CALENDAR_HEATMAP.md)
- [Activity Page Implementation](../developer/implementation/ANALYTICS_DASHBOARD_IMPLEMENTATION.md)
- [Accessibility Guidelines](../developer/ACCESSIBILITY.md)

## Support & Issues

For bugs or feature requests related to the Time Slider:
1. Check existing Linear tickets in the "Time Slider for Calendar Heatmap" project
2. Create new ticket with tag: `features`, `ui`, `Calendar Heatmap`
3. Reference this documentation for context

---

**Last Updated**: 2025-11-24
**Component Version**: 1.0.0
**Linear Parent**: 1M-154 (Time Slider for Calendar Heatmap)
