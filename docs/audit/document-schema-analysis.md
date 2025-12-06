# Document Schema Audit Report

**Date**: 2025-12-06
**Issue**: #12 - Audit: Analyze current document schemas
**Auditor**: Research Agent

## Executive Summary

This audit examined the document schemas across 68,287+ documents (67,976 PDFs, 305 emails) totaling 32 GB. The current system uses **multiple fragmented schemas** without a unified document model. Critical gaps include:

- **No UUID system** - Documents identified by hash only
- **Inconsistent type classification** - 97% classified as "government_document"
- **Missing temporal metadata** - No document dates or timestamps
- **No structured email schema** - Only 8 emails in canonical format vs 305 total
- **Fragmented entity linking** - 3 separate indexing systems

**Recommendation**: Implement unified UUID-based schema with proper document typing and temporal metadata.

---

## Files Analyzed

### Primary Document Indexes

| File | Size | Records | Purpose |
|------|------|---------|---------|
| `all_documents_index.json` | 18 MB | 38,482 | Main document catalog with classifications |
| `master_document_index.json` | 16 MB | 38,177 | Deduplicated master index with summaries |
| `master_document_index_categorized.json` | 22 MB | 38,482 | Categorized version of master index |
| `document_entities_full.json` | 7.0 MB | 12,152 entities | Entity extraction results from documents |
| `document_entity_index.json` | 3.7 MB | 31,111 | Document→Entity mapping |
| `entity_document_index.json` | 1.7 MB | - | Entity→Document reverse index |

### Supporting Files

| File | Size | Purpose |
|------|------|---------|
| `document_classifications.json` | 398 KB | Classification results (311 docs) |
| `comprehensive_document_stats.json` | 2.0 KB | High-level statistics |
| `email_index.json` | - | Canonical email index (8 emails) |
| `news_articles_index.json` | 386 KB | News article catalog |

---

## Current Schema Analysis

### 1. Main Document Schema (`all_documents_index.json`)

**Structure**: Root object with metadata + documents array

```json
{
  "generated": "2025-11-18T05:03:28.313724",
  "version": "2.0",
  "total_documents": 38482,
  "documents": [ /* array of document objects */ ]
}
```

**Document Schema**:

| Field | Type | Required | Purpose | Sample Value |
|-------|------|----------|---------|--------------|
| `id` | string | ✅ | SHA256 hash of file | `674c8534bc4b...` |
| `type` | string | ✅ | File format | `"pdf"` |
| `source` | string | ✅ | Source collection | `"documentcloud"` |
| `path` | string | ✅ | File system path | `"data/sources/documentcloud/..."` |
| `filename` | string | ✅ | Original filename | `"epstein_docs_6250471.pdf"` |
| `file_size` | integer | ✅ | Size in bytes | `387743485` |
| `date_extracted` | null | ❌ | Extraction timestamp | `null` (always) |
| `classification` | string | ✅ | Document type | `"government_document"` |
| `classification_confidence` | float | ✅ | AI confidence | `0.9` |
| `entities_mentioned` | array | ✅ | Entity list | `[]` (mostly empty) |
| `doc_type` | string | ✅ | Duplicate of `type` | `"pdf"` |

**Classification Distribution** (38,482 documents):

```
government_document      37,492  (97.4%)
court_filing                637  (1.7%)
email                       305  (0.8%)
media_article                45  (0.1%)
administrative                2  (0.005%)
contact_directory             1  (0.003%)
```

**Issues Identified**:
- ❌ **No UUID** - Uses hash as ID, not human-readable
- ❌ **Always null** `date_extracted` field
- ❌ **Empty** `entities_mentioned` arrays (entity linking not integrated)
- ❌ **Redundant** `type` and `doc_type` fields
- ❌ **Over-classification** - 97% as "government_document" too broad
- ❌ **No document date** - Missing critical temporal metadata
- ❌ **No content field** - Text extraction not stored
- ❌ **No title field** - Document titles not captured

### 2. Master Document Index (`master_document_index.json`)

**Purpose**: Deduplicated master catalog with AI-generated summaries

**Document Schema**:

| Field | Type | Purpose | Sample |
|-------|------|---------|--------|
| `hash` | string | SHA256 identifier | `674c8534bc4b...` |
| `canonical_path` | string | Primary file location | `"data/sources/documentcloud/..."` |
| `size` | integer | File size in bytes | `387743485` |
| `sources` | array | All source paths (duplicates) | `["path1", "path2"]` |
| `source_count` | integer | Number of sources | `2` |
| `duplicate_count` | integer | Number of duplicates | `1` |
| `summary` | string | AI-generated summary | `"This document is an order from..."` (269 words) |
| `summary_generated_at` | string | Timestamp | `"2025-11-26T20:15:00.178977"` |
| `summary_model` | string | AI model used | `"openai/gpt-4o"` |
| `summary_word_count` | integer | Summary length | `269` |
| `summary_text_source` | string | Source type | `"pdf_extraction"` |

**Strengths**:
- ✅ Deduplication tracking
- ✅ AI-generated summaries (269 words avg)
- ✅ Summary metadata and provenance
- ✅ Multiple source path tracking

**Issues**:
- ❌ No document type/classification
- ❌ No entity linking
- ❌ No document date
- ❌ Not integrated with `all_documents_index.json`

### 3. Entity Schema (`document_entities_full.json`)

**Structure**: Root object with extraction metadata + entities dictionary

```json
{
  "extraction_metadata": {
    "total_documents": 33561,
    "documents_processed": 33415,
    "documents_failed": 146,
    "total_entities_found": 129114,
    "unique_entities": 12152,
    "model": "mistralai/ministral-8b",
    "total_cost": "$2.63"
  },
  "entities": { /* dictionary of entity objects */ }
}
```

**Entity Schema**:

| Field | Type | Purpose | Sample |
|-------|------|---------|--------|
| `name` | string | Entity name | `"David Oscar Markus"` |
| `type` | string | Entity type | `"person"` |
| `normalized_name` | string | Lowercase normalized | `"david oscar markus"` |
| `mention_count` | integer | Total mentions | `71` |
| `document_sources` | array | Document IDs (Bates numbers) | `["DOJ-OGR-00000001", ...]` |
| `first_seen` | string | First document | `"DOJ-OGR-00000001"` |
| `name_variations` | array | Alternate names | `["David Oscar Markus"]` |

**Entity Types**:
- `person`: 4,981 entities
- `organization`: 5,415 entities
- `location`: 1,756 entities

**Issues**:
- ❌ **Bates numbers** as document IDs - Not linked to hash-based system
- ❌ **No UUID** for entities
- ❌ **Limited types** - No emails, phones, dates, etc.
- ❌ **No disambiguation** - Multiple entities with same name not resolved

### 4. Document-Entity Index (`document_entity_index.json`)

**Purpose**: Map documents to their extracted entities

**Structure**:
```json
{
  "metadata": {
    "generated": "2025-11-29T14:35:41.469523+00:00",
    "total_documents": 31111
  },
  "document_entities": {
    "DOJ-OGR-00000001": [
      "david oscar markus",
      "united states of america",
      "washington dc",
      "miami florida"
    ]
  }
}
```

**Issues**:
- ❌ **Bates number keys** - Not integrated with hash-based document IDs
- ❌ **String arrays** - Uses normalized names, not entity UUIDs
- ❌ **No metadata** per mention (context, frequency, role)
- ❌ **31,111 docs** vs 38,482 total - Missing 7,371 documents

### 5. Email Schema (`email_index.json`)

**Structure**: Canonical email index

```json
{
  "metadata": { ... },
  "emails": [ /* array of email objects */ ]
}
```

**Email Schema**:

| Field | Type | Purpose | Sample |
|-------|------|---------|--------|
| `canonical_id` | string | Unique ID | `"epstein_email_fc43d26cccbd96ec"` |
| `title` | string | Email subject/title | `"RE: Epstein - Community control..."` |
| `date` | string | Send date | `"2010-04-01"` |
| `from` | string | Sender name | `"Barbara Burns"` |
| `from_email` | string | Sender address | `"BBurns@sa15.state.fl.us"` |
| `to` | array | Recipient names | `["Jack Goldberger"]` |
| `subject` | string | Email subject | `"RE: Epstein"` |
| `source` | string | Source collection | `"DocumentCloud 6506732..."` |
| `bates` | string | Bates number | `"N/A"` |
| `participants` | array | All participants | `["Barbara Burns", ...]` |
| `file_path` | string | Markdown file path | `".../epstein_email_fc43d26cccbd96ec.md"` |

