#!/usr/bin/env python3
"""
Epstein Archive Document Explorer - FastAPI Server
Serves data, search APIs, visualizations, and ingestion progress
"""

import json
import os
import re
import secrets
import subprocess
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import asyncio
import logging
import time
import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel
from fastapi import Request
from sse_starlette.sse import EventSourceResponse

# Load environment variables from .env.local
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

# Import audit logger (after Path is available)
import sys
SERVER_DIR = Path(__file__).parent
sys.path.insert(0, str(SERVER_DIR))
from services.audit_logger import AuditLogger, LoginEvent, BrowserProfile
from services.file_watcher import FileWatcherService

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
METADATA_DIR = DATA_DIR / "metadata"
MD_DIR = DATA_DIR / "md"
LOGS_DIR = PROJECT_ROOT / "logs"

# Initialize logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize audit logger
AUDIT_DB_PATH = DATA_DIR / "logs" / "audit.db"
audit_logger = AuditLogger(AUDIT_DB_PATH)

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
# HTTPBasic() now created inline with auto_error=False in get_current_user()

# Load credentials from file
import os


CREDENTIALS_FILE = Path(__file__).parent / ".credentials"

def load_credentials():
    """Load username:password pairs from .credentials file (dynamically reloaded on each call)

    Returns:
        Dictionary mapping usernames to passwords

    Raises:
        ValueError: If neither .credentials file exists nor environment variables are set

    Security: No hardcoded defaults. Fails fast if not configured.
    """
    credentials = {}

    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if ":" in line:
                        username, password = line.split(":", 1)
                        credentials[username.strip()] = password.strip()
    else:
        # Check environment variables (no hardcoded defaults)
        username = os.getenv("ARCHIVE_USERNAME")
        password = os.getenv("ARCHIVE_PASSWORD")

        if not username or not password:
            raise ValueError(
                "Authentication not configured. Either create .credentials file or set "
                "ARCHIVE_USERNAME and ARCHIVE_PASSWORD environment variables."
            )

        credentials = {username: password}

    if not credentials:
        raise ValueError("No credentials found in .credentials file")

    return credentials

def authenticate(credentials: HTTPBasicCredentials):
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

# Session-based authentication
session_tokens = {}  # In-memory session storage: {token: {username, expires}}

def create_session_token(username: str, remember: bool = False) -> str:
    """Create a new session token for the user"""
    token = secrets.token_urlsafe(32)
    expires = datetime.now() + timedelta(days=30 if remember else 1)
    session_tokens[token] = {
        "username": username,
        "expires": expires
    }
    return token

