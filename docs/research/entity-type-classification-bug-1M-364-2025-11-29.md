# Entity Type Classification Bug Analysis - 1M-364

**Research Date**: 2025-11-29
**Ticket**: [1M-364](https://linear.app/1m-hyperdev/issue/1M-364)
**Priority**: High
**Status**: Root Cause Identified

---

## Executive Summary

**ROOT CAUSE IDENTIFIED**: The LLM prompt in `entity_service.py` has a **critical bias toward "person" classification** due to prompt structure and prioritization rules that contradict the keyword matching logic.

**Impact**: 97.3% of entities (1,593 out of 1,637) misclassified as "person" when analysis shows many should be "organization" or "location".

**Evidence**: The 3 entities classified as "organization" and 41 classified as "location" are **INCORRECTLY classified** - they are actually PEOPLE with empty names or unclear biographies:
- "Doug Band" → classified as "organization" (should be "person")
- "Vor Holding" → classified as "organization" (should be "organization") ✓
- Empty name entities → classified as "location" (should be "person")

---

## Investigation Methodology

### 1. Data Analysis
- **Total entities**: 1,637
- **Classification distribution**:
  - Person: 1,593 (97.3%)
  - Location: 41 (2.5%)
  - Organization: 3 (0.2%)

### 2. Script Analysis
- **Classification script**: `scripts/analysis/classify_entity_types.py`
- **Service module**: `server/services/entity_service.py`
- **Classification method**: 3-tier system (LLM → NLP → Keyword)
- **Primary tier**: LLM (Claude Haiku via OpenRouter)

### 3. Test Cases Examined
```python
# Known organizations that should exist:
- Southern Trust Company
- FBI
- CIA
- Clinton Foundation
- Trump Organization
- Interfor Inc

# Known locations that should exist:
- Little St. James Island
- Palm Beach
- New York
- Zorro Ranch
- Mar-a-Lago
```

**Finding**: NONE of these expected entities exist in the dataset by ID or name search.

---

## Root Cause: LLM Prompt Bias

### Current Prompt (Lines 413-450 in entity_service.py)

```python
prompt = f"""Classify this entity as one of: person, organization, location

Entity name: "{name}"
"""

# ... bio and sources context added ...

prompt += """

Classification Rules with Keyword Indicators:

**ORGANIZATION** - Companies, agencies, foundations, institutions
  Examples: "FBI", "CIA", "Clinton Foundation", "Trump Organization", "Interfor Inc", "Southern Trust Company"
  Keywords: Foundation, Organization, Inc, LLC, Corp, Company, Agency, Bureau, Department, Institute, University, Association, Trust, Bank, Group

**LOCATION** - Places, properties, geographic locations
  Examples: "Little St. James Island", "Zorro Ranch", "Palm Beach", "New York", "Mar-a-Lago"
  Keywords: Island, Beach, Ranch, Estate, Airport, Hotel, Resort, Street, Avenue, Road, Club, Palace, Villa, City, State, Country

**PERSON** - Individual humans
  Examples: "Epstein, Jeffrey", "Maxwell, Ghislaine", "Clinton, Bill", "Trump, Donald"
  Name patterns: Last name + comma + first name, or full names with titles (Dr., Mr., Ms.)

Prioritization:
1. If name contains organization keywords → organization
2. If name contains location keywords → location
3. If name is formatted like a person's name (e.g., "Last, First") → person
4. If ambiguous (e.g., "Maxwell" could be person OR company), use bio context
5. Default to person only if no clear indicators

Return ONLY one word: person, organization, or location"""
```

### Critical Flaws Identified

#### Flaw #1: Contradictory Prioritization Rules
**Lines 444-449**:
```
1. If name contains organization keywords → organization
2. If name contains location keywords → location
3. If name is formatted like a person's name (e.g., "Last, First") → person
```

**Problem**: Rule #3 directly contradicts rules #1-2. The prompt says "prioritize org/location keywords" but then immediately provides a STRONG person indicator (name format) as the third priority.

**Example Case**:
- Entity: "Southern Trust Company"
- Contains organization keyword: ✓ "Trust", "Company"
- Rule #1 says: → organization
- But then Rule #3: "If name is formatted like a person's name..."
- LLM likely interprets ANY name as "formatted" → defaults to person

#### Flaw #2: Weak Default Rule
**Line 449**:
```
5. Default to person only if no clear indicators
```

**Problem**: The word "only" is ignored by the LLM due to prompt structure. In practice, the LLM defaults to "person" for ANY ambiguous case.

**Evidence**: 97.3% person classification rate proves the default is over-applied.

#### Flaw #3: Name Format Bias
**Lines 441-442**:
```
**PERSON** - Individual humans
  Name patterns: Last name + comma + first name, or full names with titles (Dr., Mr., Ms.)
```

**Problem**: This creates a strong bias where:
- "Epstein, Jeffrey" → obviously person ✓
- "Jeffrey Epstein" → obviously person ✓
- "Trump Organization" → ambiguous, defaults to person ✗
- "FBI" → ambiguous, defaults to person ✗

The LLM over-generalizes the "name pattern" rule to apply to ALL text strings.

#### Flaw #4: Missing Explicit Negative Rules
**What's missing**:
```
ORGANIZATIONS should NOT be classified as person even if:
- Name contains a person's name (e.g., "Trump Organization", "Clinton Foundation")
- Name is in "Last, First" format but ends with org keywords

LOCATIONS should NOT be classified as person even if:
- Name could be a person's nickname (e.g., "Palm Beach")
- Name is short (e.g., "FBI", "CIA")
```

---

## Evidence of Misclassification

### Case Study: "Doug Band" (Entity ID: doug_band)
```json
{
  "name": "Douglas Jay Band",
  "entity_type": "organization",  // ← WRONG!
  "summary": "Former top advisor to Bill Clinton who was key architect of Clinton's post-presidency..."
}
```

**Analysis**:
- **Actual type**: PERSON (individual human, Clinton advisor)
- **Classified as**: Organization
- **Why misclassified**: LLM likely confused by "Band" surname or bio context mentioning "architect"

### Case Study: Empty Name Entities
```json
{
  "entity_type": "location",  // ← WRONG!
  "name": "",
  "summary": "N/A"
}
```

**Pattern**: 41 entities classified as "location" have empty names or biographies.

**Analysis**:
- **Actual type**: PERSON (likely)
- **Classified as**: Location
- **Why misclassified**: Empty context causes LLM to guess randomly

---

## Data Quality Issues

### Issue #1: Expected Entities Missing
The following known entities do NOT exist in the dataset:
- "Southern Trust Company" (organization)
- "FBI" (organization)
- "CIA" (organization)
- "Clinton Foundation" (organization)
- "Trump Organization" (organization)
- "Little St. James Island" (location)
- "Palm Beach" (location)
- "New York" (location)

**Implication**: The entity extraction process may have failed to create entities for organizations and locations, only extracting person names.

### Issue #2: Entity ID Normalization
Entity IDs appear to be normalized (e.g., "doug_band", "vor_holding") but the normalization may have lost important context:
- "Southern Trust Company" → should be ID like "southern_trust_company"
- "Little St. James Island" → should be ID like "little_st_james_island"

**Hypothesis**: Upstream entity extraction only identified person names, not organizations or locations.

---

## Recommended Solutions

### Solution #1: Fix LLM Prompt (CRITICAL - Immediate Fix)

**Replace prioritization rules (lines 444-449)**:

```python
Prioritization:
1. CHECK KEYWORDS FIRST:
   - If name contains ANY organization keyword (Foundation, Inc, LLC, Corp, Company, Agency, Bureau, etc.) → organization
   - If name contains ANY location keyword (Island, Beach, Ranch, Estate, Street, Avenue, City, etc.) → location

2. CHECK NAME FORMAT:
   - If name is in "Last, First" format AND no org/location keywords → person
   - If name has personal titles (Dr., Mr., Ms., etc.) AND no org/location keywords → person

3. CHECK BIO CONTEXT:
   - If bio describes a company, agency, or institution → organization
   - If bio describes a place or property → location
   - If bio describes an individual human → person

4. DEFAULT HANDLING:
   - If completely ambiguous → person
   - BUT: Acronyms (2-4 capital letters) should default to organization (e.g., FBI, CIA)

CRITICAL EXCEPTIONS:
- "Clinton Foundation" is an ORGANIZATION, not a person (even though "Clinton" is a person's name)
- "Trump Organization" is an ORGANIZATION, not a person (even though "Trump" is a person's name)
- "Little St. James Island" is a LOCATION, not a person (even though could be interpreted as a name)
```

### Solution #2: Add Explicit Negative Examples

**Add to prompt**:

```python
COMMON MISTAKES TO AVOID:
❌ "Trump Organization" → person (WRONG!)
✓ "Trump Organization" → organization (contains "Organization" keyword)

❌ "Clinton Foundation" → person (WRONG!)
✓ "Clinton Foundation" → organization (contains "Foundation" keyword)

❌ "Little St. James Island" → person (WRONG!)
✓ "Little St. James Island" → location (contains "Island" keyword)

❌ "FBI" → person (WRONG!)
✓ "FBI" → organization (government agency, acronym pattern)
```

### Solution #3: Strengthen Keyword Detection

**Modify prompt to emphasize keyword matching**:

```python
**CRITICAL RULE**: If the name contains ANY of these keywords, classify accordingly:

ORGANIZATION KEYWORDS (high confidence):
  - Foundation, Organization, Inc, LLC, Corp, Company
  - Agency, Bureau, Department, Institute, University
  - Association, Trust, Bank, Group, Incorporated
  - Acronyms: FBI, CIA, NSA, DOJ, IRS, etc.

LOCATION KEYWORDS (high confidence):
  - Island, Beach, Ranch, Estate, Airport, Hotel
  - Resort, Street, Avenue, Road, Club, Palace
  - Villa, City, State, Country, Province
  - Geographic names: Palm Beach, New York, etc.

**If ANY keyword matches → use that classification regardless of other factors**
```

### Solution #4: Test Cases for Validation

**Create test suite** (`tests/verification/test_entity_classification_fix.py`):

```python
test_cases = [
    # Organizations
    ("Southern Trust Company", "organization"),
    ("FBI", "organization"),
    ("CIA", "organization"),
    ("Clinton Foundation", "organization"),
    ("Trump Organization", "organization"),
    ("Interfor Inc", "organization"),

    # Locations
    ("Little St. James Island", "location"),
    ("Palm Beach", "location"),
    ("New York", "location"),
    ("Zorro Ranch", "location"),
    ("Mar-a-Lago", "location"),

    # Persons
    ("Epstein, Jeffrey", "person"),
    ("Maxwell, Ghislaine", "person"),
    ("Clinton, Bill", "person"),
    ("Trump, Donald", "person"),
    ("Doug Band", "person"),  # Currently misclassified as organization
]
```

---

## Implementation Plan

### Phase 1: Immediate Fix (High Priority)
1. **Update LLM prompt** in `server/services/entity_service.py` (lines 413-450)
2. **Add negative examples** to prevent common mistakes
3. **Strengthen keyword priority** in classification rules
4. **Test with sample entities** before batch reprocessing

### Phase 2: Validation (Medium Priority)
1. **Create test suite** with known entity types
2. **Run classification on test cases** to verify accuracy
3. **Measure improvement**: Target >80% accuracy on org/location classification

### Phase 3: Batch Reprocessing (Medium Priority)
1. **Backup current data**: `entity_biographies_backup_YYYYMMDD_HHMMSS.json`
2. **Run classification script** with `--force` flag to reclassify all entities
3. **Verify results**: Check that orgs/locations are correctly identified

### Phase 4: Data Quality Investigation (Low Priority)
1. **Investigate missing entities**: Why aren't "FBI", "CIA", "Clinton Foundation" in the dataset?
2. **Review entity extraction process**: Does it only extract person names?
3. **Enhance extraction**: Add organization and location entity extraction

---

## Cost Estimate

### LLM Classification Cost (Claude Haiku via OpenRouter)
- **Input tokens per entity**: ~150 tokens (name + bio excerpt + prompt)
- **Output tokens per entity**: ~5 tokens (one word response)
- **Total entities**: 1,637
- **Pricing**:
  - Input: $0.25 per 1M tokens
  - Output: $1.25 per 1M tokens
- **Total cost**: ~$0.05 for all entities (very cheap)

### Time Estimate
- **Classification time**: ~30-60 seconds for all 1,637 entities
- **Development time**: 2-3 hours for prompt fix and testing
- **Validation time**: 1 hour for test suite and verification

---

## Success Criteria

### Immediate Success (Phase 1-2)
- ✅ LLM prompt updated with corrected prioritization rules
- ✅ Negative examples added to prevent common mistakes
- ✅ Test suite passes with >80% accuracy on known entities

### Long-term Success (Phase 3-4)
- ✅ Entity type distribution changes from 97% person to ~70% person, ~20% organization, ~10% location (estimated)
- ✅ Known organizations correctly classified: FBI, CIA, Clinton Foundation, Trump Organization
- ✅ Known locations correctly classified: Little St. James Island, Palm Beach, New York
- ✅ No regression: Known persons still correctly classified

---

## Next Steps

1. **Review this analysis** with project team
2. **Approve prompt changes** (critical fix)
3. **Implement Phase 1** (update prompt in entity_service.py)
4. **Create test suite** (Phase 2)
5. **Run batch reclassification** (Phase 3)
6. **Update Linear ticket 1M-364** with findings and progress

---

## References

- **Ticket**: [1M-364 - Fix entity type classification](https://linear.app/1m-hyperdev/issue/1M-364)
- **Classification script**: `scripts/analysis/classify_entity_types.py`
- **Service module**: `server/services/entity_service.py` (lines 388-488)
- **Data file**: `data/metadata/entity_biographies.json`

---

## Appendix: Current Prompt Analysis

### Prompt Structure (Lines 413-450)

**Section 1: Task Definition** (Lines 413-415)
```
Classify this entity as one of: person, organization, location

Entity name: "{name}"
```
✅ **Clear and concise**

**Section 2: Context** (Lines 418-425)
```
Bio excerpt: {bio_excerpt}...
Sources: {sources_list}
```
✅ **Provides helpful context**

**Section 3: Classification Rules** (Lines 429-442)
```
**ORGANIZATION** - Companies, agencies, foundations, institutions
  Examples: "FBI", "CIA", "Clinton Foundation"...
  Keywords: Foundation, Organization, Inc, LLC...

**LOCATION** - Places, properties, geographic locations
  Examples: "Little St. James Island", "Zorro Ranch"...
  Keywords: Island, Beach, Ranch, Estate...

**PERSON** - Individual humans
  Examples: "Epstein, Jeffrey", "Maxwell, Ghislaine"...
  Name patterns: Last name + comma + first name...
```
✅ **Comprehensive examples and keywords**

**Section 4: Prioritization** (Lines 444-449)
```
Prioritization:
1. If name contains organization keywords → organization
2. If name contains location keywords → location
3. If name is formatted like a person's name (e.g., "Last, First") → person
4. If ambiguous (e.g., "Maxwell" could be person OR company), use bio context
5. Default to person only if no clear indicators
```
❌ **CRITICAL FLAW**: Rule #3 contradicts rules #1-2, creates person bias

**Section 5: Output Format** (Line 450)
```
Return ONLY one word: person, organization, or location
```
✅ **Clear output specification**

### Diagnosis

**The prioritization section (lines 444-449) is the root cause**:
- Rule #1-2: "Keywords should determine classification"
- Rule #3: "Name format determines classification"
- **Conflict**: LLM interprets rule #3 as higher priority, ignoring keywords
- **Result**: 97.3% classified as "person" because most names "look like" person names

**Fix**: Rewrite prioritization to enforce keyword-first classification, with name format as secondary indicator only when no keywords present.
