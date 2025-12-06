# Document Schema Field Comparison

## Current vs Target Schema Field Analysis

### Field-by-Field Comparison

| Field | Current Schema | Target Schema | Status | Gap Description |
|-------|---------------|---------------|--------|-----------------|
| **Identity** |
| `document_id` | `id` (SHA256 hash) | `uuid` (UUID v4) | ❌ | Hash is not human-readable, not standard UUID |
| `legacy_ids` | N/A | Object with hash/Bates/path | ❌ | No backward compatibility mapping |
| **Type Classification** |
| `document_type` | `classification` (string) | `document_type` (enum) | ⚠️ | Present but 97% as "government_document" |
| `document_subtypes` | N/A | Array of strings | ❌ | No hierarchical/multi-label support |
| `classification_confidence` | ✅ Present (float) | ✅ Required | ✅ | Good |
| **Source Information** |
| `source` | ✅ Present | ✅ Required | ✅ | Good - collection name |
| `path` | ✅ Present | Optional | ✅ | File system path available |
| `filename` | ✅ Present | Optional | ✅ | Original filename tracked |
| **Temporal Data** |
| `date` | ❌ Missing | `date` (ISO8601) | ❌ | **Critical gap** - no document dates |
| `date_range` | ❌ Missing | `{start, end}` | ❌ | No date range support |
| `date_extracted` | Always `null` | `extracted_at` | ❌ | Field exists but never populated |
| **Content** |
| `title` | ❌ Missing | `title` (string) | ❌ | Only in master_index, not integrated |
| `content` | ❌ Missing | `content` (string/path) | ❌ | Text extracted but not in schema |
| `content_preview` | ❌ Missing | First 500 chars | ❌ | No preview field |
| `summary` | ⚠️ Separate file | Optional | ⚠️ | In master_index.json, not integrated |
| **Entity Linking** |
| `extracted_entities` | Empty arrays `[]` | Array of entity objects | ❌ | Entity data exists but not linked by hash |
| `entities_mentioned` | ✅ Present but empty | Deprecated | ⚠️ | Field exists, always empty |
| **Metadata** |
| `metadata` | ❌ Scattered | Structured object | ❌ | No consolidated metadata field |
| `file_size` | ✅ Present | In metadata | ✅ | Available |
| `type` | ✅ Present ("pdf") | In metadata | ✅ | File format tracked |
| `doc_type` | ⚠️ Duplicate of `type` | N/A | ⚠️ | Redundant field |
| **Versioning** |
| `version` | ⚠️ Index-level only | Document-level | ❌ | Schema version at root, not per doc |
| `created_at` | ❌ Missing | ISO8601 timestamp | ❌ | No creation tracking |
| `updated_at` | ❌ Missing | ISO8601 timestamp | ❌ | No update tracking |

### Email-Specific Fields (for document_type="email")

| Field | Current (email_index.json) | Target Schema | Status | Gap |
|-------|---------------------------|---------------|--------|-----|
| `from` | ✅ Present | In metadata.email | ✅ | 8 emails only |
| `from_email` | ✅ Present | In metadata.email | ✅ | 8 emails only |
| `to` | ✅ Present (array) | In metadata.email | ✅ | 8 emails only |
| `cc` | ❌ Missing | In metadata.email | ❌ | Not captured |
| `bcc` | ❌ Missing | In metadata.email | ❌ | Not captured |
| `subject` | ✅ Present | In metadata.email | ✅ | 8 emails only |
| `date` | ✅ Present | ✅ Required | ✅ | 8 emails only |
| `participants` | ✅ Present (array) | In metadata.email | ✅ | 8 emails only |
| `bates` | ✅ Present | In metadata | ✅ | Bates numbering available |
| `attachments` | ❌ Missing | In metadata.email | ❌ | No attachment tracking |
| `thread_id` | ❌ Missing | In metadata.email | ❌ | No conversation threading |
| `in_reply_to` | ❌ Missing | In metadata.email | ❌ | No reply chain |

**Critical Issue**: Only 8 emails (2.6%) in canonical email index vs 305 total emails

### Court Document Fields (for document_type="court_record")

| Field | Current | Target Schema | Status | Gap |
|-------|---------|---------------|--------|-----|
| `court_name` | ❌ Missing | In metadata.court | ❌ | Not extracted |
| `case_number` | ❌ Missing | In metadata.court | ❌ | Not extracted |
| `filing_date` | ❌ Missing | Should map to `date` | ❌ | Not extracted |
| `document_subtype` | ❌ Missing | court_order, motion, etc. | ❌ | Not classified |
| `parties` | ⚠️ In entities | In metadata.court | ⚠️ | Not structured |

### Summary Field Comparison

| Aspect | Current Schema | Target Schema v3.0 |
|--------|---------------|-------------------|
| **Identity** | Hash-based, 4 different ID systems | UUID v4 with legacy ID mapping |
| **Temporal** | 0.02% coverage (8 docs) | 80%+ coverage with date extraction |
| **Classification** | 6 types, 97% too broad | 15+ types with hierarchical subtypes |
| **Entity Linking** | 80.8% coverage (Bates only) | 100% coverage with UUID linking |
| **Content** | Not in schema | Preview + full text path |
| **Metadata** | Scattered across 10+ fields | Consolidated in `metadata` object |
| **Email Support** | 2.6% in canonical format | 100% with full email schema |
| **Versioning** | Index-level only | Per-document version tracking |

