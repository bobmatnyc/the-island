# News Canonical Schema Implementation

**Issue:** #17 - "News: Define canonical schema"
**Date:** 2025-12-06
**Status:** ✅ Complete

## Overview

Implemented canonical schema for news articles with deterministic UUID5 generation from source URLs and entity UUID linking.

## Architecture Decision

**News articles are DISTINCT from authoritative source documents:**
- News provides supplementary, non-authoritative information
- Tracks case progression and public narrative
- Links to entities but doesn't define them
- Clearly distinguishable from source documents in schema and storage

## Files Created

### 1. Schema Definition
**File:** `data/schemas/news_schema.json`

Defines canonical structure for news articles:
- **news_id**: UUID5 generated from source_url (deterministic)
- **Entity Linking**: Uses entity UUIDs from Issue #18
- **Metadata**: Credibility, article type, archive status
- **Required Fields**: news_id, source_url, title, published_date, publication

Key fields:
```json
{
  "news_id": "uuid",
  "source_url": "uri",
  "publication": "string",
  "published_date": "date (YYYY-MM-DD)",
  "extracted_entities": ["uuid"],
  "entity_mention_counts": {"uuid": count},
  "credibility_indicator": "high|medium|low|unknown",
  "article_type": "breaking_news|investigation|opinion|...",
  "legacy_ids": {"original_id": "uuid"}
}
```

### 2. UUID Generation Script
**File:** `scripts/transformations/generate_news_uuids.py`

**Design Decision - Deterministic UUID5:**
- Generated from normalized source_url
- Uses DNS namespace (standard UUID5 approach)
- Same article URL always produces same UUID
- Enables idempotent transformations

**Features:**
- Entity name → UUID mapping using normalized names
- Zero mention count filtering (data quality fix)
- Article type classification from tags
- Credibility assessment from tier mapping
- Unmatched entity tracking

**Entity Matching:**
- Uses same normalization as entity UUID generation
- Handles aliases and canonical names
- Tracks unmatched entities for review

### 3. Transformed Data
**File:** `data/transformed/news_articles.json`

**Statistics:**
- Total articles: 262
- Date range: 2018-11-28 to 2025-12-06
- Articles with entities: 239 (91.2%)
- Total entity mentions: 742
- Average mentions per article: 2.8

**Top Sources:**
- The Guardian: 36 articles (13.7%)
- NPR: 34 articles (13.0%)
- BBC News: 28 articles (10.7%)
- The New York Times: 18 articles (6.9%)
- Reuters: 18 articles (6.9%)

**Article Type Distribution:**
- Other: 149 (56.9%)
- Court coverage: 59 (22.5%)
- Investigation: 46 (17.6%)
- Analysis: 4 (1.5%)
- Profile: 3 (1.1%)
- Timeline: 1 (0.4%)

**Credibility:**
- High: 261 articles (99.6%)
- Medium: 1 article (0.4%)

### 4. UUID Mappings
**File:** `data/transformed/news_uuid_mappings.json`

Maps legacy UUIDs to new deterministic news_ids for backward compatibility.

### 5. Validation Script
**File:** `scripts/validation/validate_news.py`

**Validation Checks:**
- ✅ JSON Schema compliance
- ✅ UUID format validation
- ✅ UUID uniqueness (with duplicate detection)
- ✅ Entity UUID reference validation
- ✅ Required field presence
- ✅ URL format validation
- ✅ Date format validation (ISO 8601)
- ✅ Enum value validation
- ✅ Entity mention consistency

**Validation Results:**
- Valid articles: 261/262 (99.6%)
- Invalid: 1 (duplicate URL in source data)

## Data Quality Issues Identified

### 1. Zero Mention Counts (FIXED)
**Issue:** Source data contains entity_mention_counts with value 0
**Impact:** 53 entity mentions across 41 articles
**Fix:** Filter out entities with 0 mentions during transformation
**Result:** Schema enforces minimum count of 1

### 2. Duplicate URL (SOURCE DATA ISSUE)
**URL:** `https://www.npr.org/2025/11/20/nx-s1-5613427/epstein-files-chomsky-bannon-summers-democrats`
**Duplicate IDs:**
- `33c4edfe-cd55-42ba-bdab-31b1e38bb25a`
- `7abaf814-94c2-49ea-b52b-3ab8f2eb5c86`

