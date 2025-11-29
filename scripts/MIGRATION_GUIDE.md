# Data Pipeline Migration Guide

**Last Updated**: 2025-11-19
**Status**: Phase 1 Complete - Stabilization Tools Ready
**Purpose**: Guide for adopting new pipeline standards

---

## Overview

This guide helps you migrate existing scripts to use the new stabilization tools:

1. **Atomic writes** - Prevent data corruption
2. **Metadata tracking** - Track data provenance
3. **Canonical scripts** - Single source of truth per transformation

---

## Phase 1: Stabilization (CURRENT - Week 1-2)

### ✅ Completed

- [x] Moved 16 deprecated scripts to `DEPRECATED/`
- [x] Documented canonical scripts in `CANONICAL_SCRIPTS.md`
- [x] Created atomic write helpers (`lib/atomic_io.py`)
- [x] Added metadata tracking (`lib/metadata_tracker.py`)
- [x] Initialized `.pipeline_metadata.json`
- [x] All atomic_io tests passing (23/23)

### 🎯 Next Steps

- [ ] Update critical scripts to use atomic writes
- [ ] Add metadata tracking to canonical scripts
- [ ] Validate no disruption to existing functionality

---

## How to Use New Tools

### 1. Atomic Writes (MANDATORY for all data modifications)

**Old Pattern** (UNSAFE - can corrupt data on interruption):
```python
import json

# ❌ NEVER DO THIS
with open('data/entities/ENTITIES_INDEX.json', 'w') as f:
    json.dump(entities, f)
```

**New Pattern** (SAFE - atomic all-or-nothing):
```python
from scripts.lib.atomic_io import atomic_write_json

# ✅ DO THIS
atomic_write_json('data/entities/ENTITIES_INDEX.json', entities)
```

**Why This Matters**:
- Script crashes during write → old way leaves corrupt JSON
- Script crashes during write → new way preserves original file
- Network interruptions, system crashes, keyboard interrupts all safe

**Available Functions**:

```python
from scripts.lib.atomic_io import (
    atomic_write_json,          # Write JSON atomically
    atomic_write_text,           # Write text atomically
    safe_backup,                 # Create timestamped backup
    atomic_update_json,          # Load-modify-save pattern
    atomic_write_json_with_backup # Write with auto backup
)

# Basic write
atomic_write_json('output.json', data)

# Write with automatic backup
backup_path = atomic_write_json_with_backup('entities.json', entities)
print(f"Backup saved to: {backup_path}")

# Update existing file safely
def add_entity(data):
    data['entities']['new_person'] = {...}
    return data

atomic_update_json('entities.json', add_entity, create_backup=True)

# Create backup before risky operation
backup = safe_backup('entities.json')
# ... risky operation ...
# If it fails, restore from backup
```

### 2. Metadata Tracking (RECOMMENDED for all canonical scripts)

**Add to end of processing scripts**:

```python
from scripts.lib.metadata_tracker import record_update

# Example: entity_network.py
def main():
    # ... your processing logic ...

    entities = build_entity_network()

    # Write output atomically
    atomic_write_json('data/entities/ENTITIES_INDEX.json', entities)

    # Record metadata
    record_update(
        artifact_name="ENTITIES_INDEX.json",
        script_name="entity_network.py",
        details={
            "entities_processed": len(entities),
            "relationships_found": count_relationships(entities),
            "processing_time_seconds": elapsed_time
        }
    )

if __name__ == "__main__":
    main()
```

**Query metadata**:

```python
from scripts.lib.metadata_tracker import (
    get_last_update,
    get_recent_updates,
    needs_update,
    print_metadata_summary
)

# Check when artifact was last updated
info = get_last_update("ENTITIES_INDEX.json")
if info:
    print(f"Last updated: {info['last_updated']}")
    print(f"Updated by: {info['updated_by']}")
    print(f"Details: {info['details']}")

# Check if rebuild needed
if needs_update("entity_network.json", ["ENTITIES_INDEX.json"]):
    print("Entities changed, need to rebuild network")
    rebuild_network()

# View all metadata
print_metadata_summary()
```

### 3. Migration Checklist for Existing Scripts

For each script that modifies data files:

- [ ] **Replace `json.dump()` with `atomic_write_json()`**
  - Search: `with open(.*'w'.*) as.*:.*json.dump`
  - Replace with: `atomic_write_json(filepath, data)`

- [ ] **Add metadata tracking at end of script**
  - Import: `from scripts.lib.metadata_tracker import record_update`
  - Add: `record_update(artifact_name, script_name, details)`

- [ ] **Create backup before risky operations**
  - Import: `from scripts.lib.atomic_io import safe_backup`
  - Add: `backup_path = safe_backup(filepath)`

- [ ] **Update imports**
  - Add: `from pathlib import Path`
  - Add: `from scripts.lib.atomic_io import atomic_write_json`

- [ ] **Test changes**
  - Run script on test data
  - Verify output is correct
  - Check `.pipeline_metadata.json` updated
  - Verify backups created

---

## Example Migrations

### Example 1: Simple Entity Processing Script

