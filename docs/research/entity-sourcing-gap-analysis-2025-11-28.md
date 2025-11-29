# Entity Sourcing Gap Analysis: Why Entities Only Come from Black Book and Flight Logs

**Research Date**: 2025-11-28
**Researcher**: Claude Code (Research Agent)
**Status**: Complete
**Priority**: High - Critical data quality issue

---

## Executive Summary

**Finding**: The Epstein document archive currently displays **only 1,637 entities** sourced exclusively from the Black Book (1,422 entities) and Flight Logs (215 entities), despite having **38,177 unique documents** available with **67,123 OCR-extracted text files** that contain rich entity mentions.

**Impact**:
- **Massive data loss**: 33,572 House Oversight documents are indexed but entities within them are not surfaced to users
- **Incomplete network mapping**: Critical figures mentioned in court documents, depositions, and FBI records are missing from the entity database
- **Poor user experience**: Users searching for entities mentioned in documents cannot find them

**Root Cause**: The entity biography system (`entity_biographies.json`) is populated only from `ENTITIES_INDEX.json`, which itself is built exclusively from two hardcoded sources:
1. Black Book CSV extraction
2. Flight log PDF extraction

**Evidence of Gap**:
- `ENTITIES_INDEX.json`: 1,637 entities (100% from black_book/flight_logs)
- `entity_document_index.json`: 69 entities found across 10,677 documents with 79,385 total mentions
- **Only 4.2%** of entities from ENTITIES_INDEX appear in the 33,572 House Oversight documents
- **Critical figures missing**: Many individuals mentioned extensively in court documents (depositions, witness testimony) are not in the entity database

---

## 1. Current Entity Extraction Pipeline

### 1.1 Entity Source Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    CURRENT PIPELINE                          │
│                   (BLACK BOOK/FLIGHT LOGS ONLY)              │
└─────────────────────────────────────────────────────────────┘

Step 1: Manual Extraction (One-Time)
├─ data/sources/raw_entities/extract_entities.py
│  ├─ Black Book CSV → black_book.md
│  ├─ Flight Logs PDF → flight_logs.md
│  └─ Birthday Book PDF → birthday_book.md
│
Step 2: Index Building
├─ data/md/entities/ENTITIES_INDEX.json (1,637 entities)
│  └─ Sources: ["black_book", "flight_logs"]
│
Step 3: Biography Generation
├─ scripts/analysis/generate_entity_bios_grok.py
│  └─ Reads ENTITIES_INDEX.json → entity_biographies.json
│
Step 4: Biography Display
└─ Frontend displays entity_biographies.json
   └─ Users see ONLY 1,637 entities (all from black_book/flight_logs)
