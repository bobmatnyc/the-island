# Relationship Gap Analysis Report

**Generated:** 2025-12-06T15:16:38.626383

## Executive Summary

This audit examines relationship completeness across documents, entities, and news articles.

### Key Findings

⚠️ **Entity naming format inconsistency** between files
⚠️ **1465 asymmetric connections** (unidirectional)
⚠️ **7,371 orphan documents** (19.2% of total)

## 1. Document-Entity Relationships

### Overview
- **Entities in document_entities_full.json:** 12,152
- **Entities in entity_document_index.json:** 157
- **Documents in document_entities_full.json:** 31,111
- **Documents in entity_document_index.json:** 10,724

### Document Coverage Overlap
- **Common documents:** 10,636
- **Only in document_entities_full:** 20,475
- **Only in entity_document_index:** 88

### Critical Issue: Entity Naming Format Mismatch
⚠️ **WARNING:** The two files use different entity naming formats:

- `document_entities_full.json`: Uses lowercase normalized names (e.g., `colorado`, `nicole simmons`)
- `entity_document_index.json`: Uses "Last, First" format (e.g., `Maxwell, Ghislaine`)

**Impact:** Cannot directly compare entity lists due to format differences. Need entity name mapping.

## 2. Entity-Entity Connections

- **Network nodes:** 255
- **Network edges:** 1,482
- **Symmetric connections:** 2
- **Asymmetric connections:** 1,465
- **Enhanced relationships:** 2,228
- **Relationships with metadata:** 2,228

### Connection Sources
- **flight_log:** 1,482 edges

### Asymmetric Connections Analysis
**98.9%** of connections are unidirectional (asymmetric).

**Expected behavior:** For co-occurrence networks (e.g., appearing together in flight logs), connections should typically be symmetric (if A appears with B, then B appears with A).

**Recommendation:** Review if asymmetric connections are intentional or indicate data issues.

## 3. News-Entity Relationships

- **Total news articles:** 262
- **Articles with entity links:** 262
- **Coverage:** 100.0%
- **Unique entities mentioned:** 144
- **Total entity mentions:** 946
- **Orphan news articles:** 0

✅ **COMPLETE:** All news articles have entity links

## 4. Document Coverage

- **Total documents:** 38,482
- **Documents with entities:** 31,111
- **Orphan documents:** 7,371
- **Coverage:** 80.8%

⚠️ **GAP:** 7,371 documents have no entity extractions

## 5. Identified Gaps Summary

### P0 - Critical: Entity naming format mismatch
- **Impact:** Cannot reconcile entity references across files
- **Recommendation:** Create entity_name_mappings.json to map between formats

### P1 - High: 7,371 orphan documents
- **Impact:** 19.2% of documents lack entity extraction
- **Recommendation:** Run entity extraction on missing documents

### P2 - Medium: 1,465 asymmetric connections
- **Impact:** Network analysis may be incomplete or biased
- **Recommendation:** Review and symmetrize co-occurrence connections

## 6. Target Relationship Model

```
DOCUMENT ↔ ENTITIES (Bidirectional)
├─ Forward: document_entities_full.json
│  └─ entities.{entity}.document_sources[]
└─ Reverse: entity_document_index.json
   └─ entity_to_documents.{entity}.documents[]

ENTITY ↔ ENTITY (Bidirectional)
├─ Network: entity_network.json
│  ├─ nodes[]: {id, name, connection_count}
│  └─ edges[]: {source, target, weight, contexts[]}
└─ Enhanced: entity_relationships_enhanced.json
   └─ relationships[]: {entity_a, entity_b, type, metadata}

NEWS ↔ ENTITIES (Bidirectional)
├─ Forward: news_articles_index.json
│  └─ articles[].entities_mentioned[]
└─ Reverse: (MISSING - should track in entity_document_index)

CONNECTION METADATA (Target)
├─ source: document_id or "flight_log" or "news:{article_id}"
├─ weight: co-occurrence count
├─ contexts: ["flight_log", "legal_doc", "news"]
├─ dates: when connection observed
└─ type: relationship type (business, personal, legal, etc.)
```

## 7. Action Items

### Immediate (P0)
1. **Create entity name mapping file** (`entity_name_mappings.json`)
   - Map between normalized names and "Last, First" format
   - Enable cross-file entity reconciliation

### High Priority (P1)
1. **Process orphan documents** - Extract entities from remaining documents
2. **Add news articles to entity_document_index** - Track news as document sources

### Medium Priority (P2)
1. **Review asymmetric connections** - Determine if intentional or error
2. **Add connection metadata** - Track source, dates, relationship types
3. **Enhance relationship tracking** - Add bidirectional flags and confidence scores

### Low Priority (P3)
1. **Standardize entity naming** - Choose single format across all files
2. **Add connection strength metrics** - Beyond simple co-occurrence counts
3. **Implement relationship ontology** - Classify connection types

---
*End of Report*
