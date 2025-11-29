import { useEffect, useState } from 'react'
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  FileText,
  Users,
  Plane,
  Network,
  Calendar,
  Download,
  AlertCircle,
  BarChart3,
  PieChart as PieChartIcon,
  TrendingUp,
  Globe,
} from 'lucide-react'
import { TimelineMentions } from '@/components/visualizations/TimelineMentions'

interface UnifiedStats {
  status: string
  timestamp: string
  data: {
    documents: {
      total: number
      court_documents: number
      sources: number
    } | null
    timeline: {
      total_events: number
      date_range: {
        earliest: string
        latest: string
      }
    } | null
    entities: {
      total: number
      with_biographies: number
      types: {
        person: number
        organization: number
      }
    } | null
    flights: {
      total: number
      date_range: {
        earliest: string
        latest: string
      }
      unique_passengers: number
    } | null
    news: {
      total_articles: number
      sources: number
      date_range: {
        earliest: string
        latest: string
      }
    } | null
    network: {
      nodes: number
      edges: number
      avg_degree: number
    } | null
    vector_store: {
      total_documents: number
      court_documents: number
      news_articles: number
      collection: string
    } | null
  }
}

interface ChartDataItem {
  name: string
  value: number
  color?: string
  [key: string]: string | number | undefined
}

