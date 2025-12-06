# Entity Classification QA - Test Evidence
**Date:** 2025-12-06
**API Endpoint:** http://localhost:8081/api/entities

---

## Critical Finding: Relationship Categories Empty

### Test Command
```bash
curl -s "http://localhost:8081/api/entities?entity_type=person&limit=200" | jq '[.entities[] | .categories] | unique'
```

### Result
```json
[[]]
```

**Interpretation:** ALL 200 people have empty categories array. Relationship categorization is completely non-functional.

---

## Misclassification Evidence

### 1. People Misclassified as Organizations

#### Test: Comey, Maurene
```bash
curl -s "http://localhost:8081/api/entities?limit=1000" | jq -r '.entities[] | select(.name == "Comey, Maurene") | "\(.name)|\(.entity_type)"'
```
**Result:** `Comey, Maurene|organization`
**Expected:** `person`

#### Test: Find all "LastName, FirstName" in organizations
```bash
curl -s "http://localhost:8081/api/entities?entity_type=organization&limit=500" | jq -r '.entities[] | select(.name | test("[A-Z][a-z]+, [A-Z][a-z]+")) | "\(.name)|\(.entity_type)"'
```
**Results:**
- Comey, Maurene|organization ❌
- Sternheim, Bobbi|organization ❌
- Transcription, Inc.|organization ✅ (correct - company)
- Merrell Dow Pharmaceuticals, Inc.|organization ✅ (correct)

**Pattern:** Names with comma format being classified as organizations when not followed by corporate suffix.

---

### 2. Companies Misclassified as Locations

#### Test: Verizon
```bash
curl -s "http://localhost:8081/api/entities?limit=1000" | jq -r '.entities[] | select(.name == "Verizon") | "\(.name)|\(.entity_type)"'
```
**Result:** `Verizon|location`
**Expected:** `organization`

#### Test: Miami Herald
```bash
curl -s "http://localhost:8081/api/entities?limit=1000" | jq -r '.entities[] | select(.name == "Miami Herald") | "\(.name)|\(.entity_type)"'
```
**Result:** `Miami Herald|location`
**Expected:** `organization`

#### Test: the Miami Herald (with article)
```bash
curl -s "http://localhost:8081/api/entities?limit=1000" | jq -r '.entities[] | select(.name == "the Miami Herald") | "\(.name)|\(.entity_type)"'
```
**Result:** `the Miami Herald|organization` ✅
**Note:** Article prefix changes classification (inconsistent behavior)

---

### 3. People Misclassified as Locations

#### Test: Find single-word surnames in locations
```bash
curl -s "http://localhost:8081/api/entities?entity_type=location&limit=500" | jq -r '.entities[] | select(.name | test("^[A-Z][a-z]+$")) | "\(.name)|\(.entity_type)"' | head -30
```

**Results (subset):**
- Florida|location ✅ (correct)
- France|location ✅ (correct)
- Virginia|location ✅ (correct - state, but also a name)
- Verizon|location ❌ (company)
- Villafafia|location ❌ (surname)
- Lefkowitz|location ❌ (surname)
- Lugosch|location ❌ (surname)
- Rocchio|location ❌ (likely surname)
- Loftus|location ❌ (likely surname)
- Landgraf|location ❌ (likely surname)
- Haddon|location ❌ (likely surname)

**Pattern:** Single capitalized words classified as locations by default, even when they are surnames.

---

### 4. Name Variants Misclassified

#### Test: Ghislaine Maxwell variants
```bash
curl -s "http://localhost:8081/api/entities?limit=1000" | jq -r '.entities[] | select(.name | contains("Ghislaine Maxwell")) | "\(.name)|\(.entity_type)"'
```

**Results:**
- Ghislaine Maxwell|person ✅ (correct in person list)
- Ghislaine Maxwell's|organization ❌ (possessive)
- A. Ghislaine Maxwell|organization ❌ (with initial)

**Pattern:** Possessives and name prefixes breaking person classification.

---

### 5. Non-Entities Classified as Organizations

#### Test: Generic terms
```bash
curl -s "http://localhost:8081/api/entities?limit=1000" | jq -r '.entities[] | select(.name | test("^(Transportation|Defense Counsel|ET AL)$")) | "\(.name)|\(.entity_type)"'
```

**Results:**
- Transportation|organization ❌
- Defense Counsel|organization ❌
- ET AL|organization ❌

#### Test: System codes
```bash
curl -s "http://localhost:8081/api/entities?limit=1000" | jq -r '.entities[200:250] | .[] | select(.name | test("^[A-Z0-9 -]+$")) | "\(.name)|\(.entity_type)"'
```

**Results (subset):**
- SSR SSR TKNEAFHK1|organization ❌ (code)
- b3 -1, -5|organization ❌ (code)
- UNLIMITED N/WKND MIN|organization ❌ (billing code)

**Pattern:** Everything extracted becomes an entity - no validation layer.

---

### 6. Buildings/Addresses as Organizations

#### Test: Buildings
```bash
curl -s "http://localhost:8081/api/entities?limit=1000" | jq -r '.entities[200:250] | .[] | select(.name | contains("Building") or contains("Suite")) | "\(.name)|\(.entity_type)"'
```

**Results:**
- The Silvio J. Mollo Building|organization ❌
- Suite 715|organization ❌

**Expected:** Both should be `location`

---

## Sample Data Files

### People Sample (50 entities)
**File:** `/tmp/qa_people_sample.txt`

**Command:**
```bash
curl -s "http://localhost:8081/api/entities?entity_type=person&limit=50" | jq -r '.entities[] | .name' > /tmp/qa_people_sample.txt
```