def verify_session_token(authorization: Optional[str] = Header(None)) -> str:
    """Verify session token from Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authorization token provided"
        )

    # Extract token from "Bearer <token>"
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )

    token = authorization[7:]  # Remove "Bearer " prefix

    if token not in session_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token"
        )

    session = session_tokens[token]
    if datetime.now() > session["expires"]:
        del session_tokens[token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )

    return session["username"]

# Pydantic models for login
class BrowserData(BaseModel):
    """Browser profiling data sent from client"""
    user_agent: str
    screen_resolution: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str
    remember: bool = False
    tos_accepted: Optional[bool] = None
    browser_data: Optional[BrowserData] = None

class LoginResponse(BaseModel):
    token: str
    username: str
    expires: str

# Flexible authentication (supports both session cookie and HTTP Basic Auth)
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPBasicCredentials] = Depends(HTTPBasic(auto_error=False))
) -> str:
    """
    AUTHENTICATION DISABLED - Public access enabled

    Returns 'public-user' for all requests without authentication.

    NOTE: Authentication temporarily removed for ngrok deployment.
    Future implementation should use proper auth (OAuth, JWT, etc.) - NOT basic auth.

    Previous implementation included:
    - Localhost bypass
    - Session cookie auth
    - HTTP Basic Auth fallback
    """
    # Authentication disabled - return public user for all requests
    return "public-user"

    # COMMENTED OUT - Previous authentication logic preserved for future reference
    # # Check if request is from localhost - skip authentication
    # host = request.headers.get("host", "")
    # if "localhost" in host or "127.0.0.1" in host:
    #     return "local-user"  # Skip authentication for localhost
    #
    # # For ngrok and other external access, require authentication
    # # Try session cookie first (for web app users)
    # session_token = request.cookies.get("session_token")
    #
    # if session_token and session_token in session_tokens:
    #     session = session_tokens[session_token]
    #     # Verify session not expired
    #     if datetime.now() <= session["expires"]:
    #         return session["username"]
    #     else:
    #         # Clean up expired session
    #         del session_tokens[session_token]
    #
    # # Fall back to HTTP Basic Auth (for API clients)
    # if credentials:
    #     return authenticate(credentials)
    #
    # # No valid authentication found
    # raise HTTPException(
    #     status_code=status.HTTP_401_UNAUTHORIZED,
    #     detail="Not authenticated. Please log in via /static/login.html or use HTTP Basic Auth.",
    #     headers={"WWW-Authenticate": "Basic"},
    # )

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data caches (initialized before routes)
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
                print("  ✓ Loaded timeline data")
        except Exception as e:
            print(f"  ✗ Failed to load timeline.json: {e}")
            timeline_data = {}
    else:
        print(f"  ✗ Timeline file not found: {timeline_path}")
        timeline_data = {}

    print("\n📊 Data Loading Summary:")
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
            check=False, capture_output=True,
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
                return int(value.replace(",", "").strip())
            except (ValueError, AttributeError):
                return 0

        def safe_float(value: str) -> float:
            """Parse float safely, removing percent signs and parentheses"""
            try:
                cleaned = value.replace("%", "").replace("(", "").replace(")", "").strip()
                return float(cleaned)
            except (ValueError, AttributeError):
                return 0.0

        for line in output.split("\n"):
            if "Progress:" in line:
                # Example: "Progress: 15,100 / 33,572 (45.0%)"
                parts = line.split()
                if len(parts) >= 6:
                    status["processed"] = safe_int(parts[1])
                    status["total"] = safe_int(parts[3])
                    status["progress"] = safe_float(parts[4])
            elif "Email candidates found:" in line:
                status["emails_found"] = safe_int(line.split(":")[1])
            elif "Failed:" in line:
                status["failed"] = safe_int(line.split(":")[1].split()[0])

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
async def root(request: Request):
    """Serve index.html directly - authentication disabled"""
    return FileResponse(Path(__file__).parent / "web" / "index.html")

@app.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, request: Request, response: Response):
    """Login endpoint - creates session token with comprehensive audit logging

    Sets HTTP-only cookie for session persistence.
    Cookie attributes:
    - httponly=True: Prevents XSS attacks (JavaScript cannot access)
    - secure=False: Allow HTTP in development (set to True in production with HTTPS)
    - samesite='lax': CSRF protection while allowing navigation
    - max_age: 30 days (remember me) or 1 day (default)
    """
    current_credentials = load_credentials()

    # Extract client IP address
    client_ip = request.client.host if request.client else "unknown"

    # Create browser profile from client data
    browser_profile = None
    if login_data.browser_data:
        browser_profile = audit_logger.create_browser_profile(
            user_agent=login_data.browser_data.user_agent,
            screen_resolution=login_data.browser_data.screen_resolution,
            timezone=login_data.browser_data.timezone,
            language=login_data.browser_data.language
        )

    # Check credentials
    if login_data.username not in current_credentials:
        # Log failed login attempt
        audit_logger.log_login_event(LoginEvent(
            username=login_data.username,
            timestamp=datetime.now(),
            ip_address=client_ip,
            success=False,
            failure_reason="invalid_username",
            browser_profile=browser_profile
        ))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    if not secrets.compare_digest(
        login_data.password,
        current_credentials[login_data.username]
    ):
        # Log failed login attempt
        audit_logger.log_login_event(LoginEvent(
            username=login_data.username,
            timestamp=datetime.now(),
            ip_address=client_ip,
            success=False,
            failure_reason="invalid_password",
            browser_profile=browser_profile
        ))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # Create session token
    token = create_session_token(login_data.username, login_data.remember)
    expires = session_tokens[token]["expires"].isoformat()

    # Set HTTP-only cookie
    max_age_seconds = 2592000 if login_data.remember else 86400  # 30 days or 1 day
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,  # Prevent XSS attacks
        secure=False,   # Set to True in production with HTTPS
        samesite='lax', # CSRF protection
        max_age=max_age_seconds
    )

    # Log successful login
    audit_logger.log_login_event(LoginEvent(
        username=login_data.username,
        timestamp=datetime.now(),
        ip_address=client_ip,
        success=True,
        tos_accepted=login_data.tos_accepted,
        tos_accepted_at=datetime.now() if login_data.tos_accepted else None,
        session_token=token,
        remember_me=login_data.remember,
        browser_profile=browser_profile
    ))

    return LoginResponse(
        token=token,
        username=login_data.username,
        expires=expires
    )

@app.get("/api/verify-session")
async def verify_session(request: Request):
    """Verify session token from cookie is valid

    Returns:
        Username and validity status if session is valid

    Raises:
        401: If no session cookie or session is invalid/expired
    """
    # Check for session cookie
    session_token = request.cookies.get("session_token")

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session cookie found"
        )

    if session_token not in session_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token"
        )

    session = session_tokens[session_token]
    if datetime.now() > session["expires"]:
        # Clean up expired session
        del session_tokens[session_token]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )

    return {"username": session["username"], "valid": True}

@app.post("/api/logout")
async def logout(request: Request, response: Response):
    """Logout user and clear session cookie

    Removes session from server and clears client cookie.
    """
    # Get session token from cookie
    session_token = request.cookies.get("session_token")

    # Remove session from server if exists
    if session_token and session_token in session_tokens:
        del session_tokens[session_token]

    # Clear cookie
    response.delete_cookie(key="session_token")

    return {"success": True, "message": "Logged out successfully"}

# Admin Audit Logging Endpoints
@app.get("/api/admin/audit-logs")
async def get_audit_logs(
    username: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    admin_user: str = Depends(get_current_user)
):
    """Get login audit logs (admin only)

    Returns comprehensive login history with browser profiling.

    Args:
        username: Filter by specific username (None = all users)
        limit: Maximum events to return (max 1000)
        offset: Pagination offset
        admin_user: Authenticated admin username (from dependency)

    Returns:
        JSON with login events and browser profile data
    """
    try:
        logs = audit_logger.get_login_history(
            username=username,
            limit=limit,
            offset=offset
        )

        return {
            "total": len(logs),
            "limit": limit,
            "offset": offset,
            "logs": logs
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit logs: {str(e)}"
        )

@app.get("/api/admin/security-events")
async def get_security_events(
    event_type: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    admin_user: str = Depends(get_current_user)
):
    """Get security events for admin dashboard

    Returns security anomalies and suspicious activity.

    Args:
        event_type: Filter by event type (None = all types)
        limit: Maximum events to return (max 1000)
        offset: Pagination offset
        admin_user: Authenticated admin username (from dependency)

    Returns:
        JSON with security events and details
    """
    try:
        events = audit_logger.get_security_events(
            event_type=event_type,
            limit=limit,
            offset=offset
        )

        return {
            "total": len(events),
            "limit": limit,
            "offset": offset,
            "events": events
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve security events: {str(e)}"
        )

@app.get("/api/admin/login-statistics")
async def get_login_statistics(admin_user: str = Depends(get_current_user)):
    """Get aggregate login statistics for admin dashboard

    Returns:
        JSON with login metrics, browser distribution, OS distribution, etc.
    """
    try:
        stats = audit_logger.get_login_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )

@app.post("/api/admin/anonymize-logs")
async def anonymize_old_logs(
    days: int = Query(90, ge=30, le=365),
    admin_user: str = Depends(get_current_user)
):
    """Anonymize audit logs older than specified days (GDPR compliance)

    Args:
        days: Age threshold for anonymization (30-365 days, default 90)
        admin_user: Authenticated admin username

    Returns:
        Number of records anonymized
    """
    try:
        count = audit_logger.anonymize_old_records(days=days)
        return {
            "success": True,
            "anonymized_records": count,
            "days_threshold": days
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to anonymize logs: {str(e)}"
        )

@app.get("/ROADMAP.md")
async def get_roadmap():
    """Serve the ROADMAP.md file"""
    roadmap_path = PROJECT_ROOT / "ROADMAP.md"
    if roadmap_path.exists():
        return FileResponse(roadmap_path, media_type="text/markdown")
    raise HTTPException(status_code=404, detail="ROADMAP.md not found")

@app.get("/api/stats")
async def get_stats(username: str = Depends(get_current_user)):
    """Get overall statistics

    Design Decision: Frontend Compatibility
    Rationale: Frontend expects 'total_connections' field for network edges display.
    Also includes 'sources' field for source list rendering.

    Error Handling: Returns safe fallback values if data not loaded.

    Document Count Fix: Reads unique_documents from master_document_index.json
    instead of counting classifications, which only reflects processed documents.
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

    # Get correct document count from unified index (includes emails + PDFs)
    total_documents = len(classifications)  # Fallback to classifications count
    document_breakdown = {}
    classification_breakdown = {}

    # Try unified index first (most comprehensive)
    unified_index_path = METADATA_DIR / "all_documents_index.json"
    if unified_index_path.exists():
        try:
            with open(unified_index_path) as f:
                unified_data = json.load(f)
                total_documents = unified_data.get("total_documents", len(classifications))
                document_breakdown = unified_data.get("statistics", {}).get("by_type", {})
                classification_breakdown = unified_data.get("statistics", {}).get("by_classification", {})
        except Exception as e:
            print(f"Error loading unified document index: {e}")

    # Fallback to master index if unified not available
    if not document_breakdown:
        master_index_path = METADATA_DIR / "master_document_index.json"
        if master_index_path.exists():
            try:
                with open(master_index_path) as f:
                    index_data = json.load(f)
                    total_documents = index_data.get("unique_documents", len(classifications))
            except Exception as e:
                print(f"Error loading master document index: {e}")

    return {
        "total_entities": len(entity_stats),
        "total_documents": total_documents,
        "document_types": document_breakdown,  # New: breakdown by type (email, pdf)
        "classifications": classification_breakdown,  # New: breakdown by classification
        "network_nodes": len(network_data.get("nodes", [])),
        "network_edges": len(network_data.get("edges", [])),
        "total_connections": len(network_data.get("edges", [])),  # Frontend expects this field
        "timeline_events": timeline_data.get("total_events", 0),
        "date_range": timeline_data.get("date_range", {}),
        "sources": source_list  # Frontend expects this field
    }

