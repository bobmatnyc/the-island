import { useState, useEffect } from 'react'
import { CalendarHeatmap } from '@/components/visualizations/CalendarHeatmap'
import { YearSlider } from '@/components/visualizations/YearSlider'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'

export function Activity() {
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear())
  const [entityFilter, setEntityFilter] = useState('')
  const [availableYears, setAvailableYears] = useState<number[]>([])
  const [activityData, setActivityData] = useState<Record<number, number>>({})

  useEffect(() => {
    // Fetch available years and activity data from flight data
    const fetchYears = async () => {
      try {
        const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081'
        const response = await fetch(`${API_BASE_URL}/api/flights/all`)
        const data = await response.json()

        const years = new Set<number>()
        const yearFlightCounts: Record<number, number> = {}

        data.routes?.forEach((route: any) => {
          route.flights?.forEach((flight: any) => {
            // Parse year from date (handle both formats)
            let yearStr: string
            if (flight.date.includes('/')) {
              yearStr = flight.date.split('/')[2]
            } else {
              yearStr = flight.date.split('-')[0]
            }
            const year = parseInt(yearStr)
            years.add(year)

            // Count flights per year for activity visualization
            yearFlightCounts[year] = (yearFlightCounts[year] || 0) + 1
          })
        })

        const sortedYears = Array.from(years).sort((a, b) => b - a)
        setAvailableYears(sortedYears)
        setActivityData(yearFlightCounts)

        // Set to most recent year with data
        if (sortedYears.length > 0) {
          setSelectedYear(sortedYears[0])
        }
      } catch (err) {
        console.error('Failed to fetch years:', err)
        // Default years if fetch fails
        const defaultYears = Array.from(
          { length: 31 },
          (_, i) => new Date().getFullYear() - i
        )
        setAvailableYears(defaultYears)
      }
    }

    fetchYears()
  }, [])

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">Flight Activity Calendar</h1>
            <p className="text-muted-foreground">
              Visualize flight frequency patterns over time
            </p>
          </div>

          {/* Entity Filter - moved to top right */}
          <div className="flex items-center gap-4">
            <div className="min-w-[200px]">
              <Input
                placeholder="Filter by passenger name..."
                value={entityFilter}
                onChange={(e) => setEntityFilter(e.target.value)}
                className="w-full"
              />
            </div>

            {entityFilter && (
              <Badge
                variant="secondary"
                className="cursor-pointer"
                onClick={() => setEntityFilter('')}
              >
                Clear filter
              </Badge>
            )}
          </div>
        </div>

        {/* Year Timeline Scrubber - Full width below header */}
        <Card className="bg-muted/50">
          <CardContent className="pt-6 pb-8">
            <YearSlider
              years={availableYears}
              selectedYear={selectedYear}
              onYearChange={setSelectedYear}
              activityData={activityData}
            />
          </CardContent>
        </Card>
      </div>

      {/* Info Card */}
      <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <div className="text-blue-600 dark:text-blue-400">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="text-sm text-blue-900 dark:text-blue-100">
              <strong>How to use:</strong> Hover over any cell to see flight details for that day.
              Use the year selector to switch between years, or filter by passenger name to see
              specific travel patterns.
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Heatmap */}
      <Card>
        <CardHeader>
          <CardTitle>
            {selectedYear} Activity Heatmap
            {entityFilter && (
              <span className="text-base font-normal text-muted-foreground ml-2">
                (filtered by "{entityFilter}")
              </span>
            )}
          </CardTitle>
          <CardDescription>
            Each cell represents a day. Color intensity indicates flight frequency.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CalendarHeatmap
            year={selectedYear}
            entityFilter={entityFilter}
            minFlights={1}
          />
        </CardContent>
      </Card>

      {/* Additional Info */}
      <Card>
        <CardHeader>
          <CardTitle>About this Visualization</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm text-muted-foreground">
          <p>
            This calendar heatmap shows flight activity across the year, inspired by GitHub's
            contribution graph. Each cell represents one day, with color intensity indicating
            the number of flights on that date.
          </p>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-semibold text-foreground mb-2">Color Scale</h4>
              <ul className="space-y-1">
                <li>• Gray: No flights</li>
                <li>• Light Blue (1-2 flights): Minimal activity</li>
                <li>• Medium Blue (3-5 flights): Moderate activity</li>
                <li>• Dark Blue (6-10 flights): High activity</li>
                <li>• Darkest Blue (11+ flights): Very high activity</li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-foreground mb-2">Features</h4>
              <ul className="space-y-1">
                <li>• View any year from 1995-present</li>
                <li>• Filter by passenger name</li>
                <li>• Interactive tooltips with flight details</li>
                <li>• Statistics panel showing key metrics</li>
                <li>• Identify travel patterns and peak activity periods</li>
              </ul>
            </div>
          </div>

          <p className="text-xs">
            Data source: Flight logs from the Epstein Archive ({availableYears.length} years of data available)
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
