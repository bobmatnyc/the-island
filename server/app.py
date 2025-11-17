#!/usr/bin/env python3
"""
Epstein Archive Document Explorer - FastAPI Server
Serves data, search APIs, visualizations, and ingestion progress
"""

from fastapi import FastAPI, Query, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, HttpUrl
from pathlib import Path
import json
from typing import List, Optional, Dict
import uvicorn
import subprocess
import secrets
import urllib.parse
import re
from datetime import datetime
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env.local
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
METADATA_DIR = DATA_DIR / "metadata"
MD_DIR = DATA_DIR / "md"
LOGS_DIR = PROJECT_ROOT / "logs"

# Initialize OpenRouter client
openrouter_client = None
openrouter_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")

def get_openrouter_client():
    """Initialize OpenRouter client (lazy loading)"""
    global openrouter_client
    if openrouter_client is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not set in .env.local")

        openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
    return openrouter_client

app = FastAPI(
    title="Epstein Document Archive API",
    description="Search and explore the Epstein document archive",
    version="1.0.0"
)

# Basic auth for password protection
security = HTTPBasic()

# Load credentials from file
import os
CREDENTIALS_FILE = Path(__file__).parent / ".credentials"

def load_credentials():
    """Load username:password pairs from .credentials file (dynamically reloaded on each call)"""
    credentials = {}
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if ':' in line:
                        username, password = line.split(':', 1)
                        credentials[username.strip()] = password.strip()
    else:
        # Fallback to defaults
        credentials = {
            os.getenv("ARCHIVE_USERNAME", "epstein"): os.getenv("ARCHIVE_PASSWORD", "archive2025")
        }
    return credentials

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify username and password against .credentials file (dynamically reloaded)"""
    # Reload credentials on each request for dynamic updates
    current_credentials = load_credentials()

    if credentials.username in current_credentials:
        correct_password = secrets.compare_digest(
            credentials.password,
            current_credentials[credentials.username]
        )
        if correct_password:
            return credentials.username

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Basic"},
    )

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "web"), name="static")

# Data caches
entity_stats = {}
network_data = {}
semantic_index = {}
classifications = {}
timeline_data = {}

def load_data():
    """Load all JSON data into memory with error handling"""
    global entity_stats, network_data, semantic_index, classifications, timeline_data

    print("Loading data...")

    # Entity statistics
    stats_path = METADATA_DIR / "entity_statistics.json"
    if stats_path.exists():
        try:
            with open(stats_path) as f:
                data = json.load(f)
                # Fix: entity_statistics.json has structure: {statistics: {entity_name: {...}}}
                entity_stats = data.get("statistics", {})
                print(f"  ✓ Loaded {len(entity_stats)} entities from entity_statistics.json")
        except Exception as e:
            print(f"  ✗ Failed to load entity_statistics.json: {e}")
            entity_stats = {}
    else:
        print(f"  ✗ Entity statistics file not found: {stats_path}")
        entity_stats = {}

    # Network
    network_path = METADATA_DIR / "entity_network.json"
    if network_path.exists():
        try:
            with open(network_path) as f:
                network_data = json.load(f)
                print(f"  ✓ Loaded {len(network_data.get('nodes', []))} network nodes")
        except Exception as e:
            print(f"  ✗ Failed to load entity_network.json: {e}")
            network_data = {}
    else:
        print(f"  ✗ Network file not found: {network_path}")
        network_data = {}

    # Semantic index
    semantic_path = METADATA_DIR / "semantic_index.json"
    if semantic_path.exists():
        try:
            with open(semantic_path) as f:
                data = json.load(f)
                semantic_index = data.get("entity_to_documents", {})
                print(f"  ✓ Loaded semantic index for {len(semantic_index)} entities")
        except Exception as e:
            print(f"  ✗ Failed to load semantic_index.json: {e}")
            semantic_index = {}
    else:
        print(f"  ✗ Semantic index not found: {semantic_path}")
        semantic_index = {}

    # Classifications
    class_path = METADATA_DIR / "document_classifications.json"
    if class_path.exists():
        try:
            with open(class_path) as f:
                data = json.load(f)
                classifications = data.get("results", {})
                print(f"  ✓ Loaded {len(classifications)} document classifications")
        except Exception as e:
            print(f"  ✗ Failed to load document_classifications.json: {e}")
            classifications = {}
    else:
        print(f"  ✗ Classifications file not found: {class_path}")
        classifications = {}

    # Timeline
    timeline_path = METADATA_DIR / "timeline.json"
    if timeline_path.exists():
        try:
            with open(timeline_path) as f:
                timeline_data = json.load(f)
                print(f"  ✓ Loaded timeline data")
        except Exception as e:
            print(f"  ✗ Failed to load timeline.json: {e}")
            timeline_data = {}
    else:
        print(f"  ✗ Timeline file not found: {timeline_path}")
        timeline_data = {}

    print(f"\n📊 Data Loading Summary:")
    print(f"  Entities: {len(entity_stats)}")
    print(f"  Network nodes: {len(network_data.get('nodes', []))}")
    print(f"  Network edges: {len(network_data.get('edges', []))}")
    print(f"  Classifications: {len(classifications)}")

def get_ocr_status():
    """Get current OCR processing status

    Design Decision: Safe Number Parsing
    Rationale: OCR status script outputs formatted numbers with commas (e.g., "33,572")
    which Python's int() cannot parse directly. We need to strip commas before conversion.

    Error Handling: Return safe fallback values rather than failing the entire API call.
    """
    try:
        result = subprocess.run(
            ["python3", str(PROJECT_ROOT / "scripts/extraction/check_ocr_status.py")],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = result.stdout

        # Parse output
        status = {
            "active": "Progress:" in output,
            "progress": 0,
            "processed": 0,
            "total": 0,
            "emails_found": 0,
            "failed": 0
        }

        def safe_int(value: str) -> int:
            """Parse integer safely, removing commas and whitespace"""
            try:
                return int(value.replace(',', '').strip())
            except (ValueError, AttributeError):
                return 0

        def safe_float(value: str) -> float:
            """Parse float safely, removing percent signs and parentheses"""
            try:
                cleaned = value.replace('%', '').replace('(', '').replace(')', '').strip()
                return float(cleaned)
            except (ValueError, AttributeError):
                return 0.0

        for line in output.split('\n'):
            if "Progress:" in line:
                # Example: "Progress: 15,100 / 33,572 (45.0%)"
                parts = line.split()
                if len(parts) >= 6:
                    status["processed"] = safe_int(parts[1])
                    status["total"] = safe_int(parts[3])
                    status["progress"] = safe_float(parts[4])
            elif "Email candidates found:" in line:
                status["emails_found"] = safe_int(line.split(':')[1])
            elif "Failed:" in line:
                status["failed"] = safe_int(line.split(':')[1].split()[0])

        return status
    except subprocess.TimeoutExpired:
        return {"active": False, "error": "OCR status check timeout"}
    except Exception as e:
        return {"active": False, "error": str(e)}

@app.on_event("startup")
async def startup_event():
    """Load data on startup"""
    load_data()

@app.get("/")
async def root():
    """Redirect to web interface"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="0; url=/static/index.html" />
    </head>
    <body>
        <p>Redirecting to <a href="/static/index.html">Document Explorer</a>...</p>
    </body>
    </html>
    """)

@app.get("/ROADMAP.md")
async def get_roadmap():
    """Serve the ROADMAP.md file"""
    roadmap_path = PROJECT_ROOT / "ROADMAP.md"
    if roadmap_path.exists():
        return FileResponse(roadmap_path, media_type="text/markdown")
    raise HTTPException(status_code=404, detail="ROADMAP.md not found")

@app.get("/api/stats")
async def get_stats(username: str = Depends(authenticate)):
    """Get overall statistics

    Design Decision: Frontend Compatibility
    Rationale: Frontend expects 'total_connections' field for network edges display.
    Also includes 'sources' field for source list rendering.

    Error Handling: Returns safe fallback values if data not loaded.
    """
    # Load source index for sources list
    source_list = []
    source_index_path = METADATA_DIR / "source_index.json"
    if source_index_path.exists():
        try:
            with open(source_index_path) as f:
                sources_data = json.load(f)
                # source_index.json has structure: {sources: {key: {description: ...}}}
                sources = sources_data.get("sources", {})
                for source_key, source_info in sources.items():
                    description = source_info.get("description", source_key)
                    if description:
                        source_list.append(description)
                    else:
                        # Fallback to formatted key name
                        source_list.append(source_key.replace("_", " ").title())
        except Exception as e:
            print(f"Error loading source index: {e}")

    return {
        "total_entities": len(entity_stats),
        "total_documents": len(classifications),
        "network_nodes": len(network_data.get("nodes", [])),
        "network_edges": len(network_data.get("edges", [])),
        "total_connections": len(network_data.get("edges", [])),  # Frontend expects this field
        "timeline_events": timeline_data.get("total_events", 0),
        "date_range": timeline_data.get("date_range", {}),
        "sources": source_list  # Frontend expects this field
    }

@app.get("/api/ingestion/status")
async def get_ingestion_status(username: str = Depends(authenticate)):
    """Get ingestion progress status

    Design Decision: Frontend Compatibility
    Rationale: Frontend expects specific field names:
    - status, files_processed, total_files, progress_percentage
    - current_source, last_updated

    Returns flat structure matching frontend expectations.
    """
    ocr_status = get_ocr_status()

    # Get entity stats
    merged_index_path = MD_DIR / "entities/ENTITIES_INDEX_MERGED.json"
    if merged_index_path.exists():
        try:
            with open(merged_index_path) as f:
                entity_data = json.load(f)
                entities_merged = entity_data.get("duplicates_merged", 0)
                total_entities = entity_data.get("total_entities", 0)
        except Exception as e:
            print(f"Error loading merged index: {e}")
            entities_merged = 0
            total_entities = len(entity_stats)
    else:
        entities_merged = 0
        total_entities = len(entity_stats)

    # Calculate progress percentage
    processed = ocr_status.get("processed", 0)
    total = ocr_status.get("total", 0)
    progress_pct = (processed / total * 100) if total > 0 else 0

    # Determine status
    if processed >= total and total > 0:
        status_text = "complete"
    elif ocr_status.get("active"):
        status_text = "processing"
    else:
        status_text = "idle"

    # Get last updated timestamp
    progress_path = METADATA_DIR.parent / "sources/house_oversight_nov2025/ocr_progress.json"
    last_updated = None
    current_source = "House Oversight Committee Nov 2025"

    if progress_path.exists():
        try:
            with open(progress_path) as f:
                progress_data = json.load(f)
                last_updated = progress_data.get("last_updated")
        except Exception:
            pass

    # Return frontend-compatible format
    return {
        "status": status_text,
        "files_processed": processed,
        "total_files": total,
        "progress_percentage": progress_pct,
        "current_source": current_source if status_text == "processing" else None,
        "last_updated": last_updated,
        "ocr": ocr_status,  # Keep detailed OCR status for compatibility
        "entities": {
            "total": total_entities,
            "duplicates_merged": entities_merged,
            "in_network": len(network_data.get("nodes", [])),
            "billionaires": sum(1 for e in entity_stats.values() if e.get("is_billionaire"))
        },
        "documents": {
            "total": len(classifications),
            "classified": len(classifications),
            "emails_found": ocr_status.get("emails_found", 0)
        },
        "network": {
            "nodes": len(network_data.get("nodes", [])),
            "edges": len(network_data.get("edges", []))
        }
    }

@app.get("/api/entities")
async def get_entities(
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    sort_by: str = Query("documents", enum=["documents", "connections", "name"]),
    filter_billionaires: bool = Query(False),
    filter_connected: bool = Query(False),
    username: str = Depends(authenticate)
):
    """Get list of entities with optional filtering and sorting"""
    entities_list = list(entity_stats.values())

    if filter_billionaires:
        entities_list = [e for e in entities_list if e.get("is_billionaire", False)]
    if filter_connected:
        entities_list = [e for e in entities_list if e.get("connection_count", 0) > 0]

    if sort_by == "documents":
        entities_list.sort(key=lambda e: e.get("total_documents", 0), reverse=True)
    elif sort_by == "connections":
        entities_list.sort(key=lambda e: e.get("connection_count", 0), reverse=True)
    elif sort_by == "name":
        entities_list.sort(key=lambda e: e.get("name", ""))

    total = len(entities_list)
    entities_page = entities_list[offset:offset+limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "entities": entities_page
    }

@app.get("/api/entities/{name}")
async def get_entity(name: str, username: str = Depends(authenticate)):
    """Get detailed information about a specific entity with disambiguation support

    Handles name variations like:
    - "Je Je Epstein" -> "Jeffrey Epstein"
    - "Ghislaine Ghislaine" -> "Ghislaine Maxwell"
    """
    disambiguator = get_disambiguator()

    # Try disambiguation search first
    entity = disambiguator.search_entity(name, entity_stats)

    if not entity:
        raise HTTPException(
            status_code=404,
            detail=f"Entity not found: '{name}'. Try canonical name or check spelling."
        )

    # Add normalized name to response
    return {
        **entity,
        "search_name": name,
        "canonical_name": disambiguator.normalize_name(name)
    }

@app.get("/api/network")
async def get_network(
    min_connections: int = Query(0),
    max_nodes: int = Query(500, le=1000),
    deduplicate: bool = Query(True),
    username: str = Depends(authenticate)
):
    """Get network graph data with optional deduplication

    Query Parameters:
        min_connections: Minimum connections to include node (default: 0)
        max_nodes: Maximum nodes to return (default: 500, max: 1000)
        deduplicate: Apply name disambiguation to merge duplicates (default: True)

    Returns:
        Network graph with nodes, edges, and metadata
    """
    # Get disambiguator
    disambiguator = get_disambiguator()

    # Get nodes
    nodes = network_data.get("nodes", [])

    # Apply deduplication if requested
    if deduplicate:
        original_count = len(nodes)
        nodes = disambiguator.merge_duplicate_nodes(nodes)
        deduplicated_count = original_count - len(nodes)
        print(f"Deduplicated {deduplicated_count} duplicate nodes ({original_count} -> {len(nodes)})")

    # Filter by minimum connections
    nodes = [
        n for n in nodes
        if n.get("connection_count", 0) >= min_connections
    ]

    # Sort by connections and limit
    nodes.sort(key=lambda n: n.get("connection_count", 0), reverse=True)
    nodes = nodes[:max_nodes]

    # Get node IDs for edge filtering
    node_ids = {n["id"] for n in nodes}

    # Filter edges
    edges = [
        e for e in network_data.get("edges", [])
        if e["source"] in node_ids and e["target"] in node_ids
    ]

    # Build node name mapping for edge deduplication
    if deduplicate:
        node_mapping = {n.get("id", ""): n.get("name", "") for n in nodes}
        edges = disambiguator.deduplicate_edges(edges, node_mapping)

    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            **network_data.get("metadata", {}),
            "deduplicated": deduplicate,
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }
    }

@app.get("/api/search")
async def search(
    q: str = Query(..., min_length=1),
    type: Optional[str] = Query(None),
    limit: int = Query(50, le=500),
    username: str = Depends(authenticate)
):
    """Search for entities or documents"""
    results = []

    for entity_name, entity_data in entity_stats.items():
        if q.lower() in entity_name.lower():
            results.append({
                "type": "entity",
                "name": entity_name,
                "data": entity_data
            })

    for doc_path, doc_data in classifications.items():
        if type and doc_data.get("type") != type:
            continue

        if q.lower() in doc_path.lower():
            results.append({
                "type": "document",
                "path": doc_path,
                "data": doc_data
            })

    return {
        "query": q,
        "total": len(results),
        "results": results[:limit]
    }

@app.get("/api/timeline")
async def get_timeline(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(1000, le=5000),
    username: str = Depends(authenticate)
):
    """Get timeline events"""
    events = timeline_data.get("events", [])

    if start_date:
        events = [e for e in events if e["date"] >= start_date]
    if end_date:
        events = [e for e in events if e["date"] <= end_date]

    return {
        "total": len(events),
        "events": events[:limit],
        "date_range": timeline_data.get("date_range", {})
    }

# Chatbot models
class ChatMessage(BaseModel):
    message: str

# Project context for chatbot
PROJECT_CONTEXT = """
You are a helpful assistant for the Epstein Document Archive project.

