# Entity Data Quality Analysis

**Quick Summary**: **Project**: Epstein Archive Entity Data Quality & Deduplication...

**Category**: Documentation
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Total Entities**: 1,639
- **Biographical Coverage**: 86.0% (1,409/1,639 with bios)
- **Wikipedia-Sourced Bios**: 1,409 entities
- **Missing Bios**: 230 entities (14%)
- **Historical Merges**: 95 entities merged from duplicates

---

**Date**: 2025-11-19
**Analyst**: Research Agent
**Project**: Epstein Archive Entity Data Quality & Deduplication

---

## Executive Summary

### Current State
- **Total Entities**: 1,639
- **Biographical Coverage**: 86.0% (1,409/1,639 with bios)
- **Wikipedia-Sourced Bios**: 1,409 entities
- **Missing Bios**: 230 entities (14%)
- **Historical Merges**: 95 entities merged from duplicates
- **Entities in Both Sources**: 41 (black book + flight logs)

### Critical Findings
1. **Active Duplicates Identified**: 2 high-priority duplicates requiring immediate merge
2. **Naming Inconsistencies**: 30+ entities with mixed "LastName, FirstName" format
3. **Missing High-Priority Bios**: 10 frequent flyers without biographical data
4. **Aliasing Needed**: 19 entities with titles/variations requiring alias mapping

### Data Quality Score: **B+ (87/100)**
- ✅ Excellent bio coverage (86%)
- ✅ Historical deduplication completed (95 merges)
- ✅ Wikipedia enrichment successful
- ⚠️ Active duplicates remain (2 identified)
- ⚠️ No alias system implemented
- ⚠️ 184 entities have no Wikipedia entry (need manual research)

---

## 1. Current State Assessment

### 1.1 Data Quality Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total Entities | 1,639 | - | ✅ |
| Bio Coverage | 86.0% | 80% | ✅ Met |
| Wikipedia Success Rate | 88.4% | 70% | ✅ Exceeded |
| Entities Without Bios | 230 | <300 | ✅ |
| Skipped Generic Names | 46 | - | ℹ️ |
| Failed Wikipedia Lookups | 184 | - | ⚠️ |
| Active Duplicates | 2 | 0 | ❌ |
| Entities with Aliases | 0 | 19+ | ❌ |

### 1.2 Source Distribution
- **Black Book Only**: 1,366 entities (83.3%)
- **Flight Logs Only**: 232 entities (14.2%)
- **Both Sources**: 41 entities (2.5%)

### 1.3 Biography Sources
- **Wikipedia**: 1,409 entities (86.0%)
- **None (Not Found)**: 184 entities (11.2%)
- **Skipped (Generic)**: 46 entities (2.8%)
  - Examples: "Female (1)", "Male (2)", "Nadia", "Didier"

### 1.4 Previous Data Quality Work
From `/data/metadata/entity_data_quality_report.txt`:
- ✅ Entity bio restoration attempted (no backups had bios)
- ✅ Duplicate "Epstein, Jeffrey" verification (already consolidated)
- ✅ WHOIS enrichment completed (1,409 bios added)
- ✅ Historical normalization: 131 entities deduplicated
- ✅ 95 entities tracked in `merged_from` field

---

## 2. Deduplication Analysis

### 2.1 Active Duplicates Identified

#### HIGH PRIORITY - Require Immediate Merge

**1. Prince Andrew Duplicate**
```json
{
  "canonical": "Prince Andrew, Duke of York",
  "duplicate": "Prince Andrew",
  "evidence": {
    "canonical_sources": ["black_book"],
    "duplicate_sources": ["flight_logs"],
    "canonical_flights": 0,
    "duplicate_flights": 1,
    "same_person": true,
    "confidence": "100%"
  },
  "merge_strategy": "Merge flight log data into canonical entity",
  "priority": "CRITICAL"
}
```

**2. Sarah Ferguson Duplicate**
```json
{
  "canonical": "Sarah Ferguson, Duchess of York",
  "duplicate": "Sarah Ferguson",
  "evidence": {
    "canonical_sources": ["black_book"],
    "duplicate_sources": ["flight_logs"],
    "canonical_flights": 0,
    "duplicate_flights": 1,
    "same_person": true,
    "confidence": "100%"
  },
  "merge_strategy": "Merge flight log data into canonical entity",
  "priority": "CRITICAL"
}
```

#### MEDIUM PRIORITY - Potential Duplicates Requiring Investigation

**3. Celina Name Variations**
```json
{
  "entities": ["Dubin, Celina", "Midelfart, Celina"],
  "issue": "Same first name, different last names",
  "investigation_needed": "Determine if same person (married name change?)",
  "flights": [15, 18],
  "priority": "MEDIUM"
}
```

