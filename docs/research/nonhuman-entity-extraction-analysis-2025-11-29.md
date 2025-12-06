# Non-Human Entity Extraction Analysis

**Date:** November 29, 2025
**Ticket:** 1M-410 - Extract non-human entities (organizations, locations) from documents
**Status:** Dry-run completed, ready for production extraction
**Script:** `scripts/analysis/extract_nonhuman_entities.py`

## Executive Summary

Successfully completed dry-run extraction of non-human entities (organizations and locations) from the Epstein archive documents using spaCy NER. The script processed **33,561 documents** and identified **920 organizations** and **458 locations** that meet the minimum mention threshold of 10 occurrences.

## Current Status

**Extraction Files Status:**
- `data/metadata/entity_organizations.json` - **NOT EXISTS** (extraction not yet run)
- `data/metadata/entity_locations.json` - **NOT EXISTS** (extraction not yet run)

**Script Status:**
- ✅ Script tested and working correctly
- ✅ spaCy dependencies installed (en_core_web_lg model)
- ✅ Dry-run completed successfully with --min-mentions 10

## Dry-Run Results (--min-mentions 10)

### Document Processing
- **Documents processed:** 33,561 text files
- **Processing time:** ~21 minutes (21:19.3)
- **Average speed:** ~26 documents/second

### Entity Statistics

**Before filtering (raw spaCy NER output):**
- Organizations: **78,158** mentions
- Locations: **54,481** mentions

**After filtering (>= 10 mentions):**
- Organizations: **920** entities
- Locations: **458** entities

**Filtering efficiency:**
- Organizations: 98.8% reduction (78,158 → 920)
- Locations: 99.2% reduction (54,481 → 458)

### Top 10 Organizations

| Rank | Organization | Mentions | Notes |
|------|-------------|----------|-------|
| 1 | Government | 3,116 | Generic term, may need refinement |
| 2 | Ghislaine Maxwell | 2,743 | Person, not organization (NER misclassification) |
| 3 | PQH API | 864 | Unknown acronym |
| 4 | Department | 771 | Generic term, may need filtering |
| 5 | NYM Housing Units Housing Units | 751 | Possible duplicate text issue |
| 6 | Villafafia | 721 | Unknown entity type |
| 7 | the Second Circuit | 719 | Legal entity (court) |
| 8 | MCC New York | 538 | Metropolitan Correctional Center |
| 9 | Samsung Galaxy | 527 | Technology brand |
| 10 | District Court | 490 | Legal entity (court) |

**Quality Issues Identified:**
1. **Person misclassified as Organization**: "Ghislaine Maxwell" (should be filtered)
2. **Generic terms**: "Government", "Department" (may need context-based filtering)
3. **Duplicate text**: "NYM Housing Units Housing Units"
4. **Technology brands**: "Samsung Galaxy" (device, not organization)

### Top 10 Locations

| Rank | Location | Mentions | Notes |
|------|---------|----------|-------|
| 1 | United States | 10,394 | Valid |
| 2 | New York | 9,584 | Valid |
| 3 | SOUTHERN DISTRICT | 4,930 | Legal district reference |
| 4 | U.S. | 4,344 | Duplicate of "United States" |
| 5 | NPA | 4,321 | Non-Prosecution Agreement (not a location) |
| 6 | Florida | 2,842 | Valid |
| 7 | the United States | 2,134 | Duplicate of "United States" |
| 8 | Palm Beach | 1,772 | Valid |
| 9 | USA | 1,570 | Duplicate of "United States" |
| 10 | New Mexico | 1,250 | Valid |

**Quality Issues Identified:**
1. **Duplicates**: "United States" / "U.S." / "the United States" / "USA" (need deduplication)
2. **Misclassified**: "NPA" (Non-Prosecution Agreement, not a location)
3. **Legal entities**: "SOUTHERN DISTRICT" (reference to legal jurisdiction)

## Quality Assessment

### Strengths
- ✅ High-frequency entities are mostly relevant (courts, locations, organizations)
- ✅ Captures important legal entities (courts, districts)
- ✅ Geographic locations are well-identified
- ✅ Filtering by mentions (10+) effectively reduces noise

### Issues to Address

**1. Entity Type Misclassification**
- Persons classified as organizations (e.g., "Ghislaine Maxwell")
- Acronyms misclassified as locations (e.g., "NPA" = Non-Prosecution Agreement)
- **Impact:** Medium - Can be filtered post-extraction

**2. Duplicate Entities**
- Multiple variants of "United States" (U.S., USA, the United States)
- Duplicate text patterns ("NYM Housing Units Housing Units")
- **Impact:** Medium - Affects mention counts and data quality

**3. Generic Terms**
- "Government", "Department" lack specificity
- Context would help disambiguate
- **Impact:** Low - Can be filtered or kept for analysis

**4. Technical/Product Names**
- "Samsung Galaxy" (device, not organization)
- **Impact:** Low - Minor noise in organization data

## Recommendations

### Recommended Parameters for Production Extraction

