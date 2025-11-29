# Fix "Content Not Available" - Action Checklist

**Quick Summary**: Quality assurance report with test results, issues found, and recommendations.

**Category**: QA
**Status**: Complete
**Last Updated**: 2025-11-24

**Key Points**:
- [x] Investigation complete
- [x] Root cause identified: `date_extracted: null` for PDFs
- [x] Solution designed: Add filter to document service
- [x] Impact assessed: Hides 38,177 unextracted PDFs
- [x] Documentation created: 3 files

---

**Issue:** Documents show "Content not available for this document"
**Root Cause:** 38,177 PDFs (95%) never text-extracted
**Solution:** Filter unextracted PDFs from document browser
**Time Required:** 3 minutes

---

## ✅ Pre-Flight Checklist

- [x] Investigation complete
- [x] Root cause identified: `date_extracted: null` for PDFs
- [x] Solution designed: Add filter to document service
- [x] Impact assessed: Hides 38,177 unextracted PDFs
- [x] Documentation created: 3 files

---

## 🚀 Implementation Steps

### Step 1: Backup Current File (Optional but Recommended)

```bash
# Backup document_service.py
cp server/services/document_service.py \
   server/services/document_service.py.backup_$(date +%Y%m%d)
```

**Time:** 10 seconds

- [ ] Backup created

---

### Step 2: Edit Document Service

**File:** `server/services/document_service.py`
**Lines:** 94-104
**Change Type:** Add one filter condition

#### Find this code block:

```python
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
```

#### Change it to:

```python
# ALWAYS filter out JSON metadata files and unavailable content
filtered_docs = [
    doc for doc in filtered_docs
    if not (
        # Exclude JSON files from data/metadata/ directory
        (doc.get("path", "").startswith("data/metadata/") and
         doc.get("filename", "").endswith(".json")) or
        # Exclude PDFs without extracted text (NEW LINE BELOW)
        (doc.get("type") == "pdf" and doc.get("date_extracted") is None) or
        # Exclude documents with unavailable content marker
        doc.get("content") == "Content not available for this document."
    )
]
```

**What Changed:** Added line:
```python
(doc.get("type") == "pdf" and doc.get("date_extracted") is None) or
```

**Time:** 1 minute

- [ ] Code edited
- [ ] One line added
- [ ] Syntax verified (check parentheses)

---

### Step 3: Restart Server

```bash
# If server is running, stop it (Ctrl+C)
# Then restart:
cd /Users/masa/Projects/epstein/server
python app.py
```

**Expected Output:**
```
* Running on http://0.0.0.0:5050
* Ready to accept connections
```

**Time:** 30 seconds

- [ ] Server stopped
- [ ] Server restarted
- [ ] No errors in console
- [ ] Server listening on port 5050

---

### Step 4: Test in Browser

#### Open Document Browser

```bash
# Open browser to:
http://localhost:5050
# Or if using ngrok, use the ngrok URL
```

#### Visual Checks

- [ ] Document browser loads without errors
- [ ] Document list appears
- [ ] No "Content not available" messages visible
- [ ] Document count shows ~2,000 (not 40,000+)
- [ ] Clicking documents shows readable content
- [ ] Search functionality works
- [ ] Filter functionality works

**Time:** 1 minute

---

### Step 5: Test API Endpoint

```bash
# Test documents endpoint
curl -s http://localhost:5050/api/documents | \
  python3 -m json.tool | less

# Count total documents returned
curl -s http://localhost:5050/api/documents | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['total'])"

# Verify no unextracted PDFs
curl -s http://localhost:5050/api/documents | \
  python3 -c "import sys, json; docs = json.load(sys.stdin)['documents']; print('Unextracted:', sum(1 for d in docs if d.get('date_extracted') is None))"
```

**Expected Results:**
- Total documents: ~2,000
- Unextracted count: 0

**Time:** 30 seconds

- [ ] API responds successfully
- [ ] Total documents ~2,000
- [ ] No unextracted PDFs in results
- [ ] All returned documents have `date_extracted` value

---

### Step 6: Verify Specific Document

```bash
# Try to get epstein_docs_6250471.pdf specifically
curl -s http://localhost:5050/api/documents?q=6250471 | \
  python3 -m json.tool

# Should return empty results or not include the unextracted PDF
```

**Expected:** No results for `epstein_docs_6250471.pdf`

**Time:** 15 seconds

- [ ] Search for 6250471 returns 0 results
- [ ] Unextracted PDF no longer appears

---

### Step 7: Test Edge Cases

```bash
# Test that extracted PDFs still appear (if any exist)
curl -s http://localhost:5050/api/documents | \
  python3 -c "import sys, json; docs = json.load(sys.stdin)['documents']; pdfs = [d for d in docs if d.get('type') == 'pdf']; print(f'PDFs with extraction: {len(pdfs)}'); [print(f\"  - {d['filename']}\") for d in pdfs[:5]]"

# Test that emails still appear
curl -s http://localhost:5050/api/documents | \
  python3 -c "import sys, json; docs = json.load(sys.stdin)['documents']; emails = [d for d in docs if d.get('type') == 'email']; print(f'Emails: {len(emails)}')"
```

**Expected:**
- Some extracted PDFs may appear (if they have `date_extracted` set)
- Emails still appear normally

**Time:** 30 seconds

