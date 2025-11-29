"""
Unit Tests for Entity Pydantic Models

Test Coverage:
- Entity model validation
- EntityBiography model validation
- EntityTag model validation
- NetworkNode model validation
- NetworkEdge model validation
- NetworkGraph model validation with integrity checks
- Field validators and model validators
- Error cases and edge conditions

Run tests:
    pytest tests/test_entity_models.py -v
    pytest tests/test_entity_models.py::test_entity_validation -v
"""

import pytest
from pydantic import ValidationError

from server.models import (
    DocumentReference,
    Entity,
    EntityBiography,
    EntityTag,
    EntityType,
    NetworkEdge,
    NetworkGraph,
    NetworkNode,
    SourceType,
    TopConnection,
)


class TestEntity:
    """Test Entity model validation"""

    def test_entity_minimal_valid(self):
        """Test entity with minimal required fields"""
        entity = Entity(
            name="Epstein, Jeffrey",
            normalized_name="Jeffrey Epstein"
        )
        assert entity.name == "Epstein, Jeffrey"
        assert entity.normalized_name == "Jeffrey Epstein"
        assert entity.connection_count == 0
        assert entity.flight_count == 0
        assert entity.entity_type == EntityType.UNKNOWN

    def test_entity_full_valid(self):
        """Test entity with all fields populated"""
        entity = Entity(
            name="Epstein, Jeffrey",
            normalized_name="Jeffrey Epstein",
            name_variations=["Jeff Epstein", "J. Epstein"],
            entity_type=EntityType.PERSON,
            in_black_book=True,
            is_billionaire=True,
            connection_count=262,
            flight_count=8,
            total_documents=15,
            sources=[SourceType.BLACK_BOOK, SourceType.FLIGHT_LOGS],
            black_book_pages=["p1", "p5"],
            top_connections=[
                TopConnection(name="Maxwell, Ghislaine", flights_together=50)
            ],
            documents=[
                DocumentReference(
                    path="/data/flight_logs.md",
                    type="flight_log",
                    context="Mentioned in flight logs"
                )
            ]
        )
        assert entity.connection_count == 262
        assert entity.in_black_book is True
        assert len(entity.sources) == 2
        assert len(entity.top_connections) == 1

    def test_entity_name_normalization(self):
        """Test name normalization removes extra whitespace"""
        entity = Entity(
            name="Test",
            normalized_name="  Epstein,  Jeffrey  "
        )
        # Should strip and collapse whitespace
        assert entity.normalized_name == "Epstein, Jeffrey"

    def test_entity_top_connections_auto_sorted(self):
        """Test top connections are automatically sorted by flights_together"""
        entity = Entity(
            name="Test",
            normalized_name="Test",
            top_connections=[
                TopConnection(name="A", flights_together=5),
                TopConnection(name="B", flights_together=10),
                TopConnection(name="C", flights_together=3)
            ]
        )
        # Should be sorted descending by flights_together
        assert entity.top_connections[0].flights_together == 10
        assert entity.top_connections[1].flights_together == 5
        assert entity.top_connections[2].flights_together == 3

    def test_entity_top_connections_limited_to_10(self):
        """Test top connections are limited to 10"""
        connections = [
            TopConnection(name=f"Person{i}", flights_together=i)
            for i in range(15)
        ]
        entity = Entity(
            name="Test",
            normalized_name="Test",
            top_connections=connections
        )
        # Should limit to 10 highest
        assert len(entity.top_connections) == 10

    def test_entity_sources_deduplicated(self):
        """Test duplicate sources are removed"""
        entity = Entity(
            name="Test",
            normalized_name="Test",
            sources=[
                SourceType.BLACK_BOOK,
                SourceType.FLIGHT_LOGS,
                SourceType.BLACK_BOOK  # Duplicate
            ]
        )
        # Should remove duplicates
        assert len(entity.sources) == 2
        assert SourceType.BLACK_BOOK in entity.sources
        assert SourceType.FLIGHT_LOGS in entity.sources

    def test_entity_document_count_validation(self):
        """Test document count auto-corrects if inconsistent"""
        entity = Entity(
            name="Test",
            normalized_name="Test",
            total_documents=5,  # Inconsistent with document_types
            document_types={"flight_log": 3, "court_doc": 2}
        )
        # Should auto-correct to sum of document_types
        assert entity.total_documents == 5

    def test_entity_negative_connection_count_fails(self):
        """Test negative connection count is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            Entity(
                name="Test",
                normalized_name="Test",
                connection_count=-1
            )
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_entity_empty_name_fails(self):
        """Test empty name is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            Entity(
                name="",
                normalized_name="Test"
            )
        assert "at least 1 character" in str(exc_info.value)


