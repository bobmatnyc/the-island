import { useState, useEffect, useMemo } from 'react'
import HeatMap from '@uiw/react-heat-map'
import { format, parseISO, startOfYear, endOfYear, eachDayOfInterval } from 'date-fns'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface FlightData {
  date: string
  count: number
  passengers: string[]
  flights: Array<{
    id: string
    aircraft: string
    route: string
  }>
}

interface CalendarHeatmapProps {
  year?: number
  entityFilter?: string
  minFlights?: number
}

interface HeatMapValue {
  date: string
  count: number
  content?: string
}

export function CalendarHeatmap({
  year = new Date().getFullYear(),
  entityFilter,
  minFlights = 1
}: CalendarHeatmapProps) {
  const [flightData, setFlightData] = useState<Record<string, FlightData>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [hoveredDate, setHoveredDate] = useState<FlightData | null>(null)
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })

  useEffect(() => {
    const fetchFlightData = async () => {
      setLoading(true)
      setError(null)

      try {
        const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081'
        const response = await fetch(`${API_BASE_URL}/api/flights/all`)
        if (!response.ok) {
          throw new Error(`Failed to fetch flight data: ${response.status} ${response.statusText}`)
        }

        const data = await response.json()
        const dateMap: Record<string, FlightData> = {}

        // Transform flight data into date → count map
        data.routes?.forEach((route: any) => {
          route.flights?.forEach((flight: any) => {
            // Parse date (handle both MM/DD/YYYY and YYYY-MM-DD formats)
            let dateStr: string
            if (flight.date.includes('/')) {
              const [month, day, yearPart] = flight.date.split('/')
              dateStr = `${yearPart}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`
            } else {
              dateStr = flight.date
            }

            // Filter by entity if specified
            if (entityFilter) {
              const hasEntity = flight.passengers?.some((p: string) =>
                p.toLowerCase().includes(entityFilter.toLowerCase())
              )
              if (!hasEntity) return
            }

            // Filter by year
            const flightYear = parseInt(dateStr.split('-')[0])
            if (flightYear !== year) return

            if (!dateMap[dateStr]) {
              dateMap[dateStr] = {
                date: dateStr,
                count: 0,
                passengers: [],
                flights: []
              }
            }

            dateMap[dateStr].count++

            // Add unique passengers
            flight.passengers?.forEach((p: string) => {
              if (p && !dateMap[dateStr].passengers.includes(p)) {
                dateMap[dateStr].passengers.push(p)
              }
            })

            // Add flight details
            dateMap[dateStr].flights.push({
              id: flight.id || `${dateStr}_${flight.aircraft}`,
              aircraft: flight.aircraft || 'Unknown',
              route: `${route.origin?.code || '?'}-${route.destination?.code || '?'}`
            })
          })
        })

        setFlightData(dateMap)
        console.log(`CalendarHeatmap: Loaded ${Object.keys(dateMap).length} days of flight data for year ${year}`)
        if (Object.keys(dateMap).length > 0) {
          console.log('Sample dates:', Object.keys(dateMap).slice(0, 5))
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
        console.error('CalendarHeatmap error:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchFlightData()
  }, [year, entityFilter])

  // Convert to HeatMap format
  const heatmapData: HeatMapValue[] = useMemo(() => {
    const startDate = startOfYear(new Date(year, 0, 1))
    const endDate = endOfYear(new Date(year, 11, 31))
    const allDates = eachDayOfInterval({ start: startDate, end: endDate })

    return allDates.map(date => {
      const dateStr = format(date, 'yyyy-MM-dd')
      const dayData = flightData[dateStr]
      const count = dayData?.count || 0

      return {
        date: dateStr,
        count: count >= minFlights ? count : 0,
        content: count > 0 ? `${count} flight${count > 1 ? 's' : ''}` : ''
      }
    })
  }, [flightData, year, minFlights])

  // Calculate statistics
  const stats = useMemo(() => {
    const values = Object.values(flightData)
    const totalFlights = values.reduce((sum, d) => sum + d.count, 0)
    const activeDays = values.length

    const mostActiveDay = values.reduce((max, curr) =>
      curr.count > max.count ? curr : max
    , { date: '', count: 0, passengers: [], flights: [] })

    // Find busiest month
    const monthCounts: Record<string, number> = {}
    values.forEach(d => {
      const month = d.date.substring(0, 7) // YYYY-MM
      monthCounts[month] = (monthCounts[month] || 0) + d.count
    })

    const busiestMonth = Object.entries(monthCounts).reduce(
      (max, [month, count]) => count > max.count ? { month, count } : max,
      { month: '', count: 0 }
    )

    return {
      totalFlights,
      activeDays,
      mostActiveDay,
      busiestMonth
    }
  }, [flightData])

  // Color scale based on flight frequency
  const getColor = (count: number) => {
    if (count === 0) return 'rgb(235, 237, 240)' // bg-muted
    if (count <= 2) return 'rgb(191, 219, 254)' // bg-blue-200
    if (count <= 5) return 'rgb(96, 165, 250)' // bg-blue-400
    if (count <= 10) return 'rgb(37, 99, 235)' // bg-blue-600
    return 'rgb(30, 64, 175)' // bg-blue-800
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    setMousePosition({ x: e.clientX, y: e.clientY })
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <div className="animate-pulse">Loading flight data...</div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-red-500">
          Error: {error}
        </CardContent>
      </Card>
    )
  }

  const hasAnyData = Object.keys(flightData).length > 0

  return (
    <div className="space-y-6">
      {/* No Data Warning */}
      {!hasAnyData && (
        <Card className="bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <div className="text-yellow-600 dark:text-yellow-400">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="text-sm text-yellow-900 dark:text-yellow-100">
                <strong>No flight data for {year}</strong> - Flight records are available for 1995-2006.
                Please select a different year using the slider above.
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Statistics Panel */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats.totalFlights}</div>
            <div className="text-sm text-muted-foreground">Total Flights</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats.activeDays}</div>
            <div className="text-sm text-muted-foreground">Active Days</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats.mostActiveDay.count}</div>
            <div className="text-sm text-muted-foreground">
              Most Active Day
              {stats.mostActiveDay.date && (
                <div className="text-xs mt-1">
                  {format(parseISO(stats.mostActiveDay.date), 'MMM d, yyyy')}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="text-2xl font-bold">{stats.busiestMonth.count}</div>
            <div className="text-sm text-muted-foreground">
              Busiest Month
              {stats.busiestMonth.month && (
                <div className="text-xs mt-1">
                  {format(parseISO(`${stats.busiestMonth.month}-01`), 'MMMM yyyy')}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Heatmap */}
      <Card>
        <CardContent className="pt-6">
          <div
            className="overflow-x-auto"
            onMouseMove={handleMouseMove}
          >
            <HeatMap
              value={heatmapData}
              startDate={new Date(year, 0, 1)}
              endDate={new Date(year, 11, 31)}
              rectSize={14}
              legendCellSize={0}
              space={3}
              style={{ width: '100%' }}
              rectRender={(props, data) => {
                const dayData = flightData[data.date]
                const tooltipData = dayData || {
                  date: data.date,
                  count: 0,
                  passengers: [],
                  flights: []
                }
                return (
                  <rect
                    {...props}
                    fill={getColor(data.count || 0)}
                    onMouseEnter={() => setHoveredDate(tooltipData)}
                    onMouseLeave={() => setHoveredDate(null)}
                    className="transition-opacity hover:opacity-80 cursor-pointer"
                    style={{ cursor: dayData ? 'pointer' : 'default' }}
                  />
                )
              }}
            />
          </div>

          {/* Legend */}
          <div className="flex items-center justify-end gap-2 mt-4 text-sm">
            <span className="text-muted-foreground">Less</span>
            <div className="flex gap-1">
              <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgb(235, 237, 240)' }} />
              <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgb(191, 219, 254)' }} />
              <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgb(96, 165, 250)' }} />
              <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgb(37, 99, 235)' }} />
              <div className="w-4 h-4 rounded" style={{ backgroundColor: 'rgb(30, 64, 175)' }} />
            </div>
            <span className="text-muted-foreground">More</span>
          </div>
        </CardContent>
      </Card>

      {/* Tooltip */}
      {hoveredDate && hoveredDate.date && (
        <div
          className="fixed z-[9999] bg-popover text-popover-foreground rounded-lg shadow-lg border border-border p-3 max-w-sm pointer-events-none"
          style={{
            left: mousePosition.x + 10,
            top: mousePosition.y + 10,
          }}
        >
          <div className="font-semibold mb-2">
            {(() => {
              try {
                return format(parseISO(hoveredDate.date), 'EEEE, MMMM d, yyyy')
              } catch {
                return hoveredDate.date
              }
            })()}
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant={hoveredDate.count > 0 ? "default" : "secondary"}>
                {hoveredDate.count} flight{hoveredDate.count !== 1 ? 's' : ''}
              </Badge>
              {hoveredDate.count > 0 && (
                <span className="text-sm text-muted-foreground">
                  {hoveredDate.passengers.length} passenger{hoveredDate.passengers.length !== 1 ? 's' : ''}
                </span>
              )}
            </div>

            {hoveredDate.count === 0 && (
              <div className="text-sm text-muted-foreground italic">
                No flights on this date
              </div>
            )}

            {hoveredDate.flights.length > 0 && (
              <div className="text-xs space-y-1">
                <div className="font-medium">Routes:</div>
                {hoveredDate.flights.slice(0, 3).map((flight, idx) => (
                  <div key={idx} className="text-muted-foreground">
                    {flight.route} ({flight.aircraft})
                  </div>
                ))}
                {hoveredDate.flights.length > 3 && (
                  <div className="text-muted-foreground">
                    +{hoveredDate.flights.length - 3} more
                  </div>
                )}
              </div>
            )}

            {hoveredDate.passengers.length > 0 && (
              <div className="text-xs">
                <div className="font-medium">Passengers:</div>
                <div className="text-muted-foreground">
                  {hoveredDate.passengers.slice(0, 5).join(', ')}
                  {hoveredDate.passengers.length > 5 && `, +${hoveredDate.passengers.length - 5} more`}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
