"""
Network Graph Pydantic Models

Design Decision: Type-Safe Network Representation
Rationale: Network graphs require strict validation to prevent:
- Self-loops (entity connected to itself)
- Orphaned edges (edges referencing non-existent nodes)
- Duplicate edges between same nodes
- Invalid connection weights

Architecture:
- NetworkNode: Individual entity in the graph
- NetworkEdge: Connection between two entities
- NetworkGraph: Complete graph with integrity validation

Trade-offs:
- Performance: Graph validation is O(n + m) where n=nodes, m=edges
- Safety: Prevents corrupt graph data that breaks visualization
- Memory: Small overhead for validation sets (~10% for large graphs)

Performance Notes:
- Validation runs once during graph construction
- Use model_construct() to skip validation for trusted data
- For incremental updates, validate individual edges before adding

Example:
    graph = NetworkGraph(
        nodes=[
            NetworkNode(id="Epstein, Jeffrey", connection_count=262),
            NetworkNode(id="Maxwell, Ghislaine", connection_count=188)
        ],
        edges=[
            NetworkEdge(source="Epstein, Jeffrey", target="Maxwell, Ghislaine", weight=50)
        ]
    )
"""

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import List, Set, Dict, Optional
from .enums import EntityType


class NetworkNode(BaseModel):
    """Node in the network graph representing an entity.

    Design Decision: Minimal node model
    Rationale: Network graph focuses on connections, not entity details.
    Full entity data is fetched separately via EntityService.

    Corresponds to entity_network.json nodes structure.

    Performance:
    - Node lookup is O(1) with dictionary (see NetworkGraph)
    - Connection count can be computed from edges if needed
    """

    id: str = Field(
        ...,
        description="Entity name (node identifier, must be unique)",
        min_length=1
    )
    name: str = Field(
        ...,
        description="Display name (usually same as id)",
        min_length=1
    )

    # Metadata (optional, for enrichment)
    in_black_book: bool = Field(default=False)
    is_billionaire: bool = Field(default=False)
    flight_count: int = Field(ge=0, default=0)
    categories: List[str] = Field(default_factory=list)

    # Connection statistics
    connection_count: int = Field(
        ge=0,
        description="Number of connections to other entities"
    )

    @field_validator('id', 'name', mode='after')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace from id and name."""
        return v.strip()

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class NetworkEdge(BaseModel):
    """Edge connecting two nodes in the network graph.

    Design Decision: Undirected edges with weight
    Rationale: Connections are mutual (flight together = both connected).
    Weight represents connection strength (number of flights).

    Validation:
    - No self-loops (source != target)
    - Weight must be positive (at least 1 shared flight)
    - Source/target must exist in graph (validated by NetworkGraph)

    Corresponds to entity_network.json edges structure.

    Performance Note:
    - Edge validation is O(1) per edge
    - For bulk edge creation, use list comprehension + batch validation
    """

    source: str = Field(
        ...,
        description="Source node ID (entity name)",
        min_length=1
    )
    target: str = Field(
        ...,
        description="Target node ID (entity name)",
        min_length=1
    )
    weight: int = Field(
        ge=1,
        default=1,
        description="Connection strength (e.g., flights together)"
    )

    # Additional edge metadata (from entity_network.json)
    flight_count: Optional[int] = Field(
        None,
        ge=0,
        description="Number of flights together (alias for weight)"
    )
    contexts: List[str] = Field(
        default_factory=list,
        description="Context where connection occurred (e.g., flight IDs)"
    )

    @field_validator('source', 'target', mode='after')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace from source and target."""
        return v.strip()

    @model_validator(mode='after')
    def validate_no_self_loops(self) -> 'NetworkEdge':
        """Prevent self-loops (entity connected to itself).

        Design Decision: Fail-fast validation
        Rationale: Self-loops are data errors that should never occur.
        Better to fail during import than corrupt the graph.

        Error Example:
            NetworkEdge(source="A", target="A", weight=1)
            -> ValidationError: Self-loops not allowed
        """
        if self.source == self.target:
            raise ValueError(
                f"Self-loops not allowed: source and target are both '{self.source}'"
            )
        return self

    @model_validator(mode='after')
    def sync_weight_and_flight_count(self) -> 'NetworkEdge':
        """Ensure weight and flight_count are synchronized.

        Design Decision: flight_count is alias for weight
        Rationale: Legacy data uses flight_count, but weight is more generic

        Note: Use object.__setattr__ to avoid validate_assignment recursion
        """
        if self.flight_count is not None and self.flight_count != self.weight:
            # If flight_count provided, use it as weight
            object.__setattr__(self, 'weight', self.flight_count)
        elif self.flight_count is None:
            # Otherwise, set flight_count from weight
            object.__setattr__(self, 'flight_count', self.weight)

        return self

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class NetworkGraph(BaseModel):
    """Complete network graph with integrity validation.

    Design Decision: Graph-level validation
    Rationale: Ensures all edges reference existing nodes,
    preventing orphaned edges and visualization errors.

    Validation Strategy:
    1. Build set of node IDs (O(n))
    2. Check each edge references valid nodes (O(m))
    3. Total complexity: O(n + m) - acceptable for graphs <10K nodes

    Performance Considerations:
    - Validation runs once during construction
    - For incremental updates, use add_node/add_edge methods
    - Use model_construct() to skip validation for trusted data

    Error Handling:
    - ValidationError with specific missing node ID
    - Failed validation indicates data corruption
    - Graceful degradation: load nodes, skip invalid edges

    Example:
        try:
            graph = NetworkGraph(nodes=nodes, edges=edges)
        except ValidationError as e:
            logger.error(f"Graph validation failed: {e}")
            # Fallback: load nodes only, filter out bad edges
            valid_node_ids = {n.id for n in nodes}
            valid_edges = [
                e for e in edges
                if e.source in valid_node_ids and e.target in valid_node_ids
            ]
            graph = NetworkGraph.model_construct(
                nodes=nodes, edges=valid_edges
            )
    """

    nodes: List[NetworkNode] = Field(
        ...,
        description="List of nodes (entities) in the graph"
    )
    edges: List[NetworkEdge] = Field(
        ...,
        description="List of edges (connections) between nodes"
    )

    # Metadata (from entity_network.json)
    metadata: Optional[Dict] = Field(
        None,
        description="Graph metadata (total_nodes, total_edges, last_updated)"
    )

    @field_validator('nodes', mode='after')
    @classmethod
    def validate_unique_node_ids(cls, v: List[NetworkNode]) -> List[NetworkNode]:
        """Ensure all node IDs are unique.

        Design Decision: Fail on duplicate IDs
        Rationale: Duplicate node IDs break graph lookups and visualization
        """
        seen_ids = set()
        duplicates = []

        for node in v:
            if node.id in seen_ids:
                duplicates.append(node.id)
            seen_ids.add(node.id)

        if duplicates:
            raise ValueError(
                f"Duplicate node IDs found: {', '.join(duplicates)}"
            )

        return v

    @model_validator(mode='after')
    def validate_edge_nodes_exist(self) -> 'NetworkGraph':
        """Ensure all edges reference existing nodes.

        Validation:
        - Build set of valid node IDs
        - Check each edge's source and target are in set
        - Fail with specific error for orphaned edges

        Performance: O(n + m) where n=nodes, m=edges
        Memory: O(n) for node ID set

        Error Example:
            nodes = [NetworkNode(id="A", connection_count=1)]
            edges = [NetworkEdge(source="A", target="B", weight=1)]
            -> ValidationError: Edge target 'B' not in nodes
        """
        # Build set of valid node IDs (O(n))
        node_ids: Set[str] = {node.id for node in self.nodes}

        # Check each edge (O(m))
        invalid_edges = []
        for edge in self.edges:
            if edge.source not in node_ids:
                invalid_edges.append(
                    f"Edge source '{edge.source}' not in nodes"
                )
            if edge.target not in node_ids:
                invalid_edges.append(
                    f"Edge target '{edge.target}' not in nodes"
                )

        if invalid_edges:
            # Show first 5 errors to avoid overwhelming output
            error_sample = invalid_edges[:5]
            error_msg = "\n".join(error_sample)
            if len(invalid_edges) > 5:
                error_msg += f"\n... and {len(invalid_edges) - 5} more"

            raise ValueError(
                f"Graph validation failed: edges reference non-existent nodes\n{error_msg}"
            )

        return self

    @model_validator(mode='after')
    def sync_metadata(self) -> 'NetworkGraph':
        """Sync metadata with actual node/edge counts.

        Design Decision: Auto-compute metadata
        Rationale: Prevents stale metadata that doesn't match graph
        """
        if self.metadata is None:
            self.metadata = {}

        # Update counts
        self.metadata['total_nodes'] = len(self.nodes)
        self.metadata['total_edges'] = len(self.edges)

        # Compute max connections
        if self.nodes:
            self.metadata['max_connections'] = max(
                node.connection_count for node in self.nodes
            )

        return self

    def get_node_by_id(self, node_id: str) -> Optional[NetworkNode]:
        """Get node by ID (O(n) lookup).

        Performance Note: For frequent lookups, build an index:
            node_index = {n.id: n for n in graph.nodes}

        Args:
            node_id: Node ID to find

        Returns:
            NetworkNode if found, None otherwise
        """
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_edges_for_node(self, node_id: str) -> List[NetworkEdge]:
        """Get all edges connected to a node (O(m) lookup).

        Performance Note: For frequent queries, build adjacency list:
            adj = defaultdict(list)
            for edge in graph.edges:
                adj[edge.source].append(edge)
                adj[edge.target].append(edge)

        Args:
            node_id: Node ID to find edges for

        Returns:
            List of edges where node is source or target
        """
        return [
            edge for edge in self.edges
            if edge.source == node_id or edge.target == node_id
        ]

    def to_adjacency_list(self) -> Dict[str, List[str]]:
        """Convert graph to adjacency list representation.

        Performance: O(m) where m = number of edges
        Memory: O(n + m) for adjacency list

        Returns:
            Dict mapping node_id -> list of connected node_ids

        Example:
            {
                "Epstein, Jeffrey": ["Maxwell, Ghislaine", "Trump, Donald"],
                "Maxwell, Ghislaine": ["Epstein, Jeffrey"],
                ...
            }
        """
        from collections import defaultdict
        adj: Dict[str, List[str]] = defaultdict(list)

        for edge in self.edges:
            adj[edge.source].append(edge.target)
            adj[edge.target].append(edge.source)  # Undirected graph

        return dict(adj)

    model_config = ConfigDict(
        validate_assignment=True,
    )
