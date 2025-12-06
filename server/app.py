#!/usr/bin/env python3
"""
Epstein Archive Document Explorer - FastAPI Server
Serves data, search APIs, visualizations, and ingestion progress
"""

import asyncio
import json
import logging
import os
import re
import secrets
import subprocess
import time
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from uuid import UUID

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse


# Load environment variables from .env.local
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.local")

# CRITICAL: Disable ChromaDB telemetry BEFORE any imports that use chromadb
# ChromaDB 1.3.5 has a telemetry bug causing "no such column: collections.topic" error
# Must be set before entity_similarity service is imported
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_IMPL"] = "none"

# Import audit logger (after Path is available)
import sys


SERVER_DIR = Path(__file__).parent
sys.path.insert(0, str(SERVER_DIR))
from services.audit_logger import AuditLogger, LoginEvent
from services.file_watcher import FileWatcherService
from services.document_similarity import get_similarity_service
from services.entity_similarity import get_entity_similarity_service
from entity_detector import get_entity_detector

# Database imports
from sqlalchemy import text
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Entity, EntityBiography


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

        openrouter_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    return openrouter_client


app = FastAPI(
    title="Epstein Document Archive API",
    description="Search and explore the Epstein document archive",
    version="1.0.0",
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
                if line and not line.startswith("#") and ":" in line:
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
            credentials.password, current_credentials[credentials.username]
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
    session_tokens[token] = {"username": username, "expires": expires}
    return token


def verify_session_token(authorization: Optional[str] = Header(None)) -> str:
    """Verify session token from Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No authorization token provided"
        )

    # Extract token from "Bearer <token>"
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header format"
        )

    token = authorization[7:]  # Remove "Bearer " prefix

    if token not in session_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token"
        )

    session = session_tokens[token]
    if datetime.now() > session["expires"]:
        del session_tokens[token]
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

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
    credentials: Optional[HTTPBasicCredentials] = Depends(HTTPBasic(auto_error=False)),
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
entity_stats = {}  # ID -> Entity dict
entity_bios = {}  # ID/Name -> Biography dict
network_data = {}
semantic_index = {}
classifications = {}
timeline_data = {}

# Reverse mappings for backward compatibility
name_to_id = {}  # Name/variation -> ID
id_to_name = {}  # ID -> Primary name
guid_to_id = {}  # GUID -> ID mapping for v3 API


def build_name_mappings():
    """Build reverse mappings from names to entity IDs for backward compatibility"""
    global name_to_id, id_to_name

    for entity_id, entity_data in entity_stats.items():
        # Map ID to primary name
        primary_name = entity_data.get("name", "")
        id_to_name[entity_id] = primary_name

        # Map primary name to ID
        name_to_id[primary_name] = entity_id

        # Map all name variations to ID
        for variation in entity_data.get("name_variations", []):
            if variation and variation not in name_to_id:
                name_to_id[variation] = entity_id

        # Also map normalized name if different
        normalized = entity_data.get("normalized_name")
        if normalized and normalized != primary_name and normalized not in name_to_id:
            name_to_id[normalized] = entity_id


def build_guid_mapping():
    """Build GUID-to-ID mapping for v3 API endpoint

    Design Decision: GUID-based URLs for SEO-friendly permalinks
    Rationale: GUIDs provide stable, unique identifiers while allowing
    human-readable names in URLs (e.g., /entities/{guid}/jeffrey-epstein)

    Performance: O(1) lookup via dictionary, built once at startup
    """
    global guid_to_id

    guid_to_id.clear()
    for entity_id, entity_data in entity_stats.items():
        guid = entity_data.get("guid")
        if guid:
            guid_to_id[guid] = entity_id

    logger.info(f"Built GUID mapping: {len(guid_to_id)} entities indexed")


def load_data():
    """Load all JSON data into memory with error handling"""
    global entity_stats, entity_bios, network_data, semantic_index, classifications, timeline_data
    global name_to_id, id_to_name, guid_to_id

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

                # Build reverse mappings for name-based lookups
                build_name_mappings()
                print(f"  ✓ Built name mappings: {len(name_to_id)} name variations indexed")

                # Build GUID-to-ID mapping for v3 API
                build_guid_mapping()
                print(f"  ✓ Built GUID mappings: {len(guid_to_id)} GUIDs indexed")
        except Exception as e:
            print(f"  ✗ Failed to load entity_statistics.json: {e}")
            entity_stats = {}
    else:
        print(f"  ✗ Entity statistics file not found: {stats_path}")
        entity_stats = {}

    # Entity biographies - load from all three files
    entity_files = [
        ("entity_biographies.json", "person"),      # 1,637 persons from contact books
        ("entity_organizations.json", "organization"),  # ~920 orgs from documents
        ("entity_locations.json", "location")       # ~458 locations from documents
    ]

    entity_bios = {}
    total_loaded = 0

    for filename, entity_type in entity_files:
        file_path = METADATA_DIR / filename
        if file_path.exists():
            try:
                with open(file_path) as f:
                    data = json.load(f)
                    entities = data.get("entities", {})

                    # Merge entities, ensuring entity_type is set
                    for entity_key, entity_data in entities.items():
                        # Ensure entity_type field exists
                        if "entity_type" not in entity_data:
                            entity_data["entity_type"] = entity_type

                        entity_bios[entity_key] = entity_data

                    print(f"  ✓ Loaded {len(entities)} entities from {filename}")
                    total_loaded += len(entities)
            except Exception as e:
                print(f"  ✗ Failed to load {filename}: {e}")
        else:
            print(f"  ✗ Entity file not found: {filename}")

    if total_loaded == 0:
        print(f"  ✗ No entity biography files found")
    else:
        print(f"  ✓ Total entity biographies loaded: {total_loaded}")

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
    print(f"  Biographies: {len(entity_bios)}")
    print(f"  Network nodes: {len(network_data.get('nodes', []))}")
    print(f"  Network edges: {len(network_data.get('edges', []))}")
    print(f"  Classifications: {len(classifications)}")


def get_entity_news_count(entity_name: str) -> int:
    """Count news articles mentioning an entity.

    Args:
        entity_name: Entity name (in "LastName, FirstName" or "FirstName LastName" format)

    Returns:
        Count of news articles mentioning this entity

    Design Decision: Lazy load news data on demand
    Rationale: News index can be large, only load when needed for entity counts
    """
    try:
        news_index_path = METADATA_DIR / "news_articles_index.json"
        if not news_index_path.exists():
            return 0

        with open(news_index_path) as f:
            news_data = json.load(f)
            articles = news_data.get("articles", [])

            # Count articles mentioning this entity
            # News articles use "FirstName LastName" format, entity stats use "LastName, FirstName"
            # Need to check both formats
            count = 0
            entity_name_reversed = None
            if ", " in entity_name:
                # Convert "Epstein, Jeffrey" -> "Jeffrey Epstein"
                parts = entity_name.split(", ", 1)
                entity_name_reversed = f"{parts[1]} {parts[0]}"

            for article in articles:
                entities_mentioned = article.get("entities_mentioned", [])
                # Check both formats
                if entity_name in entities_mentioned or (entity_name_reversed and entity_name_reversed in entities_mentioned):
                    count += 1

            return count
    except Exception as e:
        logger.error(f"Error counting news for entity {entity_name}: {e}")
        return 0


def get_entity_timeline_count(entity_name: str) -> int:
    """Count timeline events mentioning an entity.

    Args:
        entity_name: Entity name (in "LastName, FirstName" or "FirstName LastName" format)

    Returns:
        Count of timeline events mentioning this entity

    Design Decision: Use in-memory timeline_data for performance
    Rationale: Timeline data is already loaded at startup, no need to reload
    """
    try:
        events = timeline_data.get("events", [])

        # Count events mentioning this entity
        # Timeline uses "FirstName LastName" format
        count = 0
        entity_name_reversed = None
        if ", " in entity_name:
            # Convert "Epstein, Jeffrey" -> "Jeffrey Epstein"
            parts = entity_name.split(", ", 1)
            entity_name_reversed = f"{parts[1]} {parts[0]}"

        for event in events:
            related_entities = event.get("related_entities", [])
            # Check both formats
            if entity_name in related_entities or (entity_name_reversed and entity_name_reversed in related_entities):
                count += 1

        return count
    except Exception as e:
        logger.error(f"Error counting timeline events for entity {entity_name}: {e}")
        return 0


def detect_entity_type(entity_name: str) -> str:
    """Detect entity type from name using word boundary regex to prevent false positives.

    Uses word boundary matching to avoid substring false positives:
    - "Boardman" will NOT match "board" (word boundary prevents it)
    - "Trump Organization" WILL match "organization" (whole word)
    - "Little St James Island" WILL match "island" (whole word)

    Args:
        entity_name: Entity name to analyze

    Returns:
        Entity type: 'person', 'business', 'location', or 'organization'
    """
    name = entity_name.lower()

    # Business/Organization indicators
    business_keywords = [
        "corp",
        "corporation",
        "inc",
        "incorporated",
        "llc",
        "ltd",
        "limited",
        "company",
        "co.",
        "enterprises",
        "group",
        "holdings",
        "international",
        "partners",
        "associates",
        "ventures",
        "capital",
        "investments",
        "trust",
        "fund",
        "bank",
        "financial",
        "consulting",
    ]

    # Location indicators
    location_keywords = [
        "island",
        "airport",
        "beach",
        "estate",
        "ranch",
        "street",
        "avenue",
        "road",
        "boulevard",
        "drive",
        "place",
        "manor",
        "villa",
        "palace",
        "hotel",
        "resort",
        "club",
    ]

    # Organization indicators (non-profit, government, etc.)
    # NOTE: "foundation" moved here from business_keywords to prioritize non-profits
    organization_keywords = [
        "organization",
        "foundation",
        "institute",
        "university",
        "college",
        "school",
        "department",
        "agency",
        "commission",
        "board",
        "council",
        "society",
        "association",
        "federation",
        "alliance",
    ]

    # Check for organization FIRST (with word boundaries)
    # Organizations checked before businesses to prioritize non-profits/gov
    for keyword in organization_keywords:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, name):
            return "organization"

    # Check for business (with word boundaries)
    for keyword in business_keywords:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, name):
            return "business"

    # Check for location (with word boundaries)
    for keyword in location_keywords:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, name):
            return "location"

    # Default to person
    return "person"


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
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )

        output = result.stdout

        # Parse output
        status = {
            "active": "Progress:" in output,
            "progress": 0,
            "processed": 0,
            "total": 0,
            "emails_found": 0,
            "failed": 0,
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


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring backend availability.

    Returns:
        Status information including timestamp and service health.

    Design Decision: Simple health check for frontend connectivity testing.
    No authentication required - public endpoint for monitoring.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "epstein-archive-api",
        "version": "1.0.0",
    }


# Root path is now handled by StaticFiles mount (see bottom of file)
# Serves React frontend from frontend/dist/index.html
# Removed hardcoded route that was serving old vanilla JS frontend


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
            language=login_data.browser_data.language,
        )

    # Check credentials
    if login_data.username not in current_credentials:
        # Log failed login attempt
        audit_logger.log_login_event(
            LoginEvent(
                username=login_data.username,
                timestamp=datetime.now(),
                ip_address=client_ip,
                success=False,
                failure_reason="invalid_username",
                browser_profile=browser_profile,
            )
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password"
        )

    if not secrets.compare_digest(login_data.password, current_credentials[login_data.username]):
        # Log failed login attempt
        audit_logger.log_login_event(
            LoginEvent(
                username=login_data.username,
                timestamp=datetime.now(),
                ip_address=client_ip,
                success=False,
                failure_reason="invalid_password",
                browser_profile=browser_profile,
            )
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password"
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
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",  # CSRF protection
        max_age=max_age_seconds,
    )

    # Log successful login
    audit_logger.log_login_event(
        LoginEvent(
            username=login_data.username,
            timestamp=datetime.now(),
            ip_address=client_ip,
            success=True,
            tos_accepted=login_data.tos_accepted,
            tos_accepted_at=datetime.now() if login_data.tos_accepted else None,
            session_token=token,
            remember_me=login_data.remember,
            browser_profile=browser_profile,
        )
    )

    return LoginResponse(token=token, username=login_data.username, expires=expires)


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
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No session cookie found"
        )

    if session_token not in session_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token"
        )

    session = session_tokens[session_token]
    if datetime.now() > session["expires"]:
        # Clean up expired session
        del session_tokens[session_token]
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

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
    admin_user: str = Depends(get_current_user),
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
        logs = audit_logger.get_login_history(username=username, limit=limit, offset=offset)

        return {"total": len(logs), "limit": limit, "offset": offset, "logs": logs}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit logs: {e!s}",
        )


@app.get("/api/admin/security-events")
async def get_security_events(
    event_type: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    admin_user: str = Depends(get_current_user),
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
        events = audit_logger.get_security_events(event_type=event_type, limit=limit, offset=offset)

        return {"total": len(events), "limit": limit, "offset": offset, "events": events}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve security events: {e!s}",
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
            detail=f"Failed to retrieve statistics: {e!s}",
        )


@app.post("/api/admin/anonymize-logs")
async def anonymize_old_logs(
    days: int = Query(90, ge=30, le=365), admin_user: str = Depends(get_current_user)
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
        return {"success": True, "anonymized_records": count, "days_threshold": days}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to anonymize logs: {e!s}",
        )


@app.get("/ROADMAP.md")
async def get_roadmap():
    """Serve the ROADMAP.md file"""
    roadmap_path = PROJECT_ROOT / "ROADMAP.md"
    if roadmap_path.exists():
        return FileResponse(roadmap_path, media_type="text/markdown")
    raise HTTPException(status_code=404, detail="ROADMAP.md not found")


@app.get("/api/about")
async def get_about(username: str = Depends(get_current_user)):
    """Get ABOUT.md content for home page

    Returns:
        JSON with markdown content and metadata:
        - content: Full markdown text of ABOUT.md
        - updated_at: Last modification timestamp
        - file_size: Size of ABOUT.md in bytes

    Design Decision: Markdown Content API
    Rationale: Frontend renders markdown client-side for flexibility.
    Could pre-render to HTML server-side for performance, but markdown
    gives frontend control over styling and React component integration.

    Error Handling: Returns 404 if ABOUT.md not found (should always exist)
    """
    try:
        about_path = PROJECT_ROOT / "ABOUT.md"

        if not about_path.exists():
            raise HTTPException(
                status_code=404,
                detail="ABOUT.md not found. Please create this file in the project root.",
            )

        # Read markdown content
        with open(about_path, encoding="utf-8") as f:
            content = f.read()

        # Get file metadata
        stat = about_path.stat()
        updated_at = datetime.fromtimestamp(stat.st_mtime).isoformat()

        return {"content": content, "updated_at": updated_at, "file_size": stat.st_size}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading ABOUT.md: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read ABOUT.md: {e!s}")


@app.get("/api/updates")
async def get_updates(
    limit: int = Query(default=10, ge=1, le=50), username: str = Depends(get_current_user)
):
    """Get latest git commits for home page updates feed

    Args:
        limit: Number of commits to return (1-50, default 10)

    Returns:
        JSON with commit history:
        - commits: Array of commit objects with hash, author, time, message
        - total: Total number of commits returned

    Design Decision: Git History as Update Feed
    Rationale: Git commits provide transparent changelog of archive updates.
    Shows users what changed recently without manual changelog maintenance.

    Performance: Git command runs quickly (<100ms) with subprocess timeout.

    Error Handling: Returns 500 if git command fails or times out.
    """
    try:
        # Run git log command with specific format
        result = subprocess.run(
            ["git", "log", f"-n{limit}", "--pretty=format:%h|%an|%ar|%s"],
            check=False,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=5,
        )

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Git command failed: {result.stderr}")

        # Parse git log output
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            parts = line.split("|", 3)
            if len(parts) == 4:
                commit_hash, author, time_ago, message = parts
                commits.append(
                    {"hash": commit_hash, "author": author, "time": time_ago, "message": message}
                )

        return {"commits": commits, "total": len(commits)}

    except subprocess.TimeoutExpired:
        logger.error("Git log command timed out")
        raise HTTPException(status_code=500, detail="Git command timed out")
    except Exception as e:
        logger.error(f"Error fetching git updates: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching updates: {e!s}")


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
                classification_breakdown = unified_data.get("statistics", {}).get(
                    "by_classification", {}
                )
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

    # Get flight count from flight data
    flight_count = 0
    flight_data_path = MD_DIR / "entities/flight_logs_by_flight.json"
    if flight_data_path.exists():
        try:
            with open(flight_data_path) as f:
                flight_data = json.load(f)
                flight_count = len(flight_data.get("flights", []))
        except Exception as e:
            print(f"Error loading flight data: {e}")

    # Get news articles count from news articles index
    news_articles_count = 0
    news_index_path = METADATA_DIR / "news_articles_index.json"
    if news_index_path.exists():
        try:
            with open(news_index_path) as f:
                news_data = json.load(f)
                news_articles_count = len(news_data.get("articles", []))
        except Exception as e:
            print(f"Error loading news articles index: {e}")

    return {
        "total_entities": len(entity_stats),
        "total_documents": total_documents,
        "document_types": document_breakdown,  # New: breakdown by type (email, pdf)
        "classifications": classification_breakdown,  # New: breakdown by classification
        "flight_count": flight_count,  # Flight logs count
        "news_articles": news_articles_count,  # News articles count
        "network_nodes": len(network_data.get("nodes", [])),
        "network_edges": len(network_data.get("edges", [])),
        "total_connections": len(network_data.get("edges", [])),  # Frontend expects this field
        "timeline_events": timeline_data.get("metadata", {}).get("total_events", 0),
        "date_range": timeline_data.get("metadata", {}).get("date_range", {}),
        "sources": source_list,  # Frontend expects this field
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
                "error": "Master document index not found",
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
                source_name = (
                    parts[2]
                    if len(parts) >= 3 and parts[0] == "data" and parts[1] == "sources"
                    else "unknown"
                )

                if source_name not in source_stats:
                    source_stats[source_name] = {"unique_docs": 0, "total_size": 0}

                # Each document counts as one unique doc for each source it appears in
                source_stats[source_name]["unique_docs"] += 1
                source_stats[source_name]["total_size"] += doc_size

        # Build sources list
        for source_name, source_meta in source_info.items():
            total_files = source_meta.get("document_count", 0)
            stats = source_stats.get(source_name, {"unique_docs": total_files, "total_size": 0})

            sources.append(
                {
                    "name": source_name.replace("_", " ").title(),
                    "total_files": total_files,
                    "unique_docs": stats["unique_docs"],
                    "total_size": stats["total_size"],
                    "status": "downloaded" if total_files > 0 else "pending",
                }
            )

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

                    cross_source.append(
                        {
                            "document": doc_name,
                            "sources": sorted(source_names),
                            "file_count": len(doc_sources),
                        }
                    )

        return {
            "total_files": index_data.get("total_files", 0),
            "unique_documents": index_data.get("unique_documents", 0),
            "sources": sources,
            "cross_source_duplicates": cross_source,
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
            "error": str(e),
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
                dedup_stats["rate"] = (
                    (total_files_count - unique_docs_count) / total_files_count
                ) * 100
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
            "billionaires": sum(1 for e in entity_stats.values() if e.get("is_billionaire")),
        },
        "documents": {
            "total": len(classifications),
            "classified": len(classifications),
            "emails_found": ocr_status.get("emails_found", 0),
        },
        "network": {
            "nodes": len(network_data.get("nodes", [])),
            "edges": len(network_data.get("edges", [])),
        },
        "downloads": download_stats,
        "deduplication": dedup_stats,
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
            detail="Knowledge index not found. Run: python3 scripts/metadata/build_chatbot_knowledge_index.py",
        )

    try:
        with open(knowledge_path) as f:
            knowledge = json.load(f)

        return JSONResponse(content=knowledge)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load knowledge index: {e!s}")


@app.get("/api/entity-biographies")
async def get_entity_biographies(
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get entity biography summaries (database-backed)

    Returns:
        Dictionary mapping entity IDs to biographical information
        Format: {entity_id: {display_name: str, summary: str, ...}}

    Design Decision: Database Migration
    Rationale: Migrated from JSON to SQLite for better query performance,
    transactional integrity, and full-text search capabilities.
    Falls back to JSON if database query fails for backward compatibility.

    Error Handling: Returns empty dict if database query fails (graceful degradation)
    """
    try:
        # Query all entities with biographies from database
        entities_with_bio = (
            db.query(Entity, EntityBiography)
            .join(EntityBiography, Entity.id == EntityBiography.entity_id)
            .all()
        )

        # Build response dictionary matching JSON format
        result = {}
        for entity, bio in entities_with_bio:
            # Parse JSON fields
            key_facts = json.loads(bio.key_facts) if bio.key_facts else []
            timeline = json.loads(bio.timeline) if bio.timeline else []
            relationships = json.loads(bio.relationships) if bio.relationships else {}
            aliases = json.loads(entity.aliases) if entity.aliases else []

            result[entity.id] = {
                "id": entity.id,
                "display_name": entity.display_name,
                "full_name": entity.display_name,
                "born": bio.birth_date,
                "died": bio.death_date,
                "nationality": bio.nationality,
                "occupation": bio.occupation,
                "summary": bio.summary,
                "key_facts": key_facts,
                "timeline": timeline,
                "relationships": relationships,
                "aliases": aliases,
                # Metadata
                "source": bio.source,
                "quality_score": bio.quality_score,
                "word_count": bio.word_count,
            }

        return result

    except Exception as e:
        logger.error(f"Error loading entity biographies from database: {e}")
        # Fallback to JSON file for backward compatibility
        try:
            bio_path = METADATA_DIR / "entity_biographies.json"
            if not bio_path.exists():
                return {}

            with open(bio_path) as f:
                data = json.load(f)
                entities = data.get("entities", {})
                return entities
        except Exception as json_error:
            logger.error(f"Error loading entity biographies from JSON fallback: {json_error}")
            return {}


@app.get("/api/entities/{entity_id}/bio")
async def get_entity_bio(
    entity_id: str,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get biography for a specific entity

    Args:
        entity_id: Entity ID (e.g., "jeffrey_epstein")

    Returns:
        Biography object with all biographical fields

    Error Handling:
        - 404: Entity not found or has no biography
        - 500: Database error
    """
    try:
        # Query entity with biography
        entity = db.query(Entity).filter(Entity.id == entity_id).first()

        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")

        if not entity.biography:
            raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' has no biography")

        bio = entity.biography

        # Parse JSON fields
        key_facts = json.loads(bio.key_facts) if bio.key_facts else []
        timeline = json.loads(bio.timeline) if bio.timeline else []
        relationships = json.loads(bio.relationships) if bio.relationships else {}
        aliases = json.loads(entity.aliases) if entity.aliases else []

        return {
            "id": entity.id,
            "display_name": entity.display_name,
            "entity_type": entity.entity_type,
            "aliases": aliases,
            # Biography fields
            "summary": bio.summary,
            "birth_date": bio.birth_date,
            "death_date": bio.death_date,
            "occupation": bio.occupation,
            "nationality": bio.nationality,
            "key_facts": key_facts,
            "timeline": timeline,
            "relationships": relationships,
            # Metadata
            "source": bio.source,
            "model_used": bio.model_used,
            "quality_score": bio.quality_score,
            "word_count": bio.word_count,
            "has_dates": bio.has_dates,
            "has_statistics": bio.has_statistics,
            "generated_at": bio.generated_at.isoformat() if bio.generated_at else None,
            "enriched_at": bio.enriched_at.isoformat() if bio.enriched_at else None,
            "verified_at": bio.verified_at.isoformat() if bio.verified_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching biography for entity '{entity_id}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch biography: {str(e)}")


@app.get("/api/entities/{entity_id}/connections")
async def get_entity_connections(
    entity_id: str,
    limit: int = Query(8, ge=1, le=20),
    username: str = Depends(get_current_user)
):
    """Get top connections for a specific entity

    Args:
        entity_id: Entity ID (e.g., "jeffrey_epstein")
        limit: Maximum number of connections to return (default: 8, max: 20)

    Returns:
        List of connections with entity_id, display_name, guid, relationship_type, and strength

    Design Decision: Network-based Connections
    Rationale: Use entity_network.json edges to find strongest connections based on
    co-occurrence in flight logs. This provides real, data-backed relationships.

    Trade-offs:
    - Performance: O(n) scan of edges vs. pre-computed top_connections
    - Freshness: Always current vs. potentially stale cached data
    - Flexibility: Can filter by context type vs. fixed list

    Error Handling:
        - 404: Entity not found in entity_stats or network data
        - 500: Network data loading error
    """
    try:
        # Get entity from stats to verify it exists
        entity = entity_stats.get(entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")

        entity_name = entity.get("name", entity_id)

        # Find all edges where this entity is source or target
        edges = network_data.get("edges", [])
        entity_edges = []

        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            weight = edge.get("weight", 0)
            contexts = edge.get("contexts", [])

            # Check if entity matches (by ID - network data uses entity IDs)
            connected_id = None
            if source == entity_id:
                connected_id = target
            elif target == entity_id:
                connected_id = source
            else:
                continue

            # Get the connected entity from stats
            connected_entity = entity_stats.get(connected_id)

            if connected_entity:
                entity_edges.append({
                    "entity_id": connected_entity.get("id"),
                    "display_name": connected_entity.get("name"),
                    "guid": connected_entity.get("guid"),
                    "relationship_type": ", ".join(contexts) if contexts else "co-occurrence",
                    "strength": weight,
                    "shared_flights": weight if "flight_log" in contexts else 0
                })

        # Sort by strength (weight) descending and limit
        entity_edges.sort(key=lambda x: x["strength"], reverse=True)
        limited_edges = entity_edges[:limit]

        return {
            "entity_id": entity_id,
            "entity_name": entity_name,
            "total_connections": len(entity_edges),
            "connections": limited_edges
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching connections for entity '{entity_id}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch connections: {str(e)}")


@app.get("/api/entities/{entity_id}/similar")
async def get_similar_entities(
    entity_id: str,
    limit: int = Query(10, ge=1, le=20),
    min_similarity: float = Query(0.0, ge=0.0, le=1.0),
    username: str = Depends(get_current_user)
):
    """Get entities similar to the specified entity based on biography text.

    Uses semantic similarity search on entity biography embeddings in ChromaDB.
    Finds entities with similar roles, activities, and connections based on
    biographical text content.

    Args:
        entity_id: Entity ID (e.g., "jeffrey_epstein")
        limit: Maximum number of similar entities to return (default: 10, max: 20)
        min_similarity: Minimum similarity threshold 0.0-1.0 (default: 0.0)

    Returns:
        List of similar entities with:
        - entity_id: Entity identifier
        - display_name: Display name
        - similarity_score: Similarity score (0-1, higher = more similar)
        - primary_category: Main relationship category
        - quality_score: Biography quality score
        - biography_excerpt: First 200 chars of biography

    Example Response:
        {
          "entity_id": "jeffrey_epstein",
          "display_name": "Jeffrey Epstein",
          "similar_entities": [
            {
              "entity_id": "ghislaine_maxwell",
              "display_name": "Ghislaine Maxwell",
              "similarity_score": 0.6003,
              "primary_category": "associates",
              "quality_score": 0.95,
              "biography_excerpt": "British socialite and convicted..."
            }
          ],
          "count": 1
        }

    Error Handling:
        - 404: Entity not found in vector store
        - 500: ChromaDB or embedding model error
    """
    try:
        # Get entity similarity service
        similarity_service = get_entity_similarity_service()

        # Find similar entities
        similar_entities = similarity_service.find_similar_entities(
            entity_name=entity_id,
            limit=limit,
            min_similarity=min_similarity
        )

        return {
            "entity_id": entity_id,
            "similar_entities": similar_entities,
            "count": len(similar_entities)
        }

    except ValueError as e:
        # Entity not found
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error finding similar entities for '{entity_id}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find similar entities: {str(e)}")


@app.get("/api/entities/{entity_id}/similar/by-category")
async def get_similar_entities_by_category(
    entity_id: str,
    limit: int = Query(20, ge=1, le=50),
    username: str = Depends(get_current_user)
):
    """Get similar entities grouped by relationship category.

    Finds entities similar to the specified entity and groups them by their
    primary relationship category. Useful for discovering entity clusters.

    Args:
        entity_id: Entity ID (e.g., "jeffrey_epstein")
        limit: Maximum total similar entities to retrieve (default: 20, max: 50)

    Returns:
        Dictionary mapping category names to lists of similar entities.
        Each category contains entities sorted by similarity score (descending).

    Example Response:
        {
          "entity_id": "jeffrey_epstein",
          "categories": {
            "associates": [
              {
                "entity_id": "ghislaine_maxwell",
                "display_name": "Ghislaine Maxwell",
                "similarity_score": 0.6003
              }
            ],
            "public_figures": [...]
          },
          "total_entities": 10
        }

    Error Handling:
        - 404: Entity not found in vector store
        - 500: ChromaDB or embedding model error
    """
    try:
        # Get entity similarity service
        similarity_service = get_entity_similarity_service()

        # Find similar entities grouped by category
        by_category = similarity_service.cluster_by_category(
            entity_name=entity_id,
            limit=limit
        )

        # Count total entities
        total_entities = sum(len(entities) for entities in by_category.values())

        return {
            "entity_id": entity_id,
            "categories": by_category,
            "total_entities": total_entities
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error clustering similar entities for '{entity_id}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cluster similar entities: {str(e)}")


@app.get("/api/entities/search/by-text")
async def search_entities_by_text(
    query: str = Query(..., min_length=3),
    limit: int = Query(10, ge=1, le=20),
    category: Optional[str] = Query(None),
    username: str = Depends(get_current_user)
):
    """Search entities by free text query using semantic similarity.

    Searches entity biographies for semantic matches to the query text.
    Useful for finding entities by role, activity, or characteristics.

    Args:
        query: Free text search query (min 3 chars)
        limit: Maximum results to return (default: 10, max: 20)
        category: Optional category filter (e.g., "associates", "public_figures")

    Returns:
        List of matching entities with similarity scores

    Example Response:
        {
          "query": "British socialite convicted",
          "entities": [
            {
              "entity_id": "ghislaine_maxwell",
              "display_name": "Ghislaine Maxwell",
              "similarity_score": 0.8234,
              "primary_category": "associates",
              "biography_excerpt": "British socialite and convicted..."
            }
          ],
          "count": 1
        }

    Error Handling:
        - 400: Query too short (< 3 chars)
        - 500: ChromaDB or embedding model error
    """
    try:
        # Get entity similarity service
        similarity_service = get_entity_similarity_service()

        # Search by text
        matching_entities = similarity_service.search_by_text(
            query_text=query,
            limit=limit,
            category_filter=category
        )

        return {
            "query": query,
            "category_filter": category,
            "entities": matching_entities,
            "count": len(matching_entities)
        }

    except Exception as e:
        logger.error(f"Error searching entities by text '{query}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search entities: {str(e)}")


@app.get("/api/biographies/stats")
async def get_biography_stats(
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get biography quality statistics

    Returns aggregate quality metrics from v_biography_quality_stats view.
    Provides insights into biography data quality, coverage, and sources.

    Returns:
        List of statistics grouped by source with quality metrics
        Format: [{
            "source": str,
            "total_count": int,
            "avg_quality": float,
            "avg_words": float,
            "with_dates": int,
            "with_statistics": int
        }]

    Error Handling:
        - 500: Database error
    """
    try:
        # Query the database view directly
        result = db.execute(
            text("SELECT * FROM v_biography_quality_stats")
        ).fetchall()

        # Convert rows to dictionaries
        stats = []
        for row in result:
            stats.append({
                "source": row[0],
                "total_count": row[1],
                "avg_quality": round(row[2], 2) if row[2] else 0.0,
                "avg_words": round(row[3], 1) if row[3] else 0.0,
                "with_dates": row[4],
                "with_statistics": row[5],
            })

        # Calculate overall totals
        total_biographies = sum(s["total_count"] for s in stats)
        avg_quality = sum(s["avg_quality"] * s["total_count"] for s in stats) / total_biographies if total_biographies > 0 else 0.0
        total_with_dates = sum(s["with_dates"] for s in stats)
        total_with_stats = sum(s["with_statistics"] for s in stats)

        return {
            "by_source": stats,
            "totals": {
                "total_biographies": total_biographies,
                "avg_quality": round(avg_quality, 2),
                "with_dates": total_with_dates,
                "with_statistics": total_with_stats,
                "coverage_percentage": round((total_with_dates / total_biographies * 100), 1) if total_biographies > 0 else 0.0,
            }
        }

    except Exception as e:
        logger.error(f"Error fetching biography statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {str(e)}")


@app.get("/api/biographies/search")
async def search_biographies(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, le=100, description="Maximum results to return"),
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search entity biographies using full-text search

    Uses SQLite FTS5 (Full-Text Search) for fast, relevant search across
    entity names, summaries, and key facts. Falls back to LIKE search if
    FTS5 query fails.

    Args:
        q: Search query (minimum 2 characters)
        limit: Maximum number of results (default 20, max 100)

    Returns:
        List of matching entities with biographical information
        Format: [{
            "entity_id": str,
            "display_name": str,
            "summary": str,
            "occupation": str,
            "relevance": float  # FTS5 rank score (lower is better)
        }]

    Error Handling:
        - 500: Database error
    """
    try:
        # Try FTS5 search first for better relevance
        try:
            # FTS5 search syntax: supports phrase search, AND/OR operators, etc.
            # MATCH query returns ranked results (lower rank = more relevant)
            result = db.execute(
                text("""
                SELECT
                    b.entity_id,
                    b.display_name,
                    b.summary,
                    eb.occupation,
                    b.rank
                FROM biography_fts b
                JOIN entity_biographies eb ON b.entity_id = eb.entity_id
                WHERE biography_fts MATCH :query
                ORDER BY rank
                LIMIT :limit
                """),
                {"query": q, "limit": limit}
            ).fetchall()

            matches = []
            for row in result:
                matches.append({
                    "entity_id": row[0],
                    "display_name": row[1],
                    "summary": row[2],
                    "occupation": row[3],
                    "relevance": row[4],
                    "search_method": "fts5"
                })

            return {
                "query": q,
                "total": len(matches),
                "results": matches,
                "method": "fts5"
            }

        except Exception as fts_error:
            # FTS5 search failed (possibly invalid query syntax), fall back to LIKE
            logger.warning(f"FTS5 search failed, falling back to LIKE: {fts_error}")

            result = db.execute(
                text("""
                SELECT
                    e.id,
                    e.display_name,
                    eb.summary,
                    eb.occupation
                FROM entities e
                JOIN entity_biographies eb ON e.id = eb.entity_id
                WHERE
                    e.display_name LIKE :query
                    OR eb.summary LIKE :query
                    OR eb.key_facts LIKE :query
                ORDER BY e.display_name
                LIMIT :limit
                """),
                {"query": f"%{q}%", "limit": limit}
            ).fetchall()

            matches = []
            for row in result:
                matches.append({
                    "entity_id": row[0],
                    "display_name": row[1],
                    "summary": row[2],
                    "occupation": row[3],
                    "search_method": "like"
                })

            return {
                "query": q,
                "total": len(matches),
                "results": matches,
                "method": "like_fallback"
            }

    except Exception as e:
        logger.error(f"Error searching biographies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search biographies: {str(e)}")


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
    entity_type: Optional[str] = Query(None, enum=["person", "organization", "location"]),
    username: str = Depends(get_current_user),
):
    """Get list of entities with optional filtering and sorting

    Design Decision: Filter Generic Entities
    Rationale: Exclude non-disambiguatable entities (Male, Female, Nanny (1))
    from API results. These are placeholders, not actual identifiable people.

    Bug Fix (2025-12-06): Added entity_type parameter and field
    - Frontend sends entity_type=person/organization/location for filtering
    - Person entities from entity_stats now include entity_type="person"
    - All entities now have connection_count field for slider filtering
    """
    # Start with entity_stats (persons with document statistics)
    # BUG FIX: Add entity_type field to person entities
    entities_list = []
    for entity_data in entity_stats.values():
        entity_copy = dict(entity_data)
        entity_copy['entity_type'] = 'person'
        entities_list.append(entity_copy)

    # Add organizations and locations from entity_bios that aren't in entity_stats
    entity_stats_names = {e.get("name", "") for e in entities_list}
    entity_stats_ids = {e.get("id", "") for e in entities_list}

    orgs_added = 0
    locs_added = 0

    for entity_key, entity_data in entity_bios.items():
        # Skip if already in entity_stats (persons)
        if entity_key in entity_stats_names or entity_key in entity_stats_ids:
            continue

        # Skip person entities (they should be in entity_stats)
        bio_entity_type = entity_data.get("entity_type")
        if bio_entity_type == "person":
            continue

        # Add organization/location entity with basic structure
        entities_list.append({
            "id": entity_key,
            "name": entity_data.get("name", entity_key),
            "entity_type": bio_entity_type,
            "total_documents": 0,  # Organizations/locations don't have document counts yet
            "connection_count": 0,
            "sources": []
        })

        if bio_entity_type == "organization":
            orgs_added += 1
        elif bio_entity_type == "location":
            locs_added += 1

    print(f"[API] Added {orgs_added} organizations and {locs_added} locations to entity list")

    # Filter out generic entities (Male, Female, etc.)
    entities_list = [e for e in entities_list if not entity_filter.is_generic(e.get("name", ""))]

    # BUG FIX: Filter by entity_type if specified
    if entity_type:
        entities_list = [e for e in entities_list if e.get("entity_type") == entity_type]

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
    entities_page = entities_list[offset : offset + limit]

    return {"total": total, "offset": offset, "limit": limit, "entities": entities_page}


@app.get("/api/v2/entities/{entity_id}")
async def get_entity_v2(entity_id: str, username: str = Depends(get_current_user)):
    """Get entity by ID (v2 - recommended)

    Args:
        entity_id: Unique entity identifier (snake_case slug, e.g., 'jeffrey_epstein')

    Returns:
        Entity data with full details including enriched biography, news count, and timeline count

    Design Decision: ID-based lookups for performance and stability
    Rationale: Entity IDs are stable identifiers (17-20x faster than name matching)
    """
    entity = entity_stats.get(entity_id)

    if not entity:
        raise HTTPException(
            status_code=404,
            detail=f"Entity not found: '{entity_id}'. Use /api/entities/resolve to find entity ID from name.",
        )

    # Merge enriched biography data if available
    # Try ID first, then fallback to name for backward compatibility
    if entity_id in entity_bios:
        entity["bio"] = entity_bios[entity_id]
        logger.debug(f"Merged bio for {entity_id} (by ID)")
    elif entity.get("name") in entity_bios:
        entity["bio"] = entity_bios[entity.get("name")]
        logger.debug(f"Merged bio for {entity.get('name')} (by name)")

    # Add news and timeline counts
    entity_name = entity.get("name", "")
    entity["news_articles_count"] = get_entity_news_count(entity_name)
    entity["timeline_events_count"] = get_entity_timeline_count(entity_name)

    return entity


@app.get("/api/v3/entities/{guid}/{name}")
@app.get("/api/v3/entities/{guid}")
async def get_entity_v3(
    guid: str,
    name: Optional[str] = None,
    username: str = Depends(get_current_user)
):
    """Get entity by GUID with optional SEO-friendly name (v3 - SEO-optimized)

    URL Pattern: /api/v3/entities/{guid}/{name?}
    - GUID: Required - Unique identifier for entity lookup (UUID4 format)
    - Name: Optional - SEO-friendly slug (ignored in lookup, for human readability only)

    Examples:
        /api/v3/entities/a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d
        /api/v3/entities/a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d/jeffrey-epstein

    Design Decision: GUID-based permalinks with SEO names
    Rationale:
        - GUIDs provide globally unique, stable identifiers
        - SEO names improve URL readability without coupling to entity names
        - O(1) lookup performance via guid_to_id mapping
        - Frontend can change display names without breaking links

    Trade-offs:
        - Performance: O(1) GUID lookup (pre-built mapping at startup)
        - Stability: GUIDs never change, safe for bookmarks/sharing
        - SEO: Human-readable names in URLs aid search engine indexing
        - Flexibility: Name parameter allows URL customization without backend changes

    Args:
        guid: Entity GUID (UUID4 format, e.g., 'a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d')
        name: Optional SEO-friendly name slug (not used in lookup)

    Returns:
        Entity data with full details

    Error Conditions:
        - 400: Invalid GUID format (not a valid UUID)
        - 404: Entity not found (GUID not in database)
    """
    # Validate GUID format (UUID4)
    try:
        UUID(guid, version=4)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid GUID format: '{guid}'. Expected UUID4 format (e.g., 'a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d')."
        )

    # Lookup entity ID from GUID (O(1) operation)
    entity_id = guid_to_id.get(guid)

    if not entity_id:
        raise HTTPException(
            status_code=404,
            detail=f"Entity not found for GUID: '{guid}'. GUID may not exist or entity may have been removed."
        )

    # Retrieve entity data
    entity = entity_stats.get(entity_id)

    if not entity:
        # This should never happen if guid_to_id is in sync, but defensive check
        logger.error(f"GUID mapping out of sync: GUID '{guid}' maps to ID '{entity_id}' but entity not found")
        raise HTTPException(
            status_code=500,
            detail="Internal error: Entity data inconsistency detected."
        )

    # Merge enriched biography data if available
    # Try ID first, then fallback to name for backward compatibility
    if entity_id in entity_bios:
        entity["bio"] = entity_bios[entity_id]
        logger.debug(f"Merged bio for {entity_id} (by ID)")
    elif entity.get("name") in entity_bios:
        entity["bio"] = entity_bios[entity.get("name")]
        logger.debug(f"Merged bio for {entity.get('name')} (by name)")

    # Add news and timeline counts
    entity_name = entity.get("name", "")
    entity["news_articles_count"] = get_entity_news_count(entity_name)
    entity["timeline_events_count"] = get_entity_timeline_count(entity_name)

    return entity


@app.get("/api/entities/{name_or_id}")
async def get_entity(name_or_id: str, username: str = Depends(get_current_user)):
    """Get entity by name or ID (v1 - backward compatible)

    Handles both:
    - Entity IDs: 'jeffrey_epstein', 'ghislaine_maxwell'
    - Entity names: 'Epstein, Jeffrey', 'Je Je Epstein' (with disambiguation)

    Design Decision: Dual-lookup for backward compatibility
    Rationale: Try ID lookup first (fast), fallback to name search (slower)

    Deprecation: Use /api/v2/entities/{entity_id} for new code (faster, more reliable)
    """
    # Try ID lookup first (fast path)
    entity = entity_stats.get(name_or_id)

    if not entity:
        # Fallback to name lookup with disambiguation
        disambiguator = get_disambiguator()
        entity = disambiguator.search_entity(name_or_id, entity_stats)

    if not entity:
        # Try name-to-ID mapping
        entity_id = name_to_id.get(name_or_id)
        if entity_id:
            entity = entity_stats.get(entity_id)

    if not entity:
        raise HTTPException(
            status_code=404,
            detail=f"Entity not found: '{name_or_id}'. Try canonical name, check spelling, or use entity ID.",
        )

    # Add bio field if available (lookup by ID first, fallback to name)
    entity_name = entity.get("name", "")
    if name_or_id in entity_bios:
        entity["bio"] = entity_bios[name_or_id]
    elif entity_name in entity_bios:
        entity["bio"] = entity_bios[entity_name]

    # Add deprecation header
    headers = {"X-API-Deprecation": "Use /api/v2/entities/{entity_id} for better performance"}

    # Add normalized name to response for backward compatibility
    return JSONResponse(
        content={**entity, "search_name": name_or_id, "canonical_name": entity.get("name", "")},
        headers=headers,
    )


@app.get("/api/entities/resolve/{name}")
async def resolve_entity_name_to_id(name: str, username: str = Depends(get_current_user)):
    """Resolve entity name to ID

    Args:
        name: Entity name or variation (e.g., 'Epstein, Jeffrey', 'Jeffrey Epstein')

    Returns:
        {"name": "Epstein, Jeffrey", "entity_id": "jeffrey_epstein"}

    Design Decision: Name resolution utility endpoint
    Rationale: Helps clients migrate from name-based to ID-based lookups
    """
    # Try direct name-to-ID mapping first
    entity_id = name_to_id.get(name)

    if not entity_id:
        # Try disambiguation search
        disambiguator = get_disambiguator()
        entity = disambiguator.search_entity(name, entity_stats)
        if entity:
            entity_id = entity.get("id")

    if not entity_id:
        raise HTTPException(
            status_code=404,
            detail=f"Could not resolve name: '{name}'. Try canonical name or check spelling.",
        )

    return {"name": name, "entity_id": entity_id, "canonical_name": id_to_name.get(entity_id, "")}


class BatchResolveRequest(BaseModel):
    names: list[str]


@app.post("/api/entities/batch/resolve")
async def batch_resolve_names(
    request: BatchResolveRequest, username: str = Depends(get_current_user)
):
    """Batch resolve names to IDs

    Args:
        names: List of entity names to resolve

    Returns:
        {"results": {"Epstein, Jeffrey": "jeffrey_epstein", ...}, "not_found": ["Unknown Name"]}

    Design Decision: Batch resolution for efficiency
    Rationale: Reduce API round-trips when resolving multiple names
    """
    results = {}
    not_found = []

    for name in request.names:
        # Try direct mapping
        entity_id = name_to_id.get(name)

        if not entity_id:
            # Try disambiguation
            disambiguator = get_disambiguator()
            entity = disambiguator.search_entity(name, entity_stats)
            if entity:
                entity_id = entity.get("id")

        if entity_id:
            results[name] = entity_id
        else:
            not_found.append(name)

    return {
        "results": results,
        "not_found": not_found,
        "total_requested": len(request.names),
        "resolved": len(results),
        "failed": len(not_found),
    }


@app.get("/api/network")
async def get_network(
    min_connections: int = Query(0),
    max_nodes: int = Query(500, le=1000),
    deduplicate: bool = Query(False),  # FIXED: Disabled until deduplication works with snake_case IDs
    username: str = Depends(get_current_user),
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

    # Build mapping from ALL original IDs to canonical IDs BEFORE any filtering
    # This is critical because edges reference original IDs from network_data
    original_to_canonical = {}
    if deduplicate:
        for node in nodes:
            original_id = node.get("id", node.get("name", ""))
            original_to_canonical[original_id] = disambiguator.normalize_name(original_id)

    # Filter out generic entities
    nodes = [n for n in nodes if not entity_filter.is_generic(n.get("name", ""))]

    # Apply deduplication if requested
    if deduplicate:
        original_count = len(nodes)
        nodes = disambiguator.merge_duplicate_nodes(nodes)
        deduplicated_count = original_count - len(nodes)
        print(
            f"Deduplicated {deduplicated_count} duplicate nodes ({original_count} -> {len(nodes)})"
        )

    # Filter by minimum connections
    nodes = [n for n in nodes if n.get("connection_count", 0) >= min_connections]

    # Sort by connections and limit
    nodes.sort(key=lambda n: n.get("connection_count", 0), reverse=True)
    nodes = nodes[:max_nodes]

    # Get node IDs for edge filtering (after deduplication, these are canonical IDs)
    canonical_node_ids = {n["id"] for n in nodes}

    # When filtering edges, accept edges that reference either original or canonical IDs
    # because edges still use original IDs before deduplicate_edges is called
    if deduplicate:
        # Build set of all valid IDs (original + canonical)
        valid_edge_ids = canonical_node_ids.copy()
        for orig_id, canon_id in original_to_canonical.items():
            if canon_id in canonical_node_ids:
                valid_edge_ids.add(orig_id)
    else:
        valid_edge_ids = canonical_node_ids

    # Filter edges using valid ID set
    edges = [
        e
        for e in network_data.get("edges", [])
        if e["source"] in valid_edge_ids and e["target"] in valid_edge_ids
    ]

    # Deduplicate and normalize edge IDs to canonical form
    if deduplicate:
        edges = disambiguator.deduplicate_edges(edges, original_to_canonical)

    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            **network_data.get("metadata", {}),
            "deduplicated": deduplicate,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
        },
    }


@app.get("/api/search")
async def search(
    q: str = Query(..., min_length=1),
    type: Optional[str] = Query(None),
    limit: int = Query(50, le=500),
    username: str = Depends(get_current_user),
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
            results.append({"type": "entity", "name": entity_name, "data": entity_data})

    for doc_path, doc_data in classifications.items():
        if type and doc_data.get("type") != type:
            continue

        if q.lower() in doc_path.lower():
            results.append({"type": "document", "path": doc_path, "data": doc_data})

    return {"query": q, "total": len(results), "results": results[:limit]}


@app.get("/api/timeline")
async def get_timeline(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(1000, le=5000),
    username: str = Depends(get_current_user),
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
        "date_range": timeline_data.get("date_range", {}),
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


# OLD CHAT ENDPOINT - DEPRECATED
# This endpoint has been replaced by the enhanced chat router in routes/chat_enhanced.py
# The enhanced version provides intent detection, entity recognition, and better navigation
# Keeping this commented out to avoid route conflicts
#
# @app.post("/api/chat")
# async def chat(message: ChatMessage, username: str = Depends(get_current_user)):
#     """Chat with GPT-4.5 assistant about the archive with RAG-powered document retrieval
#
#     Flow:
#     1. Vector search via ChromaDB to find semantically relevant documents
#     2. Retrieve top 5 most relevant document excerpts
#     3. Build context from retrieved documents
#     4. LLM synthesizes answer from context
#     5. Return conversational response with source citations
#     """
# DEPRECATED - DO NOT USE
#     try:
#         # Import RAG dependencies
#         try:
#             import chromadb
#             from chromadb.config import Settings
#             from sentence_transformers import SentenceTransformer
#         except ImportError:
#             # Fallback to basic search if ChromaDB not available
#             return {
#                 "response": "RAG system not available. Please install ChromaDB dependencies: pip install chromadb sentence-transformers",
#                 "error": "chromadb_not_installed",
#             }
# 
#         # Initialize ChromaDB and embedding model
#         try:
#             VECTOR_STORE_DIR = PROJECT_ROOT / "data/vector_store/chroma"
#             COLLECTION_NAME = "epstein_documents"
# 
#             chroma_client = chromadb.PersistentClient(
#                 path=str(VECTOR_STORE_DIR), settings=Settings(anonymized_telemetry=False)
#             )
#             collection = chroma_client.get_collection(name=COLLECTION_NAME)
#             embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
# 
#         except Exception as e:
#             logger.error(f"Failed to initialize ChromaDB: {e}")
#             return {
#                 "response": "Vector store not initialized. Please run build_vector_store.py first.",
#                 "error": "vector_store_not_initialized",
#             }
# 
#         # Perform semantic search to retrieve relevant documents
#         query_embedding = embedding_model.encode([message.message])[0]
# 
#         search_results = collection.query(
#             query_embeddings=[query_embedding.tolist()],
#             n_results=5,  # Top 5 most relevant documents
#         )
# 
#         # Extract retrieved documents with excerpts
#         retrieved_docs = []
#         if search_results["ids"][0]:
#             for i in range(len(search_results["ids"][0])):
#                 doc_id = search_results["ids"][0][i]
#                 distance = search_results["distances"][0][i]
#                 similarity = 1 - distance
#                 text = search_results["documents"][0][i]
#                 metadata = search_results["metadatas"][0][i]
# 
#                 # Create excerpt (first 500 chars)
#                 excerpt = text[:500] + "..." if len(text) > 500 else text
# 
#                 retrieved_docs.append(
#                     {
#                         "id": doc_id,
#                         "similarity": float(similarity),
#                         "excerpt": excerpt,
#                         "full_text": text,
#                         "metadata": metadata,
#                         "filename": metadata.get("filename", "Unknown"),
#                         "doc_type": metadata.get("doc_type", "unknown"),
#                     }
#                 )
# 
#         # Build RAG context from retrieved documents
#         if retrieved_docs:
#             rag_context = "\n\n=== RELEVANT ARCHIVE DOCUMENTS ===\n\n"
#             for i, doc in enumerate(retrieved_docs, 1):
#                 rag_context += f"Document {i} ({doc['filename']}):\n"
#                 rag_context += f"{doc['full_text'][:800]}\n"  # Use more context for LLM
#                 rag_context += f"[Similarity: {doc['similarity']:.2f}]\n\n"
#         else:
#             rag_context = "\n[No relevant documents found in vector store for this query]"
# 
#         # Build system prompt with RAG context
#         stats_context = f"""
# CURRENT ARCHIVE STATUS:
# - Total Entities: {len(entity_stats)}
# - Documents in Vector Store: {collection.count()}
# - Network Nodes: {len(network_data.get('nodes', []))}
# - Network Connections: {len(network_data.get('edges', []))}
# 
# RETRIEVED DOCUMENTS (via semantic search):
# {rag_context}
# """
# 
#         full_context = PROJECT_CONTEXT + "\n" + stats_context
# 
#         # Call OpenRouter LLM to synthesize answer
#         try:
#             client = get_openrouter_client()
# 
#             completion = client.chat.completions.create(
#                 model=openrouter_model,
#                 messages=[
#                     {
#                         "role": "system",
#                         "content": full_context
#                         + "\n\nIMPORTANT: Answer the user's question based ONLY on the retrieved documents above. Cite document sources when possible. If the documents don't contain relevant information, say so clearly.",
#                     },
#                     {"role": "user", "content": message.message},
#                 ],
#                 temperature=0.3,  # Lower temperature for more factual responses
#                 max_tokens=800,
#                 timeout=30.0,
#             )
# 
#             response = completion.choices[0].message.content.strip()
# 
#             # Format sources for frontend
#             sources = [
#                 {
#                     "doc_id": doc["id"],
#                     "filename": doc["filename"],
#                     "excerpt": doc["excerpt"],
#                     "similarity": doc["similarity"],
#                     "doc_type": doc["doc_type"],
#                 }
#                 for doc in retrieved_docs
#             ]
# 
#             return {
#                 "response": response,
#                 "model": openrouter_model,
#                 "sources": sources,
#                 "rag_enabled": True,
#                 "documents_retrieved": len(retrieved_docs),
#             }
# 
#         except Exception as api_error:
#             logger.error(f"OpenRouter API error: {api_error}")
#             return {
#                 "response": f"Sorry, I'm having trouble connecting to the AI service. Error: {api_error!s}",
#                 "error": str(api_error),
#                 "sources": (
#                     [
#                         {"filename": doc["filename"], "excerpt": doc["excerpt"]}
#                         for doc in retrieved_docs
#                     ]
#                     if retrieved_docs
#                     else []
#                 ),
#             }
# 
#     except Exception as e:
#         logger.error(f"Chat error: {e}")
#         return {"response": f"Error: {e!s}"}


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
    watch_dirs=[METADATA_DIR, MD_DIR / "entities"], enable_hot_reload=ENABLE_HOT_RELOAD
)


# Start file watcher on app startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on server startup"""
    if ENABLE_HOT_RELOAD:
        file_watcher_service.start()
        logger.info(
            f"File watcher started (monitoring {len(file_watcher_service.watch_dirs)} directories)"
        )
    else:
        logger.info("Hot-reload disabled")


# Source Suggestion Endpoints


@app.post("/api/suggestions", status_code=201)
async def create_suggestion(
    suggestion: SuggestedSourceCreate, username: str = Depends(get_current_user)
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
    urllib.parse.urlparse(suggestion.url)

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
        "suggestion": created,
    }


@app.get("/api/suggestions")
async def list_suggestions(
    status: Optional[SourceStatus] = Query(None),
    priority: Optional[SourcePriority] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    username: str = Depends(get_current_user),
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
        status=status, priority=priority, limit=limit, offset=offset
    )

    return {"total": total, "offset": offset, "limit": limit, "suggestions": suggestions}


@app.get("/api/suggestions/{suggestion_id}")
async def get_suggestion(suggestion_id: str, username: str = Depends(get_current_user)):
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
    suggestion_id: str, update: SuggestedSourceUpdate, username: str = Depends(get_current_user)
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
    updated = suggestion_service.update_status(suggestion_id, update, reviewed_by=username)

    if not updated:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    return {"status": "success", "suggestion": updated}


@app.delete("/api/suggestions/{suggestion_id}")
async def delete_suggestion(suggestion_id: str, username: str = Depends(get_current_user)):
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

    return {"status": "success", "message": "Suggestion deleted successfully"}


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
    entity_id: str, force_refresh: bool = Query(False), username: str = Depends(get_current_user)
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
            (eid, edata)
            for eid, edata in entity_stats.items()
            if eid == entity_id or edata.get("name") == entity_id
        ]

        if not matching_entities:
            raise HTTPException(
                status_code=404,
                detail=f"Entity '{entity_id}' not found in archive. "
                "Only entities in existing documents can be enriched.",
            )

        entity_id, entity_data = matching_entities[0]

    entity_name = entity_data.get("name", entity_id)

    try:
        # Perform enrichment
        enrichment = await enrichment_service.enrich_entity(
            entity_id=entity_id, entity_name=entity_name, force_refresh=force_refresh
        )

        # Format for UI
        return format_for_ui(enrichment)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enriching entity: {e!s}")


