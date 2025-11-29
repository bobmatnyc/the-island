# Linear Ticket: 1M-266 - PDF Viewer Summary Enhancement

**Created**: 2025-11-26
**Priority**: Medium-High (User Experience)
**Type**: Enhancement + Bug Fix

## Problem
PDF documents fail to load in browser viewer with error:
> "Failed to load PDF document. The file may be corrupted or too large. Try using the RAG search to find specific information from this document."

**Root Cause**: Large PDFs (>5MB) timeout or fail to render in browser PDF.js viewer

## Proposed Solution
Replace immediate PDF viewer with 2-step approach:

### Step 1: Show AI-Generated Summary First
1. Generate document summaries using Grok (x-ai/grok-4.1-fast:free)
2. Display summary on document detail page
3. Include key information:
   - Document type/category
   - Main topics covered
   - Key entities mentioned
   - Date range/relevance
   - Page count and file size

### Step 2: Offer Download Option
- "Download Full PDF" button below summary
- Direct download link (no browser rendering)
- Preserves original PDF functionality

## Technical Implementation

### Backend Changes
**File**: `server/app.py`

1. **New endpoint**: `/api/documents/{doc_id}/summary`
   ```python
   @app.get("/api/documents/{document_id}/summary")
   async def get_document_summary(document_id: str):
       # Check if summary exists in metadata
       # If not, generate using Grok
       # Return summary text
   ```

2. **Summary generation** (using existing Grok integration):
   ```python
   def generate_document_summary(doc_id: str, content: str) -> dict:
       # Use x-ai/grok-4.1-fast:free model
       # Prompt: "Summarize this document in 200-300 words..."
       # Cache result in master_document_index.json
   ```

### Frontend Changes
**File**: `frontend/src/pages/DocumentDetail.tsx`

**Current Flow**:
```
Document Detail Page → Direct PDF Viewer → Error/Timeout
```

**New Flow**:
```
Document Detail Page → 
  ├─ AI Summary (load instantly)
  ├─ Download PDF Button
  └─ "View in Browser" (optional, if small PDF)
```

**Component Structure**:
```tsx
<DocumentSummary 
  documentId={id}
  onSummaryLoad={(summary) => setDocumentSummary(summary)}
/>

<DownloadButton 
  documentId={id}
  filename={document.filename}
/>

{fileSize < 5MB && (
  <ViewInBrowserButton onClick={() => setShowPDF(true)} />
)}
```

### Data Storage
**File**: `data/metadata/master_document_index.json`

Add `summary` field to each document:
```json
{
  "documents": {
    "doc-12345": {
      "id": "doc-12345",
      "title": "...",
      "summary": "AI-generated summary text...",
      "summary_generated_at": "2025-11-26T17:00:00Z",
      "summary_model": "x-ai/grok-4.1-fast:free",
      ...
    }
  }
}
```

## Batch Summary Generation Script
**File**: `scripts/add_doc_summaries.py` (already exists!)

Use existing script with Grok integration:
```bash
python3 scripts/add_doc_summaries.py \
  --limit 100 \
  --model grok-4.1-fast \
  --output data/metadata/master_document_index.json
```

## Implementation Plan

### Phase 1: Summary Generation (Backend)
1. ✅ Script exists: `scripts/add_doc_summaries.py`
2. Add `/api/documents/{id}/summary` endpoint
3. Generate summaries for all documents (batch process)
4. Cache in master_document_index.json

### Phase 2: Frontend Integration
1. Create `DocumentSummary` component
2. Update `DocumentDetail` page to show summary first
3. Add download button
4. Make PDF viewer optional (for small files only)

### Phase 3: Testing
1. Test with large PDFs (>5MB)
2. Test with small PDFs (<1MB)
3. Verify summary quality
4. Check download functionality

## Estimated Effort
- Backend: 1-2 hours (endpoint + batch generation)
- Frontend: 1-2 hours (component + integration)
- Testing: 30 minutes
- **Total**: 3-4 hours

## Benefits
- ✅ Instant document preview (no loading delays)
- ✅ Better UX for large documents
- ✅ Reduces server load (no PDF rendering)
- ✅ Provides searchable summary text
- ✅ Uses free Grok API (no cost)

## Dependencies
- OpenRouter API (already configured)
- Grok model access (already available)
- Existing summary script (already exists)

## Success Criteria
- [ ] All documents have AI-generated summaries
- [ ] Summary loads in <2 seconds
- [ ] Download button works for all PDFs
- [ ] No more "Failed to load PDF" errors
- [ ] Users can still view small PDFs in browser (optional)

## Related Files
- `scripts/add_doc_summaries.py` - Summary generation
- `server/app.py` - Backend endpoint
- `frontend/src/pages/DocumentDetail.tsx` - Frontend page
- `data/metadata/master_document_index.json` - Data storage

---

**Status**: Ready for implementation
**Next Step**: Generate summaries for all documents using existing script
