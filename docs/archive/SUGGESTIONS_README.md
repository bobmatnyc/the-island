# Source Suggestion System - Documentation

**Created**: 2025-11-16
**Status**: Production Ready ✅

## Overview

A comprehensive source suggestion system for the Epstein Document Archive that allows users to submit document sources for review, with an admin interface for managing suggestions through a complete workflow.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
├─────────────────────────────────────────────────────────────┤
│  - Main Site: Source submission form                         │
│  - Admin Panel: /admin.html (review and management)          │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
├─────────────────────────────────────────────────────────────┤
│  POST   /api/suggestions          - Create suggestion        │
│  GET    /api/suggestions          - List with filters        │
│  GET    /api/suggestions/{id}     - Get single suggestion    │
│  PATCH  /api/suggestions/{id}/... - Update status            │
│  DELETE /api/suggestions/{id}     - Delete suggestion        │
│  GET    /api/suggestions/stats/.. - Get statistics           │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                   Service Layer (Business Logic)             │
├─────────────────────────────────────────────────────────────┤
│  SuggestionService:                                          │
│    - create_suggestion()     - Add new suggestion            │
│    - get_all_suggestions()   - List with filtering           │
│    - get_suggestion_by_id()  - Retrieve single               │
│    - update_status()         - Change workflow state         │
│    - delete_suggestion()     - Remove suggestion             │
│    - get_statistics()        - Dashboard stats               │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│                   Storage Layer (File-based)                 │
├─────────────────────────────────────────────────────────────┤
│  /data/suggestions/suggested_sources.json                    │
│    - File locking for concurrent access                      │
│    - Atomic writes (temp file + rename)                      │
│    - Automatic backup (.bak) on updates                      │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

```
/Users/masa/Projects/Epstein/
├── server/
│   ├── models/
│   │   ├── __init__.py
│   │   └── suggested_source.py          # Pydantic models
│   ├── services/
│   │   ├── __init__.py
│   │   └── suggestion_service.py        # Business logic
│   ├── web/
│   │   └── admin.html                   # Admin interface
│   └── app.py                           # FastAPI endpoints
├── data/
│   └── suggestions/
│       ├── suggested_sources.json       # Main storage
│       └── suggested_sources.json.bak   # Auto backup
└── test_suggestions.py                  # Test script
```

## Data Model

### SuggestedSource
Complete suggestion record with full metadata:

```python
{
    "id": "uuid-v4",                      # Auto-generated unique ID
    "url": "https://...",                 # HTTP/HTTPS validated URL
    "description": "...",                 # 10-2000 characters
    "source_name": "Optional Name",       # Optional display name
    "submitter_email": "user@example.com", # Optional email
    "status": "pending|approved|rejected|processing|completed|failed",
    "submitted_at": "2025-11-16T...",     # ISO 8601 timestamp
    "submitted_by": "username",           # From auth system
    "reviewed_at": "2025-11-16T...",      # When status changed
    "reviewed_by": "admin",               # Who reviewed
    "review_notes": "...",                # Admin comments
    "priority": "low|medium|high|critical",
    "document_count_estimate": 500,       # Estimated docs
    "tags": ["court-docs", "fbi"],        # Max 10 tags
    "processing_started_at": "...",       # When processing began
    "processing_completed_at": "...",     # When finished
    "documents_ingested": 450,            # Actual count ingested
    "error_message": "..."                # If failed
}
```

### Workflow States

```
PENDING
  ↓ (admin review)
APPROVED / REJECTED
  ↓ (if approved, start processing)
PROCESSING
  ↓
COMPLETED / FAILED
```

## API Endpoints

### 1. Create Suggestion

**Endpoint**: `POST /api/suggestions`
**Auth**: Required
**Rate Limit**: 10/hour per user

**Request Body**:
```json
{
    "url": "https://example.com/documents",
    "description": "Collection of court documents from 2019",
    "source_name": "Court Archive 2019",
    "submitter_email": "user@example.com",
    "priority": "medium",
    "document_count_estimate": 500,
    "tags": ["court-docs", "2019"]
}
```

**Security Validation**:
- Only HTTP/HTTPS URLs
- Blocks localhost, private IPs (192.168.x.x, 10.x.x.x, 127.0.0.1)
- Blocks file:// protocol
- URL length limit: 2048 characters

**Response**:
```json
{
    "status": "success",
    "message": "Thank you for your suggestion!...",
    "suggestion": { /* full suggestion object */ }
}
```

### 2. List Suggestions

**Endpoint**: `GET /api/suggestions`
**Auth**: Required

**Query Parameters**:
- `status`: Filter by status (pending, approved, rejected, etc.)
- `priority`: Filter by priority (low, medium, high, critical)
- `limit`: Max results (default: 100, max: 500)
- `offset`: Pagination offset (default: 0)