@app.get("/api/entities/{entity_id}/enrichment")
async def get_enrichment(entity_id: str, username: str = Depends(get_current_user)):
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
            (eid, edata)
            for eid, edata in entity_stats.items()
            if eid == entity_id or edata.get("name") == entity_id
        ]

        if not matching_entities:
            raise HTTPException(
                status_code=404, detail=f"Entity '{entity_id}' not found in archive"
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
        "cache_ttl_days": enrichment_service.CACHE_TTL_DAYS,
    }


@app.post("/api/entities/enrich/batch")
async def enrich_batch(
    entity_ids: list[str],
    max_concurrent: int = Query(3, ge=1, le=5),
    username: str = Depends(get_current_user),
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
        raise HTTPException(status_code=400, detail="Maximum 20 entities per batch request")

    # Verify all entities exist
    entities = []
    for entity_id in entity_ids:
        entity_data = entity_stats.get(entity_id)
        if not entity_data:
            # Try name match
            matching = [
                (eid, edata)
                for eid, edata in entity_stats.items()
                if eid == entity_id or edata.get("name") == entity_id
            ]
            if not matching:
                raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")
            entity_id, entity_data = matching[0]

        entities.append({"id": entity_id, "name": entity_data.get("name", entity_id)})

    try:
        # Perform batch enrichment
        enrichments = await enrichment_service.enrich_batch(
            entities=entities, max_concurrent=max_concurrent
        )

        # Format for UI
        return {"total": len(enrichments), "enrichments": [format_for_ui(e) for e in enrichments]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during batch enrichment: {e!s}")


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
            "is_semantic": True,
        }
    return {
        "type": "chore",
        "scope": None,
        "breaking": False,
        "message": message,
        "is_semantic": False,
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
            return {"routes": [], "total_flights": 0, "error": "Flight data not found"}

        with open(flight_data_path) as f:
            flight_data = json.load(f)

        # Load location database
        locations_path = METADATA_DIR / "flight_locations.json"
        if not locations_path.exists():
            return {"routes": [], "total_flights": 0, "error": "Location database not found"}

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
                    "origin": {"code": origin_code, **origin_data},
                    "destination": {"code": dest_code, **dest_data},
                    "flights": [],
                }

            # Add flight to route
            route_map[route_key]["flights"].append(
                {
                    "id": flight.get("id"),
                    "date": flight_date,
                    "passengers": flight.get("passengers", []),
                    "passenger_count": flight.get(
                        "passenger_count", len(flight.get("passengers", []))
                    ),
                    "aircraft": flight.get("tail_number", ""),
                }
            )

        # Convert route_map to array with frequency
        routes = []
        for route_key, route_data in route_map.items():
            routes.append(
                {
                    "origin": route_data["origin"],
                    "destination": route_data["destination"],
                    "flights": route_data["flights"],
                    "frequency": len(route_data["flights"]),
                }
            )

        # Sort routes by frequency (most traveled routes first)
        routes.sort(key=lambda r: r["frequency"], reverse=True)

        # Calculate date range
        date_range = {}
        if all_dates:
            # Sort dates (handle MM/DD/YYYY format)
            sorted_dates = sorted(all_dates, key=lambda d: parse_date_for_sort(d))
            date_range = {"start": sorted_dates[0], "end": sorted_dates[-1]}

        # Calculate actual processed flights (flights that made it onto the map)
        processed_flight_count = sum(len(route["flights"]) for route in routes)

        return {
            "routes": routes,
            "total_flights": processed_flight_count,
            "unique_routes": len(routes),
            "unique_passengers": len(unique_passengers_set),
            "date_range": date_range,
            "airports": airports,
        }

    except Exception as e:
        import traceback

        traceback.print_exc()
        return {"routes": [], "total_flights": 0, "error": str(e)}


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
    username: str = Depends(get_current_user),
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
            doc
            for doc in filtered_docs
            if not (
                # Exclude JSON files from data/metadata/ directory
                (
                    doc.get("path", "").startswith("data/metadata/")
                    and doc.get("filename", "").endswith(".json")
                )
                or
                # Exclude documents with unavailable content
                doc.get("content") == "Content not available for this document."
            )
        ]

        # Filter by entity
        if entity:
            entity_lower = entity.lower()
            filtered_docs = [
                doc
                for doc in filtered_docs
                if any(entity_lower in e.lower() for e in doc.get("entities_mentioned", []))
            ]

        # Filter by document type
        if doc_type:
            filtered_docs = [
                doc
                for doc in filtered_docs
                if doc.get("classification", "").lower() == doc_type.lower()
            ]

        # Filter by source
        if source:
            filtered_docs = [
                doc for doc in filtered_docs if source.lower() in doc.get("source", "").lower()
            ]

        # Full-text search in filename and path
        if q:
            q_lower = q.lower()
            filtered_docs = [
                doc
                for doc in filtered_docs
                if q_lower in doc.get("filename", "").lower()
                or q_lower in doc.get("path", "").lower()
            ]

        # Get total before pagination
        total = len(filtered_docs)

        # Paginate
        paginated_docs = filtered_docs[offset : offset + limit]

        # Generate facets for filtering
        all_types = {doc.get("classification", "unknown") for doc in documents}
        all_sources = {doc.get("source", "unknown") for doc in documents}

        return {
            "documents": paginated_docs,
            "total": total,
            "limit": limit,
            "offset": offset,
            "filters": {"types": sorted(all_types), "sources": sorted(all_sources)},
        }

    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return {"documents": [], "total": 0, "error": str(e)}