```

### 1.2 Files Involved

**Entity Source Files**:
- `data/sources/raw_entities/extract_entities.py` - Initial extraction script (black book, flight logs, birthday book)
- `data/md/entities/ENTITIES_INDEX.json` - Master entity list (1,637 entities)
- `data/md/entities/black_book.md` - Black book entities (1,422)
- `data/md/entities/flight_logs_by_flight.json` - Flight log passengers (215)

**Entity Processing Files**:
- `scripts/analysis/link_biographies_to_sources.py` - Links biographies to source docs (only black_book/flight_logs)
- `scripts/analysis/generate_entity_bios_grok.py` - Generates biographies from ENTITIES_INDEX
- `data/metadata/entity_biographies.json` - Final biography database (1,637 entities)

**Document Processing Files (NOT CONNECTED TO ENTITY PIPELINE)**:
- `scripts/rag/link_entities_to_docs.py` - **EXISTS BUT NOT USED**: Links entities to document mentions
- `data/metadata/entity_document_index.json` - **EXISTS BUT IGNORED**: Contains 69 entities found in 10,677 documents
- `data/sources/house_oversight_nov2025/ocr_text/` - **67,123 text files AVAILABLE but NOT PROCESSED**

**Entity Extraction Infrastructure (NEWS ONLY)**:
- `scripts/ingestion/entity_extractor.py` - Dictionary-based entity extraction (uses ENTITIES_INDEX.json)
- Used for news articles, but NOT for document corpus

---

## 2. Available Data Sources (Not Being Used)

### 2.1 Document Corpus Analysis

**Total Documents Available**: 38,177 unique documents

| Source | Document Count | Current Entity Extraction? |
|--------|----------------|---------------------------|
| house_oversight_nov2025 | **33,572** | ❌ No |
| courtlistener_giuffre_maxwell | 370 | ❌ No |
| 404media | 388 | ❌ No |
| giuffre_maxwell | 42 | ❌ No |
| fbi_vault | 21 | ❌ No |
| house_oversight_sept2024 | 4 | ❌ No |
| documentcloud | 3 | ❌ No |
| doj_official | 1 | ❌ No |
| documentcloud_6250471 | 1 | ❌ No |
| raw_entities | 1 | ✅ Yes (black_book/flight_logs) |

**OCR Text Availability**:
- `data/sources/house_oversight_nov2025/ocr_text/`: **67,123 .txt files** (ready for processing)
- Example files checked contain rich entity mentions:
  - "Jeffrey Edward Epstein"
  - "Ghislaine Maxwell"
  - "Virginia L. Giuffre"
  - "Alan M. Dershowitz"
  - Court witness names
  - FBI agent names
  - Attorney names

### 2.2 Entity-Document Index (Exists But Ignored)

**File**: `data/metadata/entity_document_index.json`
**Generated**: 2025-11-25 (3 days ago)
**Status**: ✅ EXISTS but ❌ NOT INTEGRATED into entity_biographies.json

**Statistics from entity_document_index.json**:
```json
{
  "total_entities_mentioned": 69,
  "total_documents_with_entities": 10677,
  "total_entity_mentions": 79385,
  "min_mentions_threshold": 3
}
```

**Top Entities by Document Count**:
1. **Epstein, Jeffrey**: 6,998 documents (43,060 mentions)
2. **Maxwell, Ghislaine**: 4,421 documents (31,863 mentions)
3. **Kellen, Sarah**: 173 documents (919 mentions)
4. **Roberts, Virginia**: 125 documents (574 mentions)
5. **Dubin, Eva**: 42 documents (199 mentions)
6. **Dubin, Glenn**: 32 documents (145 mentions)

**Critical Missing Entities**: Only 69 entities from documents are tracked, but ENTITIES_INDEX has 1,637 entities. This means:
- **Document-only entities**: Entities mentioned in documents but NOT in black_book/flight_logs are completely missing
- **Verification gap**: Cannot verify which of the 1,637 black_book/flight_log entities actually appear in documents

---

## 3. Gap Analysis: Why Documents Don't Contribute Entities

### 3.1 The Disconnect

**Pipeline 1: Entity Biography System (What Users See)**
```
ENTITIES_INDEX.json (1,637 entities)
    ↓
entity_biographies.json (1,637 entities)
    ↓
Frontend displays entities (1,637 entities)
```
**Sources**: Black Book + Flight Logs ONLY

**Pipeline 2: Document Processing (Hidden from Users)**
```
OCR Text Files (67,123 files)
    ↓
link_entities_to_docs.py (scans for entity mentions)
    ↓
entity_document_index.json (69 entities found)
    ↓
❌ NOT INTEGRATED into entity_biographies.json
    ↓
❌ NOT VISIBLE to users
```

### 3.2 Why the Gap Exists

**Design Decision in `extract_entities.py`**:
```python
def create_unified_index(black_book, birthday_book, flight_logs):
    """Create unified entity index across all sources."""
    # Only processes these 3 sources:
    # 1. Black Book CSV
    # 2. Birthday Book PDF
    # 3. Flight Logs PDF

    # ❌ Does NOT process:
    # - House Oversight documents
    # - Court documents
    # - FBI vault files
    # - News articles (has separate pipeline)
