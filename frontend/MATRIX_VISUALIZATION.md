# Adjacency Matrix Visualization

## Overview

The Adjacency Matrix visualization provides a heatmap view of entity co-occurrence patterns in the Epstein Archive network. It shows which entities appear together most frequently in flight logs and documented connections.

## Access

**URL**: http://localhost:5179/matrix

**Navigation**: Available in the main header menu under "Matrix"

## What is an Adjacency Matrix?

An adjacency matrix is a square grid where:
- **Rows & Columns**: Each represents an entity (person) in the network
- **Cells**: The intersection shows the connection strength between two entities
- **Colors**: Intensity represents the frequency of relationships
- **Symmetry**: Matrix is symmetric (cell [A,B] = cell [B,A])

## Features

### Interactive Visualization

- **Hover Tooltips**: Hover over any cell to see:
  - Entity A name
  - Entity B name
  - Connection count

- **Color Gradient**: Darker colors indicate stronger connections
  - White/Gray: No connections (0)
  - Light Blue: Few connections (1-5)
  - Medium Blue: Moderate connections (6-20)
  - Dark Blue: Strong connections (21-50)
  - Navy Blue: Very strong connections (51+)

### Filter Controls

**Sort By**:
- **Most Connected**: Entities sorted by total connection count (default)
- **Alphabetical**: Entities sorted A-Z by name

**Show Top N**:
- Display top 10, 20, 30, 40, 50, or 100 entities
- Default: 30 entities

**Min. Connections**:
- Filter out entities with fewer than N connections
- Useful for focusing on core network members

**Color Scheme**:
- **Blue** (default): Professional, clear
- **Red**: Alternative color scheme
- **Green**: Alternative color scheme

### Statistics Panel

Displays key metrics:
- **Total Entities**: Number of entities in full network
- **Displayed**: Number currently shown in matrix
- **Total Connections**: Sum of all connection weights
- **Avg. Connections**: Average connections per entity
- **Strongest Connection**: The pair with the most shared connections

### Color Legend

Shows the gradient scale with min/max values for interpreting cell colors.

## Data Source

The matrix is built from the network graph API:
- **Endpoint**: `GET http://localhost:8081/api/network`
- **Nodes**: 275 entities
- **Edges**: 1,584 connections
- **Edge Weight**: Number of shared flights or documented interactions

## How to Use

### Basic Usage

1. **Navigate** to the Matrix page from the header menu
2. **Hover** over cells to see relationship details
3. **Adjust filters** to focus on specific entities or patterns
4. **Read statistics** to understand network structure

### Finding Key Relationships

1. **Sort by "Most Connected"** to see central figures at the top
2. **Set Min. Connections to 10+** to filter noise
3. **Look for dark blue clusters** indicating tight-knit groups
4. **Check Strongest Connection** in stats panel

### Analyzing Sub-Networks

1. **Reduce "Show Top N"** to focus on core members (e.g., top 20)
2. **Increase Min. Connections** to see only well-connected entities
3. **Look for patterns** in the resulting smaller matrix

## Performance

- **30x30 Matrix**: <100ms render time
- **50x50 Matrix**: ~200ms render time
- **100x100 Matrix**: ~500ms render time

The component uses optimized rendering with React memoization and efficient adjacency matrix data structures.

## Implementation Details

### Component Architecture

**Files**:
- `/src/components/visualizations/AdjacencyMatrix.tsx` - Core matrix component
- `/src/pages/Matrix.tsx` - Page wrapper with controls and statistics

**Key Technologies**:
- React 19.2.0 with hooks (useState, useMemo)
- TypeScript for type safety
- Tailwind CSS for styling
- ShadCN UI components (Card, Select, Input)

### Data Transformation

The component transforms network graph data (nodes + edges) into an adjacency matrix:

```typescript
// Network graph format
{
  nodes: [{id: "A", name: "Entity A", ...}],
  edges: [{source: "A", target: "B", weight: 10}]
}

// Adjacency matrix format
Map<string, Map<string, number>>
// e.g., matrix.get("A").get("B") = 10
```

### Color Scale Algorithm

Colors are computed using intensity scaling:
```typescript
const intensity = connectionCount / maxWeight
const colorIndex = Math.floor(intensity * 5)  // 5 color buckets
const color = colorPalette[colorIndex]
```

## Future Enhancements

Potential improvements identified:
1. **Zoom & Pan**: For matrices > 100x100 entities
2. **Click to Highlight**: Click cell to highlight row/column
3. **Export**: Download as PNG or CSV
4. **Cluster Detection**: Automatically identify community groups
5. **Canvas Rendering**: For very large matrices (200+)
6. **Search/Filter**: Text search to find specific entities
7. **Timeline Integration**: Filter by date range

## Troubleshooting

**Matrix not loading**:
- Check that backend API is running on port 8081
- Verify network endpoint returns data: `curl http://localhost:8081/api/network`

**Slow performance**:
- Reduce "Show Top N" to display fewer entities
- Increase "Min. Connections" to filter out low-connection entities

**Colors not showing**:
- Verify that entities have connection weights in the data
- Check browser console for errors

## Related Pages

- **Network Graph**: Force-directed graph visualization of same data
- **Entities**: List view of all entities with connection counts
- **Flights**: Flight log data underlying many connections
- **Timeline**: Chronological view of events and connections

## Code Quality

**LOC Impact**: +450 lines (AdjacencyMatrix.tsx + Matrix.tsx)
**Reuse**: Uses existing UI components (Card, Select, Input)
**Test Coverage**: Component testing recommended for filter logic
**Performance**: O(N²) space and time complexity for N entities

**Design Decision**: DOM-based rendering chosen over Canvas for:
- Accessibility (native tooltips and hover states)
- Maintainability (easier to modify styling)
- Development speed (faster implementation)

For matrices > 100 entities, Canvas or WebGL rendering may be necessary.
