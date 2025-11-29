# PDF Viewer Fix - Session Summary
**Date**: November 26, 2025, 18:05 EST
**Status**: Planning Complete, Implementation Ready

## Problem Identified
PDF documents fail to load in browser viewer with error:
> "Failed to load PDF document. The file may be corrupted or too large."

**Root Cause**: Large PDFs (>5MB) timeout or fail to render in browser PDF.js viewer

## Solution Approach

### Original Plan (Revised)
- ❌ **Batch generate summaries for all 38,177 documents** (too resource-intensive)
- ✅ **On-demand summary generation** (generate when user visits document page)
- ✅ **Cache summaries once generated** (store in master_document_index.json)

### Revised Implementation Strategy

#### 1. On-Demand Summary Generation
- Generate summaries **only when document page is visited**
- Use Grok API (x-ai/grok-4.1-fast:free) - no cost until Dec 3, 2025
- Cache result in master_document_index.json for future requests
- Fallback to PDF viewer if summary generation fails

#### 2. User Flow
```
User visits /documents/{id}
    ↓
Backend checks if summary exists
    ├─ Summary exists → Return cached summary immediately
    ↓
    └─ Summary doesn't exist → Generate via Grok API
        ↓
        Store in master_document_index.json
        ↓
        Return summary to frontend
```

#### 3. Frontend Display
```
Document Detail Page:
├─ AI-Generated Summary (loads first)
│  ├─ Document type/category
│  ├─ Main topics
│  ├─ Key entities mentioned
│  ├─ Date range/relevance
│  └─ Page count & file size
│
├─ Download Button (always available)
│
└─ View in Browser (optional, for small PDFs <5MB)
```

## Technical Findings

### Document Structure
- **Total documents**: 38,177
- **Documents with summaries**: 0 (0% coverage)
- **Document metadata** (current structure):
  ```json
  {
    "hash": "...",
    "canonical_path": "data/sources/documentcloud/epstein_docs_6250471.pdf",
    "size": 387743485,
    "sources": [...],
    "source_count": 2,
    "duplicate_count": 1
  }
  ```

### Required Changes

#### Backend: server/app.py
**New endpoint**:
```python
@app.get("/api/documents/{document_id}/summary")
async def get_document_summary(document_id: str):
    # 1. Look up document in master_document_index
    # 2. Check if summary already exists
    # 3. If yes: return cached summary
    # 4. If no: extract PDF text, generate with Grok, cache, return
```

#### Frontend: frontend/src/pages/DocumentDetail.tsx
**Component updates**:
- Add DocumentSummary component (loads on page load)
- Show summary first, download button second
- Make PDF viewer conditional (<5MB files only)

#### Data: data/metadata/master_document_index.json
**Add summary fields**:
```json
{
  "hash": "...",
  "canonical_path": "...",
  "summary": "AI-generated summary...",
  "summary_generated_at": "2025-11-26T18:00:00Z",
  "summary_model": "x-ai/grok-4.1-fast:free",
  "summary_word_count": 250
}
```

## Implementation Tasks

### Phase 1: Backend (Priority)
- [ ] Add `/api/documents/{id}/summary` endpoint
- [ ] Implement PDF text extraction (PyPDF2 or similar)
- [ ] Integrate Grok API for summary generation
- [ ] Add caching logic to master_document_index.json

### Phase 2: Frontend (Priority)
- [ ] Create DocumentSummary component
- [ ] Update DocumentDetail page layout
- [ ] Add download button component
- [ ] Make PDF viewer conditional

### Phase 3: Testing
- [ ] Test with large PDF (>5MB)
- [ ] Test with small PDF (<1MB)
- [ ] Verify caching works
- [ ] Test download functionality

## Estimated Effort
- Backend implementation: 2-3 hours
- Frontend implementation: 1-2 hours
- Testing & refinement: 30-60 minutes
- **Total**: 4-6 hours

## Benefits of On-Demand Approach
✅ **No upfront cost** - only generate summaries for viewed documents
✅ **Faster deployment** - no 38K batch generation required
✅ **Better UX** - instant download option while summary generates
✅ **Resource efficient** - only process documents users actually access
✅ **Gradual coverage** - summaries build up organically over time

## Current Status
- ✅ Problem analyzed
- ✅ Solution approach designed
- ✅ Technical investigation complete
- ✅ Ticket documented (1M-266)
- ⏳ Implementation pending

## Related Files
- `docs/linear-tickets/1M-266-PDF-VIEWER-SUMMARY-FIX.md` - Detailed ticket
- `data/metadata/master_document_index.json` - Data storage
- `server/app.py` - Backend endpoint location
- `frontend/src/pages/DocumentDetail.tsx` - Frontend component

## Next Steps
1. Implement backend `/api/documents/{id}/summary` endpoint
2. Create DocumentSummary React component
3. Update DocumentDetail page layout
4. Test with real PDFs
5. Deploy and verify fix

---

**Session paused at 18:05 EST** - ready for implementation when resumed
