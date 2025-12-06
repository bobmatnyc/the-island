# Document Data Integrity Verification Checklist

**Issue:** #29 - Document Data Integrity Verification Suite
**Status:** ✗ INCOMPLETE - Issues found requiring remediation
**Date:** 2025-12-06

---

## Verification Checklist

### ✓ Schema Compliance
- [x] Schema file loaded successfully
- [x] Document structure matches interim format
- [x] Classification enum values documented
- [ ] **ACTION REQUIRED:** Full schema compliance after canonical format transformation

### ✗ UUID Integrity (FAILED)
- [x] All IDs are unique (38,482 unique IDs)
- [x] No duplicate IDs found
- [ ] **CRITICAL:** 305 email documents use DOJ control numbers instead of SHA256
  - **Fix Required:** Generate SHA256 hashes from email metadata paths
  - **Affected Files:** data/emails/house_oversight_nov2025/*_metadata.json
  - **Command:** Generate SHA256 from path, update document_classifications.json

### ✗ Classification Coverage (FAILED)
- [x] All documents have classification (100% coverage)
- [x] No missing classifications
- [ ] **CRITICAL:** 278 documents use invalid 'court_filing' classification
  - **Fix Required:** Remap 'court_filing' → 'court_record'
  - **Source:** courtlistener_giuffre_maxwell collection
  - **Validation:** Must be in schema enum

**Valid Classifications:**
```
email, court_record, flight_log, fbi_report, deposition,
correspondence, financial, administrative, contact_directory,
government_document, media_article, other
```

### ✓ Required Fields (PASSED)
- [x] All documents have 'id' field
- [x] All documents have 'filename' field
- [x] All documents have 'path' field
- [x] All documents have 'source' field
- [x] All documents have 'new_classification' field

### ✗ Data Consistency (FAILED)
- [x] Confidence scores valid (0.0-1.0 range)
- [x] No invalid confidence values
- [ ] **IMPORTANT:** 305 email documents use absolute paths
  - **Fix Required:** Convert to relative paths (remove `/Users/masa/Projects/epstein/`)
  - **Impact:** Portability issues, deployment will fail
  - **Priority:** P2 - Should fix

**Confidence Distribution:**
- High (≥0.8): 1,011 documents (2.63%)
- Medium (0.5-0.8): 37,471 documents (97.37%)
- Low (<0.5): 0 documents (0.00%)

### ✓ File Existence (PASSED)
- [x] Sampled 100 random documents
- [x] All sampled files exist at specified paths
- [x] No missing files detected

---

## Issues Summary

| Issue | Severity | Count | Impact | Status |
|-------|----------|-------|--------|--------|
| Non-SHA256 email IDs | P1 Critical | 305 | Schema violation, processing failures | Open |
| Invalid 'court_filing' classification | P1 Critical | 278 | Schema validation failures | Open |
| Absolute paths in emails | P2 Important | 305 | Portability, deployment issues | Open |

**Total Issues:** 3 critical data integrity problems affecting 888 documents (2.31%)

---

## Fix Script Requirements

Create `scripts/verification/fix_document_issues.py` to:

1. **Fix Email Document IDs**
   ```python
   # For each email document:
   if doc['source'] == 'house_oversight_nov2025_emails':
       path = doc['path']
       # Strip absolute path prefix if present
       if path.startswith('/Users/masa/Projects/epstein/'):
           path = path[len('/Users/masa/Projects/epstein/'):]
       # Generate SHA256 from relative path
       doc_id = hashlib.sha256(path.encode()).hexdigest()
       doc['id'] = doc_id
   ```

2. **Remap Court Filing Classification**
   ```python
   # For all documents with invalid classification:
   if doc['new_classification'] == 'court_filing':
       doc['new_classification'] = 'court_record'
       doc['original_classification'] = 'court_filing'  # Preserve history
   ```

3. **Normalize Email Paths**
   ```python
   # For each email document:
   if doc['path'].startswith('/Users/masa/Projects/epstein/'):
       doc['path'] = doc['path'][len('/Users/masa/Projects/epstein/'):]
   ```

---

## Verification Re-run

After fixes applied:

```bash
# 1. Run fix script
python3 scripts/verification/fix_document_issues.py --backup --apply

# 2. Verify fixes
python3 scripts/verification/verify_documents.py --verbose

# 3. Expected result: All checks PASS
```

**Success Criteria:**
- [ ] UUID Integrity: PASS (0 invalid IDs)
- [ ] Classification Coverage: PASS (0 invalid classifications)
- [ ] Data Consistency: PASS (0 absolute paths)
- [ ] Overall Status: PASS

---

## Sign-off

- [ ] All critical issues (P1) resolved
- [ ] All important issues (P2) resolved or accepted
- [ ] Verification re-run passed (exit code 0)
- [ ] Documentation updated
- [ ] Linear issue #29 updated with results
- [ ] Ready to proceed to Entity Verification (Issue #30)

**QA Engineer:** _______________________  **Date:** __________

**PM Approval:** _______________________  **Date:** __________

---

## Related Issues

- **Current:** #29 - Document Data Integrity Verification Suite
- **Next:** #30 - Entity Data Integrity Verification Suite
- **Milestone:** M5 - Verification & Launch