**Option 1: Conservative (Recommended)**
```bash
python scripts/analysis/extract_nonhuman_entities.py --min-mentions 15
```
- **Reasoning:** Increases quality by focusing on frequently mentioned entities
- **Expected output:** ~600-700 organizations, ~300-350 locations
- **Pros:** Higher quality, less noise
- **Cons:** May miss some legitimate but less-mentioned entities

**Option 2: Balanced (Current)**
```bash
python scripts/analysis/extract_nonhuman_entities.py --min-mentions 10
```
- **Reasoning:** Good balance between coverage and quality
- **Expected output:** 920 organizations, 458 locations
- **Pros:** Comprehensive coverage
- **Cons:** Requires post-processing to remove noise

**Option 3: Comprehensive**
```bash
python scripts/analysis/extract_nonhuman_entities.py --min-mentions 5
```
- **Reasoning:** Maximum coverage of entities
- **Expected output:** ~1,500-2,000 organizations, ~800-1,000 locations
- **Pros:** Captures rare but relevant entities
- **Cons:** Significantly more noise, requires extensive post-processing

### Post-Processing Improvements Needed

**1. Person Name Filtering**
- Cross-reference with `entity_biographies.json` to filter known persons
- Use additional NER models to verify organization classification
- **Implementation:** Filter out entities that exist in person entity database

**2. Deduplication Strategy**
- Normalize entity names (lowercase, remove articles "the")
- Merge variants: "United States" = "U.S." = "USA" = "the United States"
- Use fuzzy matching (Levenshtein distance) for similar names
- **Implementation:** Add normalization step after extraction

**3. Generic Term Filtering**
- Create blocklist: ["Government", "Department", "Agency"] (standalone)
- Allow these terms when part of longer names: "Department of Justice" ✓
- **Implementation:** Add filter for single-word generic terms

**4. Acronym Classification Improvement**
- Build acronym dictionary: {"NPA": "legal_term", "FBI": "organization"}
- Use context to disambiguate
- **Implementation:** Add acronym resolver with context analysis

### Production Extraction Plan

**Phase 1: Initial Extraction (Now)**
1. Run with `--min-mentions 10` (balanced approach)
2. Save to `entity_organizations.json` and `entity_locations.json`
3. Generate placeholder biographies from document contexts

**Phase 2: Post-Processing (Next)**
1. Filter persons from organizations (cross-reference with entity_biographies.json)
2. Deduplicate entities (merge variants of "United States", etc.)
3. Filter generic terms
4. Classify acronyms properly

**Phase 3: Biography Generation (Later)**
1. Use LLM (OpenRouter) to generate biographies from document contexts
2. Similar to person entity biography generation
3. Include entity type, mention frequency, key documents

**Phase 4: Integration (Final)**
1. Merge with person entities in unified entity system
2. Update entity_classifications.json with organization/location types
3. Rebuild entity_network.json to include non-human entities

## Script Analysis

### Script Capabilities

**Current Features:**
- ✅ spaCy NER extraction (ORG, GPE, LOC labels)
- ✅ Frequency-based filtering (--min-mentions)
- ✅ Context extraction (200 characters around mention)
- ✅ Document source tracking
- ✅ Deduplication by normalized name
- ✅ Dry-run mode for testing
- ✅ Statistics reporting

**Limitations:**
- ⚠️ No person name filtering
- ⚠️ No entity variant merging
- ⚠️ Placeholder biographies only (no LLM generation yet)
- ⚠️ No acronym disambiguation
- ⚠️ No generic term filtering

### Script Parameters

**Available Options:**
- `--entity-type {org,location,all}` - Type of entities to extract (default: all)
- `--min-mentions N` - Minimum mentions required (default: 5)
- `--dry-run` - Test without writing files
- `--data-dir PATH` - Data directory path

**Usage Examples:**
```bash
# Dry-run with min 10 mentions (completed)
python scripts/analysis/extract_nonhuman_entities.py --min-mentions 10 --dry-run

# Production extraction with recommended settings
python scripts/analysis/extract_nonhuman_entities.py --min-mentions 10

# Organizations only with higher threshold
python scripts/analysis/extract_nonhuman_entities.py --entity-type org --min-mentions 15

# Locations only
python scripts/analysis/extract_nonhuman_entities.py --entity-type location --min-mentions 10
```

## Data Quality by Threshold

### Estimated Quality at Different Thresholds

| Threshold | Organizations | Locations | Quality | Coverage | Recommendation |
|-----------|--------------|-----------|---------|----------|----------------|
| 5 mentions | ~1,800 | ~900 | Medium | Comprehensive | If you need maximum coverage |
| 10 mentions | **920** | **458** | Good | Balanced | **✅ Recommended** |
| 15 mentions | ~650 | ~320 | High | Focused | If you prioritize quality |
| 20 mentions | ~500 | ~250 | Very High | Core entities | If you want minimal noise |

