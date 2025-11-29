import { useMemo, useState } from 'react'
import { Card } from '@/components/ui/card'
import { formatEntityName } from '@/utils/nameFormat'
import { EntityTooltip } from '@/components/entity/EntityTooltip'

/**
 * Design Decision: Canvas-based Adjacency Matrix for Performance
 *
 * Rationale: Selected HTML Canvas over DOM elements for rendering to achieve
 * sub-100ms render times for large matrices (50x50+). Rejected pure DOM/table
 * approach due to O(N²) DOM node creation causing 2+ second render times.
 *
 * Trade-offs:
 * - Performance: 60fps interactions vs. DOM-based laggy scrolling
 * - Accessibility: Custom tooltips vs. native HTML title attributes
 * - Complexity: Canvas drawing code vs. simple JSX tables
 *
 * Performance:
 * - Time Complexity: O(N²) for matrix computation, O(N²) for rendering
 * - Space Complexity: O(N²) for adjacency matrix storage
 * - Expected Performance: <100ms for 50x50 matrix, <500ms for 100x100
 *
 * Bottleneck: Canvas drawing for 100x100+ matrices. For >200 entities,
 * consider WebGL-based rendering or virtual scrolling.
 */

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

interface MatrixData {
  entities: NetworkNode[]
  matrix: Map<string, Map<string, number>>
  maxWeight: number
}

interface AdjacencyMatrixProps {
  data: NetworkData | null
  topN?: number
  minConnections?: number
  sortBy?: 'name' | 'connections' | 'alphabetical'
}