@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str, username: str = Depends(get_current_user)):
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

        return {"document": document, "content": content}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{doc_id}/summary")
async def get_document_summary(doc_id: str, username: str = Depends(get_current_user)):
    """Get document summary with preview text and detected entities from OCR.

    Design Decision: Summary endpoint for large PDFs with entity extraction
    Rationale: Large PDFs (>50MB) can't load in browser. This endpoint provides:
    - Preview text from OCR (first 3000 characters)
    - Document metadata (size, page count, entities)
    - Detected entities with mention counts and GUIDs
    - OCR availability status

    Performance Target: <500ms total (entity detection ~50-200ms)

    Returns:
        {
            "document_id": str,
            "filename": str,
            "file_size": int,
            "has_ocr_text": bool,
            "preview_text": str | None,  # First 3000 chars
            "full_text_length": int,     # Total OCR text length
            "entities_mentioned": list[str],  # Legacy list of names
            "detected_entities": list[{       # NEW: Entity detection results
                "guid": str,
                "name": str,
                "mentions": int,
                "entity_type": str
            }],
            "metadata": dict             # Original document metadata
        }

    Error Handling:
    - 404 if document not found
    - Returns has_ocr_text=False if OCR file doesn't exist
    - preview_text=None if no OCR available
    - Entity detection failures are logged but don't fail request
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

        # Initialize response
        summary = {
            "document_id": doc_id,
            "filename": document.get("filename", ""),
            "file_size": document.get("file_size", 0),
            "has_ocr_text": False,
            "preview_text": None,
            "full_text_length": 0,
            "entities_mentioned": document.get("entities_mentioned", []),
            "detected_entities": [],  # NEW: Will populate from entity detection
            "metadata": document,
        }

        # Check for OCR text file
        # OCR files are in data/sources/house_oversight_nov2025/ocr_text/
        # Pattern: {filename without extension}.txt
        filename = document.get("filename", "")
        if filename:
            # Remove .pdf extension and add .txt
            base_name = filename.rsplit(".", 1)[0]
            ocr_text_path = Path("data/sources/house_oversight_nov2025/ocr_text") / f"{base_name}.txt"

            if ocr_text_path.exists():
                try:
                    with open(ocr_text_path, "r", encoding="utf-8") as f:
                        full_text = f.read()

                    summary["has_ocr_text"] = True
                    summary["full_text_length"] = len(full_text)
                    # Provide first 3000 characters as preview
                    summary["preview_text"] = full_text[:3000]

                    # NEW: Detect entities in full OCR text
                    try:
                        detector = get_entity_detector()
                        # Use full text for accurate mention counts
                        detected = detector.detect_entities(full_text, max_results=20)
                        summary["detected_entities"] = [
                            {
                                "guid": entity.guid,
                                "name": entity.name,
                                "mentions": entity.mentions,
                                "entity_type": entity.entity_type,
                            }
                            for entity in detected
                        ]
                        logger.info(f"Detected {len(detected)} entities in document {doc_id}")
                    except Exception as e:
                        logger.warning(f"Entity detection failed for {doc_id}: {e}")
                        # Continue without entity detection - not critical

                    # Try to load OCR metadata JSON if available
                    ocr_json_path = ocr_text_path.with_suffix(".json")
                    if ocr_json_path.exists():
                        try:
                            with open(ocr_json_path, "r") as f:
                                ocr_metadata = json.load(f)
                                summary["ocr_metadata"] = ocr_metadata
                        except Exception as e:
                            logger.warning(f"Could not load OCR metadata for {doc_id}: {e}")

                except Exception as e:
                    logger.warning(f"Could not read OCR text for {doc_id}: {e}")

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching summary for {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{doc_id}/rag-summary")
async def get_document_rag_summary(
    doc_id: str,
    username: str = Depends(get_current_user)
):
    """
    Generate AI-powered summary from RAG-extracted document content.

    Design Decision: Use ChromaDB + Grok for intelligent document summarization
    Rationale:
    - PDFs often fail to display due to CORS issues
    - Users need to understand document content without downloading
    - We have RAG content available in ChromaDB vector store
    - Grok API can generate concise, accurate summaries from chunks

    Process:
    1. Query ChromaDB for document chunks by doc_id
    2. Get top 10-15 most relevant chunks
    3. Combine chunks into context (max 4000 chars)
    4. Use Grok API to generate 150-200 word summary
    5. Return summary with metadata

    Performance Target: <3 seconds (ChromaDB query ~100ms, Grok API ~2s)

    Returns:
        {
            "document_id": str,
            "summary": str,           # AI-generated summary
            "chunk_count": int,       # Number of chunks used
            "total_content_length": int,
            "generated_at": str,      # ISO timestamp
            "source": "rag_chromadb"
        }

    Error Handling:
    - 404 if document not found in ChromaDB
    - 503 if Grok API unavailable
    - Graceful degradation to OCR preview if RAG fails
    """
    try:
        # Get ChromaDB collection
        from server.routes.rag import get_chroma_collection
        collection = get_chroma_collection()

        # Query for document chunks
        try:
            # Get document from ChromaDB
            result = collection.get(ids=[doc_id])

            if not result["ids"]:
                # Try with different ID format (some docs may have prefixes)
                raise HTTPException(
                    status_code=404,
                    detail=f"Document {doc_id} not found in RAG vector store"
                )

            # Get document text
            doc_text = result["documents"][0] if result["documents"] else ""
            metadata = result["metadatas"][0] if result["metadatas"] else {}

            if not doc_text:
                raise HTTPException(
                    status_code=404,
                    detail="No RAG content available for this document"
                )

            # Truncate to reasonable length for summarization (4000 chars)
            content_for_summary = doc_text[:4000]

            # Generate summary using Grok API
            try:
                client = get_openrouter_client()

                response = client.chat.completions.create(
                    model=openrouter_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a legal document analyzer. Generate concise, factual summaries of court documents and legal filings. Focus on key facts, parties involved, and main allegations or findings. Be objective and precise."
                        },
                        {
                            "role": "user",
                            "content": f"Summarize this document in 150-200 words. Focus on the most important facts and findings:\n\n{content_for_summary}"
                        }
                    ],
                    max_tokens=400,
                    temperature=0.3,  # Low temperature for factual summaries
                )

                summary_text = response.choices[0].message.content.strip()

                return {
                    "document_id": doc_id,
                    "summary": summary_text,
                    "chunk_count": 1,
                    "total_content_length": len(doc_text),
                    "content_preview_length": len(content_for_summary),
                    "generated_at": datetime.now().isoformat(),
                    "source": "rag_chromadb",
                    "metadata": metadata
                }

            except Exception as e:
                logger.error(f"Grok API failed for {doc_id}: {e}")
                raise HTTPException(
                    status_code=503,
                    detail=f"AI summary generation failed: {str(e)}"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"ChromaDB query failed for {doc_id}: {e}")
            # Fallback to OCR summary if RAG fails
            raise HTTPException(
                status_code=404,
                detail=f"RAG content not available. Use /api/documents/{doc_id}/summary for OCR preview."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating RAG summary for {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{document_id}/ai-summary")
async def get_document_ai_summary(
    document_id: str,
    username: str = Depends(get_current_user)
):
    """
    Generate on-demand AI summary from PDF document with caching.

    Design Decision: Direct PDF extraction + Grok summarization with persistent caching
    Rationale:
    - Large PDFs (>5MB) fail to render in browser
    - Users need quick understanding without downloading full file
    - Extract text directly from PDF files (not relying on OCR or RAG)
    - Cache summaries in master_document_index.json to avoid regeneration
    - Use Grok for fast, accurate summarization (x-ai/grok-4.1-fast:free)

    Process:
    1. Look up document by hash in master_document_index.json
    2. Check if summary already cached in document metadata
    3. If cached: return immediately (no API call)
    4. If not cached:
       a. Extract text from PDF file using pypdf
       b. Generate summary using Grok API
       c. Cache summary in master_document_index.json
       d. Return generated summary

    Performance:
    - Cached: <50ms (file read only)
    - Uncached: 2-5s (PDF extraction ~500ms, Grok API ~2-4s)

    Returns:
        {
            "document_id": str,           # Document hash
            "summary": str,                # AI-generated summary (200-300 words)
            "summary_generated_at": str,   # ISO timestamp
            "summary_model": str,          # Model used for generation
            "word_count": int,             # Word count of summary
            "from_cache": bool,            # Whether summary was cached
            "document_metadata": {         # Original document info
                "canonical_path": str,
                "size": int,
                "source_count": int
            }
        }

    Error Handling:
    - 404 if document_id not found in master_document_index.json
    - 404 if PDF file doesn't exist at canonical_path
    - 500 if PDF extraction fails
    - 503 if Grok API fails (doesn't cache failed attempts)
    """
    try:
        # Load master document index
        master_index_path = METADATA_DIR / "master_document_index.json"
        if not master_index_path.exists():
            raise HTTPException(
                status_code=404,
                detail="Master document index not found"
            )

        # Read index
        with open(master_index_path, "r", encoding="utf-8") as f:
            index_data = json.load(f)

        documents = index_data.get("documents", [])

        # Find document by hash (document_id is the hash)
        document = next(
            (doc for doc in documents if doc.get("hash") == document_id),
            None
        )

        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document with hash {document_id} not found"
            )

        # Check if summary already exists (cached)
        if "summary" in document and document.get("summary"):
            logger.info(f"Returning cached summary for {document_id}")
            return {
                "document_id": document_id,
                "summary": document["summary"],
                "summary_generated_at": document.get("summary_generated_at", "unknown"),
                "summary_model": document.get("summary_model", "unknown"),
                "word_count": document.get("summary_word_count", len(document["summary"].split())),
                "from_cache": True,
                "text_source": document.get("summary_text_source", "unknown"),
                "document_metadata": {
                    "canonical_path": document.get("canonical_path", ""),
                    "size": document.get("size", 0),
                    "source_count": document.get("source_count", 0)
                }
            }

        # Summary not cached - need to generate
        canonical_path = document.get("canonical_path")
        if not canonical_path:
            raise HTTPException(
                status_code=500,
                detail="Document missing canonical_path"
            )

        pdf_path = PROJECT_ROOT / canonical_path
        if not pdf_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"PDF file not found at {canonical_path}"
            )

        # Extract text from PDF - try direct extraction first, fall back to OCR
        extracted_text = ""
        text_source = "pdf_extraction"

        try:
            from pypdf import PdfReader

            logger.info(f"Extracting text from {pdf_path}")
            reader = PdfReader(str(pdf_path))

            # Extract text from all pages (limit to first 50 pages for performance)
            max_pages = min(len(reader.pages), 50)

            for page_num in range(max_pages):
                try:
                    page_text = reader.pages[page_num].extract_text()
                    extracted_text += page_text + "\n"
                except Exception as e:
                    logger.warning(f"Failed to extract page {page_num}: {e}")
                    continue

            if extracted_text.strip():
                logger.info(f"Extracted {len(extracted_text)} characters from PDF")
            else:
                raise ValueError("No text could be extracted from PDF")

        except Exception as pdf_error:
            logger.warning(f"PDF extraction failed: {pdf_error}. Trying OCR text fallback...")

            # Try to find OCR text file (for house_oversight_nov2025 documents)
            filename = canonical_path.split("/")[-1]
            base_name = filename.rsplit(".", 1)[0] if "." in filename else filename

            # Check common OCR locations
            ocr_paths = [
                PROJECT_ROOT / "data" / "sources" / "house_oversight_nov2025" / "ocr_text" / f"{base_name}.txt",
                pdf_path.parent / "ocr_text" / f"{base_name}.txt",
            ]

            ocr_found = False
            for ocr_path in ocr_paths:
                if ocr_path.exists():
                    try:
                        with open(ocr_path, "r", encoding="utf-8") as f:
                            extracted_text = f.read()
                        if extracted_text.strip():
                            logger.info(f"Using OCR text from {ocr_path} ({len(extracted_text)} chars)")
                            text_source = "ocr"
                            ocr_found = True
                            break
                    except Exception as ocr_error:
                        logger.warning(f"Failed to read OCR file {ocr_path}: {ocr_error}")

            if not ocr_found:
                logger.error(f"No extractable text found for {document_id}")
                raise HTTPException(
                    status_code=422,
                    detail="This document appears to be a scanned PDF with no OCR text available. Cannot generate summary."
                )

        # Truncate to reasonable length for summarization (8000 chars)
        content_for_summary = extracted_text[:8000]

        # Generate summary using Grok API
        try:
            client = get_openrouter_client()

            # Use configured model or default to gpt-4o-mini for summaries
            model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

            logger.info(f"Generating summary with {model}")

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a document analyzer specializing in legal and investigative documents. Generate clear, factual summaries that help readers understand the document's content quickly."
                    },
                    {
                        "role": "user",
                        "content": f"""Summarize this document in 200-300 words. Include:
1. Document type (court filing, deposition, letter, etc.)
2. Main topics and subject matter
3. Key entities/people mentioned
4. Date range or time period (if mentioned)
5. Key findings or important details

Document text:
{content_for_summary}"""
                    }
                ],
                max_tokens=500,
                temperature=0.3,  # Low temperature for consistency
            )

            summary_text = response.choices[0].message.content.strip()
            word_count = len(summary_text.split())
            generated_at = datetime.now().isoformat()

            logger.info(f"Generated summary: {word_count} words")

            # Cache summary in document metadata
            document["summary"] = summary_text
            document["summary_generated_at"] = generated_at
            document["summary_model"] = model
            document["summary_word_count"] = word_count
            document["summary_text_source"] = text_source

            # Write back to master_document_index.json
            try:
                with open(master_index_path, "w", encoding="utf-8") as f:
                    json.dump(index_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Cached summary for {document_id} in master_document_index.json")
            except Exception as e:
                logger.error(f"Failed to cache summary: {e}")
                # Don't fail the request - still return the summary

            return {
                "document_id": document_id,
                "summary": summary_text,
                "summary_generated_at": generated_at,
                "summary_model": model,
                "word_count": word_count,
                "from_cache": False,
                "text_source": text_source,  # "pdf_extraction" or "ocr"
                "document_metadata": {
                    "canonical_path": canonical_path,
                    "size": document.get("size", 0),
                    "source_count": document.get("source_count", 0)
                }
            }

        except Exception as e:
            logger.error(f"Grok API failed for {document_id}: {e}")
            raise HTTPException(
                status_code=503,
                detail=f"AI summary generation failed: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating AI summary for {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{doc_id}/similar")
async def get_similar_documents(
    doc_id: str,
    limit: int = Query(5, ge=1, le=20),
    similarity_threshold: float = Query(0.7, ge=0.3, le=1.0),
    username: str = Depends(get_current_user)
):
    """
    Find semantically similar documents using vector embeddings.

    Design Decision: RAG-based document similarity search
    Rationale:
    - Uses sentence-transformers for semantic similarity (not just keyword matching)
    - Helps users discover related documents across the archive
    - Enhances document exploration and research workflows

    Algorithm:
    1. Load source document text (OCR or markdown)
    2. Generate embedding using all-MiniLM-L6-v2 model
    3. Compare against all other documents using cosine similarity
    4. Return top N most similar documents above threshold

    Performance:
    - First request: ~500ms (model loading + embedding generation)
    - Cached requests: ~200ms (embeddings cached in memory)
    - Embedding cache: LRU with 1000 document limit

    Args:
        doc_id: Source document ID to find similar documents for
        limit: Maximum number of similar documents to return (1-20, default 5)
        similarity_threshold: Minimum similarity score 0.0-1.0 (default 0.7)
        username: Authenticated user (from dependency)

    Returns:
        {
            "document_id": str,              # Source document ID
            "source_title": str,             # Source document filename
            "similar_documents": [
                {
                    "document_id": str,      # Similar document ID
                    "title": str,            # Document filename
                    "similarity_score": float, # Cosine similarity (0.0-1.0)
                    "preview": str,          # First 200 chars of content
                    "entities": [str],       # Entities mentioned in document
                    "doc_type": str,         # Document type (pdf, md, etc)
                    "file_size": int,        # File size in bytes
                    "date": str,             # Date extracted
                    "classification": str    # Document classification
                }
            ],
            "total_found": int,              # Number of results
            "search_time_ms": float          # Processing time
        }

    Error Conditions:
    - 404: Source document not found
    - 400: Invalid parameters (limit, threshold out of range)
    - 500: Model loading or similarity calculation failed
    - Empty results: No similar documents above threshold

    Usage Notes:
    - Results are NOT cached (documents may change)
    - Embeddings ARE cached (LRU, max 1000 documents)
    - Higher threshold = fewer but more relevant results
    - Lower threshold = more results but less relevant
    """
    import time
    start_time = time.time()

    try:
        # Load document index
        doc_index_path = METADATA_DIR / "all_documents_index.json"
        if not doc_index_path.exists():
            raise HTTPException(status_code=404, detail="Document index not found")

        with open(doc_index_path) as f:
            doc_data = json.load(f)

        documents = doc_data.get("documents", [])

        # Find source document
        source_doc = next((doc for doc in documents if doc.get("id") == doc_id), None)
        if not source_doc:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        # Get similarity service
        similarity_service = get_similarity_service()

        # Find similar documents
        similar_docs = similarity_service.find_similar_documents(
            doc_id=doc_id,
            all_documents=documents,
            limit=limit,
            similarity_threshold=similarity_threshold
        )

        # Calculate search time
        search_time_ms = round((time.time() - start_time) * 1000, 2)

        return {
            "document_id": doc_id,
            "source_title": source_doc.get("filename", "Unknown"),
            "similar_documents": similar_docs,
            "total_found": len(similar_docs),
            "search_time_ms": search_time_ms,
            "parameters": {
                "limit": limit,
                "similarity_threshold": similarity_threshold
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar documents for {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Similarity search failed: {str(e)}")


@app.options("/api/documents/{doc_id}/download")
async def options_download_document(doc_id: str):
    """Handle CORS preflight for PDF downloads.

    Design Decision: Explicit OPTIONS handler for CORS preflight
    Rationale: Browser sends OPTIONS request before GET when Authorization header present.
    Without this handler, backend returns 405 Method Not Allowed, breaking PDF.js loading.

    CORS Headers:
    - Allow-Origin: * (permissive, matches existing CORS middleware)
    - Allow-Methods: GET, OPTIONS (only methods needed for this endpoint)
    - Allow-Headers: Authorization, Content-Type (required for authenticated requests)
    - Max-Age: 86400 (cache preflight for 24h to reduce OPTIONS requests)

    Error Case: No authentication required for OPTIONS (preflight before auth)
    """
    return JSONResponse(
        content={"ok": True},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400",
        }
    )


@app.head("/api/documents/{doc_id}/download")
async def head_download_document(doc_id: str, username: str = Depends(get_current_user)):
    """Handle HEAD requests for download endpoint (check file size/existence).

    Design Decision: Add HEAD handler for browser download compatibility
    Rationale: Browsers may make HEAD request before GET to check:
    - File existence (404 vs 200)
    - Content-Length (for download progress indication)
    - Content-Type (verify file type)

    Returns same status codes as GET endpoint for consistency.
    """
    try:
        doc_index_path = METADATA_DIR / "all_documents_index.json"
        if not doc_index_path.exists():
            raise HTTPException(status_code=404, detail="Document index not found")

        with open(doc_index_path) as f:
            doc_data = json.load(f)

        documents = doc_data.get("documents", [])
        document = next((doc for doc in documents if doc.get("id") == doc_id), None)

        if not document:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        doc_path = document.get("path", "")
        if not doc_path:
            raise HTTPException(status_code=404, detail="Document path not found in metadata")

        file_path = PROJECT_ROOT / doc_path

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Document file not found on disk: {doc_path}"
            )

        filename = document.get("filename", file_path.name)
        media_type = "application/pdf" if file_path.suffix == ".pdf" else "application/octet-stream"
        file_size = file_path.stat().st_size

        return Response(
            status_code=200,
            headers={
                "Content-Type": media_type,
                "Content-Length": str(file_size),
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Accept-Ranges": "bytes",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Expose-Headers": "Content-Disposition, Content-Type, Content-Length"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in HEAD request for document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{doc_id}/download")
async def download_document(doc_id: str, username: str = Depends(get_current_user)):
    """Download document file (PDF, etc.) by ID.

    Returns:
        FileResponse with the actual document file

    Error Handling:
    1. DocumentNotFoundError: Returns 404 with "Document not found" message
    2. FileNotFoundError: Returns 404 with "Document file not found on disk"
    3. PermissionError: Returns 403 with permission error details
    4. IOError: Returns 500 with file read error details

    Design Decision: Direct file serving vs. streaming
    Rationale: Using FileResponse for efficient binary file serving.
    FastAPI handles streaming automatically for large files.

    Performance:
    - FileResponse uses streaming by default (no memory issues for 370MB files)
    - Browser handles download progress and cancellation
    - No server-side buffering needed

    Trade-offs:
    - Simplicity: Direct file serving vs. chunked streaming API
    - Performance: Relies on uvicorn's file serving (sufficient for our use case)
    - Memory: Minimal server memory usage (streaming, not loading into RAM)
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

        # Get file path
        doc_path = document.get("path", "")
        if not doc_path:
            raise HTTPException(status_code=404, detail="Document path not found in metadata")

        # Resolve to absolute path
        file_path = PROJECT_ROOT / doc_path

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Document file not found on disk: {doc_path}"
            )

        # Get filename and media type
        filename = document.get("filename", file_path.name)
        media_type = "application/pdf" if file_path.suffix == ".pdf" else "application/octet-stream"

        # Return file for download with explicit CORS headers
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Expose-Headers": "Content-Disposition, Content-Type, Content-Length"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.options("/api/documents/{doc_id}/view")
async def options_view_document(doc_id: str):
    """Handle CORS preflight for PDF viewing.

    Design Decision: Explicit OPTIONS handler for CORS preflight
    Rationale: Browser sends OPTIONS request before GET when Authorization header present.
    Without this handler, PDF.js fails to load documents in DocumentViewer component.

    CORS Headers:
    - Allow-Origin: * (permissive, matches existing CORS middleware)
    - Allow-Methods: GET, HEAD, OPTIONS (PDF.js needs HEAD for Content-Length check)
    - Allow-Headers: Authorization, Content-Type (required for authenticated requests)
    - Max-Age: 86400 (cache preflight for 24h to reduce OPTIONS requests)

    Error Case: No authentication required for OPTIONS (preflight before auth)

    Fix for 1M-112: Added HEAD to allowed methods to prevent 405 error
    """
    return JSONResponse(
        content={"ok": True},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400",
        }
    )