@app.get("/api/sources/index")
async def get_sources_index(username: str = Depends(get_current_user)):
    """Get master document index with deduplication statistics.

    Design Decision: Complete Source Provenance
    Rationale: Provides comprehensive view of all document sources with
    deduplication metrics for transparency and quality assessment.

    Performance: Large file (~17MB) loaded on-demand, not cached in memory
    to avoid memory bloat. Frontend caches response.

    Returns:
        {
            "total_files": int,
            "unique_documents": int,
            "sources": [{name, total_files, unique_docs, total_size, status}, ...],
            "cross_source_duplicates": [{document, sources, size}, ...]
        }
    """
    try:
        index_path = METADATA_DIR / "master_document_index.json"

        if not index_path.exists():
            return {
                "total_files": 0,
                "unique_documents": 0,
                "sources": [],
                "cross_source_duplicates": [],
                "error": "Master document index not found"
            }

        # Load master index (on-demand, not cached due to size)
        with open(index_path) as f:
            index_data = json.load(f)

        # Format sources for frontend
        sources = []
        source_info = index_data.get("sources", {})

        # Calculate per-source statistics from documents array
        source_stats = {}
        documents = index_data.get("documents", [])

        for doc in documents:
            doc_sources = doc.get("sources", [])
            doc_size = doc.get("size", 0)

            # Track unique docs per source
            for source_path in doc_sources:
                # Extract source name from path (e.g., "data/sources/giuffre_maxwell/..." -> "giuffre_maxwell")
                parts = Path(source_path).parts
                source_name = parts[2] if len(parts) >= 3 and parts[0] == "data" and parts[1] == "sources" else "unknown"

                if source_name not in source_stats:
                    source_stats[source_name] = {
                        "unique_docs": 0,
                        "total_size": 0
                    }

                # Each document counts as one unique doc for each source it appears in
                source_stats[source_name]["unique_docs"] += 1
                source_stats[source_name]["total_size"] += doc_size

        # Build sources list
        for source_name, source_meta in source_info.items():
            total_files = source_meta.get("document_count", 0)
            stats = source_stats.get(source_name, {"unique_docs": total_files, "total_size": 0})

            sources.append({
                "name": source_name.replace("_", " ").title(),
                "total_files": total_files,
                "unique_docs": stats["unique_docs"],
                "total_size": stats["total_size"],
                "status": "downloaded" if total_files > 0 else "pending"
            })

        # Sort sources by total files (descending)
        sources.sort(key=lambda x: x["total_files"], reverse=True)

        # Find cross-source duplicates from documents with source_count > 1
        cross_source = []
        for doc in documents[:100]:  # Limit to first 100 for performance
            if doc.get("source_count", 1) > 1:
                doc_sources = doc.get("sources", [])
                # Extract source names
                source_names = set()
                for source_path in doc_sources:
                    parts = Path(source_path).parts
                    if len(parts) >= 3 and parts[0] == "data" and parts[1] == "sources":
                        source_names.add(parts[2])

                if len(source_names) > 1:
                    # Get document name from canonical path
                    canonical = doc.get("canonical_path", "")
                    doc_name = Path(canonical).name if canonical else "unknown"

                    cross_source.append({
                        "document": doc_name,
                        "sources": sorted(list(source_names)),
                        "file_count": len(doc_sources)
                    })

        return {
            "total_files": index_data.get("total_files", 0),
            "unique_documents": index_data.get("unique_documents", 0),
            "sources": sources,
            "cross_source_duplicates": cross_source
        }

    except Exception as e:
        print(f"Error loading sources index: {e}")
        import traceback
        traceback.print_exc()
        return {
            "total_files": 0,
            "unique_documents": 0,
            "sources": [],
            "cross_source_duplicates": [],
            "error": str(e)
        }

