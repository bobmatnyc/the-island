# Document Classification Report

**Generated:** 2025-12-06 20:54:37 UTC

## Summary

Total documents classified: **38,482**

## Classification Distribution

### Before Reclassification

| Type | Count | Percentage |
|------|-------|------------|
| government_document | 37,492 | 97.4% |
| court_filing | 637 | 1.7% |
| email | 305 | 0.8% |
| media_article | 45 | 0.1% |
| administrative | 2 | 0.0% |
| contact_directory | 1 | 0.0% |

### After Semantic Classification

| Type | Count | Percentage | Change |
|------|-------|------------|--------|
| government_document | 37,469 | 97.4% | -23 |
| court_record | 362 | 0.9% | +362 |
| email | 305 | 0.8% | 0 |
| court_filing | 278 | 0.7% | -359 |
| media_article | 45 | 0.1% | 0 |
| fbi_report | 22 | 0.1% | +22 |
| contact_directory | 1 | 0.0% | 0 |

## Classification Quality

### Confidence Distribution

- **High confidence (≥0.8):** 1,011 documents (2.6%)
- **Medium confidence (0.5-0.8):** 37,471 documents (97.4%)
- **Low confidence (<0.5):** 0 documents (0.0%)

### Classification Methods

| Method | Count | Percentage |
|--------|-------|------------|
| existing | 37,770 | 98.1% |
| path_source | 707 | 1.8% |
| content_analysis | 5 | 0.0% |

## Examples by Type

### Contact Directory

- **epstein-birthday-book.pdf**
  - Path: `data/sources/raw_entities/epstein-birthday-book.pdf`
  - Confidence: 0.9

### Court Filing

- **gov.uscourts.nysd.447706.1328.17.pdf**
  - Path: `data/sources/404media/Epstein Docs 1.5.24/gov.uscourts.nysd.447706.1328.17.pdf`
  - Confidence: 0.95

- **1320-30.pdf**
  - Path: `data/sources/404media/Epstein docs 2/1320-30.pdf`
  - Confidence: 0.95

- **gov.uscourts.nysd.447706.1328.28.pdf**
  - Path: `data/sources/404media/Epstein Docs 1.5.24/gov.uscourts.nysd.447706.1328.28.pdf`
  - Confidence: 0.95

### Court Record

- **epstein_docs_6250471.pdf**
  - Path: `data/sources/documentcloud/epstein_docs_6250471.pdf`
  - Confidence: 0.91
  - Keywords: court, plaintiff, defendant

- **unsealing_jan2024_943pages.pdf**
  - Path: `data/sources/documentcloud/unsealing_jan2024_943pages.pdf`
  - Confidence: 0.95
  - Keywords: court, case no, plaintiff

- **Final_Epstein_documents_2024_943pages.pdf**
  - Path: `data/sources/giuffre_maxwell/2024_unsealed/Final_Epstein_documents_2024_943pages.pdf`
  - Confidence: 0.95
  - Keywords: court, case no, plaintiff

### Email

- **DOJ-OGR-00015682_metadata.json**
  - Path: `/Users/masa/Projects/epstein/data/emails/house_oversight_nov2025/2001-05/DOJ-OGR-00015682_metadata.json`
  - Confidence: 0.9

- **DOJ-OGR-00015681_metadata.json**
  - Path: `/Users/masa/Projects/epstein/data/emails/house_oversight_nov2025/2001-25/DOJ-OGR-00015681_metadata.json`
  - Confidence: 0.9

- **DOJ-OGR-00032939_metadata.json**
  - Path: `/Users/masa/Projects/epstein/data/emails/house_oversight_nov2025/2005-09/DOJ-OGR-00032939_metadata.json`
  - Confidence: 0.9

### Fbi Report

- **doj_feb2025_release.pdf**
  - Path: `data/sources/documentcloud/doj_feb2025_release.pdf`
  - Confidence: 0.74
  - Keywords: fbi, investigation, field office

- **jeffrey_epstein_part_03.pdf**
  - Path: `data/sources/fbi_vault/jeffrey_epstein_part_03.pdf`
  - Confidence: 0.9

- **jeffrey_epstein_part_18.pdf**
  - Path: `data/sources/fbi_vault/jeffrey_epstein_part_18.pdf`
  - Confidence: 0.9

### Government Document

- **document_4.pdf**
  - Path: `data/sources/house_oversight_sept2024/document_4.pdf`
  - Confidence: 0.72

- **document_3.pdf**
  - Path: `data/sources/house_oversight_sept2024/document_3.pdf`
  - Confidence: 0.72

- **document_1.pdf**
  - Path: `data/sources/house_oversight_sept2024/document_1.pdf`
  - Confidence: 0.72

### Media Article

- **1325-2.pdf**
  - Path: `data/sources/404media/1.4.23 Epstein Docs/1325-2.pdf`
  - Confidence: 0.9

- **1331-15.pdf**
  - Path: `data/sources/404media/Epstein Docs 1.5.24/1331-15.pdf`
  - Confidence: 0.9

- **1325-18.pdf**
  - Path: `data/sources/404media/1.4.23 Epstein Docs/1325-18.pdf`
  - Confidence: 0.9


## Key Findings

1. **Generic classification reduction:** Government documents reduced from 97.4% to 97.4%
2. **Specific types identified:** 7 distinct document types
3. **High confidence classifications:** 2.6% of documents
4. **Most common types:**
   - government_document: 37,469 (97.4%)
   - court_record: 362 (0.9%)
   - email: 305 (0.8%)
   - court_filing: 278 (0.7%)
   - media_article: 45 (0.1%)

## Critical Finding: Missing Summaries

**Issue**: Only **6 out of 38,177** documents (0.02%) have summaries in the master document index.

This severely limits semantic classification capabilities:
- Cannot analyze document content for 99.98% of documents
- Forced to rely on path/filename patterns and existing classifications
- Many documents likely misclassified due to lack of content analysis

### Impact on Classification

| Method | Documents | Percentage |
|--------|-----------|------------|
| Existing classification (pre-generated) | 37,773 | 98.2% |
| Path/source patterns | 707 | 1.8% |
| Content analysis (summary-based) | 5 | 0.01% |

**Root Cause**: Document summarization process incomplete. Most DOJ-OGR documents from house_oversight_nov2025 batch (37,469 docs) lack summaries.

## Next Steps

### Immediate Actions (High Priority)

1. **Generate document summaries** for the 37,469 house_oversight_nov2025 documents
   - Run summarization pipeline on all unsummarized documents
   - Prioritize court-related documents (likely many false "government_document" classifications)
   - Use batch processing to handle large volume efficiently

2. **Re-run classification** after summaries generated
   - Expected improvement: 20-30% of documents reclassified from generic types to specific types
   - Target: Reduce "government_document" from 97.4% to <50%

### Medium Priority

3. **Add specialized court record detection**
   - Many house_oversight documents are likely court filings (based on DOJ-OGR prefix)
   - Add regex patterns for case numbers, court names, legal terminology
   - Validate against known court filing patterns

4. **Enhance keyword matching**
   - Add domain-specific terminology (legal, financial, aviation)
   - Implement multi-word phrase matching (e.g., "sworn testimony", "wire transfer")
   - Weight important keywords higher (e.g., "deposition" vs "document")

### Long-term Improvements

5. **Validate classification accuracy** through manual sampling
   - Sample 100 documents from each classification type
   - Calculate precision/recall metrics
   - Identify systematic misclassifications

6. **Update search and filtering** to use new semantic classifications
   - Add document type filters to search interface
   - Enable type-specific advanced search options
   - Surface document type statistics in UI