@app.head("/api/documents/{doc_id}/view")
async def head_view_document(doc_id: str, username: str = Depends(get_current_user)):
    """Handle HEAD requests for PDF viewer (check file size/existence).

    Design Decision: Add HEAD handler for PDF.js compatibility
    Rationale: PDF.js/react-pdf makes HEAD request before GET to check:
    - File existence (404 vs 200)
    - Content-Length (for progress bars)
    - Content-Type (verify it's actually a PDF)

    Without HEAD handler, FastAPI returns 405 Method Not Allowed, causing
    "Failed to load PDF document" error in DocumentViewer component.

    Error Handling: Returns same status codes as GET endpoint:
    - 404: Document not found in index or file missing on disk
    - 500: Server error reading document metadata
    """
    try:
        doc_index_path = METADATA_DIR / "all_documents_index.json"
        if not doc_index_path.exists():
            raise HTTPException(status_code=404, detail="Document index not found")

        with open(doc_index_path) as f:
            doc_data = json.load(f)

        documents = doc_data.get("documents", [])
        document = next((doc for doc in documents if doc.get("id") == doc_id), None)

        if not document:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        doc_path = document.get("path", "")
        if not doc_path:
            raise HTTPException(status_code=404, detail="Document path not found in metadata")

        file_path = PROJECT_ROOT / doc_path

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Document file not found on disk: {doc_path}"
            )

        filename = document.get("filename", file_path.name)
        media_type = "application/pdf" if file_path.suffix == ".pdf" else "application/octet-stream"
        file_size = file_path.stat().st_size

        # Return headers without body (HEAD response)
        return Response(
            status_code=200,
            headers={
                "Content-Type": media_type,
                "Content-Length": str(file_size),
                "Content-Disposition": f'inline; filename="{filename}"',
                "Accept-Ranges": "bytes",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Expose-Headers": "Content-Disposition, Content-Type, Content-Length"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in HEAD request for document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{doc_id}/view")
async def view_document(doc_id: str, username: str = Depends(get_current_user)):
    """Serve document file for inline viewing (PDF in browser).

    Similar to download endpoint but sets Content-Disposition to 'inline'
    so browsers display the PDF instead of downloading it.

    Returns:
        FileResponse with inline display headers

    Design Decision: Separate view vs download endpoints
    Rationale: Explicit control over browser behavior:
    - /download: Forces file download
    - /view: Displays in browser (PDF.js will fetch from here)

    This allows frontend flexibility:
    - DocumentViewer can use /view for inline PDF.js display
    - Download button can use /download for saving file
    """
    try:
        # Load document index (same as download endpoint)
        doc_index_path = METADATA_DIR / "all_documents_index.json"
        if not doc_index_path.exists():
            raise HTTPException(status_code=404, detail="Document index not found")

        with open(doc_index_path) as f:
            doc_data = json.load(f)

        documents = doc_data.get("documents", [])
        document = next((doc for doc in documents if doc.get("id") == doc_id), None)

        if not document:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")

        doc_path = document.get("path", "")
        if not doc_path:
            raise HTTPException(status_code=404, detail="Document path not found in metadata")

        file_path = PROJECT_ROOT / doc_path

        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Document file not found on disk: {doc_path}"
            )

        filename = document.get("filename", file_path.name)
        media_type = "application/pdf" if file_path.suffix == ".pdf" else "application/octet-stream"

        # Return file for inline viewing with explicit CORS headers
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Expose-Headers": "Content-Disposition, Content-Type, Content-Length"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/git/recent-commits")
async def get_recent_commits(
    limit: int = Query(default=10, ge=1, le=50), username: str = Depends(get_current_user)
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
            ["git", "log", f"-n {limit}", "--pretty=format:%H|%an|%ae|%ad|%s", "--date=relative"],
            check=False,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=5,
        )

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Git command failed: {result.stderr}")

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

            commits.append(
                {
                    "hash": commit_hash[:7],
                    "author": author,
                    "email": email,
                    "date": date,
                    "type": parsed["type"],
                    "scope": parsed["scope"],
                    "breaking": parsed["breaking"],
                    "message": parsed["message"],
                    "full_message": message,
                    "is_semantic": parsed["is_semantic"],
                }
            )

        return {"commits": commits, "total": len(commits)}

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Git command timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching commits: {e!s}")


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
                "data": json.dumps(
                    {
                        "message": "Hot-reload connected",
                        "timestamp": time.time(),
                        "enabled": ENABLE_HOT_RELOAD,
                    }
                ),
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
                    yield {"event": event_data["event"], "data": json.dumps(event_data["data"])}

                except asyncio.TimeoutError:
                    # Send keepalive ping
                    yield {"event": "ping", "data": json.dumps({"timestamp": time.time()})}

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