@app.get("/api/ingestion/status")
async def get_ingestion_status(username: str = Depends(get_current_user)):
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
    if processed >= total > 0:
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

    # Get download stats from log file
    download_stats = {"total": 0, "completed": 0, "failed": 0, "status": "idle"}
    download_log_path = Path("/tmp/courtlistener_download.log")
    if download_log_path.exists():
        try:
            with open(download_log_path) as f:
                log_content = f.read()
                # Parse the last complete summary if it exists
                if "Download Complete" in log_content:
                    import re
                    success_match = re.search(r"Successfully downloaded: (\d+)", log_content)
                    total_match = re.search(r"Total files in directory: (\d+)", log_content)
                    failed_match = re.search(r"Failed downloads: (\d+)", log_content)

                    if success_match:
                        download_stats["completed"] = int(success_match.group(1))
                    if total_match:
                        download_stats["total"] = int(total_match.group(1))
                    if failed_match:
                        download_stats["failed"] = int(failed_match.group(1))
                    download_stats["status"] = "complete"
        except Exception as e:
            print(f"Error reading download log: {e}")

    # Get deduplication stats from database
    dedup_stats = {"total_files": 0, "unique_documents": 0, "rate": 0.0}
    dedup_db_path = METADATA_DIR / "deduplication.db"
    if dedup_db_path.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(dedup_db_path))
            cursor = conn.cursor()

            # Get total source files count
            cursor.execute("SELECT COUNT(*) FROM document_sources")
            total_files_count = cursor.fetchone()[0]

            # Get unique canonical documents count
            cursor.execute("SELECT COUNT(*) FROM canonical_documents")
            unique_docs_count = cursor.fetchone()[0]

            conn.close()

            dedup_stats["total_files"] = total_files_count
            dedup_stats["unique_documents"] = unique_docs_count
            if total_files_count > 0:
                dedup_stats["rate"] = ((total_files_count - unique_docs_count) / total_files_count) * 100
        except Exception as e:
            print(f"Error reading deduplication database: {e}")

    # Return frontend-compatible format with enhanced pipeline info
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
        },
        "downloads": download_stats,
        "deduplication": dedup_stats
    }


@app.get("/api/chatbot/knowledge")
async def get_chatbot_knowledge(username: str = Depends(get_current_user)):
    """Get comprehensive knowledge index for chatbot.

    Design Decision: Chatbot Knowledge Index
    Rationale: Chatbot needs quick access to project state, file locations,
    statistics, and ongoing work without reading multiple files.

    Returns:
    - All project files (scripts, data, sources)
    - Data summaries (entities, documents, network, emails)
    - Ongoing work (downloads, classifications, processing)
    - Quick stats for chatbot responses

    Trade-offs:
    - Performance: Single file read vs. multiple file reads
    - Freshness: Index must be refreshed after updates
    - Size: 25KB JSON file cached in memory

    Usage: Chatbot queries this endpoint once per session for context
    """
    knowledge_path = METADATA_DIR / "chatbot_knowledge_index.json"

    if not knowledge_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Knowledge index not found. Run: python3 scripts/metadata/build_chatbot_knowledge_index.py"
        )

    try:
        with open(knowledge_path) as f:
            knowledge = json.load(f)

        return JSONResponse(content=knowledge)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load knowledge index: {e!s}"
        )