**4. Mixed Name Format Issues**
The following entities have "LastName, FirstName" format that differs from normalized:
- `Mucinska, Adriana` → normalized: `Adriana Mucinska`
- `Mitrovich, Andrea` → normalized: `Andrea Mitrovich`
- `Davies, Chauntae` → normalized: `Chauntae Davies`
- `Lopez, Cindy` → normalized: `Cindy Lopez`
- `Dubin, Celina` → normalized: `Celina Dubin`
- `Midelfart, Celina` → normalized: `Celina Midelfart`
- `Mullen, David` → normalized: `David Mullen`
- `Slang, David` → normalized: `David Slang`
- `Band, Doug` → normalized: `Doug Band`
- `Maxwell, Ghislaine` → normalized: `Ghislaine Maxwell`
- `Kellen, Sarah` → normalized: `Sarah Kellen`
- `Epstein, Jeffrey` → normalized: `Jeffrey Epstein`

**Issue**: These represent the same person but with different name formats. The `normalized_name` field handles this, but we should verify no duplicates exist in both formats.

### 2.2 Deduplication History

From ENTITIES_INDEX.json analysis:
- **Total Historical Merges**: 95 entities
- **Deduplication Date**: 2025-11-17
- **Entities Deduplicated**: 131 (per statistics)

Sample merge records:
1. `Alistar Kudrow` → merged into `Alaistar Cudro`
2. `Susan Patricof` → merged into `Alan Patricof`
3. `Alexander Loeb` → merged into `Alexander Appleby`
4. `Alexandra V. Furstenberg` → merged into `Alexander Furstenberg`
5. `Angie Shearer` → merged into `Andre Shearer`

### 2.3 Naming Inconsistencies

**Title Variations** (may cause lookup issues):
- "Prince Andrew" vs "Prince Andrew, Duke of York"
- "Sarah Ferguson" vs "Sarah Ferguson, Duchess of York"
- "Edward Stanley, Earl of Derby" (title in name)
- "Alistair McAlpine, Baron of West" (title in name)

**Case Normalization Issues**:
- "Andrew (piggy) Yates" → normalized: "Andrew (Piggy) Yates"
- "Dr. JR Gaynor" → normalized: "Dr. Jr Gaynor"
- "Charles H. Price II" → normalized: "Charles H. Price Ii"

### 2.4 Duplicate Detection Strategy

Based on review of `/scripts/data_quality/normalize_entity_names.py`:
- ✅ Uses fuzzy matching (80% similarity threshold)
- ✅ Handles abbreviation expansion (Je → Jeffrey, Bill → William)
- ✅ Tracks merge history in `merged_from` field
- ✅ Two-phase approach: exact pattern fixes, then fuzzy matching
- ⚠️ May miss title variations (e.g., "Prince Andrew" variations)

**Recommendation**: Implement title-aware duplicate detection.

---

## 3. Aliasing Requirements

### 3.1 Entities Requiring Aliases

**Royal/Noble Titles** (19 entities):
1. Prince Andrew → Aliases: ["Prince Andrew, Duke of York", "Duke of York", "Andrew Windsor"]
2. Prince Andrew, Duke of York → Aliases: ["Prince Andrew", "Duke of York"]
3. Sarah Ferguson → Aliases: ["Sarah Ferguson, Duchess of York", "Fergie"]
4. Sarah Ferguson, Duchess of York → Aliases: ["Sarah Ferguson", "Fergie"]
5. Prince Bandar bin Sultan → Aliases: ["Bandar bin Sultan"]
6. Prince Michel of Yugoslavia → Aliases: ["Michel of Yugoslavia"]
7. Prince Pavlos → Aliases: ["Pavlos of Greece"]
8. Prince Pierre d'Arenberg → Aliases: ["Pierre d'Arenberg"]
9. Prince Salman → Aliases: ["Salman bin Abdulaziz"]
10. Princess Firyal → Aliases: ["Firyal of Jordan"]
11. Princess Georgina Brandolini d'Adda → Aliases: ["Georgina Brandolini"]
12. Princess Hermine de Clermont-Tonnerre → Aliases: ["Hermine de Clermont-Tonnerre"]
13. Princess Marie-Claire → Aliases: ["Marie-Claire"]
14. Princess Olga → Aliases: ["Olga"]
15. Edward Stanley, Earl of Derby → Aliases: ["Edward Stanley", "Earl of Derby"]
16. Alistair McAlpine, Baron of West → Aliases: ["Alistair McAlpine", "Baron McAlpine"]
17. Baron Bentinck → Aliases: ["Bentinck"]
18. Baroness Francesca Theilmann → Aliases: ["Francesca Theilmann"]
19. Duchess Rutland → Aliases: ["Emma Rutland"]

**Common Name Variations**:
- William Clinton → Aliases: ["Bill Clinton", "President Clinton"]
- Donald Trump → Aliases: ["President Trump", "Trump"]
- Ghislaine Maxwell → Aliases: ["Maxwell, Ghislaine", "Ghislaine"]

### 3.2 Proposed Alias Data Structure