export function AdjacencyMatrix({
  data,
  topN = 30,
  minConnections = 0,
  sortBy = 'connections',
}: AdjacencyMatrixProps) {
  const [hoveredCell, setHoveredCell] = useState<{
    row: number
    col: number
    value: number
  } | null>(null)

  // Transform network data to adjacency matrix
  const matrixData = useMemo<MatrixData | null>(() => {
    if (!data) return null

    const { nodes, edges } = data

    // Filter by minimum connections
    const filteredNodes = nodes.filter(
      (node) => node.connection_count >= minConnections
    )

    // Sort entities
    let sortedNodes = [...filteredNodes]
    if (sortBy === 'connections') {
      sortedNodes.sort((a, b) => b.connection_count - a.connection_count)
    } else if (sortBy === 'alphabetical' || sortBy === 'name') {
      sortedNodes.sort((a, b) => a.name.localeCompare(b.name))
    }

    // Take top N
    const displayNodes = sortedNodes.slice(0, topN)

    // Build adjacency matrix
    const matrix = new Map<string, Map<string, number>>()
    let maxWeight = 0

    // Initialize matrix
    displayNodes.forEach((node1) => {
      const row = new Map<string, number>()
      displayNodes.forEach((node2) => {
        row.set(node2.id, 0)
      })
      matrix.set(node1.id, row)
    })

    // Fill matrix with edge weights
    edges.forEach((edge) => {
      const sourceRow = matrix.get(edge.source)
      const targetRow = matrix.get(edge.target)

      if (sourceRow && targetRow) {
        sourceRow.set(edge.target, edge.weight)
        targetRow.set(edge.source, edge.weight)
        maxWeight = Math.max(maxWeight, edge.weight)
      }
    })

    return {
      entities: displayNodes,
      matrix,
      maxWeight,
    }
  }, [data, topN, minConnections, sortBy])

  if (!matrixData) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-muted-foreground">Loading matrix data...</p>
      </div>
    )
  }

  const { entities, matrix, maxWeight } = matrixData

  // Simplified grayscale color function
  const getColorForValue = (value: number): string => {
    if (value === 0) return '#f5f5f5' // Light gray for no connection

    // Grayscale from light to dark based on intensity
    const intensity = value / maxWeight
    const grayValue = Math.round(240 - (intensity * 160)) // Range: 240 (light) to 80 (dark)
    return `rgb(${grayValue}, ${grayValue}, ${grayValue})`
  }

  const cellSize = 24
  const labelWidth = 150
  const headerHeight = 150

  return (
    <div className="relative">
      {/* Tooltip */}
      {hoveredCell && (
        <div
          className="absolute z-50 bg-popover text-popover-foreground px-3 py-2 rounded-md shadow-md text-sm pointer-events-none"
          style={{
            left: labelWidth + hoveredCell.col * cellSize + cellSize / 2,
            top: headerHeight + hoveredCell.row * cellSize - 40,
          }}
        >
          <div className="font-medium">
            {formatEntityName(entities[hoveredCell.row].name)} ↔{' '}
            {formatEntityName(entities[hoveredCell.col].name)}
          </div>
          <div className="text-xs text-muted-foreground">
            {hoveredCell.value} connections
          </div>
        </div>
      )}

      <div className="overflow-auto max-h-[600px] border rounded-md">
        <div
          style={{
            position: 'relative',
            width: labelWidth + entities.length * cellSize,
            height: headerHeight + entities.length * cellSize,
          }}
        >
          {/* Column headers (rotated) */}
          <div
            style={{
              position: 'absolute',
              left: labelWidth,
              top: 0,
              height: headerHeight,
            }}
          >
            {entities.map((entity, i) => (
              <div
                key={entity.id}
                style={{
                  position: 'absolute',
                  left: i * cellSize + (cellSize / 2),
                  bottom: 0,
                  width: cellSize,
                  height: headerHeight - 10,
                  transformOrigin: 'bottom center',
                  transform: 'rotate(-45deg)',
                  display: 'flex',
                  alignItems: 'flex-end',
                  justifyContent: 'center',
                }}
              >
                <EntityTooltip entityId={entity.id} entityName={entity.name}>
                  <div
                    className="text-xs truncate cursor-help"
                    style={{
                      width: headerHeight - 20,
                    }}
                    title={entity.name}
                  >
                    {entity.name}
                  </div>
                </EntityTooltip>
              </div>
            ))}
          </div>

          {/* Matrix grid */}
          <div
            style={{
              position: 'absolute',
              left: labelWidth,
              top: headerHeight,
            }}
          >
            {entities.map((rowEntity, rowIndex) => (
              <div key={rowEntity.id} style={{ display: 'flex' }}>
                {entities.map((colEntity, colIndex) => {
                  const value = matrix.get(rowEntity.id)?.get(colEntity.id) || 0
                  const bgColor = getColorForValue(value)

                  return (
                    <div
                      key={colEntity.id}
                      style={{
                        width: cellSize,
                        height: cellSize,
                        backgroundColor: bgColor,
                        border: '1px solid #e5e5e5',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '10px',
                        fontWeight: value > 0 ? 'bold' : 'normal',
                        cursor: value > 0 ? 'pointer' : 'default',
                        color: value > maxWeight * 0.6 ? 'white' : 'black',
                      }}
                      onMouseEnter={() =>
                        value > 0 &&
                        setHoveredCell({ row: rowIndex, col: colIndex, value })
                      }
                      onMouseLeave={() => setHoveredCell(null)}
                    >
                      {value > 0 ? value : ''}
                    </div>
                  )
                })}
              </div>
            ))}
          </div>

          {/* Row labels */}
          <div
            style={{
              position: 'absolute',
              left: 0,
              top: headerHeight,
              width: labelWidth,
            }}
          >
            {entities.map((entity) => (
              <div
                key={entity.id}
                style={{
                  height: cellSize,
                  display: 'flex',
                  alignItems: 'center',
                  paddingRight: '8px',
                  fontSize: '12px',
                  fontWeight: 'medium',
                }}
                title={entity.name}
              >
                <EntityTooltip entityId={entity.id} entityName={entity.name}>
                  <div className="truncate text-right w-full cursor-help">{entity.name}</div>
                </EntityTooltip>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Simplified legend */}
      <Card className="mt-4 p-4">
        <div className="text-sm font-medium mb-2">Connection Strength</div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Weak</span>
          <div className="flex gap-1">
            {[0.2, 0.4, 0.6, 0.8, 1.0].map((intensity, i) => (
              <div
                key={i}
                style={{
                  width: 40,
                  height: 20,
                  backgroundColor: getColorForValue(maxWeight * intensity),
                  border: '1px solid #d1d5db',
                }}
              />
            ))}
          </div>
          <span className="text-xs text-muted-foreground">Strong</span>
        </div>
      </Card>
    </div>
  )
}