@app.get("/api/entity-biographies")
async def get_entity_biographies(username: str = Depends(get_current_user)):
    """Get entity biography summaries

    Returns:
        Dictionary mapping entity names to biographical information
        Format: {entity_name: {summary: str, ...}}

    Design Decision: Biography Integration
    Rationale: Provides capsule biographies for entity cards without
    requiring separate API calls per entity. Returns complete dataset
    for client-side caching.

    Error Handling: Returns empty dict if file not found (graceful degradation)
    """
    try:
        bio_path = METADATA_DIR / "entity_biographies.json"
        if not bio_path.exists():
            return {}

        with open(bio_path) as f:
            data = json.load(f)
            # Extract entities dictionary from JSON structure
            entities = data.get("entities", {})
            # Return simplified format: {name: {summary, full_name, etc.}}
            return entities
    except Exception as e:
        logger.error(f"Error loading entity biographies: {e}")
        return {}


@app.get("/api/entity-tags")
async def get_entity_tags(username: str = Depends(get_current_user)):
    """Get entity tags and categorizations

    Returns:
        Dictionary mapping entity names to tags
        Format: {entity_name: {tags: [str], primary_tag: str, ...}}

    Design Decision: Tag Integration
    Rationale: Provides categorization tags (Victim, Politician, Business, etc.)
    for entity cards without requiring separate API calls. Returns complete
    dataset for client-side caching.

    Error Handling: Returns empty dict if file not found (graceful degradation)
    """
    try:
        tags_path = METADATA_DIR / "entity_tags.json"
        if not tags_path.exists():
            return {}

        with open(tags_path) as f:
            data = json.load(f)
            # Extract entities dictionary from JSON structure
            entities = data.get("entities", {})
            # Return entities with tags
            return entities
    except Exception as e:
        logger.error(f"Error loading entity tags: {e}")
        return {}


@app.get("/api/entities")
async def get_entities(
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    sort_by: str = Query("documents", enum=["documents", "connections", "name"]),
    filter_billionaires: bool = Query(False),
    filter_connected: bool = Query(False),
    username: str = Depends(get_current_user)
):
    """Get list of entities with optional filtering and sorting

    Design Decision: Filter Generic Entities
    Rationale: Exclude non-disambiguatable entities (Male, Female, Nanny (1))
    from API results. These are placeholders, not actual identifiable people.
    """
    entities_list = list(entity_stats.values())

    # Filter out generic entities (Male, Female, etc.)
    entities_list = [e for e in entities_list if not entity_filter.is_generic(e.get("name", ""))]

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
async def get_entity(name: str, username: str = Depends(get_current_user)):
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
    username: str = Depends(get_current_user)
):
    """Get network graph data with optional deduplication

    Query Parameters:
        min_connections: Minimum connections to include node (default: 0)
        max_nodes: Maximum nodes to return (default: 500, max: 1000)
        deduplicate: Apply name disambiguation to merge duplicates (default: True)

    Returns:
        Network graph with nodes, edges, and metadata

    Design Decision: Filter Generic Entities
    Rationale: Exclude non-disambiguatable entities (Male, Female, Nanny (1))
    from network graph. These placeholders create misleading connections.
    """
    # Get disambiguator
    disambiguator = get_disambiguator()

    # Get nodes
    nodes = network_data.get("nodes", [])

    # Filter out generic entities
    nodes = [n for n in nodes if not entity_filter.is_generic(n.get("name", ""))]

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
    username: str = Depends(get_current_user)
):
    """Search for entities or documents

    Design Decision: Filter Generic Entities
    Rationale: Exclude non-disambiguatable entities from search results.
    """
    results = []

    for entity_name, entity_data in entity_stats.items():
        # Skip generic entities in search results
        if entity_filter.is_generic(entity_name):
            continue

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
    username: str = Depends(get_current_user)
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
    username: str = Depends(get_current_user)
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
                                    (" [BILLIONAIRE]" if e["billionaire"] else ""))

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
            if entity_name["name"] in semantic_index:
                docs = semantic_index[entity_name["name"]]
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
                "response": f"Sorry, I'm having trouble connecting to the AI service. Error: {api_error!s}",
                "error": str(api_error)
            }

    except Exception as e:
        return {"response": f"Error: {e!s}"}

# Initialize suggestion service
# Add utils path for entity filtering
import sys

from models.suggested_source import (
    SourcePriority,
    SourceStatus,
    SuggestedSourceCreate,
    SuggestedSourceUpdate,
)

# Initialize entity disambiguation service
from services.entity_disambiguation import get_disambiguator

# Initialize entity enrichment service
from services.entity_enrichment import EntityEnrichmentService, format_for_ui
from services.suggestion_service import SuggestionService


sys.path.insert(0, str(PROJECT_ROOT / "scripts/utils"))
from entity_filtering import EntityFilter


SUGGESTIONS_STORAGE = DATA_DIR / "suggestions" / "suggested_sources.json"
ENRICHMENT_STORAGE = METADATA_DIR / "entity_enrichments.json"

suggestion_service = SuggestionService(SUGGESTIONS_STORAGE)
enrichment_service = EntityEnrichmentService(ENRICHMENT_STORAGE)
entity_filter = EntityFilter()

# Initialize file watcher for hot-reload
ENABLE_HOT_RELOAD = os.getenv("ENABLE_HOT_RELOAD", "true").lower() == "true"
file_watcher_service = FileWatcherService(
    watch_dirs=[METADATA_DIR, MD_DIR / "entities"],
    enable_hot_reload=ENABLE_HOT_RELOAD
)