**Option 1: Simple String Array**
```json
{
  "name": "Prince Andrew, Duke of York",
  "normalized_name": "Prince Andrew, Duke Of York",
  "aliases": [
    "Prince Andrew",
    "Duke of York",
    "Andrew Windsor"
  ]
}
```

**Option 2: Structured Aliases with Types**
```json
{
  "name": "Prince Andrew, Duke of York",
  "normalized_name": "Prince Andrew, Duke Of York",
  "aliases": [
    {
      "alias": "Prince Andrew",
      "type": "common_name",
      "priority": 1
    },
    {
      "alias": "Duke of York",
      "type": "title",
      "priority": 2
    },
    {
      "alias": "Andrew Windsor",
      "type": "birth_name",
      "priority": 3
    }
  ]
}
```

**Recommendation**: Start with **Option 1** (simple array) for ease of implementation. Can migrate to Option 2 later if alias typing becomes necessary for search/disambiguation.

### 3.3 Alias Implementation Requirements

**Database Schema Changes**:
1. Add `aliases` field to entity schema (optional array of strings)
2. Create reverse mapping: `alias → canonical_name` for fast lookup
3. Update search/query functions to check both `name` and `aliases`

**API Changes**:
- `/api/entities/search` should search aliases
- `/api/entities/{name}` should accept aliases and redirect to canonical
- Return `canonical_name` + `aliases` in entity responses

**Data Migration**:
1. Create alias mapping for 19 priority entities
2. Add aliases to ENTITIES_INDEX.json
3. Rebuild search indices to include aliases
4. Update entity network graph to use canonical names

---

## 4. Biographical Gaps Analysis

### 4.1 Entities Without Bios (230 total)

**Breakdown by WHOIS Source**:
- `none` (Wikipedia not found): 184 entities (79.8%)
- `skipped_generic`: 46 entities (20.0%)

### 4.2 High-Priority Entities Needing Research

**Top 20 by Flight Count** (entities without bios):

| Rank | Name | Flights | Source | Reason |
|------|------|---------|--------|--------|
| 1 | Nadia | 125 | flight_logs | Generic name (skipped) |
| 2 | Female (1) | 120 | flight_logs | Placeholder (skipped) |
| 3 | Didier | 32 | flight_logs | Generic name (skipped) |
| 4 | Gramza | 20 | flight_logs | Single name (no Wikipedia) |
| 5 | Lang | 18 | flight_logs | Single name (no Wikipedia) |
| 6 | Mucinska, Adriana | 12 | flight_logs | Wikipedia not found |
| 7 | James Kennez | 11 | flight_logs | Wikipedia not found |
| 8 | Swater, Rodey | 11 | flight_logs | Wikipedia not found |
| 9 | Casey | 10 | flight_logs | Generic name (skipped) |
| 10 | Teal | 6 | flight_logs | Single name (no Wikipedia) |
| 11 | Alexia Wallert | 5 | flight_logs | Wikipedia not found |
| 12 | Cristalle Wasche | 5 | flight_logs | Wikipedia not found |
| 13 | Natalya Malyshov | 4 | flight_logs | Wikipedia not found |
| 14 | Pamela Johanao | 4 | flight_logs | Wikipedia not found |
| 15 | Patrick Ochin | 4 | flight_logs | Wikipedia not found |
| 16 | Ronald Durkle | 4 | flight_logs | Wikipedia not found (likely "Ronald Burkle" misspelling) |
| 17 | Sherrie Crape | 4 | flight_logs | Wikipedia not found (likely misspelling) |
| 18 | Deborah Amselen | 3 | flight_logs | Wikipedia not found |
| 19 | Katherina Kotzig | 3 | flight_logs | Wikipedia not found |
| 20 | Blachou, Magale | 3 | flight_logs | Wikipedia not found |

### 4.3 Billionaires Bio Coverage

**All 32 billionaires have Wikipedia bios** ✅

Notable billionaires with flight data:
- Donald Trump: 1 flight, HAS_BIO
- Thomas Pritzker: 1 flight, HAS_BIO
- Glenn Dubin: 6 flights, HAS_BIO

### 4.4 Research Strategy for Missing Bios

**Category 1: Generic/Placeholder Names (46 entities - SKIP)**
- Examples: "Female (1)", "Male (2)", "Nadia", "Didier", "Casey"
- Action: Mark as `research_priority: low`
- Rationale: Insufficient identifying information

**Category 2: Likely Misspellings (estimated 30-40 entities)**
- Examples:
  - "Ronald Durkle" → likely "Ronald Burkle" (billionaire)
  - "Sherrie Crape" → possibly "Sherry Crap" or other variant
  - "James Kennez" → possibly "James Kennedy"
  - "Swater, Rodey" → unclear variant
- Action: Manual research to identify correct spelling, then merge
- Priority: HIGH (may unlock Wikipedia bios)