---

## Schema Evolution

### Current Schema (v2.0)
```json
{
  "id": "674c8534bc4b...",
  "type": "pdf",
  "source": "documentcloud",
  "path": "data/sources/...",
  "filename": "epstein_docs.pdf",
  "file_size": 387743485,
  "date_extracted": null,
  "classification": "government_document",
  "classification_confidence": 0.9,
  "entities_mentioned": [],
  "doc_type": "pdf"
}
```

**Issues**: 
- No UUID
- No document date
- Empty entities array
- No content
- Redundant type fields

### Target Schema (v3.0)
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "legacy_ids": {
    "hash": "674c8534bc4b...",
    "bates": "DOJ-OGR-00000001"
  },
  "document_type": "court_record",
  "document_subtypes": ["court_order", "unsealing_order"],
  "source": "documentcloud",
  "title": "Order on Unsealing Court Records",
  "date": "2019-08-09T00:00:00Z",
  "date_range": {"start": "2019-08-09", "end": "2019-08-09"},
  "content_preview": "UNITED STATES COURT OF APPEALS...",
  "content_path": "data/content/uuid/550e8400.txt",
  "extracted_entities": [
    {
      "entity_id": "ent_12345",
      "name": "Ghislaine Maxwell",
      "type": "person",
      "role": "defendant",
      "mention_count": 15
    },
    {
      "entity_id": "ent_67890",
      "name": "United States Court of Appeals",
      "type": "organization",
      "role": "issuer",
      "mention_count": 3
    }
  ],
  "classification": {
    "primary": "court_record",
    "secondary": ["court_order", "unsealing_order"],
    "confidence": 0.95,
    "model": "gpt-4o",
    "classified_at": "2025-11-17T00:21:54Z"
  },
  "metadata": {
    "file_size": 387743485,
    "file_format": "pdf",
    "page_count": 3,
    "summary": "Order from Second Circuit denying Maxwell's petition...",
    "court": {
      "name": "United States Court of Appeals for the Second Circuit",
      "case_number": "18-2868-cv",
      "filing_date": "2019-08-09"
    }
  },
  "extraction_metadata": {
    "extracted_at": "2025-11-16T22:15:00Z",
    "extraction_model": "gpt-4o-2024-08-06",
    "summary_model": "gpt-4o",
    "summary_generated_at": "2025-11-26T20:15:00Z"
  },
  "version": "3.0",
  "created_at": "2025-12-06T00:00:00Z",
  "updated_at": "2025-12-06T00:00:00Z"
}
```

**Improvements**:
- ✅ UUID-based identity
- ✅ Document date and date range
- ✅ Hierarchical classification
- ✅ Rich entity objects with roles
- ✅ Content preview and path
- ✅ Consolidated metadata
- ✅ Type-specific fields (court metadata)
- ✅ Versioning and timestamps

---

## Critical Path to Target Schema

### Phase 1: Identity (Week 1) - BLOCKING
```python
# Generate UUIDs for all documents
for doc in all_documents:
    doc['document_id'] = str(uuid.uuid4())
    doc['legacy_ids'] = {
        'hash': doc['id'],
        'bates': lookup_bates_number(doc['id']),
        'file_path': doc['path']
    }
```

### Phase 2: Temporal (Week 2) - CRITICAL
```python
# Extract dates from content
for doc in all_documents:
    if doc['classification'] == 'email':
        doc['date'] = extract_email_date(doc)
    elif doc['classification'] == 'court_filing':
        doc['date'] = extract_filing_date(doc)
    else:
        doc['date'] = infer_date_from_content(doc)
```

### Phase 3: Classification (Week 3) - HIGH PRIORITY
```python
# Refine document types
for doc in all_documents:
    if doc['classification'] == 'government_document':
        # Reclassify to specific subtype
        doc['document_type'] = classify_government_doc(doc)
        doc['document_subtypes'] = extract_subtypes(doc)
```

### Phase 4: Entity Integration (Week 4) - HIGH PRIORITY
```python
# Link entities using UUIDs
for doc in all_documents:
    bates = doc['legacy_ids']['bates']
    entity_names = document_entity_index[bates]
    doc['extracted_entities'] = [
        get_entity_object(name) for name in entity_names
    ]
```

### Phase 5: Consolidation (Week 5) - CLEANUP
```python
# Merge fragmented data
for doc in all_documents:
    # Add summary from master_index
    doc['metadata']['summary'] = master_index[doc['legacy_ids']['hash']]['summary']
    
    # Add type-specific metadata
    if doc['document_type'] == 'email':
        doc['metadata']['email'] = get_email_metadata(doc)
    elif doc['document_type'] == 'court_record':
        doc['metadata']['court'] = get_court_metadata(doc)
```

---

## Next Steps

1. **Approve target schema v3.0** (with stakeholders)
2. **Begin Phase 1**: UUID generation (estimated: 2-3 days)
3. **Update API endpoints** to support both hash and UUID lookups during migration
4. **Implement backward compatibility** layer for legacy hash-based queries
5. **Track progress** in Linear Issue #12

---

*Generated: 2025-12-06*
*Related: docs/audit/document-schema-analysis.md*