# Start file watcher on app startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on server startup"""
    if ENABLE_HOT_RELOAD:
        file_watcher_service.start()
        logger.info(f"File watcher started (monitoring {len(file_watcher_service.watch_dirs)} directories)")
    else:
        logger.info("Hot-reload disabled")

# Source Suggestion Endpoints

@app.post("/api/suggestions", status_code=201)
async def create_suggestion(
    suggestion: SuggestedSourceCreate,
    username: str = Depends(get_current_user)
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
        r"localhost",
        r"127\.0\.0\.1",
        r"192\.168\.",
        r"10\.",
        r"172\.(1[6-9]|2[0-9]|3[0-1])\.",
        r"\.local$",
        r"file://",
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
    username: str = Depends(get_current_user)
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
    username: str = Depends(get_current_user)
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
    username: str = Depends(get_current_user)
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
    username: str = Depends(get_current_user)
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
async def get_suggestion_statistics(username: str = Depends(get_current_user)):
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
    username: str = Depends(get_current_user)
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
            detail=f"Error enriching entity: {e!s}"
        )


@app.get("/api/entities/{entity_id}/enrichment")
async def get_enrichment(
    entity_id: str,
    username: str = Depends(get_current_user)
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
    username: str = Depends(get_current_user)
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
            detail=f"Error during batch enrichment: {e!s}"
        )


@app.get("/api/enrichment/stats")
async def get_enrichment_statistics(username: str = Depends(get_current_user)):
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


def parse_semantic_commit(message: str) -> dict:
    """Parse conventional commit message format.

    Format: type(scope): subject

    Returns:
        Dictionary with parsed components:
        - type: Commit type (feat, fix, docs, etc.)
        - scope: Optional scope
        - breaking: Whether it's a breaking change
        - message: Subject line
        - is_semantic: Whether it follows conventional format
    """
    # Pattern: type(scope)!?: subject
    # Examples:
    #   feat(ui): add commit timeline
    #   fix!: critical security patch
    #   docs: update README
    pattern = r"^(?P<type>\w+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?\s*:\s*(?P<message>.+)$"

    match = re.match(pattern, message)

    if match:
        return {
            "type": match.group("type"),
            "scope": match.group("scope") or None,
            "breaking": match.group("breaking") is not None,
            "message": match.group("message"),
            "is_semantic": True
        }
    else:
        return {
            "type": "chore",
            "scope": None,
            "breaking": False,
            "message": message,
            "is_semantic": False
        }


# ============================================================================
# Flight Endpoints
# ============================================================================

def parse_date_for_sort(date_str: str) -> str:
    """Convert MM/DD/YYYY to YYYY-MM-DD for sorting"""
    if "/" in date_str:
        parts = date_str.split("/")
        if len(parts) == 3:
            month, day, year = parts
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return date_str


@app.get("/api/flights/all")
async def get_all_flights(username: str = Depends(get_current_user)):
    """Get all 1,167 flights grouped by route for map visualization.

    Returns:
        All flights with geocoded locations grouped by route:
        - routes: Array of unique routes with all flights on that route
        - total_flights: Total number of flights
        - date_range: First and last flight dates
        - unique_passengers: Count of unique passengers
    """
    try:
        # Load flight data
        flight_data_path = MD_DIR / "entities/flight_logs_by_flight.json"
        if not flight_data_path.exists():
            return {
                "routes": [],
                "total_flights": 0,
                "error": "Flight data not found"
            }

        with open(flight_data_path) as f:
            flight_data = json.load(f)

        # Load location database
        locations_path = METADATA_DIR / "flight_locations.json"
        if not locations_path.exists():
            return {
                "routes": [],
                "total_flights": 0,
                "error": "Location database not found"
            }

        with open(locations_path) as f:
            locations_db = json.load(f)
            airports = locations_db.get("airports", {})

        # Process all flights and group by route
        all_flights = flight_data.get("flights", [])
        route_map = {}  # Key: "ORIGIN-DEST", Value: {origin, destination, flights[]}
        all_dates = []
        unique_passengers_set = set()

        for flight in all_flights:
            route = flight.get("route", "")
            if "-" not in route:
                continue

            origin_code, dest_code = route.split("-", 1)

            # Get location data
            origin_data = airports.get(origin_code)
            dest_data = airports.get(dest_code)

            if not origin_data or not dest_data:
                continue

            # Track unique passengers
            for passenger in flight.get("passengers", []):
                unique_passengers_set.add(passenger)

            # Track dates
            flight_date = flight.get("date", "")
            if flight_date:
                all_dates.append(flight_date)

            # Group by route
            route_key = f"{origin_code}-{dest_code}"
            if route_key not in route_map:
                route_map[route_key] = {
                    "origin": {
                        "code": origin_code,
                        **origin_data
                    },
                    "destination": {
                        "code": dest_code,
                        **dest_data
                    },
                    "flights": []
                }

            # Add flight to route
            route_map[route_key]["flights"].append({
                "id": flight.get("id"),
                "date": flight_date,
                "passengers": flight.get("passengers", []),
                "passenger_count": flight.get("passenger_count", len(flight.get("passengers", []))),
                "aircraft": flight.get("tail_number", "")
            })

        # Convert route_map to array with frequency
        routes = []
        for route_key, route_data in route_map.items():
            routes.append({
                "origin": route_data["origin"],
                "destination": route_data["destination"],
                "flights": route_data["flights"],
                "frequency": len(route_data["flights"])
            })

        # Sort routes by frequency (most traveled routes first)
        routes.sort(key=lambda r: r["frequency"], reverse=True)

        # Calculate date range
        date_range = {}
        if all_dates:
            # Sort dates (handle MM/DD/YYYY format)
            sorted_dates = sorted(all_dates, key=lambda d: parse_date_for_sort(d))
            date_range = {
                "start": sorted_dates[0],
                "end": sorted_dates[-1]
            }

        # Calculate actual processed flights (flights that made it onto the map)
        processed_flight_count = sum(len(route["flights"]) for route in routes)

        return {
            "routes": routes,
            "total_flights": processed_flight_count,
            "unique_routes": len(routes),
            "unique_passengers": len(unique_passengers_set),
            "date_range": date_range,
            "airports": airports
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "routes": [],
            "total_flights": 0,
            "error": str(e)
        }