export function Analytics() {
  const [stats, setStats] = useState<UnifiedStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      setLoading(true)
      setError(null)
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081'
      const response = await fetch(`${API_BASE_URL}/api/v2/stats`)
      if (!response.ok) throw new Error('Failed to fetch stats')
      const data = await response.json()
      setStats(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics data')
      console.error('Error fetching analytics:', err)
    } finally {
      setLoading(false)
    }
  }

  const exportData = (format: 'json' | 'csv') => {
    if (!stats) return

    setExporting(true)
    try {
      if (format === 'json') {
        const dataStr = JSON.stringify(stats, null, 2)
        const dataBlob = new Blob([dataStr], { type: 'application/json' })
        const url = URL.createObjectURL(dataBlob)
        const link = document.createElement('a')
        link.href = url
        link.download = `epstein-analytics-${new Date().toISOString().split('T')[0]}.json`
        link.click()
        URL.revokeObjectURL(url)
      } else {
        // CSV export
        const csvData = [
          ['Metric', 'Category', 'Value'],
          ['Total Documents', 'Documents', stats.data.documents?.total || 0],
          ['Court Documents', 'Documents', stats.data.documents?.court_documents || 0],
          ['Document Sources', 'Documents', stats.data.documents?.sources || 0],
          ['Total Entities', 'Entities', stats.data.entities?.total || 0],
          ['Entities with Biographies', 'Entities', stats.data.entities?.with_biographies || 0],
          ['Person Entities', 'Entities', stats.data.entities?.types.person || 0],
          ['Organization Entities', 'Entities', stats.data.entities?.types.organization || 0],
          ['Total Flights', 'Flights', stats.data.flights?.total || 0],
          ['Unique Passengers', 'Flights', stats.data.flights?.unique_passengers || 0],
          ['Timeline Events', 'Timeline', stats.data.timeline?.total_events || 0],
          ['News Articles', 'News', stats.data.news?.total_articles || 0],
          ['News Sources', 'News', stats.data.news?.sources || 0],
          ['Network Nodes', 'Network', stats.data.network?.nodes || 0],
          ['Network Edges', 'Network', stats.data.network?.edges || 0],
          ['Average Connections', 'Network', stats.data.network?.avg_degree || 0],
        ]
          .map((row) => row.join(','))
          .join('\n')

        const csvBlob = new Blob([csvData], { type: 'text/csv' })
        const url = URL.createObjectURL(csvBlob)
        const link = document.createElement('a')
        link.href = url
        link.download = `epstein-analytics-${new Date().toISOString().split('T')[0]}.csv`
        link.click()
        URL.revokeObjectURL(url)
      }
    } catch (err) {
      console.error('Error exporting data:', err)
    } finally {
      setExporting(false)
    }
  }

  // Prepare chart data
  const getEntityTypeData = (): ChartDataItem[] => {
    if (!stats?.data.entities) return []
    return [
      {
        name: 'People',
        value: stats.data.entities.types.person,
        color: '#3b82f6',
      },
      {
        name: 'Organizations',
        value: stats.data.entities.types.organization,
        color: '#10b981',
      },
    ]
  }

  const getDocumentDistribution = () => {
    if (!stats?.data.vector_store) return []
    return [
      { name: 'Court Documents', value: stats.data.vector_store.court_documents, color: '#3b82f6' },
      { name: 'News Articles', value: stats.data.vector_store.news_articles, color: '#10b981' },
    ]
  }

  const getNetworkMetrics = () => {
    if (!stats?.data.network) return []
    return [
      { name: 'Nodes', value: stats.data.network.nodes },
      { name: 'Edges', value: stats.data.network.edges },
      { name: 'Avg Connections', value: Math.round(stats.data.network.avg_degree) },
    ]
  }

  const getDataCoverage = () => {
    if (!stats?.data.entities) return []
    const total = stats.data.entities.total
    const withBios = stats.data.entities.with_biographies
    const withoutBios = total - withBios
    return [
      { name: 'With Biographies', value: withBios, color: '#10b981' },
      { name: 'Without Biographies', value: withoutBios, color: '#6b7280' },
    ]
  }

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="flex justify-between items-center">
          <div>
            <Skeleton className="h-10 w-64 mb-2" />
            <Skeleton className="h-6 w-96" />
          </div>
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    )
  }

  if (!stats) return null

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2">Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Comprehensive metrics and insights across all data sources
          </p>
        </div>

        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => exportData('csv')}
            disabled={exporting}
          >
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => exportData('json')}
            disabled={exporting}
          >
            <Download className="h-4 w-4 mr-2" />
            Export JSON
          </Button>
        </div>
      </div>

      {/* Status Badge */}
      {stats.status !== 'success' && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Partial Data</AlertTitle>
          <AlertDescription>
            Some data sources are unavailable. Displaying available metrics.
          </AlertDescription>
        </Alert>
      )}

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Entities */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Entities</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.data.entities?.total.toLocaleString() || 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats.data.entities?.with_biographies || 0} with biographies
            </p>
          </CardContent>
        </Card>

        {/* Total Flights */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Flight Logs</CardTitle>
            <Plane className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.data.flights?.total.toLocaleString() || 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats.data.flights?.unique_passengers || 0} unique passengers
            </p>
          </CardContent>
        </Card>

        {/* Total Documents */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Documents</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.data.documents?.total.toLocaleString() || 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats.data.documents?.sources || 0} sources
            </p>
          </CardContent>
        </Card>

        {/* Network Connections */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Network Size</CardTitle>
            <Network className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.data.network?.nodes.toLocaleString() || 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats.data.network?.edges.toLocaleString() || 0} connections
            </p>
          </CardContent>
        </Card>

        {/* Timeline Events */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Timeline Events</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.data.timeline?.total_events.toLocaleString() || 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Documented events</p>
          </CardContent>
        </Card>

        {/* News Articles */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">News Coverage</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.data.news?.total_articles.toLocaleString() || 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats.data.news?.sources || 0} publications
            </p>
          </CardContent>
        </Card>

        {/* Vector Store */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Vector Store</CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.data.vector_store?.total_documents.toLocaleString() || 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Embedded documents</p>
          </CardContent>
        </Card>

        {/* Avg Network Degree */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Connections</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.data.network?.avg_degree.toFixed(1) || 'N/A'}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Per entity</p>
          </CardContent>
        </Card>
      </div>

      {/* Visualization Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Entity Types Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChartIcon className="h-5 w-5" />
              Entity Type Distribution
            </CardTitle>
            <CardDescription>Breakdown by entity classification</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={getEntityTypeData()}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {getEntityTypeData().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Document Type Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Document Type Distribution
            </CardTitle>
            <CardDescription>Vector store content breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={getDocumentDistribution()}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {getDocumentDistribution().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Network Metrics */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Network className="h-5 w-5" />
              Network Graph Metrics
            </CardTitle>
            <CardDescription>Connection statistics</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={getNetworkMetrics()}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Entity Biography Coverage */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Entity Biography Coverage
            </CardTitle>
            <CardDescription>Data completeness metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={getDataCoverage()}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {getDataCoverage().map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Timeline Mentions Visualization */}
      <TimelineMentions />

      {/* Date Ranges Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Data Coverage Timeline
          </CardTitle>
          <CardDescription>Date ranges for different data sources</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {stats.data.flights?.date_range && (
              <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
                <div className="flex items-center gap-3">
                  <Plane className="h-5 w-5 text-primary" />
                  <div>
                    <p className="font-semibold">Flight Logs</p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(stats.data.flights.date_range.earliest).toLocaleDateString()} -{' '}
                      {new Date(stats.data.flights.date_range.latest).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <Badge variant="secondary">{stats.data.flights.total} flights</Badge>
              </div>
            )}

            {stats.data.timeline?.date_range && (
              <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
                <div className="flex items-center gap-3">
                  <Calendar className="h-5 w-5 text-primary" />
                  <div>
                    <p className="font-semibold">Timeline Events</p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(stats.data.timeline.date_range.earliest).toLocaleDateString()} -{' '}
                      {new Date(stats.data.timeline.date_range.latest).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <Badge variant="secondary">{stats.data.timeline.total_events} events</Badge>
              </div>
            )}

            {stats.data.news?.date_range && (
              <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
                <div className="flex items-center gap-3">
                  <Globe className="h-5 w-5 text-primary" />
                  <div>
                    <p className="font-semibold">News Articles</p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(stats.data.news.date_range.earliest).toLocaleDateString()} -{' '}
                      {new Date(stats.data.news.date_range.latest).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <Badge variant="secondary">{stats.data.news.total_articles} articles</Badge>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Metadata Footer */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 text-sm text-muted-foreground">
            <div>
              <p>
                Last updated:{' '}
                {new Date(stats.timestamp).toLocaleString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
              <p className="mt-1">Status: {stats.status}</p>
            </div>
            <Button variant="outline" size="sm" onClick={fetchStats}>
              Refresh Data
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
