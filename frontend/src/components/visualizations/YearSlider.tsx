import * as React from 'react'
import { Slider } from '@/components/ui/slider'
import { cn } from '@/lib/utils'

/**
 * YearSlider Props Interface
 *
 * @param years - Array of available years (e.g., [1995, 1996, ..., 2006])
 * @param selectedYear - Currently selected year
 * @param onYearChange - Callback when year selection changes
 * @param activityData - Optional map of year -> activity count for density visualization
 * @param className - Optional additional CSS classes
 */
export interface YearSliderProps {
  years: number[]
  selectedYear: number
  onYearChange: (year: number) => void
  activityData?: Record<number, number>
  className?: string
}

/**
 * Timeline Scrubber Component for Year Navigation
 *
 * Features:
 * - Interactive horizontal timeline with draggable handle
 * - Visual activity density indicators beneath timeline
 * - Keyboard navigation (Arrow keys, Home, End)
 * - Mobile-friendly touch interactions
 * - Accessible with ARIA labels
 * - Smooth transitions (300ms)
 *
 * Design Decision: Timeline scrubber pattern chosen over dropdown for:
 * - Better visual context of temporal range
 * - Intuitive year-to-year navigation
 * - Activity density at-a-glance
 *
 * Performance: Debounced drag events, memoized calculations
 * Accessibility: Full keyboard support, ARIA labels, screen reader announcements
 */