# Import Flights routes
try:
    from routes.flights import router as flights_router

    flights_available = True
except ImportError:
    logger.warning("Flights routes not available")
    flights_available = False

# Import Enhanced Chat routes
try:
    from routes.chat_enhanced import router as chat_enhanced_router

    chat_enhanced_available = True
except ImportError:
    logger.warning("Enhanced Chat routes not available")
    chat_enhanced_available = False

# Import News routes
try:
    from routes.news import router as news_router

    news_available = True
except ImportError:
    logger.warning("News routes not available")
    news_available = False

# Import Stats routes
try:
    from routes.stats import router as stats_router

    stats_available = True
except ImportError:
    logger.warning("Stats routes not available")
    stats_available = False

# Import Search routes
try:
    from routes.search import router as search_router

    search_available = True
except ImportError:
    logger.warning("Search routes not available")
    search_available = False


# Initialize services on startup
@app.on_event("startup")
async def init_api_services():
    """Initialize API v2 services"""
    api_routes.init_services(DATA_DIR)
    logger.info("API v2 services initialized")

    if rag_available:
        logger.info("RAG system available at /api/rag")

    if chat_enhanced_available:
        logger.info("Enhanced Chat system available at /api/chat/enhanced")


# Register API v2 routes
app.include_router(api_routes.router)
logger.info("API v2 routes registered at /api/v2")