class TestEntityBiography:
    """Test EntityBiography model validation"""

    def test_biography_valid(self):
        """Test valid biography"""
        bio = EntityBiography(
            entity_name="Epstein, Jeffrey",
            biography="Jeffrey Epstein was a financier and convicted sex offender.",
            last_updated="2025-01-15"
        )
        assert bio.entity_name == "Epstein, Jeffrey"
        assert len(bio.biography) > 10

    def test_biography_strips_whitespace(self):
        """Test biography text is stripped"""
        bio = EntityBiography(
            entity_name="Test",
            biography="  Valid biography text with padding  "
        )
        assert bio.biography == "Valid biography text with padding"

    def test_biography_too_short_fails(self):
        """Test biography under 10 characters is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            EntityBiography(
                entity_name="Test",
                biography="Short"
            )
        assert "at least 10 characters" in str(exc_info.value)

    def test_biography_invalid_timestamp_fails(self):
        """Test invalid timestamp format is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            EntityBiography(
                entity_name="Test",
                biography="Valid biography text",
                last_updated="not-a-date"
            )
        assert "Invalid timestamp format" in str(exc_info.value)

    def test_biography_valid_timestamp_formats(self):
        """Test various valid timestamp formats"""
        valid_dates = [
            "2025-01-15",
            "2025-01-15T10:30:00",
            "2025-01-15T10:30:00Z",
            "2025-01-15T10:30:00+00:00"
        ]
        for date in valid_dates:
            bio = EntityBiography(
                entity_name="Test",
                biography="Valid biography text",
                last_updated=date
            )
            assert bio.last_updated is not None


class TestEntityTag:
    """Test EntityTag model validation"""

    def test_tag_valid(self):
        """Test valid tag"""
        tag = EntityTag(
            entity_name="Trump, Donald",
            tags=["politics", "business"],
            primary_tag="politics"
        )
        assert len(tag.tags) == 2
        assert tag.primary_tag == "politics"

    def test_tag_normalization(self):
        """Test tags are normalized to lowercase"""
        tag = EntityTag(
            entity_name="Test",
            tags=["Politics", "  Business  ", "FINANCE"]
        )
        assert "politics" in tag.tags
        assert "business" in tag.tags
        assert "finance" in tag.tags

    def test_tag_deduplication(self):
        """Test duplicate tags are removed"""
        tag = EntityTag(
            entity_name="Test",
            tags=["politics", "Politics", "business", "politics"]
        )
        # Should have only unique tags
        assert len(tag.tags) == 2
        assert "politics" in tag.tags
        assert "business" in tag.tags

    def test_tag_primary_auto_added(self):
        """Test primary tag is auto-added to tags list if missing"""
        tag = EntityTag(
            entity_name="Test",
            tags=["business"],
            primary_tag="politics"
        )
        # Should auto-add primary_tag to tags
        assert "politics" in tag.tags
        assert len(tag.tags) == 2

    def test_tag_empty_list_fails(self):
        """Test empty tag list is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            EntityTag(
                entity_name="Test",
                tags=[]
            )
        assert "at least 1 item" in str(exc_info.value)

    def test_tag_all_empty_strings_fails(self):
        """Test tags with all empty strings are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            EntityTag(
                entity_name="Test",
                tags=["  ", "", "   "]
            )
        assert "At least one valid tag required" in str(exc_info.value)


