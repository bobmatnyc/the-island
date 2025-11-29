# Quick Start - Source Suggestion System

**Quick Summary**: Historical documentation archived for reference purposes.

**Category**: Archive
**Status**: Historical
**Last Updated**: 2025-11-24

**Key Points**:
- **Main Site**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/static/admin.html
- **API Docs**: http://localhost:8000/docs
- **Credentials**: See `.credentials` file in server directory
- Main site will have "Suggest Source" form

---

## 🚀 Start the Server

```bash
cd /Users/masa/Projects/Epstein
source .venv/bin/activate
python3 -m server.app 8000
```

## 🌐 Access Points

- **Main Site**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/static/admin.html
- **API Docs**: http://localhost:8000/docs
- **Credentials**: See `.credentials` file in server directory

## 📝 Submit a Suggestion (User)

**Via API**:
```bash
curl -X POST http://localhost:8000/api/suggestions \
  -u epstein:archive2025 \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://archive.org/details/epstein-files",
    "description": "Archive.org collection with court documents",
    "source_name": "Archive.org Epstein Files",
    "priority": "high",
    "tags": ["archive-org", "court-docs"]
  }'
```

**Via Web** (Future):
- Main site will have "Suggest Source" form
- Users fill in URL, description, and optional metadata
- Submission tracked with unique ID

## 👨‍💼 Review Suggestions (Admin)

1. Open http://localhost:8000/static/admin.html
2. View dashboard statistics
3. Filter by status: "Pending"
4. Click "View" to see details
5. Click "Approve" or "Reject"
6. Add review notes (optional)

## 📊 Check Statistics

```bash
curl -X GET http://localhost:8000/api/suggestions/stats/summary \
  -u epstein:archive2025
```

**Response**:
```json
{
  "total": 42,
  "pending": 5,
  "approved": 30,
  "rejected": 7,
  "processing": 0,
  "completed": 0,
  "failed": 0,
  "by_priority": {
    "low": 10,
    "medium": 20,
    "high": 10,
    "critical": 2
  },
  "recent_submissions": 8
}
```

## 🔄 Workflow Example

```
1. User submits URL
   → POST /api/suggestions
   → Status: PENDING

2. Admin reviews
   → GET /api/suggestions?status=pending
   → Views in admin panel

3. Admin approves
   → PATCH /api/suggestions/{id}/status
   → Status: APPROVED
   → Priority: HIGH

4. (Future) System processes
   → Status: PROCESSING
   → Downloads and ingests documents

5. (Future) Completion
   → Status: COMPLETED
   → documents_ingested: 500
```

## 🧪 Test the System

```bash
cd /Users/masa/Projects/Epstein
source .venv/bin/activate
python3 test_suggestions.py
```

## 🛠️ Common Tasks

### List All Pending Suggestions
```bash
curl -X GET "http://localhost:8000/api/suggestions?status=pending&limit=100" \
  -u epstein:archive2025
```

### Approve a Suggestion
```bash
curl -X PATCH http://localhost:8000/api/suggestions/{ID}/status \
  -u epstein:archive2025 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved",
    "priority": "critical",
    "review_notes": "High priority - start processing immediately"
  }'
```

### Reject a Suggestion
```bash
curl -X PATCH http://localhost:8000/api/suggestions/{ID}/status \
  -u epstein:archive2025 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "rejected",
    "review_notes": "Duplicate source already in archive"
  }'
```

### Delete a Suggestion
```bash
curl -X DELETE http://localhost:8000/api/suggestions/{ID} \
  -u epstein:archive2025
```

## 📂 Data Location

**Storage**: `/Users/masa/Projects/Epstein/data/suggestions/suggested_sources.json`
**Backup**: `/Users/masa/Projects/Epstein/data/suggestions/suggested_sources.json.bak`

## 🔐 Security

**URL Validation**:
- ✅ Only HTTP/HTTPS allowed
- ❌ Blocks localhost (127.0.0.1)
- ❌ Blocks private IPs (192.168.x.x, 10.x.x.x)
- ❌ Blocks file:// protocol

**Authentication**:
- All endpoints require HTTP Basic Auth
- Credentials in `/server/.credentials`
- Format: `username:password` (one per line)

## 🎨 Admin Interface Features

**Dashboard**:
- Total suggestions count
- Pending, approved, rejected counts
- Processing and completed counts
- Recent submissions (7 days)

**Filters**:
- Status: All / Pending / Approved / Rejected / Processing / Completed / Failed
- Priority: All / Low / Medium / High / Critical

**Actions**:
- View: See full details
- Approve: One-click approval
- Reject: One-click rejection
- Delete: Remove suggestion

**Theme**:
- Light/Dark mode toggle
- Preference saved in browser
- Matches main site theme

## 📖 Full Documentation

- **Complete Guide**: `SUGGESTIONS_README.md`
- **Implementation**: `IMPLEMENTATION_SUMMARY.md`
- **API Reference**: http://localhost:8000/docs (when server running)

## 🐛 Troubleshooting

**Server won't start**:
```bash
# Install dependencies
pip install -r requirements.txt
```

**Import errors**:
```bash
# Ensure you're in venv
source .venv/bin/activate
```

**Can't access admin panel**:
- Check server is running: http://localhost:8000/
- Verify credentials in `/server/.credentials`
- Try clearing browser cache

## 💡 Tips

- Use "Pending" filter to see suggestions awaiting review
- Sort by submission date to review oldest first
- Add tags for better organization
- Use priority to indicate processing order
- Review notes help track decision rationale

---

**Quick Help**: See `SUGGESTIONS_README.md` for detailed documentation