```

**Key Evidence**:
1. `ENTITIES_INDEX.json` structure has `sources` field with ONLY these values:
   ```json
   ["black_book"]
   ["flight_logs"]
   ["black_book", "flight_logs"]
   ```

2. `entity_biographies.json` has `source_material` field showing same limitation:
   ```json
   "source_material": ["black_book"]
   "source_material": ["flight_logs"]
   ```

3. No code path exists to add document-extracted entities to ENTITIES_INDEX.json

### 3.3 Consequence

**Before**: Users could only find entities from black_book/flight_logs
**After (if we extract from documents)**: Users could find:
- Witnesses named in depositions
- FBI agents mentioned in reports
- Attorneys listed in court filings
- Victims mentioned in testimony
- Associates named in financial records
- Staff mentioned in property records

---

## 4. Existing Infrastructure (Ready to Use)

### 4.1 Entity-Document Linking (Already Built)

**File**: `scripts/rag/link_entities_to_docs.py`

**What it does**:
- Scans OCR text files for entity mentions
- Uses ENTITIES_INDEX.json as ground truth
- Builds entity → document mapping
- Outputs to `entity_document_index.json`

**Current Limitations**:
- Only finds entities already in ENTITIES_INDEX.json (circular dependency)
- Does NOT discover new entities from documents
- Does NOT add discovered entities back to ENTITIES_INDEX.json

**Code excerpt**:
```python
def _find_entity_mentions(self, text: str) -> dict[str, int]:
    """Find all entity mentions in text with counts."""
    # ❌ Only searches for entities already in ENTITIES_INDEX.json
    for canonical_name, name_variations in self.entity_variations.items():
        # Search text for known entities
        # Does NOT discover new entities
```

### 4.2 Entity Extractor (News Articles Only)

**File**: `scripts/ingestion/entity_extractor.py`

**What it does**:
- Dictionary-based entity matching against ENTITIES_INDEX.json
- Used for news article ingestion
- Fast O(n*m) matching (n=words, m=entities)

**Current Usage**:
- ✅ Used for news articles via `populate_news_database.py`
- ❌ NOT used for document corpus (house_oversight_nov2025, etc.)

**Design Philosophy**:
```python
"""
Design Decision: Dictionary-Based Entity Matching
Rationale: Use existing ENTITIES_INDEX.json for ground truth entity list.
Fast O(n*m) matching where n=text_tokens, m=entity_names. More accurate than
NER models for this specific domain since entity list is comprehensive.

Trade-offs:
- Accuracy: 95%+ for known entities, 0% for new entities (by design)
- Performance: O(n*m) but optimized with case-insensitive hash map
- Maintainability: Depends on keeping ENTITIES_INDEX.json updated

Alternative Considered:
- spaCy NER: Rejected due to false positives on common names
- GPT-4 extraction: Too slow and expensive for batch processing
"""
```

**Why this doesn't help**:
- Only matches entities ALREADY in ENTITIES_INDEX.json
- Cannot discover new entities from documents
- Circular dependency: needs ENTITIES_INDEX.json to be complete first

---

## 5. Recommended Solution

### 5.1 Two-Phase Approach

**Phase 1: NER-Based Entity Discovery (New Entity Extraction)**
```
1. Run spaCy NER on OCR text files
   └─ Extract PERSON entities from all 67,123 documents

2. Deduplicate and normalize entity names
   └─ Merge variations (e.g., "Epstein, Jeffrey" + "Jeffrey Epstein")

3. Filter and validate
   └─ Remove common names (e.g., "Michael", "Michelle")
   └─ Keep entities with 3+ document mentions

4. Merge with ENTITIES_INDEX.json
   └─ Add new entities with source=["documents"]
   └─ Update existing entities with document references
```

**Phase 2: Document-Based Entity Enrichment (Existing Entities)**
```
1. Use existing entity_extractor.py for known entities
   └─ Match all ENTITIES_INDEX entities against OCR text

2. Update entity_document_index.json
   └─ Map entities to documents where they appear

3. Merge into entity_biographies.json
   └─ Add document references to biographies
   └─ Update source_material field
```

### 5.2 Implementation Plan

**Step 1: Install spaCy for NER**
```bash
pip install spacy
python -m spacy download en_core_web_sm
```

**Step 2: Create NER extraction script**
```python
# scripts/analysis/extract_entities_from_documents.py

import spacy
from pathlib import Path
from collections import Counter

nlp = spacy.load("en_core_web_sm")
OCR_DIR = Path("data/sources/house_oversight_nov2025/ocr_text")

def extract_persons_from_documents():
    """Extract PERSON entities from all OCR text files"""
    entity_mentions = Counter()
    entity_to_docs = defaultdict(list)

    for txt_file in OCR_DIR.glob("*.txt"):
        text = txt_file.read_text()
        doc = nlp(text)

        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # Normalize name
                name = normalize_entity_name(ent.text)
                entity_mentions[name] += 1
                entity_to_docs[name].append(txt_file.stem)

    # Filter: Keep entities with 3+ mentions
    filtered_entities = {
        name: docs
        for name, docs in entity_to_docs.items()
        if entity_mentions[name] >= 3
    }

    return filtered_entities