# Register RAG routes
if rag_available:
    app.include_router(rag_router)
    logger.info("RAG routes registered at /api/rag")

# Register Flights routes
if flights_available:
    app.include_router(flights_router)
    logger.info("Flights routes registered at /api/flights")

# Register Enhanced Chat routes
if chat_enhanced_available:
    app.include_router(chat_enhanced_router)
    logger.info("Enhanced Chat routes registered at /api/chat")

# Register News routes
if news_available:
    app.include_router(news_router)
    logger.info("News routes registered at /api/news")

# Register Stats routes
if stats_available:
    app.include_router(stats_router)
    logger.info("Stats routes registered at /api/v2/stats")

# Register Search routes
if search_available:
    app.include_router(search_router)
    logger.info("Advanced Search routes registered at /api/search")


# Mount React frontend build at root
# Serves from frontend/dist/ directory (Vite build output)
# Use absolute path to avoid issues with uvicorn reload
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
logger.info(f"Mounting React frontend from: {FRONTEND_DIST}")
logger.info(f"Frontend dist exists: {FRONTEND_DIST.exists()}")
logger.info(f"Frontend index.html exists: {(FRONTEND_DIST / 'index.html').exists()}")
if not FRONTEND_DIST.exists():
    logger.error("Frontend dist directory not found! Falling back to old web directory.")
    FRONTEND_DIST = Path(__file__).resolve().parent / "web"

