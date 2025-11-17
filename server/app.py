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

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
METADATA_DIR = DATA_DIR / "metadata"
MD_DIR = DATA_DIR / "md"
LOGS_DIR = PROJECT_ROOT / "logs"

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
    """Load all JSON data into memory"""
    global entity_stats, network_data, semantic_index, classifications, timeline_data

    print("Loading data...")

    # Entity statistics
    stats_path = METADATA_DIR / "entity_statistics.json"
    if stats_path.exists():
        with open(stats_path) as f:
            entity_stats = json.load(f).get("statistics", {})

    # Network
    network_path = METADATA_DIR / "entity_network.json"
    if network_path.exists():
        with open(network_path) as f:
            network_data = json.load(f)

    # Semantic index
    semantic_path = METADATA_DIR / "semantic_index.json"
    if semantic_path.exists():
        with open(semantic_path) as f:
            semantic_index = json.load(f).get("entity_to_documents", {})

    # Classifications
    class_path = METADATA_DIR / "document_classifications.json"
    if class_path.exists():
        with open(class_path) as f:
            classifications = json.load(f).get("results", {})

    # Timeline
    timeline_path = METADATA_DIR / "timeline.json"
    if timeline_path.exists():
        with open(timeline_path) as f:
            timeline_data = json.load(f)

    print(f"  Loaded {len(entity_stats)} entities")
    print(f"  Loaded {len(network_data.get('nodes', []))} network nodes")
    print(f"  Loaded {len(classifications)} classifications")

def get_ocr_status():
    """Get current OCR processing status"""
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

        for line in output.split('\n'):
            if "Progress:" in line:
                parts = line.split()
                status["processed"] = int(parts[1])
                status["total"] = int(parts[3])
                status["progress"] = float(parts[5].replace('%', '').replace('(', ''))
            elif "Email candidates found:" in line:
                status["emails_found"] = int(line.split(':')[1].strip())
            elif "Failed:" in line:
                status["failed"] = int(line.split(':')[1].split()[0])

        return status
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

@app.get("/api/stats")
async def get_stats(username: str = Depends(authenticate)):
    """Get overall statistics"""
    return {
        "total_entities": len(entity_stats),
        "total_documents": len(classifications),
        "network_nodes": len(network_data.get("nodes", [])),
        "network_edges": len(network_data.get("edges", [])),
        "timeline_events": timeline_data.get("total_events", 0),
        "date_range": timeline_data.get("date_range", {})
    }

@app.get("/api/ingestion/status")
async def get_ingestion_status(username: str = Depends(authenticate)):
    """Get ingestion progress status"""
    ocr_status = get_ocr_status()

    # Get entity stats
    merged_index_path = MD_DIR / "entities/ENTITIES_INDEX_MERGED.json"
    if merged_index_path.exists():
        with open(merged_index_path) as f:
            entity_data = json.load(f)
            entities_merged = entity_data.get("duplicates_merged", 0)
            total_entities = entity_data.get("total_entities", 0)
    else:
        entities_merged = 0
        total_entities = len(entity_stats)

    return {
        "ocr": ocr_status,
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
    """Get detailed information about a specific entity"""
    entity = None
    for e_name, e_data in entity_stats.items():
        if e_name.lower() == name.lower():
            entity = e_data
            break

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    return entity

@app.get("/api/network")
async def get_network(
    min_connections: int = Query(0),
    max_nodes: int = Query(500, le=1000),
    username: str = Depends(authenticate)
):
    """Get network graph data"""
    nodes = [
        n for n in network_data.get("nodes", [])
        if n.get("connection_count", 0) >= min_connections
    ]

    nodes.sort(key=lambda n: n.get("connection_count", 0), reverse=True)
    nodes = nodes[:max_nodes]

    node_ids = {n["id"] for n in nodes}

    edges = [
        e for e in network_data.get("edges", [])
        if e["source"] in node_ids and e["target"] in node_ids
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": network_data.get("metadata", {})
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

class SourceSuggestion(BaseModel):
    url: str
    description: str
    source_name: Optional[str] = None

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
    """Chat with Qwen assistant about the archive with integrated search"""
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

        # Call ollama
        import subprocess
        import json

        prompt = f"{full_context}\n\nUser Question: {message.message}\n\nAssistant:"

        result = subprocess.run(
            ["ollama", "run", "qwen2.5-coder:7b", prompt],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            response = result.stdout.strip()
            return {
                "response": response,
                "model": "qwen2.5-coder:7b",
                "search_results": {
                    "entities": matching_entities[:5],
                    "documents": matching_docs[:5]
                }
            }
        else:
            return {"response": "Sorry, I'm having trouble processing your request. Please try again.", "error": result.stderr}

    except subprocess.TimeoutExpired:
        return {"response": "Response timeout. The LLM is taking longer than expected. Please try a simpler question."}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}

# Source suggestions storage
SUGGESTIONS_FILE = PROJECT_ROOT / "data" / "source_suggestions.jsonl"

@app.post("/api/suggest-source")
async def suggest_source(
    suggestion: SourceSuggestion,
    username: str = Depends(authenticate)
):
    """Submit a source suggestion for review"""

    # Security validation
    parsed_url = urllib.parse.urlparse(suggestion.url)

    # Basic URL validation
    if not parsed_url.scheme in ['http', 'https']:
        raise HTTPException(status_code=400, detail="Only HTTP/HTTPS URLs are allowed")

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

    # Create suggestion record
    suggestion_record = {
        "url": suggestion.url,
        "description": suggestion.description,
        "source_name": suggestion.source_name,
        "submitted_at": datetime.now().isoformat(),
        "submitted_by": username,
        "status": "pending_review"
    }

    # Append to suggestions file
    SUGGESTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SUGGESTIONS_FILE, 'a') as f:
        f.write(json.dumps(suggestion_record) + '\n')

    return {
        "status": "success",
        "message": "Thank you for your suggestion! It will be reviewed and validated before processing.",
        "suggestion_id": suggestion_record["submitted_at"]
    }

@app.get("/api/suggestions")
async def get_suggestions(
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=500),
    username: str = Depends(authenticate)
):
    """Get source suggestions"""
    suggestions = []

    if SUGGESTIONS_FILE.exists():
        with open(SUGGESTIONS_FILE) as f:
            for line in f:
                suggestion = json.loads(line.strip())
                if status is None or suggestion.get("status") == status:
                    suggestions.append(suggestion)

    return {
        "total": len(suggestions),
        "suggestions": suggestions[:limit]
    }

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
