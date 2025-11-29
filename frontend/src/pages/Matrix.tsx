import { useState, useEffect } from 'react'
import { AdjacencyMatrix } from '@/components/visualizations/AdjacencyMatrix'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'

interface NetworkNode {
  id: string
  name: string
  connection_count: number
  categories?: string[]
}

interface NetworkEdge {
  source: string
  target: string
  weight: number
}

interface NetworkData {
  nodes: NetworkNode[]
  edges: NetworkEdge[]
}

export function Matrix() {
  const [data, setData] = useState<NetworkData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filter/sort controls
  const [topN, setTopN] = useState(30)
  const [minConnections, setMinConnections] = useState(0)
  const [sortBy, setSortBy] = useState<'connections' | 'name' | 'alphabetical'>('connections')

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081'
        const response = await fetch(`${API_BASE_URL}/api/network`)

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const networkData = await response.json()
        setData(networkData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load network data')
        console.error('Error fetching network data:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  // Calculate statistics
  const stats = data
    ? {
        totalEntities: data.nodes.length,
        displayedEntities: Math.min(
          topN,
          data.nodes.filter((n) => n.connection_count >= minConnections).length
        ),
        totalConnections: data.edges.reduce((sum, edge) => sum + edge.weight, 0),
        avgConnections: (
          data.nodes.reduce((sum, node) => sum + node.connection_count, 0) /
          data.nodes.length
        ).toFixed(1),
        strongestPair:
          data.edges.length > 0
            ? data.edges.reduce((max, edge) => (edge.weight > max.weight ? edge : max))
            : null,
      }
    : null

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-96">
          <p className="text-muted-foreground">Loading network data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Data</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{error}</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:justify-between md:items-center">
        <div>
          <h1 className="text-3xl font-bold">Entity Adjacency Matrix</h1>
          <p className="text-muted-foreground mt-1">
            Co-occurrence patterns across flight logs and connections
          </p>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap gap-3">
          {/* Sort By */}
          <div className="w-40">
            <label className="text-xs text-muted-foreground mb-1 block">Sort By</label>
            <Select value={sortBy} onValueChange={(val) => setSortBy(val as typeof sortBy)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="connections">Most Connected</SelectItem>
                <SelectItem value="alphabetical">Alphabetical</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Top N */}
          <div className="w-32">
            <label className="text-xs text-muted-foreground mb-1 block">
              Show Top N
            </label>
            <Input
              type="number"
              min="10"
              max="100"
              step="10"
              value={topN}
              onChange={(e) => setTopN(parseInt(e.target.value) || 30)}
            />
          </div>

          {/* Min Connections */}
          <div className="w-32">
            <label className="text-xs text-muted-foreground mb-1 block">
              Min. Connections
            </label>
            <Input
              type="number"
              min="0"
              max="50"
              value={minConnections}
              onChange={(e) => setMinConnections(parseInt(e.target.value) || 0)}
            />
          </div>

        </div>
      </div>

      {/* Matrix Visualization */}
      <Card>
        <CardHeader>
          <CardTitle>Co-Occurrence Heatmap</CardTitle>
          <CardDescription>
            Entity relationships based on shared flights and network connections.
            Hover over cells to see connection details.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AdjacencyMatrix
            data={data}
            topN={topN}
            minConnections={minConnections}
            sortBy={sortBy}
          />
        </CardContent>
      </Card>

      {/* Statistics */}
      {stats && (
        <Card>
          <CardHeader>
            <CardTitle>Matrix Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <div className="text-2xl font-bold">{stats.totalEntities}</div>
                <div className="text-sm text-muted-foreground">Total Entities</div>
              </div>
              <div>
                <div className="text-2xl font-bold">{stats.displayedEntities}</div>
                <div className="text-sm text-muted-foreground">Displayed</div>
              </div>
              <div>
                <div className="text-2xl font-bold">{stats.totalConnections}</div>
                <div className="text-sm text-muted-foreground">Total Connections</div>
              </div>
              <div>
                <div className="text-2xl font-bold">{stats.avgConnections}</div>
                <div className="text-sm text-muted-foreground">Avg. Connections</div>
              </div>
            </div>

            {stats.strongestPair && (
              <div className="mt-6 pt-6 border-t">
                <div className="text-sm font-medium mb-2">Strongest Connection</div>
                <div className="text-lg">
                  <span className="font-semibold">{stats.strongestPair.source}</span>
                  {' ↔ '}
                  <span className="font-semibold">{stats.strongestPair.target}</span>
                </div>
                <div className="text-sm text-muted-foreground">
                  {stats.strongestPair.weight} shared connections
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Usage Guide */}
      <Card>
        <CardHeader>
          <CardTitle>How to Read This Matrix</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            <strong>Rows & Columns:</strong> Each represents an entity in the network
          </p>
          <p>
            <strong>Cell Color:</strong> Darker colors indicate stronger connections (more shared flights/interactions)
          </p>
          <p>
            <strong>Numbers:</strong> Show the exact number of connections between two entities
          </p>
          <p>
            <strong>Diagonal:</strong> Empty cells (entity with itself)
          </p>
          <p>
            <strong>Interaction:</strong> Hover over any cell to see the entity pair and connection count
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