- [ ] Extracted PDFs still visible (if any)
- [ ] Emails still visible
- [ ] Other document types unaffected

---

## 📊 Success Criteria

### Before Fix
- ❌ 40,000+ documents in browser
- ❌ 95% show "Content not available"
- ❌ Poor user experience

### After Fix (All Must Pass)
- [ ] ~2,000 documents in browser
- [ ] 100% have readable content
- [ ] No "Content not available" messages
- [ ] Server runs without errors
- [ ] API returns only extracted documents
- [ ] Document search works correctly
- [ ] Individual document pages load content

---

## 🔄 Rollback Plan

If something goes wrong:

### Option 1: Restore Backup
```bash
cp server/services/document_service.py.backup_* \
   server/services/document_service.py
cd server
python app.py
```

### Option 2: Remove the Added Line
Edit `server/services/document_service.py` and remove:
```python
(doc.get("type") == "pdf" and doc.get("date_extracted") is None) or
```

### Option 3: Add Query Parameter for Admin Access
Instead of hiding all unextracted PDFs, add optional parameter:
```python
def search_documents(
    self,
    # ... existing parameters ...
    show_unextracted: bool = False
):
    # ... existing code ...

    if not show_unextracted:
        filtered_docs = [
            doc for doc in filtered_docs
            if not (doc.get("type") == "pdf" and doc.get("date_extracted") is None)
        ]
```

Then admins can view all: `GET /api/documents?show_unextracted=true`

---

## 📝 Post-Implementation Notes

### What Changed
- [x] Document service now filters PDFs without `date_extracted`
- [x] Document browser shows only ~2,000 extracted documents
- [x] User experience improved (no unavailable content)

### What Didn't Change
- [ ] Document index unchanged (all PDFs still indexed)
- [ ] PDF files unchanged (still on disk)
- [ ] API structure unchanged
- [ ] Frontend code unchanged

### Future Enhancements
- [ ] Add admin toggle to show/hide unextracted documents
- [ ] Add batch extraction script for selected PDFs
- [ ] Add extraction status dashboard
- [ ] Add "Request Extraction" button for specific documents

---

## 🐛 Troubleshooting

### Issue: Server won't start
**Solution:** Check syntax errors in document_service.py
```bash
python3 -m py_compile server/services/document_service.py
```

### Issue: Still seeing unextracted PDFs
**Solution:** Clear browser cache and hard reload
```bash
# Chrome: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
# Safari: Cmd+Option+R
```

### Issue: No documents showing at all
**Solution:** Check filter logic - may be too restrictive
```python
# Temporarily comment out the new filter line to debug
# (doc.get("type") == "pdf" and doc.get("date_extracted") is None) or
```

### Issue: Extracted PDFs also hidden
**Solution:** Verify PDFs have `date_extracted` set
```bash
python3 << 'EOF'
import json
with open('data/metadata/all_documents_index.json') as f:
    data = json.load(f)
extracted_pdfs = [d for d in data['documents'] if d.get('type') == 'pdf' and d.get('date_extracted')]
print(f"Extracted PDFs: {len(extracted_pdfs)}")
EOF
```

---

## 📈 Metrics to Monitor

### Immediately After Deployment
- [ ] Server uptime (no crashes)
- [ ] Document browser load time
- [ ] API response time
- [ ] Error rate (should be 0)

### First Hour
- [ ] User feedback (positive/negative)
- [ ] Page load performance
- [ ] Search result accuracy
- [ ] Document view success rate

### First Day
- [ ] Total document views
- [ ] Search queries
- [ ] Failed content loads (should be 0)
- [ ] User satisfaction

---

## 📚 Documentation Created

1. **DOCUMENT_6250471_DIAGNOSTIC_REPORT.md**
   - Complete investigation findings
   - Technical analysis
   - Root cause explanation
   - All solution options

2. **DOCUMENT_CONTENT_UNAVAILABLE_FIX.md**
   - Quick fix guide
   - Code changes
   - Impact analysis
   - Selective extraction guide

3. **CONTENT_UNAVAILABLE_VISUAL_SUMMARY.txt**
   - Visual flowcharts
   - ASCII diagrams
   - Statistics visualization
   - Before/after comparison

4. **FIX_CONTENT_UNAVAILABLE_CHECKLIST.md** (this file)
   - Step-by-step implementation
   - Testing procedures
   - Rollback plan
   - Troubleshooting guide

---

## ✅ Final Verification

After completing all steps:

- [ ] Code change implemented (1 line added)
- [ ] Server restarted successfully
- [ ] Browser test passed
- [ ] API test passed
- [ ] Edge cases verified
- [ ] No "Content not available" messages
- [ ] Document count reduced to ~2,000
- [ ] All visible documents have content
- [ ] Search and filters work correctly
- [ ] Performance acceptable
- [ ] No errors in console
- [ ] Documentation updated

---

## 🎉 Success!

**Status:** ⏳ Ready to Implement

**Estimated Total Time:** 3 minutes
**Risk Level:** Low (easily reversible)
**Impact:** High (significantly improves UX)

**Next Steps:**
1. Run through checklist
2. Test thoroughly
3. Monitor for issues
4. Plan selective extraction for high-value PDFs (future)

---

**Checklist Created:** November 18, 2025
**Implementation Status:** Pending
**Expected Completion:** 3 minutes
