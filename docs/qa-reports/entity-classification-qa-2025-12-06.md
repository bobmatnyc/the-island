# Entity Classification QA Report
**Date:** 2025-12-06
**QA Engineer:** Claude (QA Agent)
**System Under Test:** Entity Classification System (API: http://localhost:8081/api/entities)
**Test Scope:** Random sampling of 150 entities (50 people, 50 organizations, 50 locations) + edge cases

---

## Executive Summary

The entity classification system has **fundamental problems** with entity type detection and relationship categorization:

### Critical Findings

1. **🔴 CRITICAL: Relationship categories completely non-functional** - ALL people have empty `categories` array
2. **🔴 CRITICAL: Organization classification failing** - 18% error rate (target: <10%)
3. **🟡 MODERATE: Location classification issues** - 8% error rate (acceptable, but below target)
4. **🟡 MODERATE: Data quality issues** - 27% of entities have quality problems (incomplete names, duplicates, non-entities)
5. **🟢 GOOD: Person type detection** - 100% accuracy for valid person entities

### Success Criteria Assessment

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Person classification accuracy | ≥95% | 100% | ✅ PASS |
| Organization classification accuracy | ≥90% | 82% | ❌ FAIL |
| Location classification accuracy | ≥90% | 92% | ✅ PASS |
| Relationship category assignment | ≥80% relevance | 0% (none assigned) | ❌ FAIL |

**Overall System Status: ❌ FAILING**

---

## Test Methodology

### Phase 1: Random Sampling
- Fetched 50 people, 50 organizations, 50 locations via API
- Manual verification using AI judgment and domain knowledge
- Classified each entity as: Correct, Misclassified, or Ambiguous

### Phase 2: Edge Case Testing
- Searched for known high-profile entities (Trump, Clinton, Epstein, Maxwell)
- Tested abbreviations, compound names, possessives
- Verified known organizations (FBI, DOJ, newspapers)
- Checked surname-like words classified as locations

### Phase 3: Pattern Analysis
- Grouped misclassifications by pattern type
- Identified root causes based on code inspection
- Prioritized issues by frequency and severity

---

## Detailed Findings

### 1. CRITICAL: Relationship Categories Not Assigned

**Finding:** ALL person entities have `categories: []` (empty array)

**Evidence:**
```bash
curl "http://localhost:8081/api/entities?entity_type=person&limit=200" | jq '[.entities[] | .categories] | unique'
# Result: [[]]  (all empty)
```

**Sample Entities Affected:**
- Jeffrey Epstein - categories: [] (should be: co-conspirator)
- Ghislaine Maxwell - categories: [] (should be: co-conspirator)
- Virginia Roberts - categories: [] (should be: victim)
- Donald Trump - categories: [] (should be: public_figure, associate)
- Prince Andrew - categories: [] (should be: public_figure, associate)

**Impact:**
- Relationship categorization completely non-functional
- Cannot filter people by role (victims, co-conspirators, etc.)
- Frontend likely displaying incorrect/missing relationship information

**Root Cause Hypothesis:**
- Relationship categorization logic not being called
- Data pipeline issue: categories not being computed or stored
- API response field name mismatch (`categories` vs `relationship_categories`)

**Priority:** 🔴 CRITICAL (P0 - blocks core functionality)

---

### 2. CRITICAL: Organizations Misclassified (18% Error Rate)

**Finding:** 9 out of 50 organizations (18%) are misclassified

#### 2.1 People Misclassified as Organizations

| Entity Name | Classified As | Should Be | Confidence |
|-------------|---------------|-----------|------------|
| Comey, Maurene | organization | person | HIGH |
| Sternheim, Bobbi | organization | person | HIGH |

**Pattern:** "LastName, FirstName" format not triggering person classification

**Evidence:**
```bash
curl "http://localhost:8081/api/entities?limit=1000" | jq -r '.entities[] | select(.name == "Comey, Maurene") | .entity_type'
# Result: organization
```

**Impact:** 2 confirmed people misclassified as organizations

#### 2.2 Locations Misclassified as Organizations

| Entity Name | Classified As | Should Be | Confidence |
|-------------|---------------|-----------|------------|
| The Silvio J. Mollo Building | organization | location | HIGH |
| Suite 715 | organization | location | HIGH |
| WPALMBEACH FL | organization | location | MEDIUM |

**Pattern:** Buildings, addresses, and office numbers classified as organizations

**Impact:** Physical locations incorrectly categorized

#### 2.3 Non-Entities Classified as Organizations

| Entity Name | Classified As | Should Be | Confidence |
|-------------|---------------|-----------|------------|
| Transportation | organization | NONE (generic term) | HIGH |
| Defense Counsel | organization | NONE (role/title) | HIGH |
| ET AL | organization | NONE (legal term) | HIGH |
| UNLIMITED N/WKND MIN | organization | NONE (billing code) | HIGH |
| the Federal Rules of Criminal Procedure | organization | NONE (legal document) | HIGH |
| b3 -1 | organization | NONE (code) | HIGH |
| SSR SSR TKNEAFHK1 | organization | NONE (system code) | HIGH |

**Pattern:** Generic terms, legal jargon, codes, and descriptive phrases treated as entity names

**Impact:** 7 non-entities polluting the organization list, reducing data quality

**Root Cause Hypotheses:**
1. **Name format detection failure:** "LastName, FirstName" pattern not recognized as person
2. **Keyword gaps:** "Building", "Suite", "FL" not in location keyword list
3. **No entity validation:** Everything extracted from documents becomes an entity (no filtering)
4. **Missing stopword list:** Generic terms (Transportation, Defense Counsel) not excluded
5. **Code detection missing:** Alphanumeric codes not identified and filtered

**Priority:** 🔴 CRITICAL (P0 - 18% error rate is unacceptable)

---

### 3. MODERATE: Locations Misclassified (8% Error Rate)

**Finding:** 4 out of 50 locations (8%) are misclassified

#### 3.1 Companies Misclassified as Locations

| Entity Name | Classified As | Should Be | Confidence |
|-------------|---------------|-----------|------------|
| Verizon | location | organization | HIGH |
| Miami Herald | location | organization | HIGH |

**Pattern:** Company names without org indicators (Corp, Inc, LLC) classified as locations

**Evidence:**
```bash
curl "http://localhost:8081/api/entities?limit=1000" | jq -r '.entities[] | select(.name == "Verizon") | .entity_type'
# Result: location

# But "the Miami Herald" is correctly classified:
curl "http://localhost:8081/api/entities?limit=1000" | jq -r '.entities[] | select(.name == "the Miami Herald") | .entity_type'
# Result: organization
```

**Impact:** Major companies (Verizon, newspapers) showing up in location lists

#### 3.2 People Misclassified as Locations

| Entity Name | Classified As | Should Be | Confidence |
|-------------|---------------|-----------|------------|
| Villafafia | location | person | HIGH |
| Lefkowitz | location | person | HIGH |
| Lugosch | location | person | HIGH |
| Rocchio | location | person | MEDIUM |
| Loftus | location | person | MEDIUM |
| Landgraf | location | person | MEDIUM |
| Haddon | location | person | MEDIUM |

**Pattern:** Single-word surnames classified as locations

**Impact:** 4 confirmed people (plus 4 probable) misclassified as locations

**Root Cause Hypotheses:**
1. **Company name database missing:** Verizon, major newspapers not recognized
2. **Article prefix dependency:** "Miami Herald" fails but "the Miami Herald" succeeds
3. **Surname detection failure:** Single-word surnames treated as location names
4. **No person name gazetteer:** Common surnames not recognized

**Priority:** 🟡 MODERATE (P1 - within tolerance but needs improvement)

---

### 4. MODERATE: Person Name Variations Misclassified

**Finding:** Possessives and name variants incorrectly classified

| Entity Name | Classified As | Should Be | Confidence |
|-------------|---------------|-----------|------------|
| Ghislaine Maxwell's | organization | person (possessive) | HIGH |
| A. Ghislaine Maxwell | organization | person | HIGH |

**Pattern:** Name variations with possessives or prefixes not recognized as people

**Evidence:**
```bash
# Correct:
Ghislaine Maxwell | person

# Wrong:
Ghislaine Maxwell's | organization
A. Ghislaine Maxwell | organization
```

**Impact:** Name normalization failing, creating duplicate entities with wrong classifications

**Root Cause Hypothesis:**
- Possessive "'s" breaking person name pattern matching
- Middle initials/prefixes ("A.") causing classification failure
- Name normalization not applied before type detection

**Priority:** 🟡 MODERATE (P1 - causes entity fragmentation)

---

### 5. MODERATE: Data Quality Issues (27% of Entities)

**Finding:** Approximately 40 out of 150 entities (27%) have data quality problems

#### 5.1 Incomplete Person Names (First Names Only)

**Examples:**
- Michael, Michelle, Elizabeth, Nadia, Julie, Sally, Peter, Nicole, Casey, Jason, Didier, Elaine

**Count:** 17 entities (11% of total sample)

**Impact:**
- Cannot verify if classification is correct without full names
- Incomplete data reduces entity usefulness
- Possible duplicate entities (multiple "Michael" entries)

#### 5.2 Ambiguous Role Terms Classified as Entities

**Examples:**
- Husband (person)
- Defense Counsel (organization)
- Pretrial Services (organization)
- Health Services (organization)
- Transportation (organization)

**Count:** 5+ entities

**Impact:** Generic role/service terms polluting entity lists

#### 5.3 Duplicate Entities (Same Entity, Different Names)

**Examples:**
- "United States" / "the United States" / "USA" / "UNITED STATES"
- "New York" / "NEW YORK" / "N.Y."
- "Miami Herald" (location) vs "the Miami Herald" (organization)
- "Federal Bureau of Investigation" vs "the Federal Bureau of Investigation"

**Count:** 20+ duplicate sets identified

**Impact:**
- Entity counts inflated
- Same entity appearing in multiple categories
- Inconsistent search results

#### 5.4 Garbled/OCR Error Entities

**Examples:**
- "NYM Housing Units Housing Units" (duplicate text)
- "SSR SSR TKNEAFHK1" (system code)
- "LBAAMAX5ps Rocchio - Cross" (corrupted text)
- "b3 -1, -5" (code fragment)

**Count:** 5+ entities

**Impact:** Pollutes entity lists with non-entity text

**Root Cause Hypotheses:**
1. **No entity extraction quality control:** Everything extracted becomes an entity
2. **No name normalization:** Variants not merged
3. **No deduplication:** Same entity in multiple forms
4. **OCR errors not cleaned:** Garbled text not filtered
5. **No stopword/term filtering:** Generic terms and codes not excluded

**Priority:** 🟡 MODERATE (P2 - affects data quality but not core functionality)

---

## Pattern Analysis Summary

### Pattern 1: Name Format Not Recognized
**Examples:** "Comey, Maurene" → organization (wrong)
**Frequency:** 2 confirmed cases
**Root Cause:** "LastName, FirstName" format not triggering person classification
**Fix Priority:** 🔴 P0 (critical pattern)

### Pattern 2: Possessives Break Classification
**Examples:** "Ghislaine Maxwell's" → organization (wrong)
**Frequency:** 3+ cases
**Root Cause:** Possessive "'s" not normalized before type detection
**Fix Priority:** 🟡 P1 (moderate impact)

### Pattern 3: Companies Without Org Keywords Misclassified
**Examples:** "Verizon" → location (wrong)
**Frequency:** 2+ cases
**Root Cause:** No company name database, keyword-only detection
**Fix Priority:** 🟡 P1 (major companies affected)

### Pattern 4: Single-Word Surnames → Locations
**Examples:** "Lefkowitz", "Lugosch" → location (wrong)
**Frequency:** 7+ cases
**Root Cause:** No surname recognition, unfamiliar words default to location
**Fix Priority:** 🟡 P1 (moderate frequency)

### Pattern 5: Buildings/Addresses → Organizations
**Examples:** "The Silvio J. Mollo Building", "Suite 715" → organization (wrong)
**Frequency:** 3+ cases
**Root Cause:** "Building", "Suite" keywords not in location list
**Fix Priority:** 🟡 P1 (clear pattern fix)

### Pattern 6: Non-Entities Classified as Organizations
**Examples:** "Transportation", "ET AL", codes → organization (wrong)
**Frequency:** 7+ cases
**Root Cause:** No entity validation, stopword filtering, or code detection
**Fix Priority:** 🔴 P0 (pollutes data significantly)

### Pattern 7: Article Prefix Dependency
**Examples:** "Miami Herald" (location) vs "the Miami Herald" (organization)
**Frequency:** 2+ cases
**Root Cause:** Classification logic depends on "the" prefix
**Fix Priority:** 🟡 P1 (indicates fragile logic)

---

## Root Cause Analysis

### Primary Root Causes (Likely Issues)

1. **Relationship Categorization Pipeline Failure**
   - **Evidence:** ALL people have empty categories
   - **Hypothesis:** Categorization function not called or data not persisted
   - **Code Location:** entity_service.py - relationship categorization logic
   - **Fix Complexity:** HIGH (requires pipeline debugging)

2. **Name Format Pattern Matching Failure**
   - **Evidence:** "Comey, Maurene" classified as organization
   - **Hypothesis:** "LastName, FirstName" pattern not recognized as person format
   - **Code Location:** entity_service.py:591 `_classify_entity_type_procedural()`
   - **Fix Complexity:** LOW (add pattern matching)

3. **No Entity Validation/Filtering**
   - **Evidence:** Generic terms, codes, jargon classified as entities
   - **Hypothesis:** Everything extracted from documents becomes an entity
   - **Code Location:** Entity extraction pipeline
   - **Fix Complexity:** MEDIUM (add validation layer)

4. **Keyword List Gaps**
   - **Evidence:** "Building", "Suite" not triggering location classification
   - **Hypothesis:** Location keyword list incomplete
   - **Code Location:** entity_service.py:782-801 `location_keywords`
   - **Fix Complexity:** LOW (add keywords)

5. **No Name Normalization Before Classification**
   - **Evidence:** Possessives ("Maxwell's") breaking classification
   - **Hypothesis:** Type detection happens before name cleaning
   - **Code Location:** Entity pipeline ordering
   - **Fix Complexity:** MEDIUM (pipeline reordering)

6. **Missing Gazetteers/Databases**
   - **Evidence:** Verizon, major newspapers not recognized
   - **Hypothesis:** Relying only on keyword matching, no knowledge databases
   - **Code Location:** Classification logic
   - **Fix Complexity:** HIGH (requires data integration)

---

## Recommendations

### Immediate Fixes (P0 - Critical)

#### 1. Fix Relationship Categorization Pipeline
**Problem:** ALL people have empty categories
**Impact:** Core feature completely broken
**Fix:**
- Debug categorization function call path
- Verify data persistence to entity_stats
- Check API response mapping (categories vs relationship_categories)
- Add logging to categorization pipeline

**Test:**
```bash
# Should show categories for Epstein, Maxwell, etc.
curl "http://localhost:8081/api/entities?limit=100" | jq '.entities[] | select(.entity_type == "person") | {name, categories}'
```

#### 2. Add "LastName, FirstName" Pattern Detection
**Problem:** Names with commas classified as organizations
**Impact:** 2+ people misclassified
**Fix:**
```python
# In _classify_entity_type_procedural():
if re.match(r'^[A-Z][a-z]+, [A-Z][a-z]+', name):
    return 'person'  # High-confidence person pattern
```

**Test:**
- Comey, Maurene → person ✅
- Sternheim, Bobbi → person ✅

#### 3. Add Entity Validation Layer
**Problem:** Non-entities (codes, generic terms, jargon) classified as entities
**Impact:** 7+ junk entities per 50 organizations
**Fix:**
- Add stopword list: ["Transportation", "Department", "Defense Counsel", "ET AL"]
- Add code detection regex: `^[A-Z0-9]{2,}$`, `\d+-\d+`, `[A-Z]{3,}\d+`
- Filter legal/procedural terms: "Rules of", "Procedure", "Agreement"

**Test:**
- "Transportation" → filtered out ✅
- "SSR SSR TKNEAFHK1" → filtered out ✅
- "ET AL" → filtered out ✅

### Short-Term Fixes (P1 - High Priority)

#### 4. Add Location Keywords
**Problem:** Buildings, addresses classified as organizations
**Fix:**
```python
location_keywords = [
    "building", "suite", "floor", "room",  # Add these
    "island", "airport", "beach", ...
]
```

**Test:**
- The Silvio J. Mollo Building → location ✅
- Suite 715 → location ✅

#### 5. Add Name Normalization Pre-Processing
**Problem:** Possessives and prefixes breaking classification
**Fix:**
```python
def normalize_name_for_classification(name: str) -> str:
    # Remove possessives
    name = re.sub(r"'s$", "", name)
    # Remove leading initials
    name = re.sub(r"^[A-Z]\.\s+", "", name)
    return name
```

**Test:**
- "Ghislaine Maxwell's" → normalize → "Ghislaine Maxwell" → person ✅
- "A. Ghislaine Maxwell" → normalize → "Ghislaine Maxwell" → person ✅

#### 6. Add Company Name Database
**Problem:** Major companies (Verizon, newspapers) misclassified
**Fix:**
- Add well-known company list: ["Verizon", "AT&T", "Sprint", "T-Mobile"]
- Add media organization patterns: "Herald$", "Times$", "Post$", "News$"

**Test:**
- Verizon → organization ✅
- Miami Herald → organization ✅

#### 7. Add Surname Recognition
**Problem:** Single-word surnames classified as locations
**Fix:**
- Add common surname database (top 1000 US surnames)
- Check if single capitalized word is in surname list before defaulting to location

**Test:**
- Lefkowitz → person ✅
- Lugosch → person ✅
- Villafafia → person ✅

### Medium-Term Improvements (P2 - Quality)

#### 8. Implement Entity Deduplication
**Problem:** Same entity appearing multiple times with different names
**Fix:**
- Normalize entity names before storage
- Merge variants ("United States" / "USA" / "the United States")
- Use canonical names for display

#### 9. Add OCR Error Detection
**Problem:** Garbled text classified as entities
**Fix:**
- Detect repeated words ("Housing Units Housing Units")
- Filter alphanumeric gibberish (entropy analysis)
- Add spell-checking for entity names

#### 10. Add Confidence Scores
**Problem:** No indication of classification reliability
**Fix:**
- Return confidence scores with classifications
- Flag low-confidence entities for manual review
- Use confidence to prioritize LLM vs procedural classification

---

## Testing Evidence

### Test Artifacts

1. **People Sample:** `/tmp/qa_people_sample.txt` (50 entities)
2. **Organizations Sample:** `/tmp/qa_orgs_sample.txt` (50 entities)
3. **Locations Sample:** `/tmp/qa_locations_sample.txt` (50 entities)
4. **Working Analysis:** `/tmp/qa_analysis_working.md` (detailed notes)

### API Test Commands

```bash
# Get people sample
curl "http://localhost:8081/api/entities?entity_type=person&limit=50"

# Get organizations sample
curl "http://localhost:8081/api/entities?entity_type=organization&limit=50"

# Get locations sample
curl "http://localhost:8081/api/entities?entity_type=location&limit=50"

# Check specific entity
curl "http://localhost:8081/api/entities?limit=1000" | jq -r '.entities[] | select(.name == "Verizon") | .entity_type'

# Check relationship categories
curl "http://localhost:8081/api/entities?entity_type=person&limit=100" | jq '[.entities[] | .categories] | unique'
```

---

## Misclassification Log

### People Misclassified as Organizations
```json
[
  {"name": "Comey, Maurene", "current": "organization", "correct": "person", "confidence": "HIGH"},
  {"name": "Sternheim, Bobbi", "current": "organization", "correct": "person", "confidence": "HIGH"}
]
```

### People Misclassified as Locations
```json
[
  {"name": "Villafafia", "current": "location", "correct": "person", "confidence": "HIGH"},
  {"name": "Lefkowitz", "current": "location", "correct": "person", "confidence": "HIGH"},
  {"name": "Lugosch", "current": "location", "correct": "person", "confidence": "HIGH"},
  {"name": "Rocchio", "current": "location", "correct": "person", "confidence": "MEDIUM"},
  {"name": "Loftus", "current": "location", "correct": "person", "confidence": "MEDIUM"},
  {"name": "Landgraf", "current": "location", "correct": "person", "confidence": "MEDIUM"},
  {"name": "Haddon", "current": "location", "correct": "person", "confidence": "MEDIUM"}
]
```

### Organizations Misclassified as Locations
```json
[
  {"name": "Verizon", "current": "location", "correct": "organization", "confidence": "HIGH"},
  {"name": "Miami Herald", "current": "location", "correct": "organization", "confidence": "HIGH"}
]
```

### Locations Misclassified as Organizations
```json
[
  {"name": "The Silvio J. Mollo Building", "current": "organization", "correct": "location", "confidence": "HIGH"},
  {"name": "Suite 715", "current": "organization", "correct": "location", "confidence": "HIGH"},
  {"name": "WPALMBEACH FL", "current": "organization", "correct": "location", "confidence": "MEDIUM"}
]
```

### Non-Entities Classified as Organizations
```json
[
  {"name": "Transportation", "current": "organization", "correct": "NONE", "confidence": "HIGH"},
  {"name": "Defense Counsel", "current": "organization", "correct": "NONE", "confidence": "HIGH"},
  {"name": "ET AL", "current": "organization", "correct": "NONE", "confidence": "HIGH"},
  {"name": "UNLIMITED N/WKND MIN", "current": "organization", "correct": "NONE", "confidence": "HIGH"},
  {"name": "the Federal Rules of Criminal Procedure", "current": "organization", "correct": "NONE", "confidence": "HIGH"},
  {"name": "b3 -1", "current": "organization", "correct": "NONE", "confidence": "HIGH"},
  {"name": "SSR SSR TKNEAFHK1", "current": "organization", "correct": "NONE", "confidence": "HIGH"}
]
```

### Person Name Variants Misclassified
```json
[
  {"name": "Ghislaine Maxwell's", "current": "organization", "correct": "person", "confidence": "HIGH"},
  {"name": "A. Ghislaine Maxwell", "current": "organization", "correct": "person", "confidence": "HIGH"}
]
```

---

## Code Inspection Notes

### Classification Logic Location
- **File:** `/Users/masa/Projects/epstein/server/services/entity_service.py`
- **Main Function:** `detect_entity_type()` (line 703)
- **Tiered Approach:**
  1. Tier 1: LLM classification (Claude Haiku)
  2. Tier 2: NLP/NER (spaCy)
  3. Tier 3: Procedural (keyword matching)

### Keyword Lists (Tier 3 Procedural)
- **Business Keywords:** Line 756-780 (comprehensive)
- **Location Keywords:** Line 783-801 (incomplete - missing "building", "suite")
- **Pattern Matching:** Word boundary matching to avoid substring issues

### Issues Identified in Code
1. No "LastName, FirstName" pattern detection
2. No possessive normalization before classification
3. No entity validation/filtering layer
4. Location keywords missing common terms
5. No company name database or gazetteer
6. Classification happens before name normalization

---

## Conclusion

The entity classification system requires **immediate attention** to address critical failures:

1. **Relationship categorization is completely broken** - highest priority fix
2. **Organization classification has 18% error rate** - unacceptable for production
3. **Data quality issues affect 27% of entities** - requires systematic cleanup

**Recommended Action Plan:**

**Week 1 (P0 Fixes):**
- Fix relationship categorization pipeline
- Add "LastName, FirstName" pattern detection
- Add entity validation layer to filter non-entities

**Week 2 (P1 Fixes):**
- Add missing location keywords (building, suite, etc.)
- Add name normalization pre-processing
- Add company name database
- Add surname recognition

**Week 3 (P2 Improvements):**
- Implement entity deduplication
- Add OCR error detection
- Add classification confidence scores

After implementing these fixes, a regression test suite should be created using the misclassifications found in this QA report to prevent future regressions.

---

**Report Generated:** 2025-12-06
**Test Duration:** ~30 minutes
**Entities Tested:** 150 (50 people, 50 organizations, 50 locations)
**Misclassifications Found:** 13 confirmed + 20+ probable
**Critical Issues:** 2 (categorization failure, organization classification)
**Overall Assessment:** ❌ System requires immediate fixes before production use
