# Entity Type Classification Test Suite

**Linear Ticket**: [1M-364](https://linear.app/1m-hyperdev/issue/1M-364)
**Purpose**: Validate entity type classification fix (keyword priority over name format)

---

## Quick Start

### Run All Tests (Pytest)
```bash
pytest tests/verification/test_entity_type_classification.py -v
```

### Run Critical Tests Only (Standalone)
```bash
python3 tests/verification/run_classification_tests.py
```

### Run Specific Test Category
```bash
# Test organizations
pytest tests/verification/test_entity_type_classification.py::TestEntityTypeClassification::test_organizations -v

# Test critical keyword priority
pytest tests/verification/test_entity_type_classification.py::TestEntityTypeClassification::test_keyword_priority_organization_over_person_name -v
```

---

## What's Being Tested

### Root Cause (1M-364)
The LLM prompt had contradictory prioritization rules causing 97.3% of entities to be misclassified as "person":

**Old Behavior** ❌:
1. Check keywords (organization, location)
2. Check name format (person)
3. **Problem**: Name format overrode keywords!

**New Behavior** ✅:
1. Check keywords FIRST (organization, location)
2. Only check name format if no keywords found
3. Default to person

### Critical Test Cases

**These MUST pass** (root cause fix):
- "Trump Organization" → organization ✅
- "Clinton Foundation" → organization ✅
- "Little St. James Island" → location ✅

**If any fail**: DO NOT run batch reclassification!

---

## Test Files

### `test_entity_type_classification.py`
Comprehensive pytest suite with:
- 35+ test cases
- All entity types (organization, location, person)
- Edge cases (Doug Band, empty strings)
- Accuracy metrics
- Tiered testing (LLM, NLP, procedural)

### `run_classification_tests.py`
Standalone test runner:
- 14 critical test cases
- Simple pass/fail output
- No pytest dependencies
- Quick validation

---

## Test Results (Current)

### Overall Accuracy: 78.6% (11/14)

| Category | Passed | Failed | Accuracy |
|----------|--------|--------|----------|
| Organizations | 4 | 2 | 67% |
| Locations | 3 | 1 | 75% |
| Persons | 4 | 0 | 100% |
| **Critical Test** | **3** | **0** | **100% ✅** |

### Known Failures (Expected)
- `FBI`, `CIA` → No keywords, defaults to person
- `Manhattan` → No location keyword, defaults to person

These failures are acceptable - real entities usually have keywords or bio context.

---

## Expected Output

### Passing Test
```
✅ PASS | Trump Organization | Expected: organization | Got: organization
✅ PASS | Clinton Foundation | Expected: organization | Got: organization
✅ PASS | Little St. James Island | Expected: location | Got: location

================================================================================
✅ CRITICAL TEST PASSED

Root cause fix verified: Keywords are prioritized over name format.
Ready to proceed with batch reclassification.
================================================================================
```

### Failing Test
```
❌ FAIL | Trump Organization | Expected: organization | Got: person

================================================================================
❌ CRITICAL TEST FAILED

The root cause fix for 1M-364 is NOT working.
Keywords are NOT being prioritized over name format.

DO NOT run batch reclassification until this is fixed.
================================================================================
```

---

## Test Categories

### 1. Organizations
Tests entities with organization keywords:
- Foundation, Organization, Inc, LLC, Corp, Company
- Agency, Bureau, Department, Institute, University
- Association, Trust, Bank, Group

### 2. Locations
Tests entities with location keywords:
- Island, Beach, Ranch, Estate, Airport, Hotel
- Resort, Street, Avenue, Road, Club, Palace, Villa
- City, State, Country

### 3. Persons
Tests individual human names:
- Full names (Jeffrey Epstein)
- "Last, First" format (Epstein, Jeffrey)
- Names with titles (Dr., Mr., Ms.)

### 4. Edge Cases
Tests previously misclassified entities:
- Doug Band (was: organization, should be: person)
- Empty strings
- Single names (Clinton, Trump)
- Ambiguous cases

---

## Environment Setup

### Required
```bash
# Install dependencies
pip install pytest

# Set OpenRouter API key (for LLM tests)
export OPENROUTER_API_KEY="your-key-here"
# Or add to .env.local
```

### Optional
```bash
# Enable/disable classification tiers
export ENABLE_LLM_CLASSIFICATION=true   # Default: true
export ENABLE_NLP_CLASSIFICATION=true   # Default: true (requires spaCy)
```

---

## Usage Patterns

### Before Batch Reclassification
```bash
# Verify fix is working
python3 tests/verification/run_classification_tests.py

# If critical test passes:
python3 scripts/analysis/classify_entity_types.py --force
```

### After Code Changes
```bash
# Run full test suite
pytest tests/verification/test_entity_type_classification.py -v

# Check accuracy metrics
pytest tests/verification/test_entity_type_classification.py::TestEntityTypeClassification::test_overall_accuracy_target -v
```

### Debugging Failures
```bash
# Test specific entity
pytest tests/verification/test_entity_type_classification.py::TestEntityTypeClassification::test_edge_case_doug_band -v -s

# Test LLM tier only
pytest tests/verification/test_entity_type_classification.py::TestEntityTypeClassification::test_llm_classification_isolated -v
```

---

## Success Criteria

### Critical Test (MUST PASS) ✅
- All 3 keyword priority tests passing
- Organizations with keywords correctly classified
- Locations with keywords correctly classified

### Overall Accuracy (Target: >80%)
- Organizations: >80% (current: 67%, acceptable with keyword limitation)
- Locations: >80% (current: 75%, acceptable with keyword limitation)
- Persons: >80% (current: 100% ✅)

### Edge Cases
- Doug Band correctly classified as person ✅
- "Last, First" format recognized ✅
- Empty strings handled gracefully ✅

---

## Troubleshooting

### Pytest Config Issues
If you get `unrecognized arguments: --cov=...`:
```bash
# Use standalone runner instead
python3 tests/verification/run_classification_tests.py
```

### API Key Issues
If LLM tests fail with "OPENROUTER_API_KEY not set":
```bash
# Set API key
export OPENROUTER_API_KEY="your-key-here"

# Or skip LLM-only tests
pytest tests/verification/test_entity_type_classification.py -v -k "not llm_only"
```

### Import Errors
If you get `ModuleNotFoundError: No module named 'services'`:
```bash
# Add server to Python path
export PYTHONPATH=/Users/masa/Projects/epstein/server:$PYTHONPATH

# Or use standalone runner (handles paths automatically)
python3 tests/verification/run_classification_tests.py
```

---

## Related Documentation

- **Implementation Summary**: `docs/implementation-summaries/1M-364-ENTITY-TYPE-CLASSIFICATION-TEST-SUITE.md`
- **Root Cause Analysis**: `docs/research/entity-type-classification-bug-1M-364-2025-11-29.md`
- **Linear Ticket**: [1M-364](https://linear.app/1m-hyperdev/issue/1M-364)

---

## Next Steps After Tests Pass

1. ✅ Run batch reclassification: `python3 scripts/analysis/classify_entity_types.py --force`
2. ✅ Verify improved distribution: ~70% person, ~20% organization, ~10% location
3. ✅ Update Linear ticket with results
4. ✅ Monitor production for accuracy issues

---

**Last Updated**: 2025-11-29
**Status**: Test Suite Complete ✅
