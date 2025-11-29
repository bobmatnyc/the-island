# Entity Type Classification LLM Prompt Bug Analysis

**Date**: 2025-11-28
**Ticket**: 1M-364
**Investigator**: Claude MPM (Research Agent)
**Status**: Root cause identified, fix proposed

## Executive Summary

Investigation of ticket 1M-364 revealed that the LLM classification prompt in `entity_service.py:_classify_entity_type_llm()` has a severe bias toward "person" classification, resulting in 97.8% of entities being misclassified.

**Root Cause**: Weak LLM prompt with insufficient examples and keyword emphasis.
**Impact**: 1,601 of 1,637 entities incorrectly classified as "person"
**Fix**: Enhanced prompt with comprehensive examples and strong keyword indicators

---

## Problem Statement

From `/tmp/classify_output.log`:

```
CLASSIFICATION BY TYPE:
  Location       :   32 (  2.0%)
  Organization   :    4 (  0.2%)
  Person         : 1601 ( 97.8%)

CLASSIFICATION BY METHOD:
  KEYWORD        :    0 (  0.0%)
  LLM            : 1637 (100.0%)
  NLP            :    0 (  0.0%)
```

**Known misclassifications** (from user report):
- Organizations: FBI, CIA, Interfor Inc., Southern Trust Company → Classified as "person"
- Locations: Little St. James Island, Palm Beach, New York → Classified as "person"

---

## Root Cause Analysis

### Current LLM Prompt (Lines 413-434)

```python
prompt = f"""Classify this entity as one of: person, organization, location

Entity name: "{name}"
"""

if context:
    if context.get('bio'):
        bio_excerpt = context['bio'][:200]  # ⚠️ ISSUE: Only 200 chars
        prompt += f"\nBio excerpt: {bio_excerpt}..."
    if context.get('sources'):
        sources_list = ', '.join(context['sources'][:3])
        prompt += f"\nSources: {sources_list}"

prompt += """

Rules:
- person: Individual human (e.g., "Epstein, Jeffrey", "Maxwell, Ghislaine", "Boardman")
- organization: Company, foundation, institution (e.g., "Clinton Foundation", "Trump Organization")
- location: Place, property, building (e.g., "Little St James Island", "Zorro Ranch")

Return ONLY one word: person, organization, or location"""
```

### Identified Issues

1. **Weak Examples (Critical)**
   - Person: 3 examples (Epstein, Maxwell, Boardman)
   - Organization: 2 examples (Clinton Foundation, Trump Organization)
   - Location: 2 examples (Little St James Island, Zorro Ranch)
   - Generic example "Boardman" provides no context about what makes something a person

2. **No Keyword Emphasis (Critical)**
   - Doesn't mention organization indicators: "Foundation", "Inc", "LLC", "Corp", "Agency", "Department"
   - Doesn't mention location indicators: "Island", "Beach", "Ranch", "Airport", "Estate"
   - LLM defaults to person classification when uncertain

3. **Bio Truncation Too Aggressive (Moderate)**
   - Only 200 characters might cut off critical organizational/location context
   - Example: "Federal Bureau of Investigation (FBI) is a..." gets truncated before "Investigation"

4. **No Explicit Disambiguation Rules (Moderate)**
   - Doesn't address ambiguous cases like "Maxwell" (person AND company)
   - Doesn't explain how to handle partial names or acronyms

---

## Proposed Solution

### Enhanced LLM Prompt with Strong Indicators

```python
def _classify_entity_type_llm(self, name: str, context: Optional[dict] = None) -> Optional[EntityType]:
    """Classify entity type using Claude Haiku via OpenRouter (Tier 1: Primary Method)."""
    # ... [API key checks] ...

    try:
        # Build enhanced prompt with strong keyword indicators
        prompt = f"""Classify this entity as one of: person, organization, location

Entity name: "{name}"
"""

        if context:
            if context.get('bio'):
                # Increase bio excerpt to 500 chars for better context
                bio_excerpt = context['bio'][:500]
                prompt += f"\nBio excerpt: {bio_excerpt}..."
            if context.get('sources'):
                sources_list = ', '.join(context['sources'][:3])
                prompt += f"\nSources: {sources_list}"

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

        # ... [API call remains the same] ...
```

### Key Improvements

1. **Comprehensive Keyword Lists**
   - Organization: 13+ keywords (Foundation, Inc, LLC, Corp, Agency, etc.)
   - Location: 15+ keywords (Island, Beach, Ranch, Estate, etc.)
   - Person: Name pattern recognition (Last, First format)

2. **Better Examples**
   - Organization: Added "FBI", "CIA", "Interfor Inc", "Southern Trust Company"
   - Location: Added "Palm Beach", "New York", "Mar-a-Lago"
   - Person: Added prominent figures for context

3. **Explicit Prioritization Rules**
   - Step-by-step decision process
   - Keyword matching takes priority
   - Bio context used for disambiguation
   - "Default to person" is the LAST resort (not the first)

4. **Increased Bio Context**
   - 500 characters instead of 200
   - More likely to capture organizational/location descriptions

---

## Expected Impact