export const YearSlider = React.memo<YearSliderProps>(({
  years,
  selectedYear,
  onYearChange,
  activityData,
  className
}) => {
  // Sort years ascending for consistent timeline
  const sortedYears = React.useMemo(() => {
    return [...years].sort((a, b) => a - b)
  }, [years])

  const minYear = sortedYears[0]
  const maxYear = sortedYears[sortedYears.length - 1]

  // Calculate year marks for display (show every 2-4 years depending on range)
  const yearMarks = React.useMemo(() => {
    const range = maxYear - minYear
    const step = range <= 12 ? 1 : range <= 24 ? 2 : 4

    return sortedYears.filter((year, idx) => {
      return idx === 0 || idx === sortedYears.length - 1 || (year - minYear) % step === 0
    })
  }, [sortedYears, minYear, maxYear])

  // Calculate max activity for normalization
  const maxActivity = React.useMemo(() => {
    if (!activityData) return 0
    return Math.max(...Object.values(activityData), 1)
  }, [activityData])

  // Debounced year change to prevent excessive re-renders
  const debouncedChangeRef = React.useRef<number | undefined>(undefined)

  const handleValueChange = React.useCallback((values: number[]) => {
    const newYear = values[0]

    // Clear existing debounce timer
    if (debouncedChangeRef.current) {
      clearTimeout(debouncedChangeRef.current)
    }

    // Debounce the change by 200ms during drag
    debouncedChangeRef.current = setTimeout(() => {
      if (newYear !== selectedYear && sortedYears.includes(newYear)) {
        onYearChange(newYear)
      }
    }, 200)
  }, [selectedYear, onYearChange, sortedYears])

  // Immediate change on commit (mouse/touch release)
  const handleValueCommit = React.useCallback((values: number[]) => {
    const newYear = values[0]

    // Clear debounce timer
    if (debouncedChangeRef.current) {
      clearTimeout(debouncedChangeRef.current)
    }

    // Immediately update on release
    if (newYear !== selectedYear && sortedYears.includes(newYear)) {
      onYearChange(newYear)
    }
  }, [selectedYear, onYearChange, sortedYears])

  // Keyboard navigation
  const handleKeyDown = React.useCallback((e: React.KeyboardEvent) => {
    const currentIndex = sortedYears.indexOf(selectedYear)

    switch (e.key) {
      case 'ArrowLeft':
      case 'ArrowDown':
        e.preventDefault()
        if (currentIndex > 0) {
          onYearChange(sortedYears[currentIndex - 1])
        }
        break

      case 'ArrowRight':
      case 'ArrowUp':
        e.preventDefault()
        if (currentIndex < sortedYears.length - 1) {
          onYearChange(sortedYears[currentIndex + 1])
        }
        break

      case 'Home':
        e.preventDefault()
        onYearChange(sortedYears[0])
        break

      case 'End':
        e.preventDefault()
        onYearChange(sortedYears[sortedYears.length - 1])
        break
    }
  }, [selectedYear, sortedYears, onYearChange])

  // Calculate activity color based on density
  const getActivityColor = (count: number): string => {
    if (!count || count === 0) return 'rgb(235, 237, 240)' // gray

    const normalized = count / maxActivity

    if (normalized <= 0.2) return 'rgb(191, 219, 254)' // light blue
    if (normalized <= 0.4) return 'rgb(96, 165, 250)'  // medium blue
    if (normalized <= 0.6) return 'rgb(37, 99, 235)'   // dark blue
    return 'rgb(30, 64, 175)' // darkest blue
  }

  // Calculate activity height (normalized 0-100%)
  const getActivityHeight = (count: number): number => {
    if (!count || count === 0 || maxActivity === 0) return 0
    return Math.min((count / maxActivity) * 100, 100)
  }

  // Cleanup debounce on unmount
  React.useEffect(() => {
    return () => {
      if (debouncedChangeRef.current) {
        clearTimeout(debouncedChangeRef.current)
      }
    }
  }, [])

  // Edge case: Single year or no years
  if (sortedYears.length === 0) {
    return (
      <div className={cn("text-sm text-muted-foreground", className)}>
        No year data available
      </div>
    )
  }

  if (sortedYears.length === 1) {
    return (
      <div className={cn("text-sm font-medium", className)}>
        {sortedYears[0]}
      </div>
    )
  }

  const activityCount = activityData?.[selectedYear] || 0
  const activityLabel = activityCount > 0
    ? `${activityCount} flight${activityCount !== 1 ? 's' : ''}`
    : 'No flights'

  return (
    <div className={cn("w-full space-y-3", className)}>
      {/* Year Markers */}
      <div className="relative px-2">
        <div className="flex justify-between text-xs text-muted-foreground">
          {yearMarks.map((year) => {
            const isSelected = year === selectedYear
            return (
              <button
                key={year}
                onClick={() => onYearChange(year)}
                className={cn(
                  "transition-all duration-300 hover:text-foreground hover:font-semibold cursor-pointer",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded px-1",
                  isSelected && "text-primary font-bold text-sm"
                )}
                aria-label={`Jump to year ${year}`}
              >
                {year}
              </button>
            )
          })}
        </div>
      </div>

      {/* Slider with Activity Indicators */}
      <div className="relative px-2 mb-8">
        {/* Activity Density Bars */}
        {activityData && (
          <div className="absolute top-full mt-2 left-2 right-2 h-4 flex items-end gap-[2px]">
            {sortedYears.map((year) => {
              const count = activityData[year] || 0
              const height = getActivityHeight(count)
              const color = getActivityColor(count)

              return (
                <div
                  key={year}
                  className="flex-1 transition-all duration-300 rounded-sm min-w-[2px] cursor-pointer hover:opacity-80"
                  style={{
                    height: `${height}%`,
                    backgroundColor: color,
                    minHeight: count > 0 ? '2px' : '0'
                  }}
                  onClick={() => onYearChange(year)}
                  title={`${year}: ${count} flight${count !== 1 ? 's' : ''}`}
                />
              )
            })}
          </div>
        )}

        {/* Slider Component */}
        <div onKeyDown={handleKeyDown}>
          <Slider
            value={[selectedYear]}
            onValueChange={handleValueChange}
            onValueCommit={handleValueCommit}
            min={minYear}
            max={maxYear}
            step={1}
            className="cursor-pointer"
            aria-label="Year selection slider"
            aria-valuemin={minYear}
            aria-valuemax={maxYear}
            aria-valuenow={selectedYear}
            aria-valuetext={`Year ${selectedYear}, ${activityLabel}`}
          />
        </div>
      </div>

      {/* Selected Year Display with Activity Count */}
      <div className="flex items-center justify-center gap-2 text-sm">
        <span className="font-semibold text-foreground">
          {selectedYear}
        </span>
        {activityData && (
          <span className="text-muted-foreground">
            ({activityLabel})
          </span>
        )}
      </div>

      {/* Mobile/Screen Reader Instructions */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        Year {selectedYear} selected. {activityLabel} this year.
        Use arrow keys to navigate between years, Home for first year, End for last year.
      </div>
    </div>
  )
})

YearSlider.displayName = 'YearSlider'
