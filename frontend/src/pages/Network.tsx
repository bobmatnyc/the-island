import { useEffect, useState, useCallback, useRef, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import ForceGraph2D from 'react-force-graph-2d';
import {
  Search,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Play,
  Pause,
  X,
  Filter,
  BarChart3,
  Sparkles,
  BookOpen,
} from 'lucide-react';
import { api, type NetworkNode, type NetworkEdge } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { formatEntityName } from '@/utils/nameFormat';

// Enhanced graph node type
interface GraphNode extends NetworkNode {
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

// Enhanced graph edge type
interface GraphLink extends NetworkEdge {
  id?: string;
}

// Graph data structure
interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

// Filter state
interface FilterState {
  searchQuery: string;
  categories: string[];
  inBlackBook: boolean | null;
  isBillionaire: boolean | null;
  minConnections: number;
  minFlights: number;
  minEdgeWeight: number;
}

/**
 * Network Page
 *
 * Design Enhancement: URL Parameter Support for Entity Focus
 * Rationale: Support deep linking from entity detail pages with pre-focused node.
 * URL params: ?focus=<name> for centering network view on specific entity.
 *
 * Navigation Flow:
 * EntityDetail → /network?focus=Jeffrey%20Epstein → Auto-select and center node
 *
 * Implementation: Uses searchQuery filter and auto-selects matching node,
 * then centers camera on that node once graph is loaded.
 */
export function Network() {
  const [searchParams] = useSearchParams();

  // Core data
  const [allNodes, setAllNodes] = useState<GraphNode[]>([]);
  const [allEdges, setAllEdges] = useState<GraphLink[]>([]);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Graph controls
  const graphRef = useRef<any>(null);
  const [isPaused, setIsPaused] = useState(false);
  const [highlightNodes, setHighlightNodes] = useState(new Set<string>());
  const [highlightLinks, setHighlightLinks] = useState(new Set<string>());
  const [hoverNode, setHoverNode] = useState<GraphNode | null>(null);

  // UI state
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [showFilters, setShowFilters] = useState(true);
  const [showStats, setShowStats] = useState(true);

  // Filters
  const [filters, setFilters] = useState<FilterState>({
    searchQuery: '',
    categories: [],
    inBlackBook: null,
    isBillionaire: null,
    minConnections: 0,
    minFlights: 0,
    minEdgeWeight: 0,
  });

  // Available categories
  const allCategories = useMemo(() => {
    const categories = new Set<string>();
    allNodes.forEach((node) => {
      node.categories?.forEach((cat) => categories.add(cat));
    });
    return Array.from(categories).sort();
  }, [allNodes]);

  // Read URL parameters on mount
  useEffect(() => {
    const focusParam = searchParams.get('focus');
    if (focusParam) {
      const entityName = decodeURIComponent(focusParam);
      setFilters(prev => ({ ...prev, searchQuery: entityName }));
      setShowFilters(true); // Show filters section when pre-focused
    }
  }, [searchParams]);

  // Auto-select and center on focused entity when data loads
  useEffect(() => {
    if (allNodes.length > 0 && filters.searchQuery) {
      // Try matching by ID first (for entity.id format like 'jeffrey_epstein')
      // then fall back to name matching (for legacy URLs or manual searches)
      const searchLower = filters.searchQuery.toLowerCase();
      const focusedNode = allNodes.find(
        node => node.id.toLowerCase() === searchLower ||
                node.name.toLowerCase() === searchLower
      );

      if (focusedNode) {
        setSelectedNode(focusedNode);

        // Center camera on node after a short delay (allows graph to render)
        setTimeout(() => {
          if (graphRef.current && focusedNode) {
            graphRef.current.centerAt(focusedNode.x, focusedNode.y, 1000);
            graphRef.current.zoom(3, 1000);
          }
        }, 500);
      }
    }
  }, [allNodes, filters.searchQuery]);

  // Load network data
  useEffect(() => {
    loadNetworkData();
  }, []);

  const loadNetworkData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getNetwork();

      // Add unique IDs to edges
      const edgesWithIds = data.edges.map((edge, idx) => ({
        ...edge,
        id: `${edge.source}-${edge.target}-${idx}`,
      }));

      setAllNodes(data.nodes);
      setAllEdges(edgesWithIds);
    } catch (err) {
      console.error('Failed to load network:', err);
      setError('Failed to load network data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Apply filters to graph data
  useEffect(() => {
    filterGraphData();
  }, [allNodes, allEdges, filters]);

  const filterGraphData = () => {
    let filteredNodes = allNodes;

    // Search filter
    if (filters.searchQuery) {
      const query = filters.searchQuery.toLowerCase();
      filteredNodes = filteredNodes.filter(
        (node) =>
          node.name.toLowerCase().includes(query) ||
          node.original_names?.some((name) => name.toLowerCase().includes(query))
      );
    }

    // Category filter
    if (filters.categories.length > 0) {
      filteredNodes = filteredNodes.filter((node) =>
        node.categories?.some((cat) => filters.categories.includes(cat))
      );
    }

    // Black book filter
    if (filters.inBlackBook !== null) {
      filteredNodes = filteredNodes.filter((node) => node.in_black_book === filters.inBlackBook);
    }

    // Billionaire filter
    if (filters.isBillionaire !== null) {
      filteredNodes = filteredNodes.filter(
        (node) => node.is_billionaire === filters.isBillionaire
      );
    }

    // Connection count filter
    if (filters.minConnections > 0) {
      filteredNodes = filteredNodes.filter(
        (node) => node.connection_count >= filters.minConnections
      );
    }

    // Flight count filter
    if (filters.minFlights > 0) {
      filteredNodes = filteredNodes.filter((node) => node.flight_count >= filters.minFlights);
    }

    // Filter edges to only include edges between visible nodes
    const nodeIds = new Set(filteredNodes.map((n) => n.id));
    let filteredEdges = allEdges.filter(
      (edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target)
    );

    // Edge weight filter - reduces visual clutter by showing only significant connections
    // This dramatically improves readability in dense networks by filtering weak edges
    if (filters.minEdgeWeight > 0) {
      filteredEdges = filteredEdges.filter(
        (edge) => edge.weight >= filters.minEdgeWeight
      );
    }

    setGraphData({ nodes: filteredNodes, links: filteredEdges });
  };

  // Calculate graph statistics
  const statistics = useMemo(() => {
    const nodeCount = graphData.nodes.length;
    const edgeCount = graphData.links.length;
    const maxPossibleEdges = (nodeCount * (nodeCount - 1)) / 2;
    const density = maxPossibleEdges > 0 ? (edgeCount / maxPossibleEdges) * 100 : 0;

    // Top connected nodes
    const topNodes = [...graphData.nodes]
      .sort((a, b) => b.connection_count - a.connection_count)
      .slice(0, 10);

    // Average clustering coefficient (simplified)
    let totalClustering = 0;
    graphData.nodes.forEach((node) => {
      const neighbors = new Set<string>();
      graphData.links.forEach((link) => {
        if (link.source === node.id) neighbors.add(link.target);
        if (link.target === node.id) neighbors.add(link.source);
      });

      if (neighbors.size < 2) return;

      let neighborConnections = 0;
      const neighborArray = Array.from(neighbors);
      for (let i = 0; i < neighborArray.length; i++) {
        for (let j = i + 1; j < neighborArray.length; j++) {
          const hasConnection = graphData.links.some(
            (link) =>
              (link.source === neighborArray[i] && link.target === neighborArray[j]) ||
              (link.source === neighborArray[j] && link.target === neighborArray[i])
          );
          if (hasConnection) neighborConnections++;
        }
      }

      const maxNeighborConnections = (neighbors.size * (neighbors.size - 1)) / 2;
      if (maxNeighborConnections > 0) {
        totalClustering += neighborConnections / maxNeighborConnections;
      }
    });

    const clusteringCoefficient =
      nodeCount > 0 ? (totalClustering / nodeCount) * 100 : 0;

    return {
      nodeCount,
      edgeCount,
      density: density.toFixed(2),
      topNodes,
      clusteringCoefficient: clusteringCoefficient.toFixed(2),
    };
  }, [graphData]);

  // Node click handler
  const handleNodeClick = useCallback(
    (node: GraphNode) => {
      setSelectedNode(node);

      // Highlight connected nodes and edges
      const connectedNodeIds = new Set<string>();
      const connectedLinkIds = new Set<string>();

      graphData.links.forEach((link) => {
        if (link.source === node.id) {
          connectedNodeIds.add(link.target);
          connectedLinkIds.add(link.id || '');
        }
        if (link.target === node.id) {
          connectedNodeIds.add(link.source);
          connectedLinkIds.add(link.id || '');
        }
      });

      connectedNodeIds.add(node.id);
      setHighlightNodes(connectedNodeIds);
      setHighlightLinks(connectedLinkIds);

      // Center on node
      if (graphRef.current) {
        graphRef.current.centerAt(node.x, node.y, 1000);
        graphRef.current.zoom(4, 1000);
      }
    },
    [graphData.links]
  );

  // Clear selection
  const clearSelection = useCallback(() => {
    setSelectedNode(null);
    setHighlightNodes(new Set());
    setHighlightLinks(new Set());
  }, []);

  // Graph control functions
  const handleZoomIn = () => {
    if (graphRef.current) {
      const currentZoom = graphRef.current.zoom();
      graphRef.current.zoom(currentZoom * 1.5, 300);
    }
  };

  const handleZoomOut = () => {
    if (graphRef.current) {
      const currentZoom = graphRef.current.zoom();
      graphRef.current.zoom(currentZoom / 1.5, 300);
    }
  };

  const handleResetView = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400, 50);
    }
    clearSelection();
  };

  const togglePhysics = () => {
    setIsPaused(!isPaused);
  };

  // Search for node
  const handleSearch = (query: string) => {
    setFilters({ ...filters, searchQuery: query });

    if (query && graphData.nodes.length > 0) {
      const node = graphData.nodes.find((n) =>
        n.name.toLowerCase().includes(query.toLowerCase())
      );
      if (node) {
        handleNodeClick(node);
      }
    }
  };

  // Node visualization
  const getNodeColor = (node: GraphNode) => {
    if (highlightNodes.size > 0 && !highlightNodes.has(node.id)) {
      return 'rgba(200, 200, 200, 0.3)';
    }

    if (node.in_black_book) return '#ef4444'; // Red
    if (node.is_billionaire) return '#f59e0b'; // Orange
    if (node.flight_count > 10) return '#3b82f6'; // Blue
    if (node.categories?.includes('politician')) return '#8b5cf6'; // Purple
    return '#6b7280'; // Gray
  };

  const getNodeSize = (node: GraphNode) => {
    const baseSize = 4;
    const sizeMultiplier = Math.log(node.connection_count + 1) * 2;
    return baseSize + sizeMultiplier;
  };

  // Link visualization (reserved for future use)
  // const getLinkColor = (link: any) => {
  //   const graphLink = link as GraphLink;
  //   if (highlightLinks.size > 0 && !highlightLinks.has(graphLink.id || '')) {
  //     return 'rgba(200, 200, 200, 0.1)';
  //   }
  //   return 'rgba(100, 100, 100, 0.4)';
  // };

  // const getLinkWidth = (link: any) => {
  //   const graphLink = link as GraphLink;
  //   if (highlightLinks.has(graphLink.id || '')) {
  //     return Math.log(graphLink.weight + 1) * 2;
  //   }
  //   return Math.log(graphLink.weight + 1);
  // };

  // Toggle category filter
  const toggleCategory = (category: string) => {
    if (filters.categories.includes(category)) {
      setFilters({
        ...filters,
        categories: filters.categories.filter((c) => c !== category),
      });
    } else {
      setFilters({ ...filters, categories: [...filters.categories, category] });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[600px]">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent mb-4" />
          <p className="text-muted-foreground">Loading network graph...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[600px]">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <p className="text-destructive mb-4">{error}</p>
            <Button onClick={loadNetworkData}>Retry</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-120px)] gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Network Graph</h1>
          <p className="text-muted-foreground">
            Explore {allNodes.length.toLocaleString()} entities and{' '}
            {allEdges.length.toLocaleString()} connections
          </p>
        </div>

        {/* Control Buttons */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => setShowFilters(!showFilters)}
            title="Toggle Filters"
          >
            <Filter className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={() => setShowStats(!showStats)}
            title="Toggle Statistics"
          >
            <BarChart3 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex gap-4 flex-1 min-h-0">
        {/* Left Sidebar - Filters */}
        {showFilters && (
          <Card className="w-80 overflow-y-auto flex-shrink-0">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Filter className="h-5 w-5" />
                Filters
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Search */}
              <div>
                <label className="text-sm font-medium mb-2 block">Search</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="Find entity..."
                    value={filters.searchQuery}
                    onChange={(e) => handleSearch(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              {/* Categories */}
              {allCategories.length > 0 && (
                <div>
                  <label className="text-sm font-medium mb-2 block">Categories</label>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {allCategories.map((category) => (
                      <label key={category} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={filters.categories.includes(category)}
                          onChange={() => toggleCategory(category)}
                          className="rounded"
                        />
                        <span className="text-sm">{category}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* Special Filters */}
              <div>
                <label className="text-sm font-medium mb-2 block">Special Filters</label>
                <div className="space-y-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={filters.inBlackBook === true}
                      onChange={(e) =>
                        setFilters({
                          ...filters,
                          inBlackBook: e.target.checked ? true : null,
                        })
                      }
                      className="rounded"
                    />
                    <span className="text-sm">In Black Book</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={filters.isBillionaire === true}
                      onChange={(e) =>
                        setFilters({
                          ...filters,
                          isBillionaire: e.target.checked ? true : null,
                        })
                      }
                      className="rounded"
                    />
                    <span className="text-sm">Billionaire</span>
                  </label>
                </div>
              </div>

              {/* Connection Count */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Min Connections: {filters.minConnections}
                </label>
                <input
                  type="range"
                  min="0"
                  max="50"
                  value={filters.minConnections}
                  onChange={(e) =>
                    setFilters({ ...filters, minConnections: parseInt(e.target.value) })
                  }
                  className="w-full"
                />
              </div>

              {/* Flight Count */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Min Flights: {filters.minFlights}
                </label>
                <input
                  type="range"
                  min="0"
                  max="50"
                  value={filters.minFlights}
                  onChange={(e) =>
                    setFilters({ ...filters, minFlights: parseInt(e.target.value) })
                  }
                  className="w-full"
                />
              </div>

              {/* Edge Weight Filter */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Min Edge Weight: {filters.minEdgeWeight}
                </label>
                <input
                  type="range"
                  min="0"
                  max="20"
                  value={filters.minEdgeWeight}
                  onChange={(e) =>
                    setFilters({ ...filters, minEdgeWeight: parseInt(e.target.value) })
                  }
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Filter edges by co-occurrence count to reduce visual clutter
                </p>
              </div>

              {/* Reset Filters */}
              <Button
                variant="outline"
                className="w-full"
                onClick={() =>
                  setFilters({
                    searchQuery: '',
                    categories: [],
                    inBlackBook: null,
                    isBillionaire: null,
                    minConnections: 0,
                    minFlights: 0,
                    minEdgeWeight: 0,
                  })
                }
              >
                Reset Filters
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Center - Graph Visualization */}
        <div className="flex-1 relative border rounded-lg overflow-hidden bg-white">
          {/* Graph Controls Overlay */}
          <div className="absolute top-4 right-4 z-10 flex flex-col gap-2">
            <Button variant="secondary" size="icon" onClick={handleZoomIn} title="Zoom In">
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button variant="secondary" size="icon" onClick={handleZoomOut} title="Zoom Out">
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Button
              variant="secondary"
              size="icon"
              onClick={handleResetView}
              title="Reset View"
            >
              <Maximize2 className="h-4 w-4" />
            </Button>
            <Button
              variant="secondary"
              size="icon"
              onClick={togglePhysics}
              title={isPaused ? 'Resume Physics' : 'Pause Physics'}
            >
              {isPaused ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
            </Button>
          </div>

          {/* Legend */}
          <div className="absolute top-4 left-4 z-10 bg-white/90 backdrop-blur-sm rounded-lg p-3 text-xs space-y-1">
            <div className="font-medium mb-2">Color Legend</div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[#ef4444]" />
              <span>Black Book</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[#f59e0b]" />
              <span>Billionaire</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[#3b82f6]" />
              <span>Frequent Flyer (10+)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-[#8b5cf6]" />
              <span>Politician</span>
            </div>
          </div>

          {/* Force Graph */}
          <ForceGraph2D
            ref={graphRef}
            graphData={graphData}
            nodeId="id"
            nodeLabel="name"
            nodeColor={getNodeColor}
            nodeVal={getNodeSize}
            nodeCanvasObject={(node: any, ctx, globalScale) => {
              const label = formatEntityName(node.name);
              const fontSize = 12 / globalScale;
              const nodeSize = getNodeSize(node);

              // Draw node
              ctx.beginPath();
              ctx.arc(node.x, node.y, nodeSize, 0, 2 * Math.PI);
              ctx.fillStyle = getNodeColor(node);
              ctx.fill();

              // Draw label if zoomed in or highlighted
              if (globalScale > 2 || highlightNodes.has(node.id)) {
                ctx.font = `${fontSize}px Sans-Serif`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = '#000';
                ctx.fillText(label, node.x, node.y + nodeSize + fontSize);
              }
            }}
            linkSource="source"
            linkTarget="target"
            linkCanvasObject={(link: any, ctx, globalScale) => {
              const graphLink = link as GraphLink;

              // Zoom-based edge visibility: progressive disclosure pattern
              // When zoomed out, hide weak edges to reduce clutter
              // When zoomed in, show all edges for detailed analysis
              const zoomThreshold = 1.5; // Threshold for showing weak edges
              const isZoomedIn = globalScale >= zoomThreshold;

              // Combine static filter (minEdgeWeight) with zoom-based filtering
              const effectiveMinWeight = isZoomedIn
                ? filters.minEdgeWeight  // When zoomed in, use user's filter
                : Math.max(filters.minEdgeWeight, 3);  // When zoomed out, enforce minimum of 3

              // Skip rendering if edge is too weak for current zoom level
              if (graphLink.weight < effectiveMinWeight) {
                return;
              }

              // Determine color and opacity
              let color = 'rgba(100, 100, 100, 0.4)';
              let width = Math.log(graphLink.weight + 1);

              // Highlight if selected
              if (highlightLinks.has(graphLink.id || '')) {
                color = 'rgba(100, 100, 100, 0.8)';
                width = Math.log(graphLink.weight + 1) * 2;
              }
              // Fade if other links are highlighted
              else if (highlightLinks.size > 0) {
                color = 'rgba(200, 200, 200, 0.1)';
              }

              // Draw link
              ctx.beginPath();
              ctx.moveTo(link.source.x, link.source.y);
              ctx.lineTo(link.target.x, link.target.y);
              ctx.strokeStyle = color;
              ctx.lineWidth = width / globalScale;
              ctx.stroke();
            }}
            linkDirectionalParticles={2}
            linkDirectionalParticleWidth={(link: any) =>
              highlightLinks.has(link.id || '') ? 2 : 0
            }
            onNodeClick={handleNodeClick}
            onNodeHover={setHoverNode}
            onBackgroundClick={clearSelection}
            cooldownTicks={isPaused ? 0 : Infinity}
            enableNodeDrag={true}
            enableZoomInteraction={true}
            enablePanInteraction={true}
          />

          {/* Hover Tooltip */}
          {hoverNode && !selectedNode && (
            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 bg-black/80 text-white px-3 py-2 rounded-lg text-sm z-10">
              <div className="font-medium">{formatEntityName(hoverNode.name)}</div>
              <div className="text-xs text-gray-300">
                {hoverNode.connection_count} connections • {hoverNode.flight_count} flights
              </div>
            </div>
          )}
        </div>

        {/* Right Sidebar - Node Details or Stats */}
        {(selectedNode || showStats) && (
          <Card className="w-80 overflow-y-auto flex-shrink-0">
            {selectedNode ? (
              <>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-lg pr-8">{formatEntityName(selectedNode.name)}</CardTitle>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 -mt-1"
                      onClick={clearSelection}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Badges */}
                  <div className="flex flex-wrap gap-2">
                    {selectedNode.in_black_book && (
                      <Badge variant="destructive">
                        <BookOpen className="h-3 w-3 mr-1" />
                        Black Book
                      </Badge>
                    )}
                    {selectedNode.is_billionaire && (
                      <Badge variant="secondary">
                        <Sparkles className="h-3 w-3 mr-1" />
                        Billionaire
                      </Badge>
                    )}
                  </div>

                  {/* Stats */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Connections:</span>
                      <span className="font-medium">{selectedNode.connection_count}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Flights:</span>
                      <span className="font-medium">{selectedNode.flight_count}</span>
                    </div>
                  </div>

                  {/* Categories */}
                  {selectedNode.categories && selectedNode.categories.length > 0 && (
                    <div>
                      <div className="text-sm font-medium mb-2">Categories</div>
                      <div className="flex flex-wrap gap-1">
                        {selectedNode.categories.map((cat) => (
                          <Badge key={cat} variant="outline" className="text-xs">
                            {cat}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Direct Connections */}
                  <div>
                    <div className="text-sm font-medium mb-2">
                      Direct Connections ({highlightNodes.size - 1})
                    </div>
                    <div className="space-y-1 max-h-64 overflow-y-auto">
                      {Array.from(highlightNodes)
                        .filter((id) => id !== selectedNode.id)
                        .slice(0, 20)
                        .map((nodeId) => {
                          const node = graphData.nodes.find((n) => n.id === nodeId);
                          if (!node) return null;

                          const edge = graphData.links.find(
                            (l) =>
                              (l.source === selectedNode.id && l.target === nodeId) ||
                              (l.target === selectedNode.id && l.source === nodeId)
                          );

                          return (
                            <button
                              key={nodeId}
                              onClick={() => handleNodeClick(node)}
                              className="w-full text-left px-2 py-1 rounded hover:bg-secondary text-sm"
                            >
                              <div className="flex justify-between items-center">
                                <span className="truncate">{formatEntityName(node.name)}</span>
                                {edge && (
                                  <Badge variant="outline" className="text-xs ml-2">
                                    {edge.weight}
                                  </Badge>
                                )}
                              </div>
                            </button>
                          );
                        })}
                    </div>
                  </div>
                </CardContent>
              </>
            ) : showStats ? (
              <>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    Network Statistics
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Overview Stats */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Nodes:</span>
                      <span className="font-medium">{statistics.nodeCount}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Edges:</span>
                      <span className="font-medium">{statistics.edgeCount}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Density:</span>
                      <span className="font-medium">{statistics.density}%</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Clustering:</span>
                      <span className="font-medium">{statistics.clusteringCoefficient}%</span>
                    </div>
                  </div>

                  {/* Top Connected */}
                  <div>
                    <div className="text-sm font-medium mb-2">Most Connected Nodes</div>
                    <div className="space-y-1">
                      {statistics.topNodes.map((node, idx) => (
                        <button
                          key={node.id}
                          onClick={() => handleNodeClick(node)}
                          className="w-full text-left px-2 py-1 rounded hover:bg-secondary text-sm"
                        >
                          <div className="flex justify-between items-center">
                            <div className="flex items-center gap-2">
                              <span className="text-muted-foreground">#{idx + 1}</span>
                              <span className="truncate">{formatEntityName(node.name)}</span>
                            </div>
                            <Badge variant="outline" className="text-xs">
                              {node.connection_count}
                            </Badge>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </>
            ) : null}
          </Card>
        )}
      </div>
    </div>
  );
}
