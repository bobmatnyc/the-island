"""
API Routes - New API-first endpoints

Design Decision: Separate API Routes File
Rationale: Keep new API endpoints separate from existing app.py
to avoid conflicts during refactoring. Import and register these
routes in app.py.

All business logic delegated to service layer.
Frontend makes simple JSON API calls.
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List
from pathlib import Path

# Import services
from services.entity_service import EntityService
from services.flight_service import FlightService
from services.document_service import DocumentService
from services.network_service import NetworkService

# Initialize router
router = APIRouter(prefix="/api/v2", tags=["v2"])

# Initialize services (will be set by app.py)
entity_service: Optional[EntityService] = None
flight_service: Optional[FlightService] = None
document_service: Optional[DocumentService] = None
network_service: Optional[NetworkService] = None


def init_services(data_path: Path):
    """Initialize all services

    Args:
        data_path: Path to data directory

    Call this from app.py startup event
    """
    global entity_service, flight_service, document_service, network_service

    entity_service = EntityService(data_path)
    flight_service = FlightService(data_path)
    document_service = DocumentService(data_path)
    network_service = NetworkService(data_path)


# ============================================================================
# Entity Endpoints
# ============================================================================

@router.get("/entities")
async def get_entities(
    search: Optional[str] = Query(None, description="Search entity names"),
    entity_type: Optional[str] = Query(None, description="Filter by type"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    source: Optional[str] = Query(None, description="Filter by source"),
    filter_billionaires: bool = Query(False, description="Only billionaires"),
    filter_connected: bool = Query(False, description="Only connected entities"),
    sort_by: str = Query("documents", enum=["documents", "connections", "name"]),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get filtered and sorted entity list

    All filtering and sorting logic handled by EntityService.
    Frontend just makes API call and displays results.
    """
    if not entity_service:
        raise HTTPException(status_code=500, detail="Entity service not initialized")

    return entity_service.get_entities(
        search=search,
        entity_type=entity_type,
        tag=tag,
        source=source,
        filter_billionaires=filter_billionaires,
        filter_connected=filter_connected,
        sort_by=sort_by,
        limit=limit,
        offset=offset
    )


@router.get("/entities/{entity_name}")
async def get_entity(entity_name: str):
    """Get single entity with all details

    Returns entity with bio, tags, connections, documents.
    """
    if not entity_service:
        raise HTTPException(status_code=500, detail="Entity service not initialized")

    entity = entity_service.get_entity_by_name(entity_name)

    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_name}' not found")

    return entity


@router.get("/entities/{entity_name}/connections")
async def get_entity_connections(
    entity_name: str,
    max_hops: int = Query(2, ge=1, le=3, description="Max degrees of separation"),
    min_strength: int = Query(1, ge=1, description="Min connection strength")
):
    """Get entity network connections

    Returns network subgraph centered on entity.
    """
    if not entity_service:
        raise HTTPException(status_code=500, detail="Entity service not initialized")

    return entity_service.get_entity_connections(
        entity_name=entity_name,
        max_hops=max_hops,
        min_strength=min_strength
    )


@router.get("/entities/stats/summary")
async def get_entity_stats():
    """Get entity statistics

    Returns counts by type, tag, billionaires, etc.
    """
    if not entity_service:
        raise HTTPException(status_code=500, detail="Entity service not initialized")

    return entity_service.get_statistics()


# ============================================================================
# Flight Endpoints
# ============================================================================