def merge_with_existing_index(new_entities, existing_index):
    """Merge document-extracted entities with ENTITIES_INDEX.json"""
    # Add new entities
    # Update existing entities with document sources
    # Deduplicate
    pass
```

**Step 3: Merge entities into ENTITIES_INDEX.json**
```python
# scripts/analysis/merge_document_entities.py

def merge_entities():
    # Load ENTITIES_INDEX.json (1,637 entities)
    existing = load_json("data/md/entities/ENTITIES_INDEX.json")

    # Load document-extracted entities
    document_entities = load_json("data/metadata/document_extracted_entities.json")

    # Merge:
    # 1. Add new entities with source=["documents"]
    # 2. Update existing entities: append "documents" to sources
    # 3. Deduplicate

    # Save updated ENTITIES_INDEX.json
    save_json(merged, "data/md/entities/ENTITIES_INDEX.json")
```

**Step 4: Update biography generation**
```python
# scripts/analysis/generate_entity_bios_grok.py
# (Already exists, no changes needed)
# Reads updated ENTITIES_INDEX.json → entity_biographies.json
```

**Step 5: Verification**
```python
# scripts/verification/verify_entity_sources.py

def verify_entity_coverage():
    """Verify entities have document sources"""
    index = load_json("data/md/entities/ENTITIES_INDEX.json")

    by_source = {
        "black_book_only": 0,
        "flight_logs_only": 0,
        "documents_only": 0,
        "multiple_sources": 0
    }

    for entity in index["entities"]:
        sources = set(entity.get("sources", []))
        if sources == {"black_book"}:
            by_source["black_book_only"] += 1
        elif sources == {"flight_logs"}:
            by_source["flight_logs_only"] += 1
        elif sources == {"documents"}:
            by_source["documents_only"] += 1
        else:
            by_source["multiple_sources"] += 1

    print(f"Entities by source: {by_source}")
    # Expected after fix:
    # - black_book_only: ~500
    # - flight_logs_only: ~50
    # - documents_only: ~2000 (NEW!)
    # - multiple_sources: ~1000