**Response**:
```json
{
    "total": 42,
    "offset": 0,
    "limit": 100,
    "suggestions": [ /* array of suggestions */ ]
}
```

### 3. Get Single Suggestion

**Endpoint**: `GET /api/suggestions/{id}`
**Auth**: Required

**Response**: Full suggestion object or 404 if not found

### 4. Update Status (Admin)

**Endpoint**: `PATCH /api/suggestions/{id}/status`
**Auth**: Required (admin)

**Request Body**:
```json
{
    "status": "approved",
    "priority": "high",
    "review_notes": "Verified as legitimate source"
}
```

**Response**:
```json
{
    "status": "success",
    "suggestion": { /* updated suggestion */ }
}
```

### 5. Delete Suggestion (Admin)

**Endpoint**: `DELETE /api/suggestions/{id}`
**Auth**: Required (admin)

**Response**:
```json
{
    "status": "success",
    "message": "Suggestion deleted successfully"
}
```

### 6. Get Statistics

**Endpoint**: `GET /api/suggestions/stats/summary`
**Auth**: Required

**Response**:
```json
{
    "total": 150,
    "pending": 12,
    "approved": 80,
    "rejected": 20,
    "processing": 5,
    "completed": 30,
    "failed": 3,
    "by_priority": {
        "low": 40,
        "medium": 70,
        "high": 30,
        "critical": 10
    },
    "recent_submissions": 8
}
```

## Admin Interface

### Access
- URL: `http://localhost:8000/static/admin.html`
- Requires authentication (same as main site)

### Features

**Dashboard Statistics**
- Total suggestions count
- Pending review count
- Approved, processing, completed counts
- Recent submissions (last 7 days)

**Filtering**
- By status: All / Pending / Approved / Rejected / Processing / Completed / Failed
- By priority: All / Low / Medium / High / Critical

**Table View**
- Sortable columns (click headers)
- Status badges (color-coded)
- Priority badges (color-coded)
- URL links (open in new tab)
- Submission date and submitter

**Actions**
- **View**: See full details in modal
- **Approve**: Quick approve button (pending suggestions only)
- **Reject**: Quick reject button (pending suggestions only)
- **Delete**: Remove suggestion (with confirmation)

**Review Modal**
- Change status (Approve / Reject / Mark as Processing)
- Adjust priority (Low / Medium / High / Critical)
- Add review notes (freeform text)

**Theme Support**
- Light/Dark theme toggle
- Matches main site theme system
- Preference saved in localStorage

## Usage Examples

### Submit Suggestion (API)

```bash
curl -X POST http://localhost:8000/api/suggestions \
  -u epstein:archive2025 \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://archive.org/details/epstein-files-2024",
    "description": "Archive.org collection with newly released documents",
    "source_name": "Archive.org 2024 Release",
    "priority": "high",
    "document_count_estimate": 1000,
    "tags": ["archive-org", "2024"]
  }'
```

### List Pending Suggestions (API)

```bash
curl -X GET "http://localhost:8000/api/suggestions?status=pending" \
  -u epstein:archive2025
```

### Approve Suggestion (API)

```bash
curl -X PATCH http://localhost:8000/api/suggestions/{id}/status \
  -u epstein:archive2025 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved",
    "priority": "critical",
    "review_notes": "High priority source, start processing ASAP"
  }'
```

### Python Service Usage

```python
from pathlib import Path
from services.suggestion_service import SuggestionService
from models.suggested_source import SuggestedSourceCreate, SourcePriority

# Initialize service
storage_path = Path("data/suggestions/suggested_sources.json")
service = SuggestionService(storage_path)

# Create suggestion
suggestion = SuggestedSourceCreate(
    url="https://example.com/docs",
    description="Important document collection",
    priority=SourcePriority.HIGH,
    tags=["legal"]
)

created = service.create_suggestion(suggestion, submitted_by="user123")
print(f"Created: {created.id}")

# Get all pending
pending, count = service.get_all_suggestions(status=SourceStatus.PENDING)
print(f"Found {count} pending suggestions")

# Get statistics
stats = service.get_statistics()
print(f"Total: {stats.total}, Pending: {stats.pending}")
```

## Performance Characteristics

### Time Complexity
- **Create**: O(n) read + O(1) append + O(n) write = **O(n)**
- **Read all**: O(n) where n = total suggestions
- **Get by ID**: O(n) linear scan
- **Update**: O(n) read + O(n) write = **O(n)**
- **Delete**: O(n) read + O(n) write = **O(n)**
- **Statistics**: O(n) single pass

### Space Complexity
- **Memory**: O(n) - full list loaded for operations
- **Disk**: ~500 bytes per suggestion average
- **Backup**: 2x storage (main + .bak file)

### Scalability Limits
- **Current design**: Handles ~10,000 suggestions
- **Bottleneck**: JSON parsing becomes slow beyond 10K
- **Migration path**: Move to SQLite when approaching 5,000 suggestions