**Reasoning for 10 mentions threshold:**
- Balances quality and coverage
- Captures key entities (courts, locations, organizations)
- Manageable post-processing workload
- Includes legitimate but less-frequent entities
- Dry-run shows acceptable quality at this level

## Issues and Concerns

### Known Issues

**1. NER Misclassification (spaCy limitation)**
- **Issue:** Persons labeled as organizations (e.g., "Ghislaine Maxwell")
- **Impact:** Medium - Pollutes organization data
- **Solution:** Post-processing filter using entity_biographies.json

**2. Duplicate Variants**
- **Issue:** "United States" appears as multiple variants
- **Impact:** Medium - Inflates mention counts, creates duplicate entries
- **Solution:** Entity normalization and merging

**3. Generic Terms**
- **Issue:** "Government", "Department" are too vague
- **Impact:** Low - Can be filtered or kept for context
- **Solution:** Filter standalone generic terms, keep compound names

**4. Context Quality**
- **Issue:** 200-character context may not always provide clear meaning
- **Impact:** Low - Affects biography quality
- **Solution:** Increase context window or use LLM for summarization

### Risks

**1. Processing Time**
- **Risk:** Production extraction takes ~20-25 minutes
- **Mitigation:** Run as background job, provide progress updates

**2. Memory Usage**
- **Risk:** Large document corpus may cause memory issues
- **Mitigation:** Script already limits spaCy processing to first 100k chars per document

**3. Data Quality**
- **Risk:** Extracted entities may require significant manual review
- **Mitigation:** Start with higher threshold (15 mentions), post-process rigorously

## Next Steps

### Immediate Actions

1. **Run Production Extraction**
   ```bash
   python scripts/analysis/extract_nonhuman_entities.py --min-mentions 10
   ```
   - Creates `entity_organizations.json` and `entity_locations.json`
   - Time estimate: ~25 minutes

2. **Review Top Entities**
   - Manually inspect top 50 organizations and locations
   - Identify blocklist candidates (generic terms, misclassifications)
   - Document entity variants for deduplication

3. **Post-Processing Implementation**
   - Create `scripts/analysis/filter_nonhuman_entities.py`
   - Implement person name filter
   - Implement entity deduplication
   - Implement generic term filter

### Future Enhancements

1. **LLM Biography Generation**
   - Use OpenRouter API (like person entity biographies)
   - Generate entity summaries from document contexts
   - Include entity type, key relationships, important documents

2. **Entity Relationship Extraction**
   - Extract relationships between organizations and locations
   - Link to person entities (e.g., "Person X worked at Organization Y")
   - Build comprehensive entity network

3. **Acronym Resolution**
   - Build acronym dictionary from documents
   - Use context to disambiguate
   - Link acronyms to full entity names

4. **Entity Classification**
   - Classify organizations by type: legal, government, corporate, NGO
   - Classify locations by type: country, state, city, address
   - Add to entity_classifications.json

## Conclusion

The non-human entity extraction script is **working correctly** and ready for production use. The dry-run results show:

- ✅ **Quality:** Good quality entities at 10 mentions threshold
- ✅ **Coverage:** Comprehensive coverage (920 orgs, 458 locs)
- ✅ **Performance:** Acceptable processing time (~25 minutes)
- ⚠️ **Post-processing needed:** Person filtering, deduplication, generic term filtering

**Recommendation:** Proceed with production extraction using **--min-mentions 10**, followed by post-processing to improve data quality.

**Estimated Timeline:**
- Production extraction: ~25 minutes
- Post-processing script: 2-3 hours development
- Manual review: 1-2 hours
- Biography generation: 4-6 hours (with LLM)
- Total: ~1-2 days for complete implementation

## Appendices

### A. File Locations

**Script:**
- `/Users/masa/Projects/epstein/scripts/analysis/extract_nonhuman_entities.py`

**Output Files (after production run):**
- `/Users/masa/Projects/epstein/data/metadata/entity_organizations.json`
- `/Users/masa/Projects/epstein/data/metadata/entity_locations.json`

**Source Documents:**
- `/Users/masa/Projects/epstein/data/sources/house_oversight_nov2025/ocr_text/`
- `/Users/masa/Projects/epstein/data/sources/black_book/text/`
- `/Users/masa/Projects/epstein/data/sources/flight_logs/text/`

### B. Dependencies

**Required:**
- spaCy >= 3.0
- en_core_web_lg model (400MB)
- tqdm (optional, for progress bars)

**Installation:**
```bash
pip install spacy
python -m spacy download en_core_web_lg
pip install tqdm  # optional
```

### C. Related Files

**Existing Entity Files:**
- `entity_biographies.json` - Person entities (for filtering)
- `entity_network.json` - Entity relationships
- `entity_classifications.json` - Entity type classifications
- `entity_statistics.json` - Entity statistics

**Integration Point:**
- New entities should merge with existing person entities
- Update entity_network to include organization/location nodes
- Update entity_classifications with new entity types

---

**Research Completed By:** Claude Code (Research Agent)
**Report Generated:** 2025-11-29 22:30 PST
**Next Review:** After production extraction and post-processing