**Impact:** Same URL generates same news_id (by design)
**Note:** This is expected behavior for deterministic UUIDs
**Action Required:** Deduplicate source data in `news_articles_index.json`

### 3. Unmatched Entities
**Count:** 151 mentions of 31 unique entities
**Top Unmatched:**
- Alexander Acosta
- Annie Farmer
- Barry Krischer
- Bill Clinton
- Bill Richardson
- Brad Edwards
- Courtney Wild
- Denise George
- Epstein, Jeffrey (variant spelling)
- Ghislaine Noelle Marion Maxwell (full name variant)

**Root Cause:** Name variations and missing entity records
**Action Required:**
1. Add entity records for missing individuals
2. Add aliases for name variations
3. Re-run transformation to update entity links

## Technical Details

### UUID Generation
```python
def generate_news_uuid(source_url: str) -> str:
    normalized_url = source_url.lower().rstrip('/')
    return str(uuid.uuid5(NEWS_NAMESPACE, normalized_url))
```

**Namespace:** `6ba7b810-9dad-11d1-80b4-00c04fd430c8` (DNS namespace)

### Entity Matching
Uses same normalization as entity UUID generation:
1. Lowercase
2. Remove possessives ('s)
3. Remove punctuation (except hyphens)
4. Collapse multiple spaces

### Article Type Classification
Based on tags analysis:
- "court" → court_coverage
- "investigation" → investigation
- "timeline" → timeline
- "analysis" → analysis
- "breaking" → breaking_news
- "profile"/"biography" → profile
- "opinion"/"editorial" → opinion
- Default → other

### Credibility Assessment
```
Tier 1 (high): Major newspapers, AP, Reuters
Tier 2 (medium): Regional papers, specialty outlets
Tier 3 (low): Questionable sources
```

With score adjustment:
- ≥0.8 → high
- ≥0.6 → medium
- ≥0.4 → medium
- >0 → low

## Files Modified

No existing files modified - only new files created per project organization rules.

## Testing

Validation script (`validate_news.py`) confirms:
- ✅ 99.6% schema compliance (261/262 articles)
- ✅ All required fields present
- ✅ Valid UUID formats
- ✅ Entity UUID references exist
- ✅ Date and URL formats valid
- ⚠️ 1 duplicate URL (source data issue)

## Next Steps

1. **Fix Source Data:**
   - Deduplicate NPR article in `news_articles_index.json`
   - Add missing entity records for unmatched names
   - Add aliases for name variations

2. **Re-run Transformation:**
   ```bash
   python scripts/transformations/generate_news_uuids.py
   python scripts/validation/validate_news.py
   ```

3. **API Integration:**
   - Update endpoints to use news_id (UUID5)
   - Implement entity linking via extracted_entities
   - Add credibility filtering

4. **Documentation:**
   - Update API docs with news schema
   - Document news vs. documents distinction
   - Add entity linking examples

## Code Quality Metrics

**Lines of Code:**
- Schema: 95 lines (JSON)
- Transformation: 456 lines (Python)
- Validation: 373 lines (Python)
- **Total:** 924 lines

**Reuse:**
- Entity normalization: Reused from `generate_entity_uuids.py`
- UUID5 pattern: Reused from `generate_document_uuids.py`
- Validation patterns: Adapted from document validation

**Test Coverage:**
- Schema validation: ✅
- UUID generation: ✅
- Entity mapping: ✅
- Data integrity: ✅

## References

- **Issue #17:** News canonical schema definition
- **Issue #18:** Entity UUID system (dependency)
- **M1 Audit:** News articles data quality assessment
- **Related Files:**
  - `data/metadata/news_articles_index.json` (source)
  - `data/transformed/entity_uuid_mappings.json` (dependency)
  - `scripts/transformations/generate_entity_uuids.py` (reference)
  - `scripts/transformations/generate_document_uuids.py` (reference)

---

**Implementation Complete:** 2025-12-06
**Validation Status:** 99.6% pass rate (1 duplicate URL in source)
**Ready for:** API integration after source data deduplication
