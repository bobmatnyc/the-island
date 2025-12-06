DOCUMENT DATA INTEGRITY REPORT
============================================================
Generated: 2025-12-06T18:27:20.334135
Documents File: data/transformed/document_classifications.json
Schema File: data/schemas/document_schema.json

OVERVIEW
------------------------------------------------------------
Total Documents: 38,482

UUID INTEGRITY
------------------------------------------------------------
✗ FAIL - Issues found:
  Unique IDs: 38,482
  Duplicate IDs: 0
  Invalid IDs: 305
  Errors:
    Found 305 invalid document IDs (not SHA256 format)
      - Invalid ID: DOJ-OGR-00015682 (file: DOJ-OGR-00015682_metadata.json)
      - Invalid ID: DOJ-OGR-00015681 (file: DOJ-OGR-00015681_metadata.json)
      - Invalid ID: DOJ-OGR-00032939 (file: DOJ-OGR-00032939_metadata.json)
      - Invalid ID: DOJ-OGR-00032940 (file: DOJ-OGR-00032940_metadata.json)
      - Invalid ID: DOJ-OGR-00031096 (file: DOJ-OGR-00031096_metadata.json)

CLASSIFICATION COVERAGE
------------------------------------------------------------
✗ FAIL - Issues found:
  Coverage: 100.00%
  Missing Classifications: 0
  Invalid Classifications: 278

  Distribution by Type:
    government_document       37,469 (97.37%)
    court_record                 362 ( 0.94%)
    email                        305 ( 0.79%)
    media_article                 45 ( 0.12%)
    fbi_report                    22 ( 0.06%)
    contact_directory              1 ( 0.00%)
  Errors:
    Found 278 documents with invalid classification
      - Invalid: 'court_filing' (doc: c6fc11e54e6bae261b1286e1bf5da40e0fc6ff56d396ae8877afb455a51cedcd)
      - Invalid: 'court_filing' (doc: 6170366f3d883cf30514dc31f4cc52fb950af0c670cc8b03564b9686aab65ff4)
      - Invalid: 'court_filing' (doc: 2c1be9fb4ae9d503e24f20d549d5f5e0530a47a2a82de90ffb8232971f3819bd)
      - Invalid: 'court_filing' (doc: b8e4245a07825f16dcb8dc97299ee3ff03b11673c56f68d9aec25072d7232ebb)
      - Invalid: 'court_filing' (doc: 7d7a6c0bdd37bded475f69336bfe24f9efccf2f98bb1d833fe8648f646f932dd)

REQUIRED FIELDS
------------------------------------------------------------
✓ PASS - All required fields present

DATA CONSISTENCY
------------------------------------------------------------
✗ FAIL - Consistency issues found:
  Found 305 documents with unexpected path format
    - Unexpected path: /Users/masa/Projects/epstein/data/emails/house_oversight_nov2025/2001-05/DOJ-OGR-00015682_metadata.json
    - Unexpected path: /Users/masa/Projects/epstein/data/emails/house_oversight_nov2025/2001-25/DOJ-OGR-00015681_metadata.json
    - Unexpected path: /Users/masa/Projects/epstein/data/emails/house_oversight_nov2025/2005-09/DOJ-OGR-00032939_metadata.json
    - Unexpected path: /Users/masa/Projects/epstein/data/emails/house_oversight_nov2025/2005-09/DOJ-OGR-00032940_metadata.json
    - Unexpected path: /Users/masa/Projects/epstein/data/emails/house_oversight_nov2025/2005-11/DOJ-OGR-00031096_metadata.json

  Confidence Score Distribution:
    High        1,011 ( 2.63%)
    Medium     37,471 (97.37%)
    Low             0 ( 0.00%)

  Classification Methods:
    existing             37,770 (98.15%)
    path_source             707 ( 1.84%)
    content_analysis          5 ( 0.01%)

FILE EXISTENCE
------------------------------------------------------------
✓ PASS - All sampled files exist (100 checked)

SCHEMA COMPLIANCE
------------------------------------------------------------
✓ PASS - Schema compliance verified

  Notes:
    Documents use interim classification format. Full schema compliance will be verified after transformation to canonical format.

============================================================
SUMMARY
============================================================
✗ OVERALL STATUS: FAIL
  Critical issues found: 18
  Warnings: 1

Verification completed: 2025-12-06T18:27:20.334185