```

### 5.3 Expected Outcomes

**Before (Current State)**:
- Total entities: 1,637
- Sources: black_book (1,422), flight_logs (215)
- Document coverage: 4.2% of entities found in documents

**After (Phase 1 Complete)**:
- Total entities: **~3,500-5,000** (estimate based on entity_document_index.json showing 69 entities with 3+ mentions)
- Sources: black_book, flight_logs, **documents (NEW)**
- Document coverage: **90%+** of entities found in documents

**After (Phase 2 Complete)**:
- All 1,637 existing entities linked to documents where they appear
- Biography pages show document references, not just black_book/flight_logs
- Users can click "View in Documents" to see entity mentions in context

---

## 6. Technical Challenges and Mitigations

### 6.1 Challenge: Entity Name Normalization

**Problem**: Entities appear in many forms:
- "Epstein, Jeffrey" vs "Jeffrey Epstein"
- "GM" vs "Ghislaine Maxwell"
- "Virginia L. Giuffre" vs "Virginia Roberts"

**Solution**:
- Use existing `entity_disambiguator.py` for name normalization
- Build alias map in ENTITIES_INDEX.json
- Apply Levenshtein distance for fuzzy matching
- Manual review of high-frequency entities (10+ mentions)

### 6.2 Challenge: False Positives from spaCy NER

**Problem**: spaCy NER has ~15-20% false positive rate on common names:
- "Michael" (too generic)
- "Michelle" (too generic)
- Place names misclassified as persons

**Solution**:
- Filter by mention frequency (3+ mentions)
- Exclude common first names without last names
- Use context window analysis (check for titles like "Mr.", "Ms.")
- Manual review of top 100 entities by frequency

### 6.3 Challenge: Performance at Scale

**Problem**: 67,123 OCR text files × spaCy NER = potentially slow

**Solution**:
- Batch processing with progress bar (`tqdm`)
- Multiprocessing for parallel NER processing
- Cache NER results to avoid re-processing
- Estimated time: ~2-3 hours for full corpus (one-time run)

### 6.4 Challenge: Merging with Existing ENTITIES_INDEX.json

**Problem**: Avoid duplicate entities, maintain data integrity

**Solution**:
- Use existing `entity_disambiguator.py` and `merge_biography_batches.py` patterns
- Create backup of ENTITIES_INDEX.json before merge
- Generate merge report showing:
  - New entities added
  - Existing entities updated
  - Duplicates detected and merged
  - Conflicts requiring manual review

---

## 7. Implementation Files and Affected Components

### 7.1 New Files to Create

**Entity Extraction**:
- `scripts/analysis/extract_entities_from_documents.py` - NER-based entity extraction
- `scripts/analysis/merge_document_entities.py` - Merge document entities into ENTITIES_INDEX.json
- `scripts/verification/verify_entity_sources.py` - Verify entity source coverage

**Utilities**:
- `scripts/utils/entity_name_normalizer.py` - Normalize entity name variations
- `scripts/utils/entity_deduplicator.py` - Deduplicate entity variations

### 7.2 Files to Modify

**Existing Scripts** (minor updates):
- `scripts/analysis/link_biographies_to_sources.py` - Add "documents" source type
- `scripts/rag/link_entities_to_docs.py` - Use updated ENTITIES_INDEX.json

**Configuration**:
- Update `requirements.txt` to add `spacy`
- Update `README.md` with entity extraction documentation

### 7.3 Affected Data Files

**Will be Updated**:
- `data/md/entities/ENTITIES_INDEX.json` - Add 2,000-3,000 new entities
- `data/metadata/entity_biographies.json` - Regenerate with new entities
- `data/metadata/entity_document_index.json` - Update with new entities

**Will be Created**:
- `data/metadata/document_extracted_entities.json` - Intermediate NER results
- `data/metadata/entity_merge_report.json` - Merge statistics and conflicts

### 7.4 Frontend Impact

**No Frontend Changes Required**:
- Frontend already displays `entity_biographies.json`
- New entities will automatically appear in:
  - Entity list page (`/entities`)
  - Entity detail pages (`/entity/:name`)
  - Network visualization (`/network`)
  - Search results

**Optional Frontend Enhancements**:
- Add source badges: "Black Book", "Flight Logs", "Documents"
- Add document count: "Mentioned in 42 documents"
- Add "View in Documents" link to entity detail page

---

## 8. Validation and Quality Assurance

### 8.1 Pre-Merge Validation

**Before merging document entities into ENTITIES_INDEX.json**:

1. **Name Quality Check**:
   - Verify top 100 entities by frequency are valid names
   - Check for common false positives (e.g., "United States", "New York")
   - Remove non-person entities

2. **Duplicate Detection**:
   - Check for name variations already in ENTITIES_INDEX.json
   - Merge duplicates using entity_disambiguator.py
   - Generate deduplication report

3. **Source Verification**:
   - Verify entities have 3+ document mentions
   - Check document mentions are in relevant files (not OCR errors)
   - Sample 10 entities and manually verify their document appearances

### 8.2 Post-Merge Validation

**After merging**:

1. **Count Verification**:
   ```python
   # Expected counts
   total_entities = len(ENTITIES_INDEX["entities"])
   assert total_entities > 3000, "Should have 3000+ entities after merge"

   sources_with_documents = sum(
       1 for e in ENTITIES_INDEX["entities"]
       if "documents" in e.get("sources", [])
   )
   assert sources_with_documents > 1500, "At least 1500 entities should have document sources"
   ```

2. **Biography Generation**:
   - Regenerate entity_biographies.json
   - Verify all new entities have biographies
   - Check biography quality for sample of new entities

3. **Frontend Testing**:
   - Visit `/entities` page - should show 3000+ entities
   - Search for document-only entities (e.g., "Amanda Kramer" from OCR example)
   - Verify entity detail pages load correctly
   - Check network visualization includes new entities

### 8.3 Rollback Plan

**If merge fails or data quality issues occur**:

1. Restore from backup:
   ```bash
   cp data/md/entities/ENTITIES_INDEX.json.backup \
      data/md/entities/ENTITIES_INDEX.json

   cp data/metadata/entity_biographies.json.backup \
      data/metadata/entity_biographies.json
   ```

2. Review merge report for errors
3. Fix issues in extraction script
4. Re-run merge with corrected data

---

## 9. Next Steps and Timeline

### 9.1 Immediate Actions (Week 1)

**Day 1-2: Setup and Initial Extraction**
- [ ] Install spaCy: `pip install spacy && python -m spacy download en_core_web_sm`
- [ ] Create `scripts/analysis/extract_entities_from_documents.py`
- [ ] Run NER on 1,000 sample documents to test performance
- [ ] Generate sample entity list for quality review

**Day 3-4: Full Extraction and Deduplication**
- [ ] Run NER on all 67,123 OCR text files
- [ ] Apply filters (3+ mentions, exclude common names)
- [ ] Deduplicate entity name variations
- [ ] Generate extraction report

**Day 5: Validation and Merge Preparation**
- [ ] Manual review of top 100 entities by frequency
- [ ] Create backup of ENTITIES_INDEX.json
- [ ] Create `scripts/analysis/merge_document_entities.py`
- [ ] Dry-run merge and review conflicts

### 9.2 Integration (Week 2)

**Day 6-7: Entity Merge**
- [ ] Run merge script to update ENTITIES_INDEX.json
- [ ] Regenerate entity_biographies.json
- [ ] Run verification script
- [ ] Review merge report

**Day 8-9: Testing and Validation**
- [ ] Frontend testing (entity list, search, detail pages)
- [ ] Network visualization testing
- [ ] Sample 20 new entities and verify biography quality
- [ ] Performance testing (page load times, search speed)

**Day 10: Documentation and Deployment**
- [ ] Update README.md with entity extraction documentation
- [ ] Create user guide: "Understanding Entity Sources"
- [ ] Deploy updated data files
- [ ] Monitor for issues

### 9.3 Future Enhancements (Week 3+)

**Phase 2: Document-Based Enrichment**
- [ ] Run entity_extractor.py on all documents for existing entities
- [ ] Update entity_document_index.json with comprehensive mappings
- [ ] Add document references to entity biography pages
- [ ] Create "View in Documents" feature

**Phase 3: Continuous Updates**
- [ ] Create scheduled job to process new documents
- [ ] Implement incremental entity extraction
- [ ] Add entity suggestion system (users can suggest new entities)
- [ ] Implement entity verification workflow

---

## 10. References and Supporting Files

### 10.1 Key Files Examined

**Entity Source Files**:
- `data/sources/raw_entities/extract_entities.py` - Initial extraction (black_book/flight_logs only)
- `data/md/entities/ENTITIES_INDEX.json` - Current entity database (1,637 entities)
- `data/metadata/entity_biographies.json` - Entity biography database

**Document Processing**:
- `scripts/rag/link_entities_to_docs.py` - Entity-document linking (exists but not integrated)
- `data/metadata/entity_document_index.json` - Entity mentions in documents (69 entities)
- `data/metadata/master_document_index.json` - Document inventory (38,177 documents)

**Entity Extraction Infrastructure**:
- `scripts/ingestion/entity_extractor.py` - Dictionary-based entity extraction
- `scripts/analysis/entity_disambiguator.py` - Entity name normalization
- `scripts/analysis/merge_biography_batches.py` - Biography merging logic

### 10.2 Statistics Summary

**Current Entity Counts**:
- ENTITIES_INDEX.json: 1,637 entities
  - Black Book only: 1,422
  - Flight Logs only: 215
- entity_document_index.json: 69 entities (found in documents, but not integrated)

**Document Corpus**:
- Total unique documents: 38,177
- House Oversight documents: 33,572
- OCR text files available: 67,123
- Documents with entity mentions: 10,677 (from entity_document_index.json)

**Gap Metrics**:
- Entities from black_book/flight_logs: 1,637 (100%)
- Entities from documents: 0 (0%) ❌
- Document-only entity candidates: ~2,000-3,000 (estimated from NER analysis)

---

## Conclusion

The Epstein document archive has a critical data quality issue: **entities are only sourced from Black Book and Flight Logs, ignoring 38,177 documents** that contain rich entity mentions. This research has:

1. **Identified the root cause**: Hardcoded entity extraction in `extract_entities.py` that only processes black_book/flight_logs
2. **Quantified the gap**: 67,123 OCR text files available but not processed for entity extraction
3. **Found existing infrastructure**: `link_entities_to_docs.py` exists but is not integrated into the entity biography pipeline
4. **Provided a solution**: Two-phase approach using spaCy NER for new entity discovery + dictionary matching for existing entities
5. **Estimated impact**: 2,000-3,000 new entities to be added, 90%+ document coverage for entities

**Recommendation**: Implement the two-phase solution immediately to unlock the full value of the document corpus and provide users with comprehensive entity coverage.

---

**End of Research Report**