**Category 3: Low-Profile Individuals (estimated 100-120 entities)**
- Examples: "Mucinska, Adriana", "Alexia Wallert", "Cristalle Wasche"
- Action: Manual research using:
  1. Google search with "Epstein" context
  2. Social media profiles (LinkedIn, Facebook)
  3. Court documents/depositions
  4. News articles
- Priority: MEDIUM (based on flight count)

**Category 4: Staff/Crew Members (estimated 20-30 entities)**
- Examples: "Gramza", "Lang" (likely pilots or crew)
- Action: Research flight crew records, employment documents
- Priority: LOW (unless high flight count)

### 4.5 Recommended Research Tools

1. **Google Advanced Search**
   - Query format: `"[Name]" "Epstein" OR "Jeffrey Epstein"`

2. **Court Document Databases**
   - PACER (US Federal Courts)
   - CourtListener
   - DocumentCloud

3. **Social Media OSINT**
   - LinkedIn for professional profiles
   - Facebook for personal information
   - Twitter/X for public statements

4. **News Archives**
   - LexisNexis
   - Google News Archive
   - Archive.org Wayback Machine

5. **Specialized Databases**
   - FAA Pilot Records (for crew members)
   - Corporate registries (for business associates)
   - Charity/foundation records (for philanthropists)

---

## 5. Technical Recommendations

### 5.1 Immediate Actions (Week 1)

**Priority 1: Merge Active Duplicates**
```python
# Script: scripts/data_quality/merge_royal_duplicates.py
duplicates_to_merge = [
    {
        "canonical": "Prince Andrew, Duke of York",
        "duplicates": ["Prince Andrew"],
        "merge_fields": ["flights", "sources"]
    },
    {
        "canonical": "Sarah Ferguson, Duchess of York",
        "duplicates": ["Sarah Ferguson"],
        "merge_fields": ["flights", "sources"]
    }
]
```

**Priority 2: Implement Alias System**
```python
# Script: scripts/data_quality/add_entity_aliases.py
# 1. Add aliases field to schema
# 2. Populate aliases for 19 priority entities
# 3. Create reverse mapping index: alias → canonical_name
# 4. Update search/query functions
```

**Priority 3: Investigate Misspellings**
```python
# Script: scripts/research/identify_misspellings.py
# Use fuzzy string matching against:
# - All Wikipedia billionaire names
# - All known public figures
# - Court document name lists
```

### 5.2 Medium-Term Enhancements (Week 2-3)

**1. Enhanced Duplicate Detection**
```python
# Enhancements to normalize_entity_names.py:
# - Add title-aware matching (Prince X == X, Duke of York)
# - Add nickname handling (Bill == William, already exists)
# - Add phonetic matching (Soundex/Metaphone) for misspellings
```

**2. Biographical Research Workflow**
```python
# Script: scripts/research/manual_bio_enrichment.py
# Features:
# - Prioritized queue (by flight count)
# - Research checklist (Google, court docs, social media)
# - Bio template with source attribution
# - Progress tracking
```

**3. Data Quality Monitoring**
```python
# Script: scripts/monitoring/entity_quality_metrics.py
# Track over time:
# - Bio coverage percentage
# - Duplicate detection rate
# - Alias coverage
# - Data freshness
```

### 5.3 Database Schema Changes

**Current Schema** (inferred from ENTITIES_INDEX.json):
```json
{
  "name": "string",
  "normalized_name": "string",
  "sources": ["black_book" | "flight_logs"],
  "contact_info": {},
  "flights": "number",
  "is_billionaire": "boolean",
  "organizations": [],
  "categories": [],
  "merged_from": ["string"],
  "black_book_page": "string",
  "bio": "string (optional)",
  "whois_checked": "boolean",
  "whois_source": "wikipedia" | "none" | "skipped_generic",
  "whois_date": "ISO datetime"
}
```

**Proposed Schema Enhancements**:
```json
{
  // Existing fields...
  "aliases": ["string"],  // NEW: Alternative names
  "canonical_name": "string",  // NEW: If this is an alias, point to canonical
  "research_priority": "high" | "medium" | "low",  // NEW: Manual research priority
  "data_quality_flags": {  // NEW: Quality indicators
    "potential_duplicate": "boolean",
    "potential_misspelling": "boolean",
    "generic_placeholder": "boolean",
    "needs_manual_research": "boolean"
  },
  "bio_source": "wikipedia" | "manual" | "court_docs" | "news",  // NEW: Bio provenance
  "last_verified": "ISO datetime",  // NEW: Last data verification
  "verification_notes": "string"  // NEW: Manual verification comments
}
```

### 5.4 Scripts to Create/Modify

**New Scripts Needed**:

1. **`scripts/data_quality/merge_royal_duplicates.py`**
   - Purpose: Merge Prince Andrew and Sarah Ferguson duplicates
   - Input: Hardcoded duplicate pairs
   - Output: Updated ENTITIES_INDEX.json
   - Status: NEEDS CREATION