# Mount static files FIRST (assets, favicons, etc.)
app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


# Serve common static files at root level
@app.get("/favicon.ico")
async def favicon():
    return FileResponse(FRONTEND_DIST / "favicon.ico")


@app.get("/{filename}.{extension}")
async def serve_static_files(filename: str, extension: str):
    """Serve static files at root level (favicon-*.png, manifest, etc.)"""
    static_extensions = ["png", "svg", "ico", "webmanifest", "json", "txt"]
    if extension in static_extensions:
        file_path = FRONTEND_DIST / f"{filename}.{extension}"
        if file_path.exists():
            return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Not Found")


# Catch-all for React Router (SPA routing) - handles /news, /entities, etc.
# IMPORTANT: This is a GET-only route and will NOT match POST requests!
# The issue is that FastAPI route matching happens BEFORE handler execution,
# so we can't conditionally skip routes in the handler.
#
# The proper solution: Don't use a catch-all for paths that might conflict with API routes.
# Instead, explicitly list frontend routes or use a more specific pattern.
#
# For now, we keep the catch-all but this may interfere with dynamically added API routes.
# TODO: Replace with explicit frontend route list or use middleware for SPA routing

# Explicit frontend routes (safer than catch-all)
frontend_routes = [
    "/", "/home", "/entities", "/documents", "/flights", "/network",
    "/timeline", "/chat", "/news", "/activity", "/matrix", "/analytics",
    "/advanced-search", "/entities/{entity_id:path}"
]

for route_path in frontend_routes:
    # Create a closure to capture the route_path value
    def make_handler():
        async def handler(request: Request):
            index_path = FRONTEND_DIST / "index.html"
            if not index_path.exists():
                raise HTTPException(status_code=500, detail="Frontend build not found")
            return FileResponse(index_path)
        return handler

    # Register each frontend route explicitly
    app.add_route(route_path, make_handler(), methods=["GET"], include_in_schema=False)


# Old web directory (vanilla JS) and Svelte build have been replaced by React frontend
# NOTE: Ensure React build exists: cd frontend && npm run build


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

    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True, log_level="info")


if __name__ == "__main__":
    main()