ARCHIVE OVERVIEW:
- A comprehensive, publicly accessible archive of Epstein-related documents
- Source provenance tracking for all documents
- Automatic entity extraction and deduplication
- Network analysis of connections between entities
- OCR processing of scanned documents

CURRENT STATISTICS:
- 1,702 entities (71 duplicates merged)
- 387 network nodes
- 2,221 network connections (flight co-occurrences)
- Multiple document sources being processed

KEY FEATURES:
1. Entity extraction from documents (people, organizations)
2. Entity disambiguation (fuzzy matching to merge duplicates)
3. Network graph visualization of entity connections
4. Flight passenger list analysis
5. Real-time OCR processing status
6. Document classification and semantic indexing

IMPORTANT RESTRICTIONS:
- DO NOT share any personal information about the host machine
- DO NOT provide system paths or configuration details
- DO NOT discuss implementation specifics that could expose security vulnerabilities
- Focus responses on the archive content, entities, and publicly available documents

You can answer questions about:
- Specific entities and their connections
- Document sources and classifications
- Network patterns and relationships
- Archive statistics and progress
- How to use the archive interface

NOTE: Responses may be slower as this runs on a private machine with local LLM inference.
"""

@app.post("/api/chat")
async def chat(
    message: ChatMessage,
    username: str = Depends(authenticate)
):
    """Chat with GPT-4.5 assistant about the archive with integrated search"""
    try:
        # Perform multi-vector search to gather relevant context
        search_results = []
        query_lower = message.message.lower()

        # 1. Search entities
        matching_entities = []
        for entity_name, entity_data in entity_stats.items():
            if query_lower in entity_name.lower():
                matching_entities.append({
                    "name": entity_name,
                    "documents": entity_data.get("total_documents", 0),
                    "connections": entity_data.get("connection_count", 0),
                    "billionaire": entity_data.get("is_billionaire", False)
                })

        if matching_entities:
            search_results.append(f"\nRELEVANT ENTITIES FOUND ({len(matching_entities)}):")
            for e in matching_entities[:5]:  # Top 5
                search_results.append(f"- {e['name']}: {e['documents']} documents, {e['connections']} connections" +
                                    (" [BILLIONAIRE]" if e['billionaire'] else ""))

        # 2. Search documents
        matching_docs = []
        for doc_path, doc_data in classifications.items():
            if query_lower in doc_path.lower():
                matching_docs.append({
                    "path": doc_path,
                    "type": doc_data.get("type", "unknown")
                })

        if matching_docs:
            search_results.append(f"\nRELEVANT DOCUMENTS FOUND ({len(matching_docs)}):")
            for d in matching_docs[:5]:
                search_results.append(f"- {d['path']} (Type: {d['type']})")

        # 3. Check semantic index for entity co-occurrences
        for entity_name in matching_entities[:3]:  # Top 3 entities
            if entity_name['name'] in semantic_index:
                docs = semantic_index[entity_name['name']]
                search_results.append(f"\n{entity_name['name']} appears in {len(docs)} documents")

        # Build context with search results
        search_context = "\n".join(search_results) if search_results else "\n[No direct matches found in database]"

        stats_context = f"""
        CURRENT ARCHIVE STATUS:
        - Total Entities: {len(entity_stats)}
        - Network Nodes: {len(network_data.get('nodes', []))}
        - Network Edges: {len(network_data.get('edges', []))}
        - Documents Classified: {len(classifications)}

        SEARCH RESULTS FOR THIS QUERY:
        {search_context}
        """

        full_context = PROJECT_CONTEXT + "\n" + stats_context

        # Call OpenRouter GPT-4.5
        try:
            client = get_openrouter_client()

            completion = client.chat.completions.create(
                model=openrouter_model,
                messages=[
                    {
                        "role": "system",
                        "content": full_context
                    },
                    {
                        "role": "user",
                        "content": message.message
                    }
                ],
                temperature=0.7,
                max_tokens=1000,
                timeout=30.0  # 30 second timeout
            )

            response = completion.choices[0].message.content.strip()

            return {
                "response": response,
                "model": openrouter_model,
                "search_results": {
                    "entities": matching_entities[:5],
                    "documents": matching_docs[:5]
                }
            }

        except Exception as api_error:
            # Log the error for debugging
            print(f"OpenRouter API error: {api_error}")
            return {
                "response": f"Sorry, I'm having trouble connecting to the AI service. Error: {str(api_error)}",
                "error": str(api_error)
            }

    except Exception as e:
        return {"response": f"Error: {str(e)}"}

# Initialize suggestion service
from services.suggestion_service import SuggestionService
from models.suggested_source import (
    SuggestedSourceCreate,
    SuggestedSourceUpdate,
    SourceStatus,
    SourcePriority
)

# Initialize entity disambiguation service
from services.entity_disambiguation import get_disambiguator

# Initialize entity enrichment service
from services.entity_enrichment import EntityEnrichmentService, format_for_ui

SUGGESTIONS_STORAGE = DATA_DIR / "suggestions" / "suggested_sources.json"
ENRICHMENT_STORAGE = METADATA_DIR / "entity_enrichments.json"

suggestion_service = SuggestionService(SUGGESTIONS_STORAGE)
enrichment_service = EntityEnrichmentService(ENRICHMENT_STORAGE)

# Source Suggestion Endpoints

@app.post("/api/suggestions", status_code=201)
async def create_suggestion(
    suggestion: SuggestedSourceCreate,
    username: str = Depends(authenticate)
):
    """Submit a new source suggestion

    Security Validation:
    - Only HTTP/HTTPS URLs allowed
    - Blocks localhost, private IPs, and suspicious patterns
    - URL scheme validation via Pydantic

    Returns:
        Created suggestion with generated ID
    """
    # Additional security validation
    parsed_url = urllib.parse.urlparse(suggestion.url)

    # Block suspicious domains
    suspicious_patterns = [
        r'localhost',
        r'127\.0\.0\.1',
        r'192\.168\.',
        r'10\.',
        r'172\.(1[6-9]|2[0-9]|3[0-1])\.',
        r'\.local$',
        r'file://',
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, suggestion.url, re.IGNORECASE):
            raise HTTPException(status_code=400, detail="URL contains suspicious patterns")

    # Create suggestion via service
    created = suggestion_service.create_suggestion(suggestion, submitted_by=username)

    return {
        "status": "success",
        "message": "Thank you for your suggestion! It will be reviewed before processing.",
        "suggestion": created
    }

@app.get("/api/suggestions")
async def list_suggestions(
    status: Optional[SourceStatus] = Query(None),
    priority: Optional[SourcePriority] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    username: str = Depends(authenticate)
):
    """Get list of source suggestions with filtering

    Query Parameters:
        status: Filter by status (pending, approved, rejected, processing, completed, failed)
        priority: Filter by priority (low, medium, high, critical)
        limit: Maximum results (default 100, max 500)
        offset: Pagination offset (default 0)

    Returns:
        Paginated list of suggestions with total count
    """
    suggestions, total = suggestion_service.get_all_suggestions(
        status=status,
        priority=priority,
        limit=limit,
        offset=offset
    )

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "suggestions": suggestions
    }

@app.get("/api/suggestions/{suggestion_id}")
async def get_suggestion(
    suggestion_id: str,
    username: str = Depends(authenticate)
):
    """Get single suggestion by ID

    Args:
        suggestion_id: UUID of suggestion

    Returns:
        Suggestion details

    Raises:
        404: Suggestion not found
    """
    suggestion = suggestion_service.get_suggestion_by_id(suggestion_id)

    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    return suggestion

@app.patch("/api/suggestions/{suggestion_id}/status")
async def update_suggestion_status(
    suggestion_id: str,
    update: SuggestedSourceUpdate,
    username: str = Depends(authenticate)
):
    """Update suggestion status and metadata (admin only)

    Updates:
        - status: Change workflow state
        - priority: Adjust processing priority
        - review_notes: Add review comments
        - document_count_estimate: Update estimate
        - tags: Update categorization

    Returns:
        Updated suggestion

    Raises:
        404: Suggestion not found
    """
    updated = suggestion_service.update_status(
        suggestion_id,
        update,
        reviewed_by=username
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    return {
        "status": "success",
        "suggestion": updated
    }

@app.delete("/api/suggestions/{suggestion_id}")
async def delete_suggestion(
    suggestion_id: str,
    username: str = Depends(authenticate)
):
    """Delete suggestion by ID (admin only)

    Args:
        suggestion_id: UUID of suggestion

    Returns:
        Success confirmation

    Raises:
        404: Suggestion not found
    """
    deleted = suggestion_service.delete_suggestion(suggestion_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    return {
        "status": "success",
        "message": "Suggestion deleted successfully"
    }

@app.get("/api/suggestions/stats/summary")
async def get_suggestion_statistics(username: str = Depends(authenticate)):
    """Get suggestion statistics for admin dashboard

    Returns:
        Statistics including counts by status, priority, and recent activity
    """
    stats = suggestion_service.get_statistics()
    return stats


# ============================================================================
# Entity Enrichment Endpoints
# ============================================================================

@app.get("/api/entities/{entity_id}/enrich")
async def enrich_entity(
    entity_id: str,
    force_refresh: bool = Query(False),
    username: str = Depends(authenticate)
):
    """Trigger web search enrichment for an entity.

    This endpoint performs web search to gather biographical information,
    professional background, and associations for the specified entity.

    Query Parameters:
        force_refresh: Bypass cache and force new search (default: False)

    Returns:
        Enrichment data with complete source provenance:
        - biography: Biographical summary from high-confidence sources
        - profession: Identified profession/occupation
        - sources: Complete list of sources with confidence scores
        - metadata: Search statistics and update timestamps

    Ethical Guidelines:
    - Only enriches entities already in archive documents
    - All data includes source attribution with confidence scores
    - Respects rate limits (max 5 searches per minute)
    - Returns disclaimer about accuracy

    Example Response:
        {
            "entity_id": "uuid",
            "entity_name": "Example Person",
            "summary": "Brief biography...",
            "facts": [
                {
                    "category": "Biography",
                    "text": "Information...",
                    "sources": [
                        {
                            "title": "Source Article Title",
                            "url": "https://...",
                            "confidence": 0.85,
                            "snippet": "Original text...",
                            "domain": "nytimes.com"
                        }
                    ]
                }
            ],
            "metadata": {
                "total_sources": 10,
                "average_confidence": 0.72,
                "last_updated": "2025-11-16T23:00:00Z",
                "search_queries": ['"Example Person" Epstein documents']
            },
            "disclaimer": "Information sourced from public web search..."
        }

    Error Cases:
        404: Entity not found in archive
        429: Rate limit exceeded (max 5 searches/minute)
        500: Search service unavailable
    """
    # Verify entity exists in archive
    entity_data = entity_stats.get(entity_id)
    if not entity_data:
        # Try to find by name (for backward compatibility)
        matching_entities = [
            (eid, edata) for eid, edata in entity_stats.items()
            if eid == entity_id or edata.get("name") == entity_id
        ]

        if not matching_entities:
            raise HTTPException(
                status_code=404,
                detail=f"Entity '{entity_id}' not found in archive. "
                       "Only entities in existing documents can be enriched."
            )

        entity_id, entity_data = matching_entities[0]

    entity_name = entity_data.get("name", entity_id)

    try:
        # Perform enrichment
        enrichment = await enrichment_service.enrich_entity(
            entity_id=entity_id,
            entity_name=entity_name,
            force_refresh=force_refresh
        )

        # Format for UI
        return format_for_ui(enrichment)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error enriching entity: {str(e)}"
        )


@app.get("/api/entities/{entity_id}/enrichment")
async def get_enrichment(
    entity_id: str,
    username: str = Depends(authenticate)
):
    """Get cached enrichment data for an entity.

    Returns cached enrichment if available and valid (within 30-day TTL),
    otherwise returns empty/pending status.

    This endpoint is fast as it only reads from cache without performing
    web searches. Use /enrich to trigger new search.

    Returns:
        Cached enrichment data if available, or:
        {
            "entity_id": "uuid",
            "entity_name": "Example Person",
            "status": "not_enriched",
            "message": "No enrichment data available. Use /enrich to generate."
        }

    Status Codes:
        200: Enrichment data returned (may be "not_enriched")
        404: Entity not found in archive
    """
    # Verify entity exists
    entity_data = entity_stats.get(entity_id)
    if not entity_data:
        matching_entities = [
            (eid, edata) for eid, edata in entity_stats.items()
            if eid == entity_id or edata.get("name") == entity_id
        ]

        if not matching_entities:
            raise HTTPException(
                status_code=404,
                detail=f"Entity '{entity_id}' not found in archive"
            )

        entity_id, entity_data = matching_entities[0]

    entity_name = entity_data.get("name", entity_id)

    # Check cache
    enrichment = await enrichment_service.get_enrichment(entity_id, entity_name)

    if enrichment:
        return format_for_ui(enrichment)
    else:
        return {
            "entity_id": entity_id,
            "entity_name": entity_name,
            "status": "not_enriched",
            "message": "No enrichment data available. Use POST /api/entities/{entity_id}/enrich to generate.",
            "cache_ttl_days": enrichment_service.CACHE_TTL_DAYS
        }


@app.post("/api/entities/enrich/batch")
async def enrich_batch(
    entity_ids: List[str],
    max_concurrent: int = Query(3, ge=1, le=5),
    username: str = Depends(authenticate)
):
    """Enrich multiple entities in a single request.

    Performs concurrent enrichment with rate limiting to respect
    search API constraints.

    Request Body:
        ["entity_id_1", "entity_id_2", ...]

    Query Parameters:
        max_concurrent: Maximum concurrent enrichments (1-5, default: 3)

    Returns:
        List of enrichment results (same format as /enrich)

    Rate Limiting:
        Automatically handles rate limiting across concurrent requests.
        Respects 5 searches/minute limit.

    Example:
        POST /api/entities/enrich/batch?max_concurrent=3
        ["Donald      Donald Trump", "Glenn       Glenn Dubin"]
    """
    if len(entity_ids) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 entities per batch request"
        )

    # Verify all entities exist
    entities = []
    for entity_id in entity_ids:
        entity_data = entity_stats.get(entity_id)
        if not entity_data:
            # Try name match
            matching = [
                (eid, edata) for eid, edata in entity_stats.items()
                if eid == entity_id or edata.get("name") == entity_id
            ]
            if not matching:
                raise HTTPException(
                    status_code=404,
                    detail=f"Entity '{entity_id}' not found"
                )
            entity_id, entity_data = matching[0]

        entities.append({
            "id": entity_id,
            "name": entity_data.get("name", entity_id)
        })

    try:
        # Perform batch enrichment
        enrichments = await enrichment_service.enrich_batch(
            entities=entities,
            max_concurrent=max_concurrent
        )

        # Format for UI
        return {
            "total": len(enrichments),
            "enrichments": [format_for_ui(e) for e in enrichments]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during batch enrichment: {str(e)}"
        )


@app.get("/api/enrichment/stats")
async def get_enrichment_statistics(username: str = Depends(authenticate)):
    """Get enrichment cache statistics.

    Returns:
        Statistics about cached enrichments:
        - total_enrichments: Total entities enriched
        - valid_enrichments: Within TTL (30 days)
        - stale_enrichments: Older than TTL
        - average_sources_per_entity: Avg number of sources
        - average_confidence: Avg source confidence score

    Example Response:
        {
            "total_enrichments": 150,
            "valid_enrichments": 120,
            "stale_enrichments": 30,
            "average_sources_per_entity": 8.5,
            "average_confidence": 0.72
        }
    """
    return enrichment_service.get_statistics()


# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on server shutdown"""
    await enrichment_service.close()


def main():
    """Run server"""
    import sys

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

    print("=" * 70)
    print("EPSTEIN DOCUMENT ARCHIVE SERVER")
    print("=" * 70)
    print(f"\nStarting server on http://localhost:{port}")
    creds = load_credentials()
    print(f"Credentials: {len(creds)} user(s) loaded (dynamically reloaded)")
    print(f"\nAPI docs: http://localhost:{port}/docs")
    print(f"Web interface: http://localhost:{port}/")
    print("\nPress Ctrl+C to stop")
    print("=" * 70)

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