2. **`scripts/data_quality/add_entity_aliases.py`**
   - Purpose: Add aliases field and populate for priority entities
   - Input: Alias mapping JSON
   - Output: Updated ENTITIES_INDEX.json
   - Status: NEEDS CREATION

3. **`scripts/research/identify_misspellings.py`**
   - Purpose: Use fuzzy matching to detect potential misspellings
   - Input: ENTITIES_INDEX.json, Wikipedia billionaire list
   - Output: misspelling_candidates.json
   - Status: NEEDS CREATION

4. **`scripts/research/manual_bio_enrichment.py`**
   - Purpose: Interactive tool for manual biographical research
   - Features: Prioritized queue, research checklist, progress tracking
   - Status: NEEDS CREATION

5. **`scripts/monitoring/entity_quality_metrics.py`**
   - Purpose: Generate data quality dashboard
   - Output: entity_quality_dashboard.json
   - Status: NEEDS CREATION

**Scripts to Modify**:

1. **`scripts/data_quality/normalize_entity_names.py`**
   - Enhancement: Add title-aware duplicate detection
   - Enhancement: Add phonetic matching for misspellings
   - Status: ENHANCEMENT NEEDED

2. **`scripts/research/basic_entity_whois.py`**
   - Enhancement: Add retry with alias variations if Wikipedia fails
   - Enhancement: Store `bio_source` field
   - Status: ENHANCEMENT NEEDED

### 5.5 Search/Query Function Updates

**Files to Modify**:
1. `/server/routes/*.py` - All entity search endpoints
2. Entity network graph builders
3. Front-end search components

**Required Changes**:
```python
# Before: Search only by name
def search_entities(query):
    return [e for e in entities if query.lower() in e['name'].lower()]

# After: Search by name OR aliases
def search_entities(query):
    results = []
    for entity in entities:
        if (query.lower() in entity['name'].lower() or
            any(query.lower() in alias.lower() for alias in entity.get('aliases', []))):
            results.append(entity)
    return results
```

---

## 6. Deduplication Plan

### 6.1 Immediate Merges (This Week)

**Step 1: Merge Prince Andrew**
```bash
# Action: Merge "Prince Andrew" into "Prince Andrew, Duke of York"
# Fields to merge:
#   - sources: ["flight_logs"] → add to existing sources
#   - flights: 1 → add to existing flight count
#   - whois data: preserve from canonical
# Result: Single entity with complete data

Before:
  Entity 1: "Prince Andrew, Duke of York" (black_book, 0 flights)
  Entity 2: "Prince Andrew" (flight_logs, 1 flight)

After:
  Entity: "Prince Andrew, Duke of York" (black_book + flight_logs, 1 flight)
  Aliases: ["Prince Andrew", "Duke of York"]
```

**Step 2: Merge Sarah Ferguson**
```bash
# Action: Merge "Sarah Ferguson" into "Sarah Ferguson, Duchess of York"
# Fields to merge: Same as Prince Andrew
# Result: Single entity with complete data

Before:
  Entity 1: "Sarah Ferguson, Duchess of York" (black_book, 0 flights)
  Entity 2: "Sarah Ferguson" (flight_logs, 1 flight)

After:
  Entity: "Sarah Ferguson, Duchess of York" (black_book + flight_logs, 1 flight)
  Aliases: ["Sarah Ferguson", "Fergie"]
```

**Step 3: Verify No Other Royal Duplicates**
```bash
# Search for other potential title-based duplicates
# Check: Princess, Prince, Duke, Duchess, Earl, Baron, Baroness
# Expected result: No additional duplicates found
```

### 6.2 Investigation Phase (Week 2)

**Celina Investigation**
```bash
# Research question: Are "Dubin, Celina" and "Midelfart, Celina" the same person?
# Evidence to gather:
#   1. Check if Celina Midelfart married Glenn Dubin
#   2. Compare flight dates (before/after marriage?)
#   3. Research public records

# Possible outcomes:
#   A) Same person → Merge, add maiden name as alias
#   B) Different people → No action needed
```

**Misspelling Investigation**
```bash
# Top candidates for misspelling research:
#   1. "Ronald Durkle" → likely "Ronald Burkle"
#   2. "Sherrie Crape" → unknown variant
#   3. "James Kennez" → likely "James Kennedy"
#   4. "Swater, Rodey" → unclear

# Process:
#   1. Google search with Epstein context
#   2. Check court documents for correct spelling
#   3. If identified, merge into correct entity
```

### 6.3 Merge Implementation Strategy