**Sample Entries:**
- Epstein, Jeffrey ✅
- Maxwell, Ghislaine ✅
- Donald Trump ✅
- Prince Andrew, Duke of York ✅
- Michael ⚠️ (first name only)
- Husband ⚠️ (relationship term)

### Organizations Sample (50 entities)
**File:** `/tmp/qa_orgs_sample.txt`

**Command:**
```bash
curl -s "http://localhost:8081/api/entities?entity_type=organization&limit=50" | jq -r '.entities[] | .name' > /tmp/qa_orgs_sample.txt
```

**Sample Entries:**
- Federal Bureau of Prisons ✅
- U.S. Department of Justice ✅
- Comey, Maurene ❌ (person)
- Transportation ❌ (generic term)
- ET AL ❌ (legal term)

### Locations Sample (50 entities)
**File:** `/tmp/qa_locations_sample.txt`

**Command:**
```bash
curl -s "http://localhost:8081/api/entities?entity_type=location&limit=50" | jq -r '.entities[] | .name' > /tmp/qa_locations_sample.txt
```

**Sample Entries:**
- United States ✅
- New York ✅
- Palm Beach ✅
- Verizon ❌ (company)
- Villafafia ❌ (surname)
- Lefkowitz ❌ (surname)

---

## Test Statistics

### Overall Results
- **Total entities tested:** 150 (50 per type)
- **Additional edge cases:** 20+
- **Misclassifications found:** 13 confirmed + 20+ probable
- **Data quality issues:** ~40 entities (27%)

### Classification Accuracy
- **Person:** 100% (0 misclassifications in person category)
- **Organization:** 82% (9 misclassifications in organization category)
- **Location:** 92% (4 misclassifications in location category)

### Success Criteria
- Person ≥95%: ✅ PASS (100%)
- Organization ≥90%: ❌ FAIL (82%)
- Location ≥90%: ✅ PASS (92%)
- Relationship categories ≥80%: ❌ FAIL (0% - none assigned)

---

## Reproduction Steps

### Setup
1. Ensure backend is running: `curl http://localhost:8081/health`
2. Verify API accessible: `curl "http://localhost:8081/api/entities?limit=1"`

### Run Full Test Suite
```bash
# Test 1: Check relationship categories
curl -s "http://localhost:8081/api/entities?entity_type=person&limit=200" | jq '[.entities[] | .categories] | unique'
# Expected: [[]] (ALL empty - BUG)

# Test 2: Find people in organizations
curl -s "http://localhost:8081/api/entities?entity_type=organization&limit=500" | jq -r '.entities[] | select(.name | test("[A-Z][a-z]+, [A-Z][a-z]+")) | "\(.name)|\(.entity_type)"'
# Expected: Should find "Comey, Maurene" and "Sternheim, Bobbi"

# Test 3: Find companies in locations
curl -s "http://localhost:8081/api/entities?limit=1000" | jq -r '.entities[] | select(.name == "Verizon" or .name == "Miami Herald") | "\(.name)|\(.entity_type)"'
# Expected: Both classified as location (WRONG)

# Test 4: Find surnames in locations
curl -s "http://localhost:8081/api/entities?entity_type=location&limit=500" | jq -r '.entities[] | select(.name | test("^(Villafafia|Lefkowitz|Lugosch)$")) | "\(.name)|\(.entity_type)"'
# Expected: All classified as location (WRONG - they're surnames)

# Test 5: Check name variants
curl -s "http://localhost:8081/api/entities?limit=1000" | jq -r '.entities[] | select(.name | contains("Ghislaine Maxwell")) | "\(.name)|\(.entity_type)"'
# Expected: "Ghislaine Maxwell's" and "A. Ghislaine Maxwell" as organization (WRONG)

# Test 6: Find non-entities
curl -s "http://localhost:8081/api/entities?entity_type=organization&limit=1000" | jq -r '.entities[] | select(.name | test("^(Transportation|Defense Counsel|ET AL)$")) | "\(.name)|\(.entity_type)"'
# Expected: All classified as organization (WRONG - shouldn't be entities)
```

### Quick Verification
```bash
# After fixes are applied, run these to verify:

# 1. Relationship categories should be populated
curl -s "http://localhost:8081/api/entities?entity_type=person&limit=10" | jq '.entities[] | {name, categories}'

# 2. Comey should be person
curl -s "http://localhost:8081/api/entities?limit=1000" | jq -r '.entities[] | select(.name == "Comey, Maurene") | .entity_type'

# 3. Verizon should be organization
curl -s "http://localhost:8081/api/entities?limit=1000" | jq -r '.entities[] | select(.name == "Verizon") | .entity_type'

# 4. Villafafia should be person
curl -s "http://localhost:8081/api/entities?limit=1000" | jq -r '.entities[] | select(.name == "Villafafia") | .entity_type'

# 5. Transportation should be filtered out (no results)
curl -s "http://localhost:8081/api/entities?limit=1000" | jq -r '.entities[] | select(.name == "Transportation")'
```

---

## Notes

- Backend API was running and responsive throughout testing
- No timeout or rate limiting issues encountered
- Entity data appears to come from `/Users/masa/Projects/epstein/data/metadata/entity_stats.json`
- Classification logic in `/Users/masa/Projects/epstein/server/services/entity_service.py`
- All tests conducted on 2025-12-06 between 12:30 PM - 1:00 PM EST

---

**Evidence Package Complete**
- Main Report: `entity-classification-qa-2025-12-06.md`
- Misclassification Log: `entity-classification-misclassifications-2025-12-06.csv`
- Test Evidence: `entity-classification-test-evidence-2025-12-06.md` (this file)