**Strengths**:
- ✅ Structured email metadata
- ✅ Temporal data (date field)
- ✅ Participant tracking
- ✅ Canonical ID system

**Critical Issues**:
- ❌ **Only 8 emails** indexed vs 305 total emails
- ❌ **No integration** with main document index
- ❌ **Custom ID format** - Not UUID standard
- ❌ **Missing fields**: CC, BCC, attachments, thread ID
- ❌ **No body content** in index

### 6. Classification Data (`document_classifications.json`)

**Purpose**: Document type classification results (experimental)

**Coverage**: Only 311 documents (0.8% of total)

**Sample**:
```json
{
  "/path/to/file.md": {
    "type": "administrative",
    "confidence": 0.16,
    "secondary_types": [],
    "keywords": ["HR", "EMPLOYEE"],
    "entities_mentioned": ["bill clinton", "jeffrey epstein", ...],
    "entity_count": 44
  }
}
```

**Issues**:
- ❌ **Tiny coverage** - 311 docs vs 38,482 total
- ❌ **File path keys** - Not integrated with hash IDs
- ❌ **All "unknown"** classification distribution
- ❌ **Not used** - Results not applied to main index

---

## Schema Gaps vs Target Schema

### Target Schema (from Issue #12)

```json
{
  "document_id": "uuid",
  "document_type": "email|court_record|flight_log|other",
  "source": "string",
  "date": "ISO8601",
  "title": "string",
  "content": "string",
  "extracted_entities": ["entity_uuid"],
  "classification_confidence": "float",
  "metadata": {}
}
```

### Gap Analysis

| Field | Current Status | Gap |
|-------|---------------|-----|
| `document_id` | ❌ SHA256 hash | Need UUID system |
| `document_type` | ⚠️ 97% as "government_document" | Need granular types (email, court_record, flight_log) |
| `source` | ✅ Present | Good |
| `date` | ❌ Missing | **Critical gap** - No document dates |
| `title` | ❌ Missing | Available in master_index summaries but not structured |
| `content` | ❌ Missing | Text extraction done but not in document schema |
| `extracted_entities` | ⚠️ Empty arrays | Entity data exists but not linked to docs by hash |
| `classification_confidence` | ✅ Present | Good (but classifications too broad) |
| `metadata` | ⚠️ Scattered | Need structured metadata field |

---

## Document Type Classification Issues

### Current Type Distribution
```
government_document: 37,492 (97.4%)  ← Too broad!
court_filing:           637 (1.7%)
email:                  305 (0.8%)
media_article:           45 (0.1%)
other:                    3 (0.008%)
```

### Missing Document Types

The target schema requires these types, but they're not distinguished:

| Type | Expected Count | Current Classification | Gap |
|------|---------------|----------------------|-----|
| `email` | 305 | ✅ Classified | 8 in canonical format, 297 not indexed |
| `court_record` | ~637 | ⚠️ As "court_filing" | Need distinction: filings, orders, transcripts |
| `flight_log` | ~2 | ❌ As "government_document" | Need specific classification |
| `deposition` | Unknown | ❌ As "court_filing" | Need specific type |
| `correspondence` | Unknown | ❌ As "government_document" | Need extraction |
| `financial_record` | Unknown | ❌ As "government_document" | Need identification |
| `calendar_entry` | Unknown | ❌ Mixed | Need extraction |
| `contact_book` | 1 | ✅ Identified | Good |

**Recommendation**: Implement multi-label classification to capture document subtypes.

---

## Entity Integration Issues

### Three Separate Systems Not Integrated

1. **Hash-based document IDs** (`all_documents_index.json`)
   - Uses SHA256 hashes
   - 38,482 documents

2. **Bates number system** (`document_entities_full.json`)
   - Uses "DOJ-OGR-00000001" format
   - 31,111 documents

3. **File path system** (`document_classifications.json`)
   - Uses absolute file paths
   - 311 documents

**Problem**: No cross-reference between systems

**Example**:
- Document with hash `674c8534bc4b...` has `entities_mentioned: []`
- Same document as `DOJ-OGR-00000001` has entities: `["david oscar markus", "united states of america", ...]`
- **No linkage** between the two records

### Entity Schema Gaps

| Gap | Impact |
|-----|--------|
| No entity UUIDs | Can't uniquely identify entities |
| String-based linking | `"david oscar markus"` vs entity object |
| No disambiguation | Multiple "John Smith" entities conflated |
| Limited types | Only person/org/location, missing emails, phones, dates |
| No relationship data | Can't link entities to each other |

