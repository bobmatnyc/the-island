# Deprecated Scripts

**Last Updated**: 2025-11-19
**Scripts Moved**: 16
**Reason**: Data pipeline consolidation (Phase 1 stabilization)

---

## Why These Scripts Are Deprecated

These scripts were **one-off fixes** or **duplicate implementations** created during iterative problem-solving. They are being phased out as part of the Data Pipeline Stabilization effort to:

1. **Prevent data corruption** from 37+ scripts modifying `ENTITIES_INDEX.json`
2. **Reduce maintenance burden** from duplicate/similar implementations
3. **Establish canonical paths** for each data transformation
4. **Enable proper orchestration** with clear dependencies

**DO NOT RUN THESE SCRIPTS** unless you understand their specific historical context.

---

## Deprecated Scripts by Category

### Analysis (12 scripts)
Scripts that performed one-off entity fixes or data quality improvements:

- `fix_entity_names.py` - **Replaced by**: `data_quality/normalize_entity_names.py`
  - Why deprecated: First iteration of entity name standardization, incomplete logic

- `fix_entity_name_formatting.py` - **Replaced by**: `data_quality/normalize_entity_names.py`
  - Why deprecated: Second iteration, still had edge cases

- `fix_entity_names_hybrid.py` - **Replaced by**: `data_quality/normalize_entity_names.py`
  - Why deprecated: Third iteration, merged into canonical script

- `final_entity_cleanup.py` - **Replaced by**: `analysis/final_entity_cleanup_complete.py`
  - Why deprecated: Incomplete cleanup, superseded by "complete" version

- `fix_nested_entity_refs.py` - **One-off fix** (2025-11-17)
  - Why deprecated: Fixed specific bug in entity references, no longer needed

- `remove_no_passengers_entity.py` - **One-off fix** (2025-11-17)
  - Why deprecated: Removed invalid "[No passengers listed]" entity

- `remove_invalid_entities.py` - **One-off fix** (2025-11-18)
  - Why deprecated: Removed malformed entities, now handled in validation

- `fix_duplicates_in_network.py` - **One-off fix** (2025-11-18)
  - Why deprecated: Fixed duplicate entities in network graph

- `entity_qa_mistral.py` - **Experimental** (2025-11-16)
  - Why deprecated: Mistral-based entity QA, replaced by GPT-4 version

- `comprehensive_entity_qa.py` - **Experimental** (2025-11-16)
  - Why deprecated: QA script for entity enrichment, not production-ready

### Data Quality (2 scripts)
Biography name format fixes (iterative improvements):

- `fix_biography_names.py` - **Replaced by**: `data_quality/fix_biography_names_v3.py`
  - Why deprecated: First iteration, didn't handle all edge cases

- `fix_biography_names_v2.py` - **Replaced by**: `data_quality/fix_biography_names_v3.py`
  - Why deprecated: Second iteration, improved but still incomplete

### Extraction (1 script)
Backup of old email extraction logic:

- `extract_emails_documentcloud_BACKUP.py` - **Backup** (2025-11-16)
  - Why deprecated: Backup before refactoring `extract_emails.py`
  - Safe to delete: Yes (original working version kept)

### Research (2 scripts)
Test/sample scripts for WHOIS enrichment:

- `test_whois.py` - **Test script** (2025-11-19)
  - Why deprecated: Testing WHOIS API integration
  - Replaced by: `basic_entity_whois.py` (production version)

- `whois_sample_run.py` - **Sample/demo** (2025-11-19)
  - Why deprecated: Demonstration of WHOIS functionality
  - Use instead: `basic_entity_whois.py` with sample entities

### Import (1 script)
Test for Hugging Face import:

- `test_import.py` - **Test script** (2025-11-18)
  - Why deprecated: Testing import functionality
  - Production scripts: `import_huggingface_documents.py`, `import_huggingface_emails.py`

---

## What Replaced These Scripts?

### Canonical Entity Processing
All entity modifications should now go through:

1. **`data_quality/normalize_entity_names.py`** - Name standardization
2. **`data_quality/merge_epstein_duplicates.py`** - Duplicate merging
3. **`data_quality/restore_entity_bios.py`** - Biography restoration
4. **`analysis/final_entity_cleanup_complete.py`** - Final cleanup
5. **`research/enrich_entity_data.py`** - Entity enrichment

### Canonical Document Processing
Document indexing should use:

1. **`data_quality/rebuild_all_documents_index.py`** - Master document index
2. **`indexing/build_unified_index.py`** - Unified semantic index

---

## Can These Scripts Be Deleted?

### Safe to Delete (After Phase 1 Validation)
- All `fix_entity_*` scripts (fixes already applied)
- All `remove_*` scripts (removals already done)
- `extract_emails_documentcloud_BACKUP.py` (backup no longer needed)
- Test/sample scripts (`test_*.py`, `*_sample_run.py`)

### Keep for Reference (Until Phase 3)
- Biography fix scripts (may need to understand logic for future issues)
- QA/enrichment scripts (useful patterns for future development)

---

## Migration Timeline

- **Phase 1** (Current): Scripts moved to DEPRECATED, warnings added
- **Phase 2** (Week 3-4): Canonical scripts established, testing complete
- **Phase 3** (Week 5-6): Safe deletion after 2-week deprecation period

---

## How to Handle If You Need This Functionality

If you need to perform a similar operation:

1. **DO NOT run the deprecated script directly**
2. **Check if canonical script exists** (see `scripts/CANONICAL_SCRIPTS.md`)
3. **If no canonical script exists**:
   - Review deprecated script to understand logic
   - Implement in canonical location (with code review)
   - Add to `CANONICAL_SCRIPTS.md`
4. **Use new atomic write patterns** (see `scripts/lib/atomic_io.py`)

---

## Questions?

See:
- `DATA_PIPELINE_AUDIT_REPORT.md` - Full pipeline analysis
- `scripts/CANONICAL_SCRIPTS.md` - Official script list
- `scripts/MIGRATION_GUIDE.md` - Migration instructions

**Contact**: @masa (project maintainer)