@router.get("/flights")
async def get_flights(
    passenger: Optional[str] = Query(None, description="Filter by passenger"),
    from_airport: Optional[str] = Query(None, description="Origin airport code"),
    to_airport: Optional[str] = Query(None, description="Destination airport code"),
    start_date: Optional[str] = Query(None, description="Start date (MM/DD/YYYY)"),
    end_date: Optional[str] = Query(None, description="End date (MM/DD/YYYY)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get filtered flight list

    All filtering logic in FlightService.
    """
    if not flight_service:
        raise HTTPException(status_code=500, detail="Flight service not initialized")

    return flight_service.get_all_flights(
        passenger=passenger,
        from_airport=from_airport,
        to_airport=to_airport,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )


@router.get("/flights/routes")
async def get_flight_routes():
    """Get all flights grouped by route for map visualization

    Returns routes with frequency, geocoded locations, etc.
    """
    if not flight_service:
        raise HTTPException(status_code=500, detail="Flight service not initialized")

    return flight_service.get_flights_grouped_by_route()


@router.get("/flights/passenger/{passenger_name}")
async def get_passenger_flights(passenger_name: str):
    """Get all flights for a specific passenger

    Returns flight history, routes, date range.
    """
    if not flight_service:
        raise HTTPException(status_code=500, detail="Flight service not initialized")

    return flight_service.get_flights_by_passenger(passenger_name)


@router.get("/flights/stats")
async def get_flight_stats():
    """Get flight statistics

    Returns total flights, unique passengers, routes, etc.
    """
    if not flight_service:
        raise HTTPException(status_code=500, detail="Flight service not initialized")

    return flight_service.get_statistics()


# ============================================================================
# Document Endpoints
# ============================================================================

@router.get("/documents/search")
async def search_documents(
    q: Optional[str] = Query(None, description="Full-text search"),
    entity: Optional[str] = Query(None, description="Filter by entity mention"),
    doc_type: Optional[str] = Query(None, description="Filter by type (email, pdf)"),
    source: Optional[str] = Query(None, description="Filter by source"),
    classification: Optional[str] = Query(None, description="Filter by classification"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Search documents with filters

    All search logic in DocumentService.
    """
    if not document_service:
        raise HTTPException(status_code=500, detail="Document service not initialized")

    return document_service.search_documents(
        q=q,
        entity=entity,
        doc_type=doc_type,
        source=source,
        classification=classification,
        limit=limit,
        offset=offset
    )


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get single document with full content

    Returns document metadata and text content.
    """
    if not document_service:
        raise HTTPException(status_code=500, detail="Document service not initialized")

    document = document_service.get_document_by_id(doc_id)

    if not document:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")

    return document


@router.get("/documents/entity/{entity_name}")
async def get_entity_documents(entity_name: str):
    """Get all documents mentioning an entity

    Returns document list filtered by entity mention.
    """
    if not document_service:
        raise HTTPException(status_code=500, detail="Document service not initialized")

    return document_service.get_documents_by_entity(entity_name)


@router.get("/documents/stats")
async def get_document_stats():
    """Get document statistics

    Returns counts by type, classification, source.
    """
    if not document_service:
        raise HTTPException(status_code=500, detail="Document service not initialized")

    return document_service.get_statistics()


# ============================================================================
# Network Endpoints
# ============================================================================

@router.get("/network/graph")
async def get_network_graph(
    min_connections: int = Query(0, ge=0, description="Minimum connections"),
    max_nodes: int = Query(500, ge=1, le=1000, description="Maximum nodes"),
    deduplicate: bool = Query(True, description="Apply name disambiguation"),
    entity_filter: Optional[str] = Query(None, description="Filter to entity")
):
    """Get network graph data for visualization

    All graph filtering and deduplication in NetworkService.
    """
    if not network_service:
        raise HTTPException(status_code=500, detail="Network service not initialized")

    return network_service.get_network(
        min_connections=min_connections,
        max_nodes=max_nodes,
        deduplicate=deduplicate,
        entity_filter=entity_filter
    )


@router.get("/network/path")
async def find_path(
    entity_a: str = Query(..., description="First entity name"),
    entity_b: str = Query(..., description="Second entity name")
):
    """Find shortest path between two entities

    Uses BFS algorithm to find shortest path.
    """
    if not network_service:
        raise HTTPException(status_code=500, detail="Network service not initialized")

    return network_service.find_shortest_path(entity_a, entity_b)


@router.get("/network/subgraph/{entity_name}")
async def get_entity_subgraph(
    entity_name: str,
    max_hops: int = Query(2, ge=1, le=3, description="Max hops"),
    min_strength: int = Query(1, ge=1, description="Min connection strength")
):
    """Get subgraph centered on entity

    Returns nodes and edges within max_hops of entity.
    """
    if not network_service:
        raise HTTPException(status_code=500, detail="Network service not initialized")

    return network_service.get_entity_subgraph(
        entity_name=entity_name,
        max_hops=max_hops,
        min_strength=min_strength
    )


@router.get("/network/stats")
async def get_network_stats():
    """Get network statistics

    Returns nodes, edges, density, most connected entities.
    """
    if not network_service:
        raise HTTPException(status_code=500, detail="Network service not initialized")

    return network_service.get_statistics()


# ============================================================================
# Unified Search Endpoint
# ============================================================================

@router.get("/search")
async def unified_search(
    q: str = Query(..., min_length=1, description="Search query"),
    type: Optional[str] = Query(None, enum=["entities", "documents", "flights"], description="Limit to type"),
    limit: int = Query(50, ge=1, le=100)
):
    """Unified search across entities, documents, and flights

    Searches all data types and returns ranked results.
    """
    if not all([entity_service, document_service, flight_service]):
        raise HTTPException(status_code=500, detail="Services not initialized")

    results = {
        "query": q,
        "results": {
            "entities": [],
            "documents": [],
            "flights": []
        },
        "total": 0
    }

    # Search entities
    if not type or type == "entities":
        entity_results = entity_service.get_entities(search=q, limit=limit)
        results["results"]["entities"] = entity_results["entities"]

    # Search documents
    if not type or type == "documents":
        doc_results = document_service.search_documents(q=q, limit=limit)
        results["results"]["documents"] = doc_results["documents"]

    # Search flights (by passenger name)
    if not type or type == "flights":
        flight_results = flight_service.get_all_flights(passenger=q, limit=limit)
        results["results"]["flights"] = flight_results["flights"]

    # Calculate total
    results["total"] = (
        len(results["results"]["entities"]) +
        len(results["results"]["documents"]) +
        len(results["results"]["flights"])
    )

    return results