---

## Temporal Metadata Gaps

### Critical Missing Data

| Metadata | Status | Impact |
|----------|--------|--------|
| Document creation date | ❌ Missing | Can't build timeline |
| Document modification date | ❌ Missing | Can't track versions |
| Extraction timestamp | Always `null` | Can't audit pipeline |
| Email send date | ⚠️ Only 8 emails | Can't sequence correspondence |
| Event dates | ❌ Not extracted | Can't build chronology |

**Critical Impact**: Cannot build temporal visualizations or chronological narratives without document dates.

---

## Schema Fragmentation Summary

### Data Exists But Not Integrated

| Data Type | Source File | Coverage | Integration Status |
|-----------|------------|----------|-------------------|
| Document metadata | `all_documents_index.json` | 38,482 docs | ✅ Primary index |
| Summaries | `master_document_index.json` | 38,177 docs | ❌ Separate file |
| Entities | `document_entities_full.json` | 12,152 entities | ❌ Bates numbers only |
| Entity linking | `document_entity_index.json` | 31,111 docs | ❌ Bates numbers |
| Classifications | `document_classifications.json` | 311 docs | ❌ File paths |
| Emails | `email_index.json` | 8 emails | ❌ Custom ID format |

**Result**: 6 different schemas with 4 different ID systems

---

## Recommendations

### 1. Implement UUID System (Priority: P0)

**Action**: Generate UUIDs for all documents
- Map hash → UUID
- Map Bates number → UUID
- Map file path → UUID
- Create master UUID registry

**Benefits**:
- Single source of truth for document identity
- Human-readable IDs
- Cross-system integration

### 2. Add Temporal Metadata (Priority: P0)

**Action**: Extract document dates from content
- Parse email headers for send dates
- Extract court filing dates from text
- Use OCR timestamps as fallback
- Add `document_date` and `date_range` fields

**Benefits**:
- Enable chronological analysis
- Support timeline visualizations
- Improve search and filtering

### 3. Refine Document Classification (Priority: P1)

**Action**: Implement multi-label classification
- Add document subtypes: `court_order`, `deposition`, `email`, `flight_log`
- Use hierarchical labels: `court_record → court_filing → motion`
- Increase classifier coverage from 311 to all 38,482 docs
- Add confidence scores per label

**Benefits**:
- More granular document discovery
- Better search precision
- Support type-specific visualizations

### 4. Integrate Entity System (Priority: P1)

**Action**: Unify entity linking with UUID system
- Create entity UUIDs
- Map document UUIDs → entity UUIDs
- Add entity metadata: role, context, mention count
- Implement disambiguation

**Benefits**:
- Rich entity networks
- Precise cross-references
- Better relationship mapping

### 5. Add Content Field (Priority: P2)

**Action**: Include extracted text in document schema
- Add `content` field with full text
- Add `content_preview` field (first 500 chars)
- Store content in separate files for large docs
- Index for full-text search

**Benefits**:
- Enable content search
- Support RAG systems
- Improve analysis capabilities

### 6. Consolidate Schemas (Priority: P2)

**Action**: Merge fragmented indexes into unified schema
- Single `documents.json` with all metadata
- Include summaries, classifications, entities inline
- Use references for large fields (content → separate file)
- Version the unified schema

**Benefits**:
- Simpler data access
- Reduced complexity
- Easier maintenance

---

## Proposed Unified Schema