**Before** (analysis/entity_network.py - simplified):
```python
#!/usr/bin/env python3
import json

def build_entity_network():
    # ... processing logic ...
    return entities

def main():
    entities = build_entity_network()

    # ❌ UNSAFE: Direct write
    with open('/Users/masa/Projects/Epstein/data/entities/ENTITIES_INDEX.json', 'w') as f:
        json.dump(entities, f, indent=2)

    print(f"Processed {len(entities)} entities")

if __name__ == "__main__":
    main()
```

**After** (migrated to atomic writes + metadata tracking):
```python
#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime

# NEW: Import atomic I/O and metadata tracking
from scripts.lib.atomic_io import atomic_write_json_with_backup
from scripts.lib.metadata_tracker import record_update

def build_entity_network():
    # ... processing logic ...
    return entities

def main():
    start_time = datetime.now()

    entities = build_entity_network()

    # NEW: Use relative path from project root
    project_root = Path(__file__).parent.parent.parent
    filepath = project_root / "data" / "entities" / "ENTITIES_INDEX.json"

    # NEW: Atomic write with automatic backup
    backup_path = atomic_write_json_with_backup(filepath, entities)

    if backup_path:
        print(f"Backup created: {backup_path}")

    # NEW: Record metadata
    elapsed = (datetime.now() - start_time).total_seconds()
    record_update(
        artifact_name="ENTITIES_INDEX.json",
        script_name="entity_network.py",
        details={
            "entities_processed": len(entities),
            "processing_time_seconds": elapsed
        }
    )

    print(f"Processed {len(entities)} entities")
    print(f"Output: {filepath}")

if __name__ == "__main__":
    main()
```

**Changes Made**:
1. ✅ Added imports for `atomic_io` and `metadata_tracker`
2. ✅ Replaced hard-coded path with relative path from project root
3. ✅ Replaced `json.dump()` with `atomic_write_json_with_backup()`
4. ✅ Added metadata tracking with processing details
5. ✅ Added timing information to metadata
6. ✅ Better error messages and logging

### Example 2: Document Indexing Script

**Before** (data_quality/rebuild_all_documents_index.py - simplified):
```python
#!/usr/bin/env python3
import json
import shutil
from pathlib import Path

def build_index():
    # ... process documents ...
    return {"documents": [...]}

def main():
    output_path = Path("data/metadata/all_documents_index.json")

    # ❌ Manual backup management
    if output_path.exists():
        backup_dir = Path("data/metadata/backups")
        backup_dir.mkdir(exist_ok=True)
        shutil.copy(output_path, backup_dir / "all_documents_index.json.backup")

    index = build_index()

    # ❌ UNSAFE: Direct write
    with open(output_path, 'w') as f:
        json.dump(index, f, indent=2)

if __name__ == "__main__":
    main()
```

**After**:
```python
#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime

from scripts.lib.atomic_io import atomic_write_json_with_backup
from scripts.lib.metadata_tracker import record_update

def build_index():
    # ... process documents ...
    return {"documents": [...]}

def main():
    start_time = datetime.now()

    project_root = Path(__file__).parent.parent.parent
    output_path = project_root / "data" / "metadata" / "all_documents_index.json"

    index = build_index()

    # NEW: Automatic backup with atomic write
    backup_path = atomic_write_json_with_backup(output_path, index)

    # NEW: Record metadata
    elapsed = (datetime.now() - start_time).total_seconds()
    record_update(
        artifact_name="all_documents_index.json",
        script_name="rebuild_all_documents_index.py",
        details={
            "document_count": len(index["documents"]),
            "processing_time_seconds": elapsed,
            "backup_path": str(backup_path) if backup_path else None
        }
    )

    print(f"Indexed {len(index['documents'])} documents")
    if backup_path:
        print(f"Previous version backed up to: {backup_path}")

if __name__ == "__main__":
    main()
```

**Changes Made**:
1. ✅ Removed manual backup logic (now automatic)
2. ✅ Uses atomic write with auto backup
3. ✅ Records metadata with document count and timing
4. ✅ Cleaner, safer, less code

---

## Testing Migration

### Manual Testing Checklist

After migrating a script:

1. **Dry Run Test**
   ```bash
   # Run on test/sample data first
   python3 scripts/analysis/your_script.py
   ```

2. **Verify Output**
   ```bash
   # Check output file created correctly
   cat data/output/your_artifact.json | jq . | head -20
   ```

3. **Check Metadata**
   ```bash
   # Verify metadata recorded
   cat data/.pipeline_metadata.json | jq '."your_artifact.json"'
   ```

4. **Verify Backup Created**
   ```bash
   # Check backup exists
   ls -lh data/output/your_artifact.backup_*.json
   ```

5. **Test Error Handling**
   ```python
   # Introduce error to verify rollback works
   # Ensure original file intact after failure
   ```

### Automated Testing

Create test for your migrated script:

```python
# tests/test_your_script.py
import json
import tempfile
from pathlib import Path

from scripts.analysis import your_script
from scripts.lib.metadata_tracker import get_last_update

def test_your_script_updates_metadata():
    """Test that script records metadata."""
    # Run script
    your_script.main()

    # Check metadata recorded
    info = get_last_update("your_artifact.json")
    assert info is not None
    assert info["updated_by"] == "your_script.py"

def test_your_script_creates_backup():
    """Test that script creates backup."""
    output_dir = Path("data/output")

    # Run script
    your_script.main()

    # Check backup exists
    backups = list(output_dir.glob("your_artifact.backup_*.json"))
    assert len(backups) > 0
```

---

## Rollback Procedure

If something goes wrong after migration:

### 1. Restore from Backup

```bash
# Find latest backup
ls -lt data/entities/ENTITIES_INDEX.backup_*.json | head -1

# Restore (copy, don't move, to preserve backup)
cp data/entities/ENTITIES_INDEX.backup_20251119_143025.json \
   data/entities/ENTITIES_INDEX.json
```

### 2. Revert Code Changes

```bash
# If using git
git checkout HEAD -- scripts/analysis/your_script.py

# Or restore from DEPRECATED
cp scripts/DEPRECATED/analysis/old_script.py scripts/analysis/
```

### 3. Clear Bad Metadata

```python
# scripts/lib/clear_bad_metadata.py
from scripts.lib.metadata_tracker import load_metadata, save_metadata

metadata = load_metadata()

# Remove problematic artifact
if "bad_artifact.json" in metadata:
    del metadata["bad_artifact.json"]

save_metadata(metadata)
```

---

## Common Patterns

### Pattern 1: Entity Processing with Validation

```python
from scripts.lib.atomic_io import atomic_write_json_with_backup
from scripts.lib.metadata_tracker import record_update

def process_entities():
    # ... load and process entities ...

    # Validate before writing
    if not validate_entities(entities):
        raise ValueError("Entity validation failed")

    # Atomic write with backup
    backup = atomic_write_json_with_backup(
        "data/entities/ENTITIES_INDEX.json",
        entities
    )

    # Record metadata
    record_update(
        "ENTITIES_INDEX.json",
        "process_entities.py",
        {"entity_count": len(entities), "validation_passed": True}
    )
```

### Pattern 2: Incremental Processing

```python
from scripts.lib.metadata_tracker import get_last_update, record_update

def process_incrementally():
    # Check if processing needed
    last_run = get_last_update("processed_data.json")

    if last_run:
        # Process only new items since last run
        since = last_run["last_updated"]
        items = get_items_since(since)
    else:
        # First run, process everything
        items = get_all_items()

    # ... process items ...

    # Record completion
    record_update(
        "processed_data.json",
        "incremental_processor.py",
        {"items_processed": len(items)}
    )
```

### Pattern 3: Dependency Checking

```python
from scripts.lib.metadata_tracker import needs_update, record_update

def rebuild_if_needed():
    # Check if upstream data changed
    if needs_update("entity_network.json", ["ENTITIES_INDEX.json"]):
        print("Entities changed, rebuilding network...")
        network = build_network()
        atomic_write_json("data/metadata/entity_network.json", network)
        record_update("entity_network.json", "network_builder.py")
    else:
        print("Network up to date, skipping rebuild")
```

---

## Performance Considerations

### Atomic Writes are Slightly Slower

**Impact**: ~10-50ms overhead per write (due to fsync)
**Recommendation**: Acceptable for batch processing, critical for correctness

```python
# Before: ~100ms for 10MB JSON
# After:  ~120ms for 10MB JSON
# Trade-off: 20% slower, 100% safer
```

### Metadata File Size

**Current**: < 1KB for 10 artifacts
**At 100 artifacts**: ~10KB
**Performance**: No measurable impact

---

## FAQ

**Q: Do I need to use atomic writes for read-only scripts?**
A: No, only scripts that WRITE data need atomic writes.

**Q: What if my script writes multiple files?**
A: Use atomic writes for each file, and record metadata for each artifact.

**Q: Can I still use `with open()` for reading?**
A: Yes, atomic writes only apply to WRITING operations.

**Q: What if I need to write to a database, not a file?**
A: Use database transactions for atomicity. Metadata tracking still useful.

**Q: Do deprecated scripts still work?**
A: Yes, but they should not be used. Migrate to canonical scripts.

**Q: How do I know which script is canonical?**
A: Check `scripts/CANONICAL_SCRIPTS.md` for official list.

---

## Next Steps

See `DATA_PIPELINE_AUDIT_REPORT.md` for:
- Phase 2 plans (Week 3-4): Consolidation
- Phase 3 plans (Week 5-6): Migration to unified pipeline
- Phase 4 plans (Week 7-8): Optimization

---

## Support

**Issues or Questions?**
- Check `CANONICAL_SCRIPTS.md` for script documentation
- Check `DEPRECATED/README.md` for deprecated script info
- Review `DATA_PIPELINE_AUDIT_REPORT.md` for full context
- Check test results: `python3 scripts/lib/test_atomic_io.py`

**Reporting Problems**:
- File issue with script name, error message, steps to reproduce
- Include `.pipeline_metadata.json` contents if relevant
- Note which phase of migration you're in

---

**Last Updated**: 2025-11-19
**Maintainer**: @masa
**Status**: Phase 1 Complete ✅