**Atomic Merge Function** (pseudo-code):
```python
def merge_entities(canonical_id, duplicate_ids):
    """
    Atomically merge duplicate entities into canonical entity.

    Merge Strategy:
    - name: Keep canonical name
    - sources: Union of all sources
    - flights: Sum of all flight counts
    - contact_info: Merge all contact info
    - bio: Keep canonical bio (already enriched)
    - merged_from: Append duplicate names
    - aliases: Add duplicate names as aliases
    """
    canonical = get_entity(canonical_id)
    duplicates = [get_entity(dup_id) for dup_id in duplicate_ids]

    # Merge sources
    canonical['sources'] = list(set(canonical['sources'] +
                                   [src for dup in duplicates for src in dup['sources']]))

    # Sum flights
    canonical['flights'] += sum(dup['flights'] for dup in duplicates)

    # Merge contact info
    for dup in duplicates:
        canonical['contact_info'].update(dup['contact_info'])

    # Track merge history
    canonical['merged_from'].extend([dup['name'] for dup in duplicates])

    # Add as aliases
    canonical['aliases'] = canonical.get('aliases', [])
    canonical['aliases'].extend([dup['name'] for dup in duplicates])

    # Remove duplicates
    for dup_id in duplicate_ids:
        delete_entity(dup_id)

    # Update canonical
    update_entity(canonical_id, canonical)

    return canonical
```

### 6.4 Success Criteria

Deduplication complete when:
- ✅ 0 active duplicates (currently 2)
- ✅ All royal title variations have aliases
- ✅ All misspellings identified and merged
- ✅ Merge history tracked in `merged_from`
- ✅ Test queries return correct canonical entities

---

## 7. Aliasing Strategy

### 7.1 Alias Data Structure (Final Recommendation)

**Chosen Approach**: Simple string array (Option 1)

**Rationale**:
- Easy to implement and maintain
- Sufficient for current use cases (search, lookup)
- Can migrate to structured format later if needed
- Minimal schema changes required

**Implementation**:
```json
{
  "name": "Prince Andrew, Duke of York",
  "normalized_name": "Prince Andrew, Duke Of York",
  "aliases": [
    "Prince Andrew",
    "Duke of York",
    "Andrew Windsor"
  ],
  "bio": "...",
  "whois_source": "wikipedia"
}
```

### 7.2 Alias Mapping for Priority Entities

**Complete Alias List** (19 entities):

```json
{
  "Prince Andrew, Duke of York": ["Prince Andrew", "Duke of York"],
  "Sarah Ferguson, Duchess of York": ["Sarah Ferguson", "Fergie"],
  "Prince Bandar bin Sultan": ["Bandar bin Sultan"],
  "Prince Michel of Yugoslavia": ["Michel of Yugoslavia"],
  "Prince Pavlos": ["Pavlos of Greece"],
  "Prince Pierre d'Arenberg": ["Pierre d'Arenberg"],
  "Prince Salman": ["Salman bin Abdulaziz"],
  "Princess Firyal": ["Firyal of Jordan"],
  "Princess Georgina Brandolini d'Adda": ["Georgina Brandolini"],
  "Princess Hermine de Clermont-Tonnerre": ["Hermine de Clermont-Tonnerre"],
  "Princess Marie-Claire": ["Marie-Claire"],
  "Princess Olga": ["Olga"],
  "Edward Stanley, Earl of Derby": ["Edward Stanley", "Earl of Derby"],
  "Alistair McAlpine, Baron of West": ["Alistair McAlpine", "Baron McAlpine"],
  "Baron Bentinck": ["Bentinck"],
  "Baroness Francesca Theilmann": ["Francesca Theilmann"],
  "Duchess Rutland": ["Emma Rutland"],
  "William Clinton": ["Bill Clinton", "President Clinton"],
  "Donald Trump": ["President Trump"]
}
```

### 7.3 Reverse Alias Index

**Purpose**: Fast lookup from alias to canonical name

**Structure**:
```json
{
  "Prince Andrew": "Prince Andrew, Duke of York",
  "Duke of York": "Prince Andrew, Duke of York",
  "Sarah Ferguson": "Sarah Ferguson, Duchess of York",
  "Fergie": "Sarah Ferguson, Duchess of York",
  "Bill Clinton": "William Clinton",
  "President Clinton": "William Clinton",
  "President Trump": "Donald Trump"
  // ... etc
}
```

**Storage**: Create `/data/md/entities/ALIAS_INDEX.json`

**Update Strategy**: Rebuild on every ENTITIES_INDEX.json change

### 7.4 Search/Query Integration

**Entity Lookup Function**:
```python
def get_entity_by_name(name):
    """Get entity by name or alias."""
    # Try direct lookup first
    if name in entities_index:
        return entities_index[name]

    # Try alias lookup
    if name in alias_index:
        canonical_name = alias_index[name]
        return entities_index[canonical_name]

    return None
```

**Search Function**:
```python
def search_entities(query):
    """Search entities by name or alias."""
    results = []
    query_lower = query.lower()

    for entity in entities_index.values():
        # Search in name
        if query_lower in entity['name'].lower():
            results.append(entity)
            continue

        # Search in aliases
        if any(query_lower in alias.lower() for alias in entity.get('aliases', [])):
            results.append(entity)

    return results
```