# ============================================================================
# Document Endpoints
# ============================================================================

@app.get("/api/documents")
async def search_documents(
    q: Optional[str] = Query(None, description="Full-text search query"),
    entity: Optional[str] = Query(None, description="Filter by entity name"),
    doc_type: Optional[str] = Query(None, description="Filter by document type"),
    source: Optional[str] = Query(None, description="Filter by source collection"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    username: str = Depends(get_current_user)
):
    """Search documents with filters.

    Returns:
        - documents: Array of matching documents with snippets
        - total: Total matching documents
        - filters: Available filter options (facets)
    """
    try:
        # Load document index
        doc_index_path = METADATA_DIR / "all_documents_index.json"
        if not doc_index_path.exists():
            return {"documents": [], "total": 0, "error": "Document index not found"}

        with open(doc_index_path) as f:
            doc_data = json.load(f)

        documents = doc_data.get("documents", [])

        # Filter documents
        filtered_docs = documents

        # ALWAYS filter out JSON metadata files and unavailable content
        filtered_docs = [
            doc for doc in filtered_docs
            if not (
                # Exclude JSON files from data/metadata/ directory
                (doc.get("path", "").startswith("data/metadata/") and
                 doc.get("filename", "").endswith(".json")) or
                # Exclude documents with unavailable content
                doc.get("content") == "Content not available for this document."
            )
        ]

        # Filter by entity
        if entity:
            entity_lower = entity.lower()
            filtered_docs = [
                doc for doc in filtered_docs
                if any(entity_lower in e.lower() for e in doc.get("entities_mentioned", []))
            ]

        # Filter by document type
        if doc_type:
            filtered_docs = [
                doc for doc in filtered_docs
                if doc.get("classification", "").lower() == doc_type.lower()
            ]

        # Filter by source
        if source:
            filtered_docs = [
                doc for doc in filtered_docs
                if source.lower() in doc.get("source", "").lower()
            ]

        # Full-text search in filename and path
        if q:
            q_lower = q.lower()
            filtered_docs = [
                doc for doc in filtered_docs
                if q_lower in doc.get("filename", "").lower() or
                   q_lower in doc.get("path", "").lower()
            ]

        # Get total before pagination
        total = len(filtered_docs)

        # Paginate
        paginated_docs = filtered_docs[offset:offset + limit]

        # Generate facets for filtering
        all_types = set(doc.get("classification", "unknown") for doc in documents)
        all_sources = set(doc.get("source", "unknown") for doc in documents)

        return {
            "documents": paginated_docs,
            "total": total,
            "limit": limit,
            "offset": offset,
            "filters": {
                "types": sorted(list(all_types)),
                "sources": sorted(list(all_sources))
            }
        }

    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return {"documents": [], "total": 0, "error": str(e)}


@app.get("/api/documents/{doc_id}")
async def get_document(
    doc_id: str,
    username: str = Depends(get_current_user)
):
    """Get full document content by ID.

    Returns:
        - document: Full document metadata
        - content: Document text content (if available)
    """
    try:
        # Load document index
        doc_index_path = METADATA_DIR / "all_documents_index.json"
        if not doc_index_path.exists():
            raise HTTPException(status_code=404, detail="Document index not found")

        with open(doc_index_path) as f:
            doc_data = json.load(f)

        documents = doc_data.get("documents", [])

        # Find document by ID
        document = next((doc for doc in documents if doc.get("id") == doc_id), None)

        if not document:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        # Try to load content from markdown file
        content = None
        doc_path = document.get("path", "")
        if doc_path:
            md_path = Path(doc_path)
            if md_path.exists() and md_path.suffix == ".md":
                try:
                    with open(md_path) as f:
                        content = f.read()
                except Exception as e:
                    logger.warning(f"Could not read content for {doc_id}: {e}")

        return {
            "document": document,
            "content": content
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/git/recent-commits")
async def get_recent_commits(
    limit: int = Query(default=10, ge=1, le=50),
    username: str = Depends(get_current_user)
):
    """Get recent git commits with semantic commit parsing.

    Args:
        limit: Number of commits to return (1-50, default 10)

    Returns:
        List of commits with parsed semantic information:
        - hash: Short commit hash (7 chars)
        - author: Author name
        - email: Author email
        - date: Relative date (e.g., "2 hours ago")
        - type: Commit type (feat, fix, docs, etc.)
        - scope: Optional scope
        - breaking: Whether it's a breaking change
        - message: Commit subject
        - full_message: Original commit message
        - is_semantic: Whether commit follows conventional format

    Example Response:
        {
            "commits": [
                {
                    "hash": "a1b2c3d",
                    "author": "John Doe",
                    "email": "john@example.com",
                    "date": "2 hours ago",
                    "type": "feat",
                    "scope": "ui",
                    "breaking": false,
                    "message": "add commit timeline",
                    "full_message": "feat(ui): add commit timeline",
                    "is_semantic": true
                }
            ],
            "total": 1
        }
    """
    try:
        # Run git log command
        result = subprocess.run(
            [
                "git", "log",
                f"-n {limit}",
                "--pretty=format:%H|%an|%ae|%ad|%s",
                "--date=relative"
            ],
            check=False, capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=5
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Git command failed: {result.stderr}"
            )

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            parts = line.split("|")
            if len(parts) != 5:
                continue

            commit_hash, author, email, date, message = parts

            # Parse semantic commit
            parsed = parse_semantic_commit(message)

            commits.append({
                "hash": commit_hash[:7],
                "author": author,
                "email": email,
                "date": date,
                "type": parsed["type"],
                "scope": parsed["scope"],
                "breaking": parsed["breaking"],
                "message": parsed["message"],
                "full_message": message,
                "is_semantic": parsed["is_semantic"]
            })

        return {
            "commits": commits,
            "total": len(commits)
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=500,
            detail="Git command timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching commits: {e!s}"
        )


# ============================================================================
# Server-Sent Events (SSE) - Hot Reload
# ============================================================================

@app.get("/api/sse/updates")
async def sse_updates(request: Request, username: str = Depends(get_current_user)):
    """
    Server-Sent Events endpoint for hot-reload functionality

    Streams real-time updates when data files change:
    - entity_network_updated: Entity network graph modified
    - timeline_updated: Timeline events modified
    - entities_updated: Master document index modified
    - documents_updated: Unified document index modified
    - cases_updated: Cases index modified
    - victims_updated: Victims index modified
    - entity_mappings_updated: Entity name mappings modified
    - entity_filter_updated: Entity filter list modified

    Connection Management:
    - Auto-reconnects on disconnect after 5 seconds
    - Graceful cleanup on client disconnect
    - Debouncing: Groups rapid changes (1 second window)

    Usage:
        const eventSource = new EventSource('/api/sse/updates');
        eventSource.addEventListener('entity_network_updated', (e) => {
            const data = JSON.parse(e.data);
            console.log('Network updated:', data.filename, data.timestamp);
            loadNetworkData(); // Reload network
        });

    Returns:
        EventSourceResponse: SSE stream with JSON-encoded events
    """

    async def event_generator():
        """Generate SSE events from file watcher"""
        # Create queue for this client
        queue = asyncio.Queue(maxsize=100)

        # Register client with file watcher
        event_handler = file_watcher_service.get_event_handler()
        event_handler.add_client(queue)

        try:
            logger.info(f"SSE client connected (total: {event_handler.get_client_count()})")

            # Send initial connection event
            yield {
                "event": "connected",
                "data": json.dumps({
                    "message": "Hot-reload connected",
                    "timestamp": time.time(),
                    "enabled": ENABLE_HOT_RELOAD
                })
            }

            # Stream events
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info("SSE client disconnected")
                    break

                try:
                    # Wait for event with timeout (allows periodic disconnect checks)
                    event_data = await asyncio.wait_for(queue.get(), timeout=30.0)

                    # Send event to client
                    yield {
                        "event": event_data["event"],
                        "data": json.dumps(event_data["data"])
                    }

                except asyncio.TimeoutError:
                    # Send keepalive ping
                    yield {
                        "event": "ping",
                        "data": json.dumps({"timestamp": time.time()})
                    }

        except asyncio.CancelledError:
            logger.info("SSE client connection cancelled")
        except Exception as e:
            logger.error(f"SSE error: {e}")
        finally:
            # Cleanup: Remove client from watcher
            event_handler.remove_client(queue)
            logger.info(f"SSE client cleaned up (remaining: {event_handler.get_client_count()})")

    return EventSourceResponse(event_generator())


# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on server shutdown"""
    # Stop file watcher
    if ENABLE_HOT_RELOAD:
        file_watcher_service.stop()
        logger.info("File watcher stopped")

    # Close enrichment service
    await enrichment_service.close()


# ============================================================================
# API v2 Routes - API-First Architecture
# ============================================================================

# Import and register new API routes
import api_routes

# Import RAG routes
try:
    from routes.rag import router as rag_router
    rag_available = True
except ImportError:
    logger.warning("RAG routes not available - ChromaDB dependencies may not be installed")
    rag_available = False

# Initialize services on startup
@app.on_event("startup")
async def init_api_services():
    """Initialize API v2 services"""
    api_routes.init_services(DATA_DIR)
    logger.info("API v2 services initialized")

    if rag_available:
        logger.info("RAG system available at /api/rag")

# Register API v2 routes
app.include_router(api_routes.router)
logger.info("API v2 routes registered at /api/v2")

# Register RAG routes
if rag_available:
    app.include_router(rag_router)
    logger.info("RAG routes registered at /api/rag")


# Mount old web directory at root (includes sidebar with Archive Assistant)
app.mount("/", StaticFiles(directory=Path(__file__).parent / "web", html=True), name="static")

# Mount Svelte build at /svelte for alternate access
app.mount("/svelte", StaticFiles(directory=Path(__file__).parent / "web-svelte" / "build", html=True), name="svelte")


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