### Document Schema v3.0 (Target)

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "legacy_ids": {
    "hash": "674c8534bc4b...",
    "bates": "DOJ-OGR-00000001",
    "file_path": "data/sources/..."
  },
  "document_type": "email",
  "document_subtypes": ["correspondence", "government"],
  "source": "house_oversight_nov2025",
  "title": "RE: Epstein - Community control completion",
  "date": "2010-04-01T00:00:00Z",
  "date_range": {
    "start": "2010-04-01",
    "end": "2010-04-01"
  },
  "content_preview": "From: Barbara Burns <BBurns@sa15.state.fl.us>...",
  "content_path": "data/content/uuid/550e8400-e29b-41d4-a716-446655440000.txt",
  "extracted_entities": [
    {
      "entity_id": "ent_12345",
      "name": "Barbara Burns",
      "type": "person",
      "role": "sender",
      "mention_count": 1
    }
  ],
  "classification": {
    "primary": "email",
    "secondary": ["government_correspondence"],
    "confidence": 0.95
  },
  "metadata": {
    "file_size": 12345,
    "file_format": "pdf",
    "page_count": 1,
    "summary": "Email regarding Jeffrey Epstein's community control...",
    "email": {
      "from": "Barbara Burns",
      "from_email": "BBurns@sa15.state.fl.us",
      "to": ["Jack Goldberger"],
      "subject": "RE: Epstein",
      "participants": ["Barbara Burns", "Jack Goldberger"]
    }
  },
  "extraction_metadata": {
    "extracted_at": "2025-11-29T14:35:41Z",
    "extraction_model": "mistralai/ministral-8b",
    "summary_model": "openai/gpt-4o"
  },
  "version": "3.0",
  "created_at": "2025-12-06T00:00:00Z",
  "updated_at": "2025-12-06T00:00:00Z"
}
```

---

## Migration Path

### Phase 1: Foundation (Week 1)
1. Generate UUIDs for all 38,482 documents
2. Create UUID → hash mapping table
3. Create UUID → Bates number mapping table
4. Update all indexes with UUID references

### Phase 2: Temporal Data (Week 2)
1. Extract dates from 305 emails (high priority)
2. Extract dates from 637 court filings
3. Parse dates from remaining documents
4. Add `document_date` field to schema

### Phase 3: Classification (Week 3)
1. Expand classification from 311 to all 38,482 docs
2. Implement hierarchical/multi-label system
3. Refine type taxonomy (email, court_order, deposition, etc.)
4. Validate against target types

### Phase 4: Integration (Week 4)
1. Link entities using UUIDs
2. Merge entity data into document schema
3. Add content previews
4. Consolidate into unified `documents.json`

### Phase 5: Validation (Week 5)
1. Verify all 38,482 documents have UUIDs
2. Check entity linkage completeness
3. Validate classification coverage
4. Test unified schema against API requirements

---

## Files Requiring Updates

| File | Change Required | Priority |
|------|----------------|----------|
| `all_documents_index.json` | Add UUIDs, dates, content preview | P0 |
| `master_document_index.json` | Merge into unified schema | P1 |
| `document_entities_full.json` | Add entity UUIDs, link to doc UUIDs | P1 |
| `document_entity_index.json` | Convert to UUID-based linking | P1 |
| `email_index.json` | Integrate into main document index | P2 |
| `document_classifications.json` | Expand coverage, use UUIDs | P2 |

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Documents with UUIDs | 0% | 100% |
| Documents with dates | ~0.02% (8 emails) | 80%+ |
| Document type granularity | 6 types | 15+ types |
| Entity linkage | 31,111 docs (Bates only) | 38,482 docs (UUID) |
| Emails in canonical format | 8 (2.6%) | 305 (100%) |
| Classification coverage | 311 (0.8%) | 38,482 (100%) |
| Schema files | 6 fragmented | 1 unified |

---

## Appendix: Sample Queries Not Possible Today

Due to schema gaps, these queries **cannot** be answered:

1. ❌ "Find all documents from 2010" → No document dates
2. ❌ "Show emails sent by Barbara Burns" → Only 8 emails indexed
3. ❌ "List all depositions" → Not classified separately
4. ❌ "Find documents mentioning David Markus with hash ID" → Entities use Bates numbers
5. ❌ "Show flight logs from 2005-2010" → Not typed as flight_log
6. ❌ "Documents where Jeffrey Epstein and Bill Clinton appear together" → Entity linking incomplete

**With unified schema**: All queries above become possible.

---

## Conclusion

The current document schemas are **functional but fragmented**. The system has good coverage (38,482 documents) and some advanced features (AI summaries, entity extraction), but lacks:

1. **Unified identity** (UUID system)
2. **Temporal data** (document dates)
3. **Granular classification** (too broad types)
4. **Integrated entity linking** (3 separate systems)
5. **Canonical email index** (only 2.6% coverage)

**Priority**: Implement UUID system and add temporal metadata (Phases 1-2) to enable timeline-based analysis.

**Estimated Effort**: 5 weeks for full migration to unified schema.

---

**Next Steps**:
1. Review this audit with Issue #12 stakeholders
2. Approve unified schema design (v3.0)
3. Begin Phase 1: UUID generation
4. Track progress in Linear issue updates
