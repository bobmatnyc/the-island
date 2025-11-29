# Document Viewer - Quick Start Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Full Content Display**: Complete extracted document text
- **Entity Highlighting**: Names highlighted in blue, clickable
- **Search**: Find text within document
- **Font Controls**: Adjust size, toggle monospace
- **Copy/Download**: Quick actions

---

## What Was Implemented

Enhanced the Documents page with a full content viewer that displays extracted document text, highlights entities, and provides search/navigation features.

## Quick Demo

### Before
```
┌─────────────────────────────────────┐
│ Document Card                       │
│ ─────────────────────────────────  │
│ 📄 DOJ-OGR-00019235.pdf            │
│ [Court Filing] [Government]        │
│                                     │
│ File Size: 387KB                   │
│ Entities: 2                        │
│                                     │
│ [    Download    ]                 │
└─────────────────────────────────────┘
```

### After
```
┌─────────────────────────────────────┐
│ Document Card                       │
│ ─────────────────────────────────  │
│ 📄 DOJ-OGR-00019235.pdf            │
│ [Court Filing] [Government]        │
│                                     │
│ File Size: 387KB                   │
│ Entities: 2                        │
│                                     │
│ [  👁 View Content  ] [📥]         │
└─────────────────────────────────────┘
         ↓ Click "View Content"
┌──────────────────────────────────────────────────┐
│ 📄 DOJ-OGR-00019235.pdf              [X]        │
│ [Court Filing] [Government] [PDF] [387KB]      │
├──────────────────────────────────────────────────┤
│ [🔍 Search...] [A-] 14px [A+] [Aa] [📋] [📥]   │
│ 👥 Entities (2): [Ghislaine Maxwell] [Lawrence]│
├──────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────┐ │
│ │ Case 1:20-mj-00132-AJ Document5           │ │
│ │                                            │ │
│ │ UNITED STATES DISTRICT COURT              │ │
│ │ for the District of New Hampshire         │ │
│ │                                            │ │
│ │ United States of America v.               │ │
│ │ Ghislaine Maxwell                         │ │
│ │         ^^^^^^^^^^^^^^                     │ │
│ │   (highlighted entity)                    │ │
│ │                                            │ │
│ │ Attorney: Lawrence A. Vogelman            │ │
│ │           ^^^^^^^^                         │ │
│ │      (highlighted entity)                 │ │
│ │                                            │ │
│ └────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────┤
│ Extracted: 07/06/2020 | Confidence: 95%        │
└──────────────────────────────────────────────────┘
```

## Features at a Glance

### 🎯 Core Features
- **Full Content Display**: Complete extracted document text
- **Entity Highlighting**: Names highlighted in blue, clickable
- **Search**: Find text within document
- **Font Controls**: Adjust size, toggle monospace
- **Copy/Download**: Quick actions

### 🔍 Entity Highlighting
Entities from `entities_mentioned` field are automatically:
- Highlighted with blue background
- Made clickable (filters documents by that entity)
- Listed as badges at the top of viewer

### 📊 Document Metadata
Shows comprehensive info:
- Filename
- Classification type
- Source collection
- Document type
- File size
- Extraction date
- Classification confidence

## User Workflow

```
1. Browse Documents Page
   ↓
2. Click "View Content" on any document
   ↓
3. Modal opens with full content
   ↓
4. Read, search, or click entities
   ↓
5. Click entity → filters documents by that person
   ↓
6. Copy content or download original
```

## File Changes

### New Files
- `/frontend/src/components/documents/DocumentViewer.tsx` - Main viewer component
- `/frontend/src/components/ui/dialog.tsx` - Modal component
- `/frontend/src/components/ui/scroll-area.tsx` - Scrollable area

### Modified Files
- `/frontend/src/pages/Documents.tsx` - Added viewer integration
- `/frontend/src/lib/api.ts` - Added `getDocumentById()` method
- `/frontend/package.json` - Added dialog and scroll-area dependencies

## API Integration

### Endpoint Used
```
GET /api/documents/{doc_id}
```

**Response**:
```json
{
  "document": {
    "id": "hash...",
    "filename": "DOJ-OGR-00019235.pdf",
    "classification": "court_filing",
    "entities_mentioned": ["Ghislaine Maxwell", "Lawrence A. Vogelman"],
    "file_size": 387743,
    ...
  },
  "content": "Full document text..."
}
```

## Testing Checklist

### Quick Test
```bash
# 1. Start backend
cd /Users/masa/Projects/epstein
python3 server/app.py

# 2. Start frontend (new terminal)
cd frontend
npm run dev

# 3. Open browser
# http://localhost:5173/documents

# 4. Click "View Content" on any document
```

### What to Test
- ✅ Modal opens/closes
- ✅ Content displays correctly
- ✅ Entities are highlighted
- ✅ Clicking entity filters documents
- ✅ Search box is functional
- ✅ Font controls work
- ✅ Copy button works
- ✅ Download button works
- ✅ Error states show properly

## Common Issues & Solutions

### ❌ Problem: "Content not available"
**Cause**: Document text not extracted yet
**Solution**: Use RAG search to find excerpts

### ❌ Problem: Modal doesn't open
**Cause**: Missing dependencies
**Solution**: Run `npm install` in frontend directory

### ❌ Problem: Entities not highlighted
**Cause**: Empty `entities_mentioned` array
**Solution**: Check document has entity extraction

### ❌ Problem: Build errors
**Cause**: TypeScript type mismatches
**Solution**: Already fixed - rebuild with `npm run build`

## Code Example: Using DocumentViewer

```tsx
import { DocumentViewer } from '@/components/documents/DocumentViewer';

function MyComponent() {
  const [document, setDocument] = useState<Document | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  const handleViewDocument = (doc: Document) => {
    setDocument(doc);
    setIsOpen(true);
  };

  const handleEntityClick = (entityName: string) => {
    // Navigate to entity or filter documents
    console.log('Entity clicked:', entityName);
  };

  return (
    <>
      <button onClick={() => handleViewDocument(someDoc)}>
        View Content
      </button>

      <DocumentViewer
        document={document}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        onEntityClick={handleEntityClick}
      />
    </>
  );
}
```

## Performance Notes

### ✅ Optimized
- Content loaded on-demand (not with initial page load)
- Modal only renders when open
- Entity highlighting efficient for most documents

### ⚠️ Consider for Large Docs
- 1000+ page documents may need virtualization
- Very large entity lists could slow highlighting
- Consider pagination for massive files

## Next Enhancements

### High Priority
1. Advanced search with highlighting
2. Keyboard shortcuts (Esc to close, Ctrl+F to search)
3. Document navigation (prev/next buttons)

### Medium Priority
4. Dark mode optimization
5. Mobile responsive design
6. Loading progress for large files

### Future Ideas
7. RAG Q&A integration
8. Document annotations
9. Entity relationship visualization
10. Export options (PDF, TXT)

## Success Criteria ✅

- [x] Document viewer opens smoothly
- [x] Content displays correctly
- [x] Entity highlighting works
- [x] Search functionality present
- [x] Copy/download buttons functional
- [x] Error handling graceful
- [x] No TypeScript errors
- [x] Build succeeds
- [x] Dependencies installed

## Need Help?

See full implementation details in:
`/Users/masa/Projects/epstein/DOCUMENT_VIEWER_IMPLEMENTATION.md`

---

**Status**: ✅ READY FOR TESTING
**Build**: ✅ Passing
**Dependencies**: ✅ Installed