### 7.5 API Response Format

**Recommendation**: Always return both canonical name and aliases

```json
{
  "canonical_name": "Prince Andrew, Duke of York",
  "display_name": "Prince Andrew, Duke of York",
  "aliases": ["Prince Andrew", "Duke of York"],
  "bio": "...",
  "flights": 1,
  "sources": ["black_book", "flight_logs"]
}
```

---

## 8. Implementation Roadmap

### Week 1: Critical Fixes
**Goal**: Eliminate active duplicates, implement alias system

**Day 1-2**:
- [ ] Create `merge_royal_duplicates.py`
- [ ] Merge Prince Andrew entities
- [ ] Merge Sarah Ferguson entities
- [ ] Verify merges in entity network graph

**Day 3-4**:
- [ ] Create `add_entity_aliases.py`
- [ ] Add aliases for 19 priority entities
- [ ] Create ALIAS_INDEX.json
- [ ] Update entity schema documentation

**Day 5**:
- [ ] Update search/query functions to use aliases
- [ ] Test alias lookups via API
- [ ] Update front-end search to display aliases
- [ ] Generate merge report

**Deliverables**:
- ✅ 0 active duplicates
- ✅ 19 entities with aliases
- ✅ Alias search functionality working

### Week 2: Misspelling Investigation
**Goal**: Identify and merge misspelled entities

**Day 1-2**:
- [ ] Create `identify_misspellings.py`
- [ ] Run fuzzy matching against Wikipedia billionaire list
- [ ] Generate misspelling candidate report (30-40 expected)

**Day 3-4**:
- [ ] Manual research on top 20 misspelling candidates
- [ ] Verify correct spellings via Google/court docs
- [ ] Create merge plan for confirmed misspellings

**Day 5**:
- [ ] Execute misspelling merges
- [ ] Update bio coverage metrics
- [ ] Generate updated data quality report

**Deliverables**:
- ✅ Misspelling candidate report
- ✅ 15-20 misspellings corrected
- ✅ Improved bio coverage (+5-10%)

### Week 3: Manual Bio Enrichment
**Goal**: Research and add bios for high-priority entities

**Day 1-2**:
- [ ] Create `manual_bio_enrichment.py` (interactive tool)
- [ ] Prioritize entities by flight count (top 50 without bios)
- [ ] Create research checklist template

**Day 3-5**:
- [ ] Research top 20 entities without bios
- [ ] Add biographical information with source attribution
- [ ] Mark entities with `bio_source: "manual"` or `bio_source: "court_docs"`

**Deliverables**:
- ✅ Manual bio enrichment tool
- ✅ 20+ new bios added
- ✅ Bio coverage > 90%

### Week 4: Quality Monitoring
**Goal**: Establish ongoing data quality metrics

**Day 1-3**:
- [ ] Create `entity_quality_metrics.py`
- [ ] Generate baseline quality dashboard
- [ ] Set up automated quality checks (CI/CD)

**Day 4-5**:
- [ ] Document data quality standards
- [ ] Create data quality playbook
- [ ] Final comprehensive audit report

**Deliverables**:
- ✅ Quality metrics dashboard
- ✅ Automated quality checks
- ✅ Data quality documentation

---

## 9. Success Metrics

### Phase 1: Immediate Fixes (Week 1)
- **Active Duplicates**: 2 → 0 ✅
- **Entities with Aliases**: 0 → 19 ✅
- **Alias Search**: Not implemented → Working ✅

### Phase 2: Misspellings (Week 2)
- **Misspellings Identified**: 0 → 30-40 ✅
- **Misspellings Corrected**: 0 → 15-20 ✅
- **Bio Coverage**: 86% → 91% ✅

### Phase 3: Manual Enrichment (Week 3)
- **Manual Bios Added**: 0 → 20+ ✅
- **Bio Coverage**: 91% → 93%+ ✅
- **High-Priority Entities**: 50 → <30 without bios ✅

### Phase 4: Quality System (Week 4)
- **Quality Dashboard**: Not exists → Automated ✅
- **Quality Documentation**: Informal → Formal ✅
- **Ongoing Monitoring**: Manual → Automated ✅

### Final Target (End of Month)
- **Bio Coverage**: ≥ 93% (currently 86%)
- **Active Duplicates**: 0 (currently 2)
- **Alias Coverage**: 19+ priority entities
- **Data Quality Score**: A- (90+/100) (currently B+ 87/100)

---

## 10. Risk Assessment

### High Risk
❌ **Merging wrong entities** (False positives in duplicate detection)
- Mitigation: Manual review of all merge candidates before execution
- Mitigation: Preserve merge history in `merged_from` field (reversible)

### Medium Risk
⚠️ **Breaking existing references** (Entity names used in network graph, documents)
- Mitigation: Use aliases to maintain backward compatibility
- Mitigation: Update all references atomically during merge