### Concurrent Access
- **File locking**: fcntl.flock prevents corruption
- **Atomic writes**: Temp file + rename prevents partial writes
- **Auto backup**: .bak file created on every update
- **Write serialization**: Only one writer at a time (locked)

## Error Handling

### Creation Errors
- **Invalid URL**: 400 Bad Request (Pydantic validation)
- **Suspicious URL**: 400 Bad Request (localhost, private IPs)
- **Description too short**: 400 Bad Request (min 10 chars)
- **Too many tags**: 400 Bad Request (max 10)

### Update Errors
- **Suggestion not found**: 404 Not Found
- **Invalid status**: 422 Unprocessable Entity
- **File corruption**: Attempts .bak recovery, logs error

### Storage Errors
- **File not found**: Creates new file automatically
- **Permission denied**: Propagates IOError to caller
- **JSON corruption**: Attempts .bak recovery
- **Concurrent write**: Handled by file locking

## Testing

### Run Test Suite
```bash
cd /Users/masa/Projects/Epstein
source .venv/bin/activate
python3 test_suggestions.py
```

**Test Coverage**:
- ✅ Create suggestion
- ✅ Retrieve all suggestions
- ✅ Get suggestion by ID
- ✅ Update status with review
- ✅ Delete suggestion
- ✅ Get statistics
- ✅ File cleanup

### Manual Testing Checklist

**Frontend (Admin Panel)**:
- [ ] Dashboard loads and shows statistics
- [ ] Filter by status works
- [ ] Filter by priority works
- [ ] Sort by column works
- [ ] View details modal opens
- [ ] Approve button updates status
- [ ] Reject button updates status
- [ ] Delete button removes suggestion
- [ ] Review modal submits correctly
- [ ] Theme toggle works

**Backend (API)**:
- [ ] POST creates suggestion with validation
- [ ] GET lists suggestions with filters
- [ ] GET by ID returns correct suggestion
- [ ] PATCH updates status and metadata
- [ ] DELETE removes suggestion
- [ ] Statistics endpoint returns correct counts

## Security Considerations

### URL Validation
- ✅ Only HTTP/HTTPS protocols allowed
- ✅ Blocks localhost access attempts
- ✅ Blocks private IP ranges (RFC 1918)
- ✅ Blocks file:// protocol
- ✅ Maximum URL length enforced

### Authentication
- ✅ All endpoints require HTTP Basic Auth
- ✅ Credentials from .credentials file
- ✅ Dynamic credential reloading

### Input Validation
- ✅ Pydantic models validate all fields
- ✅ Description length limits (10-2000 chars)
- ✅ Tag count limit (max 10)
- ✅ Email pattern validation
- ✅ Enum validation for status/priority

### File Security
- ✅ File locking prevents race conditions
- ✅ Atomic writes prevent corruption
- ✅ Automatic backups prevent data loss
- ✅ Path traversal prevention (storage in data/suggestions/)

## Future Enhancements

### Short-term (Next Sprint)
1. **Email Notifications**: Notify admins of new submissions
2. **Bulk Actions**: Approve/reject multiple suggestions at once
3. **Export**: Download suggestions as CSV/JSON
4. **Search**: Full-text search across URLs and descriptions

### Medium-term
1. **SQLite Migration**: When > 5,000 suggestions
2. **Webhook Integration**: Trigger ingestion on approval
3. **Duplicate Detection**: Check if URL already submitted
4. **Source Validation**: Automatic URL reachability check

### Long-term
1. **Automated Processing**: Queue approved sources for ingestion
2. **Progress Tracking**: Real-time status updates during processing
3. **Analytics Dashboard**: Submission trends, approval rates
4. **API Rate Limiting**: Per-user submission throttling

## Troubleshooting

### Server won't start
```bash
# Check if dependencies installed
cd /Users/masa/Projects/Epstein
source .venv/bin/activate
pip install -r requirements.txt
```

### Import errors in service
- The service uses try/except for both relative and absolute imports
- Works in both module context (server) and test context

### File corruption
- Service automatically attempts .bak recovery
- Check `/data/suggestions/suggested_sources.json.bak`
- Manually restore if needed

### Concurrent write issues
- File locking should prevent this
- Check for orphaned lock files
- Restart server if needed

## Maintenance

### Regular Tasks
- **Weekly**: Review pending suggestions
- **Monthly**: Check .bak file sizes, archive old suggestions
- **Quarterly**: Evaluate need for SQLite migration

### Monitoring
- Watch suggestion count (alert at 5,000)
- Track approval/rejection rates
- Monitor file size growth

### Backup Strategy
- Automatic .bak file on every write
- Consider daily snapshots to external storage
- Backup includes complete audit trail

---

**Version**: 1.0.0
**Last Updated**: 2025-11-16
**Contact**: See main README for contribution guidelines
