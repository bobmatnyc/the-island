import { useEffect, useState } from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Calendar, AlertCircle, Download, TrendingUp, Filter } from 'lucide-react'

interface TimelineMention {
  month: string
  documents: number
  flights: number
  news: number
  total: number
}

interface TimelineMentionsData {
  timeline: TimelineMention[]
  entity: string | null
  date_range: {
    start: string
    end: string
  }
  total_mentions: number
  data_sources: {
    documents: boolean
    flights: boolean
    news: boolean
  }
}

interface Entity {
  id: string
  name: string
}

export function TimelineMentions() {
  const [data, setData] = useState<TimelineMentionsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [entities, setEntities] = useState<Entity[]>([])
  const [selectedEntity, setSelectedEntity] = useState<string>('__ALL__')
  const [startDate, setStartDate] = useState<string>('')
  const [endDate, setEndDate] = useState<string>('')
  const [filterApplied, setFilterApplied] = useState(false)

  // Fetch available entities for the filter
  useEffect(() => {
    fetchEntities()
  }, [])

  // Fetch timeline data when component mounts or filters change
  useEffect(() => {
    if (filterApplied || (selectedEntity === '__ALL__' && !startDate && !endDate)) {
      fetchTimelineData()
    }
  }, [filterApplied])

  const fetchEntities = async () => {
    try {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081'
      const response = await fetch(`${API_BASE_URL}/api/entities`)
      if (!response.ok) throw new Error('Failed to fetch entities')
      const entitiesData = await response.json()

      // Extract top entities by mention count
      const topEntities = Object.entries(entitiesData)
        .map(([id, entity]: [string, any]) => ({
          id,
          name: entity.name || id,
          mentions: entity.total_mentions || 0,
        }))
        .sort((a, b) => b.mentions - a.mentions)
        .slice(0, 50) // Top 50 entities
        .map(({ id, name }) => ({ id, name }))

      setEntities(topEntities)
    } catch (err) {
      console.error('Error fetching entities:', err)
      // Continue without entity filter if fetch fails
    }
  }

  const fetchTimelineData = async () => {
    try {
      setLoading(true)
      setError(null)

      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081'
      const params = new URLSearchParams()

      if (selectedEntity && selectedEntity !== '__ALL__') params.append('entity_id', selectedEntity)
      if (startDate) params.append('start_date', startDate)
      if (endDate) params.append('end_date', endDate)

      const queryString = params.toString()
      const url = `${API_BASE_URL}/api/v2/analytics/timeline-mentions${queryString ? `?${queryString}` : ''}`

      const response = await fetch(url)
      if (!response.ok) throw new Error('Failed to fetch timeline mentions')

      const timelineData = await response.json()
      setData(timelineData)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load timeline data')
      console.error('Error fetching timeline mentions:', err)
    } finally {
      setLoading(false)
      setFilterApplied(false)
    }
  }

  const applyFilters = () => {
    setFilterApplied(true)
  }

  const clearFilters = () => {
    setSelectedEntity('')
    setStartDate('')
    setEndDate('')
    setFilterApplied(true)
  }

  const exportData = (format: 'json' | 'csv') => {
    if (!data) return

    try {
      if (format === 'json') {
        const dataStr = JSON.stringify(data, null, 2)
        const dataBlob = new Blob([dataStr], { type: 'application/json' })
        const url = URL.createObjectURL(dataBlob)
        const link = document.createElement('a')
        link.href = url
        link.download = `timeline-mentions-${new Date().toISOString().split('T')[0]}.json`
        link.click()
        URL.revokeObjectURL(url)
      } else {
        // CSV export
        const csvData = [
          ['Month', 'Documents', 'Flights', 'News', 'Total'],
          ...data.timeline.map((item) => [
            item.month,
            item.documents,
            item.flights,
            item.news,
            item.total,
          ]),
        ]
          .map((row) => row.join(','))
          .join('\n')

        const csvBlob = new Blob([csvData], { type: 'text/csv' })
        const url = URL.createObjectURL(csvBlob)
        const link = document.createElement('a')
        link.href = url
        link.download = `timeline-mentions-${new Date().toISOString().split('T')[0]}.csv`
        link.click()
        URL.revokeObjectURL(url)
      }
    } catch (err) {
      console.error('Error exporting data:', err)
    }
  }

  // Format month for display (YYYY-MM -> Month Year)
  const formatMonth = (monthKey: string) => {
    const [year, month] = monthKey.split('-')
    const date = new Date(parseInt(year), parseInt(month) - 1)
    return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
  }

  // Custom tooltip for the chart
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const total = payload.reduce((sum: number, entry: any) => sum + entry.value, 0)
      return (
        <div className="bg-background border border-border p-4 rounded-lg shadow-lg">
          <p className="font-semibold mb-2">{formatMonth(label)}</p>
          <div className="space-y-1 text-sm">
            {payload.map((entry: any, index: number) => (
              <div key={index} className="flex items-center justify-between gap-4">
                <span className="flex items-center gap-2">
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: entry.color }}
                  />
                  {entry.name}:
                </span>
                <span className="font-medium">{entry.value}</span>
              </div>
            ))}
            <div className="pt-2 mt-2 border-t border-border font-semibold flex justify-between">
              <span>Total:</span>
              <span>{total}</span>
            </div>
          </div>
        </div>
      )
    }
    return null
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-8 w-64 mb-2" />
          <Skeleton className="h-4 w-96" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-96 w-full" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Timeline Mentions</CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  if (!data) return null

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Timeline Mentions
            </CardTitle>
            <CardDescription>
              Entity mentions over time across all data sources
              {data.entity && ` - Filtered by: ${data.entity}`}
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => exportData('csv')}>
              <Download className="h-4 w-4 mr-2" />
              CSV
            </Button>
            <Button variant="outline" size="sm" onClick={() => exportData('json')}>
              <Download className="h-4 w-4 mr-2" />
              JSON
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-muted/50 rounded-lg">
          <div className="space-y-2">
            <Label htmlFor="entity-filter">Filter by Entity</Label>
            <Select value={selectedEntity} onValueChange={setSelectedEntity}>
              <SelectTrigger id="entity-filter">
                <SelectValue placeholder="All entities" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__ALL__">All entities</SelectItem>
                {entities.map((entity) => (
                  <SelectItem key={entity.id} value={entity.id}>
                    {entity.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="start-date">Start Date</Label>
            <Input
              id="start-date"
              type="month"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              placeholder="YYYY-MM"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="end-date">End Date</Label>
            <Input
              id="end-date"
              type="month"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              placeholder="YYYY-MM"
            />
          </div>

          <div className="space-y-2">
            <Label>&nbsp;</Label>
            <div className="flex gap-2">
              <Button onClick={applyFilters} className="flex-1">
                <Filter className="h-4 w-4 mr-2" />
                Apply
              </Button>
              <Button variant="outline" onClick={clearFilters}>
                Clear
              </Button>
            </div>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 bg-muted/50 rounded-lg">
            <p className="text-sm text-muted-foreground mb-1">Total Mentions</p>
            <p className="text-2xl font-bold">{data.total_mentions.toLocaleString()}</p>
          </div>
          <div className="p-4 bg-muted/50 rounded-lg">
            <p className="text-sm text-muted-foreground mb-1">Time Range</p>
            <p className="text-lg font-semibold">
              {data.date_range.start && data.date_range.end
                ? `${data.timeline.length} months`
                : 'N/A'}
            </p>
          </div>
          <div className="p-4 bg-muted/50 rounded-lg">
            <p className="text-sm text-muted-foreground mb-1">Peak Month</p>
            <p className="text-lg font-semibold">
              {data.timeline.length > 0
                ? formatMonth(
                    [...data.timeline].sort((a, b) => b.total - a.total)[0].month
                  )
                : 'N/A'}
            </p>
          </div>
          <div className="p-4 bg-muted/50 rounded-lg">
            <p className="text-sm text-muted-foreground mb-1">Data Sources</p>
            <div className="flex gap-2 mt-1">
              {data.data_sources.documents && (
                <Badge variant="secondary" className="text-xs">
                  Docs
                </Badge>
              )}
              {data.data_sources.flights && (
                <Badge variant="secondary" className="text-xs">
                  Flights
                </Badge>
              )}
              {data.data_sources.news && (
                <Badge variant="secondary" className="text-xs">
                  News
                </Badge>
              )}
            </div>
          </div>
        </div>

        {/* Chart */}
        {data.timeline.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart
              data={data.timeline}
              margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="colorDocuments" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1} />
                </linearGradient>
                <linearGradient id="colorFlights" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1} />
                </linearGradient>
                <linearGradient id="colorNews" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="month"
                tickFormatter={formatMonth}
                tick={{ fontSize: 12 }}
                interval="preserveStartEnd"
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ paddingTop: '20px' }} />
              <Area
                type="monotone"
                dataKey="documents"
                stackId="1"
                stroke="#3b82f6"
                fill="url(#colorDocuments)"
                name="Documents"
              />
              <Area
                type="monotone"
                dataKey="flights"
                stackId="1"
                stroke="#ef4444"
                fill="url(#colorFlights)"
                name="Flights"
              />
              <Area
                type="monotone"
                dataKey="news"
                stackId="1"
                stroke="#10b981"
                fill="url(#colorNews)"
                name="News"
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <Alert>
            <Calendar className="h-4 w-4" />
            <AlertTitle>No Data</AlertTitle>
            <AlertDescription>
              No mentions found for the selected filters. Try adjusting your filter criteria.
            </AlertDescription>
          </Alert>
        )}

        {/* Color Legend */}
        <div className="flex flex-wrap gap-6 justify-center pt-4 border-t border-border">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-blue-500" />
            <span className="text-sm text-muted-foreground">
              Documents (court filings, depositions)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-red-500" />
            <span className="text-sm text-muted-foreground">
              Flights (passenger mentions)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-green-500" />
            <span className="text-sm text-muted-foreground">
              News (article mentions)
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