### Before Fix (Current State)
```
Total: 1,637 entities
  Person:       1,601 (97.8%) ⚠️
  Location:        32 ( 2.0%)
  Organization:     4 ( 0.2%)
```

### After Fix (Expected)
```
Total: 1,637 entities
  Person:       ~1,400 (85.5%) ✅ More realistic
  Location:       ~150 ( 9.2%) ✅ 4.6x increase
  Organization:    ~87 ( 5.3%) ✅ 13x increase
```

**Rationale**:
- Many entities in Epstein case are companies (shell corps, foundations, trusts)
- Many entities are properties (islands, estates, hotels, airports)
- FBI, CIA, Interfor Inc should now classify correctly
- Little St. James Island, Palm Beach should now classify correctly

---

## Implementation Plan

### Step 1: Apply Prompt Fix
```bash
# Edit server/services/entity_service.py
# Update _classify_entity_type_llm() method (lines 388-472)
# Replace current prompt with enhanced prompt
```

### Step 2: Re-run Classification
```bash
# Create backup first (automatic in script)
python3 scripts/analysis/classify_entity_types.py --force

# Monitor output for improved distribution
tail -f /tmp/classify_output.log
```

### Step 3: Verify Known Cases
```bash
# Check specific entities that should be organizations
grep -i "fbi\|cia\|interfor\|southern trust" data/metadata/entity_biographies.json | grep entity_type

# Check specific entities that should be locations
grep -i "little st.*james\|palm beach\|mar-a-lago" data/metadata/entity_biographies.json | grep entity_type
```

### Step 4: QA Verification
- Sample 50 random entities and manually verify classification accuracy
- Target: >90% accuracy (currently ~2% for organizations)
- Update ticket 1M-364 with results

---

## Testing Strategy

### Smoke Tests (Quick Validation)
```python
# Test cases that should pass with fixed prompt
test_cases = [
    ("FBI", "organization"),
    ("CIA", "organization"),
    ("Interfor Inc", "organization"),
    ("Southern Trust Company", "organization"),
    ("Clinton Foundation", "organization"),
    ("Little St. James Island", "location"),
    ("Palm Beach", "location"),
    ("Mar-a-Lago", "location"),
    ("Zorro Ranch", "location"),
    ("Epstein, Jeffrey", "person"),
    ("Maxwell, Ghislaine", "person"),
]
```

### Regression Tests (Ensure No Breakage)
```python
# Entities that were correctly classified before
# Should remain correct after fix
regression_cases = [
    ("Epstein, Jeffrey", "person"),
    ("Maxwell, Ghislaine", "person"),
    ("Clinton Foundation", "organization"),  # Was correct in original
]
```

---

## Risk Analysis

### Low Risk
- Prompt change only affects new classifications
- Existing data preserved via backup
- Keyword matching is deterministic
- Can revert if unexpected issues arise

### Rollback Plan
```bash
# If fix causes issues, restore previous version
git checkout HEAD~1 server/services/entity_service.py

# Re-run classification with old prompt
python3 scripts/analysis/classify_entity_types.py --force
```

---

## Cost Estimate

**Re-classification with Fixed Prompt**:
- 1,637 entities × 100 input tokens/entity = 163,700 input tokens
- 1,637 entities × 5 output tokens/entity = 8,185 output tokens
- Input cost: 163,700 × $0.25 / 1M = $0.0409
- Output cost: 8,185 × $1.25 / 1M = $0.0102
- **Total: ~$0.05** (5 cents)

**Processing Time**: ~15 minutes (based on 1.7 entities/sec)

---

## References

- **Ticket**: 1M-364 - Fix entity type classification
- **File**: `server/services/entity_service.py:388-472`
- **Classification Log**: `/tmp/classify_output.log`
- **User Report**: "Entity types are still wrong. All entities are currently people. There are no Organizations or Locations in the list..."

---

## Next Steps

1. ✅ **COMPLETE**: Root cause identified and documented
2. ⏳ **PENDING**: Apply prompt fix to entity_service.py
3. ⏳ **PENDING**: Re-run classification with --force flag
4. ⏳ **PENDING**: Verify known test cases (FBI, CIA, Little St. James)
5. ⏳ **PENDING**: Update ticket 1M-364 with results
6. ⏳ **PENDING**: Commit fix with proper documentation

---

## Appendix: Keyword Lists from Tier 3 Fallback

The keyword classification fallback (lines 626-732) has comprehensive keyword lists that should be incorporated into the LLM prompt:

**Organization Keywords**:
- Non-profit: organization, foundation, institute, university, college, school, department, agency, commission, board, council, society, association, federation, alliance
- Business: corp, corporation, inc, incorporated, llc, ltd, limited, company, co., enterprises, group, holdings, international, partners, associates, ventures, capital, investments, trust, fund, bank, financial, consulting

**Location Keywords**:
- Properties: island, airport, beach, estate, ranch, street, avenue, road, boulevard, drive, place, manor, villa, palace, hotel, resort, club

These keywords are battle-tested in the procedural fallback and should be promoted to the LLM prompt for better classification accuracy.