class TestNetworkEdge:
    """Test NetworkEdge model validation"""

    def test_edge_valid(self):
        """Test valid edge"""
        edge = NetworkEdge(
            source="Epstein, Jeffrey",
            target="Maxwell, Ghislaine",
            weight=50
        )
        assert edge.source == "Epstein, Jeffrey"
        assert edge.target == "Maxwell, Ghislaine"
        assert edge.weight == 50

    def test_edge_self_loop_fails(self):
        """Test self-loop (source == target) is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            NetworkEdge(
                source="Epstein, Jeffrey",
                target="Epstein, Jeffrey",
                weight=1
            )
        assert "Self-loops not allowed" in str(exc_info.value)

    def test_edge_zero_weight_fails(self):
        """Test zero weight is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            NetworkEdge(
                source="A",
                target="B",
                weight=0
            )
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_edge_flight_count_sync(self):
        """Test flight_count and weight are synchronized"""
        edge = NetworkEdge(
            source="A",
            target="B",
            flight_count=10
        )
        # Should set weight from flight_count
        assert edge.weight == 10
        assert edge.flight_count == 10


class TestNetworkNode:
    """Test NetworkNode model validation"""

    def test_node_valid(self):
        """Test valid node"""
        node = NetworkNode(
            id="Epstein, Jeffrey",
            name="Epstein, Jeffrey",
            connection_count=262
        )
        assert node.id == "Epstein, Jeffrey"
        assert node.connection_count == 262

    def test_node_negative_connection_count_fails(self):
        """Test negative connection count is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            NetworkNode(
                id="Test",
                name="Test",
                connection_count=-1
            )
        assert "greater than or equal to 0" in str(exc_info.value)


class TestNetworkGraph:
    """Test NetworkGraph model validation"""

    def test_graph_valid(self):
        """Test valid graph"""
        nodes = [
            NetworkNode(id="A", name="A", connection_count=1),
            NetworkNode(id="B", name="B", connection_count=1)
        ]
        edges = [
            NetworkEdge(source="A", target="B", weight=1)
        ]
        graph = NetworkGraph(nodes=nodes, edges=edges)

        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1

    def test_graph_duplicate_node_ids_fails(self):
        """Test duplicate node IDs are rejected"""
        nodes = [
            NetworkNode(id="A", name="A", connection_count=1),
            NetworkNode(id="A", name="A duplicate", connection_count=2)
        ]
        with pytest.raises(ValidationError) as exc_info:
            NetworkGraph(nodes=nodes, edges=[])
        assert "Duplicate node IDs found" in str(exc_info.value)

    def test_graph_orphaned_edge_source_fails(self):
        """Test edge with non-existent source node is rejected"""
        nodes = [
            NetworkNode(id="B", name="B", connection_count=0)
        ]
        edges = [
            NetworkEdge(source="A", target="B", weight=1)  # A doesn't exist
        ]
        with pytest.raises(ValidationError) as exc_info:
            NetworkGraph(nodes=nodes, edges=edges)
        assert "Edge source 'A' not in nodes" in str(exc_info.value)

    def test_graph_orphaned_edge_target_fails(self):
        """Test edge with non-existent target node is rejected"""
        nodes = [
            NetworkNode(id="A", name="A", connection_count=0)
        ]
        edges = [
            NetworkEdge(source="A", target="B", weight=1)  # B doesn't exist
        ]
        with pytest.raises(ValidationError) as exc_info:
            NetworkGraph(nodes=nodes, edges=edges)
        assert "Edge target 'B' not in nodes" in str(exc_info.value)

    def test_graph_metadata_auto_sync(self):
        """Test metadata is auto-synced with node/edge counts"""
        nodes = [
            NetworkNode(id="A", name="A", connection_count=2),
            NetworkNode(id="B", name="B", connection_count=2),
            NetworkNode(id="C", name="C", connection_count=1)
        ]
        edges = [
            NetworkEdge(source="A", target="B", weight=5),
            NetworkEdge(source="A", target="C", weight=3)
        ]
        graph = NetworkGraph(nodes=nodes, edges=edges)

        # Should auto-compute metadata
        assert graph.metadata["total_nodes"] == 3
        assert graph.metadata["total_edges"] == 2
        assert graph.metadata["max_connections"] == 2

    def test_graph_get_node_by_id(self):
        """Test get_node_by_id helper method"""
        nodes = [
            NetworkNode(id="A", name="A", connection_count=0),
            NetworkNode(id="B", name="B", connection_count=0)
        ]
        graph = NetworkGraph(nodes=nodes, edges=[])

        node_a = graph.get_node_by_id("A")
        assert node_a is not None
        assert node_a.id == "A"

        node_c = graph.get_node_by_id("C")
        assert node_c is None

    def test_graph_get_edges_for_node(self):
        """Test get_edges_for_node helper method"""
        nodes = [
            NetworkNode(id="A", name="A", connection_count=2),
            NetworkNode(id="B", name="B", connection_count=1),
            NetworkNode(id="C", name="C", connection_count=1)
        ]
        edges = [
            NetworkEdge(source="A", target="B", weight=1),
            NetworkEdge(source="A", target="C", weight=1)
        ]
        graph = NetworkGraph(nodes=nodes, edges=edges)

        edges_a = graph.get_edges_for_node("A")
        assert len(edges_a) == 2

        edges_b = graph.get_edges_for_node("B")
        assert len(edges_b) == 1

    def test_graph_to_adjacency_list(self):
        """Test to_adjacency_list conversion"""
        nodes = [
            NetworkNode(id="A", name="A", connection_count=2),
            NetworkNode(id="B", name="B", connection_count=1),
            NetworkNode(id="C", name="C", connection_count=1)
        ]
        edges = [
            NetworkEdge(source="A", target="B", weight=1),
            NetworkEdge(source="A", target="C", weight=1)
        ]
        graph = NetworkGraph(nodes=nodes, edges=edges)

        adj = graph.to_adjacency_list()

        # Undirected graph, so both directions
        assert "B" in adj["A"]
        assert "C" in adj["A"]
        assert "A" in adj["B"]
        assert "A" in adj["C"]


class TestTopConnection:
    """Test TopConnection model validation"""

    def test_connection_valid(self):
        """Test valid connection"""
        conn = TopConnection(
            name="Maxwell, Ghislaine",
            flights_together=50
        )
        assert conn.name == "Maxwell, Ghislaine"
        assert conn.flights_together == 50

    def test_connection_negative_flights_fails(self):
        """Test negative flights_together is rejected"""
        with pytest.raises(ValidationError) as exc_info:
            TopConnection(
                name="Test",
                flights_together=-1
            )
        assert "greater than or equal to 0" in str(exc_info.value)


class TestDocumentReference:
    """Test DocumentReference model validation"""

    def test_document_reference_valid(self):
        """Test valid document reference"""
        doc = DocumentReference(
            path="/data/flight_logs.md",
            type="flight_log",
            context="Mentioned on page 5"
        )
        assert doc.path == "/data/flight_logs.md"
        assert doc.type == "flight_log"
        assert doc.context == "Mentioned on page 5"

    def test_document_reference_optional_context(self):
        """Test document reference without context"""
        doc = DocumentReference(
            path="/data/court_docs.md",
            type="court_doc"
        )
        assert doc.context is None


# Performance Tests (optional, for benchmarking)
class TestPerformance:
    """Performance benchmarks for Pydantic models"""

    def test_entity_construction_performance(self, benchmark=None):
        """Benchmark entity construction time"""
        if benchmark is None:
            pytest.skip("pytest-benchmark not installed")

        entity_data = {
            "name": "Epstein, Jeffrey",
            "normalized_name": "Jeffrey Epstein",
            "connection_count": 262,
            "flight_count": 8,
            "total_documents": 15,
            "sources": [SourceType.BLACK_BOOK, SourceType.FLIGHT_LOGS]
        }

        def construct_entity():
            return Entity(**entity_data)

        # Should complete in <1ms
        result = benchmark(construct_entity)
        assert result is not None

    def test_graph_validation_performance(self, benchmark=None):
        """Benchmark graph validation time for 100 nodes, 500 edges"""
        if benchmark is None:
            pytest.skip("pytest-benchmark not installed")

        nodes = [
            NetworkNode(id=f"Node{i}", name=f"Node{i}", connection_count=5)
            for i in range(100)
        ]
        edges = [
            NetworkEdge(source=f"Node{i}", target=f"Node{(i+1)%100}", weight=1)
            for i in range(500)
        ]

        def construct_graph():
            return NetworkGraph(nodes=nodes, edges=edges)

        # Should complete in <10ms for 100 nodes
        result = benchmark(construct_graph)
        assert result is not None