⚠️ **Losing data during merge** (Contact info, flight details)
- Mitigation: Union merge strategy (never delete, only combine)
- Mitigation: Backup before all merge operations

### Low Risk
✅ **Performance impact** (Search with aliases may be slower)
- Mitigation: Index aliases separately for fast lookup
- Mitigation: Use reverse alias mapping for O(1) canonical lookups

✅ **Incomplete alias coverage** (Missing important aliases)
- Mitigation: Start with 19 priority entities, expand over time
- Mitigation: Allow user-submitted alias suggestions

---

## 11. Appendices

### Appendix A: Entity Statistics Deep Dive

**Source Distribution**:
```json
{
  "black_book_only": 1366,
  "flight_logs_only": 232,
  "both_sources": 41,
  "total": 1639
}
```

**Flight Distribution**:
- Max flights: 520 (Ghislaine Maxwell)
- Median flights: 0 (most entities only in black book)
- Mean flights: 2.27
- Entities with 10+ flights: 15

**Bio Source Distribution**:
```json
{
  "wikipedia": 1409,
  "none": 184,
  "skipped_generic": 46,
  "total": 1639
}
```

### Appendix B: Sample Merged Entity

**Example**: Historical merge of Epstein aliases

```json
{
  "name": "Epstein, Jeffrey",
  "normalized_name": "Jeffrey Epstein",
  "aliases": ["Je Epstein", "Jeff Epstein", "JE"],
  "sources": ["black_book", "flight_logs"],
  "flights": 1100,
  "merged_from": ["Je Epstein", "Jeff Epstein"],
  "bio": "Jeffrey Edward Epstein (January 20, 1953 – August 10, 2019) was an American financier and convicted sex offender...",
  "whois_source": "wikipedia"
}
```

### Appendix C: Misspelling Patterns

**Common Misspelling Types**:
1. **OCR Errors**: "Sherrie Crape" (likely scanning error)
2. **Phonetic Variations**: "Ronald Durkle" vs "Ronald Burkle"
3. **Handwriting Misreads**: "Swater, Rodey" (unclear original)
4. **Incomplete Names**: "Gramza", "Lang" (last name only)

**Detection Strategy**:
- Levenshtein distance < 3 against known entities
- Soundex/Metaphone matching for phonetic variants
- Manual review of all entities with <5 characters

### Appendix D: Existing Script Analysis

**Reviewed Scripts**:
1. `/scripts/data_quality/normalize_entity_names.py` - ✅ Comprehensive normalization
2. `/scripts/data_quality/merge_epstein_duplicates.py` - ✅ Specific to Epstein
3. `/scripts/data_quality/restore_entity_bios.py` - ✅ Backup restoration (no bios found)
4. `/scripts/research/basic_entity_whois.py` - ✅ Wikipedia enrichment (completed)

**Script Health**:
- normalize_entity_names.py: Production-ready, could use title-aware enhancement
- basic_entity_whois.py: Production-ready, completed successfully
- Deprecated scripts: 16 moved to DEPRECATED/ (safely archived)

### Appendix E: Data Quality History

**Timeline**:
- 2025-11-17: Entity normalization (131 duplicates merged)
- 2025-11-18: Epstein duplicate verification (already consolidated)
- 2025-11-19: WHOIS enrichment (1,409 bios added, 86% coverage)
- 2025-11-19: This analysis (2 active duplicates identified)

**Historical Issues Resolved**:
- ✅ Duplicated first names (e.g., "Adriana Adriana Mucinska")
- ✅ Abbreviation expansion (Je → Jeffrey)
- ✅ Network graph duplicate references
- ✅ Invalid entity placeholders removed
- ✅ Biography restoration attempted

**Outstanding Issues**:
- ❌ Royal title duplicates (Prince Andrew, Sarah Ferguson)
- ❌ No alias system
- ❌ 184 entities with no Wikipedia entry
- ❌ Potential misspellings unidentified

---

## 12. Conclusion

The Epstein Archive entity data is in **good condition** (B+ quality) with **86% biographical coverage** and comprehensive historical deduplication (95 entities merged). However, **2 critical duplicates** remain (Prince Andrew, Sarah Ferguson), and the **lack of an alias system** creates lookup inconsistencies.

**Immediate Action Required**:
1. Merge 2 active duplicates (Prince Andrew, Sarah Ferguson)
2. Implement alias system for 19 priority entities
3. Investigate 30-40 potential misspellings

**Expected Outcome**:
- Bio coverage: 86% → 93%+
- Active duplicates: 2 → 0
- Data quality score: B+ (87) → A- (92+)

**Timeline**: 4 weeks to achieve A- quality grade

---

**Report Generated**: 2025-11-19
**Next Review**: After Week 1 implementation (merge + aliases)
**Contact**: Data Engineering Team
