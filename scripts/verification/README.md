# Relationship Data Verification Suite

Comprehensive verification tools for validating relationship data integrity across transformed files.

## Quick Start

```bash
# Run full verification with verbose output
python3 scripts/verification/verify_relationships.py --verbose

# Save results to JSON
python3 scripts/verification/verify_relationships.py --output results.json

# Run silently (only show summary)
python3 scripts/verification/verify_relationships.py
```

## What It Verifies

### 1. Bidirectional Consistency
Validates that `document_to_entities.json` ↔ `entity_to_documents.json` are perfectly synchronized.

**Checks:**
- Every document→entity mapping has a corresponding entity→document mapping
- Every entity→document mapping has a corresponding document→entity mapping
- No orphaned references

### 2. Network Integrity
Ensures all edges in `entity_network_full.json` reference valid nodes.

**Checks:**
- All edge sources exist as nodes
- All edge targets exist as nodes
- No dangling references

### 3. Co-appearance Validity
Confirms all entity pairs in `entity_coappearances.json` exist in the network.

**Checks:**
- All entity_a IDs exist as nodes
- All entity_b IDs exist as nodes
- No references to missing entities

### 4. Weight Consistency
Compares edge weights in network against co-appearance counts.

**Checks:**
- Edge weights match co-appearance counts
- Identifies discrepancies between sources

**Note:** Weight mismatches may occur if network includes flight log co-occurrences while co-appearances only count documents. This is a data model design choice, not an error.

### 5. Self-Loop Detection
Identifies entities connected to themselves.

**Checks:**
- No edge where source == target
- All relationships are between different entities

### 6. Bidirectional Edges
Verifies that relationships are properly bidirectional.

**Checks:**
- If A→B exists, then B→A exists
- Weights match in both directions
- Perfect symmetry

## Files Verified

| File | Description | Records |
|------|-------------|---------|
| `entity_coappearances.json` | Entity pair co-occurrences | 31,682 pairs |
| `entity_network_full.json` | Full entity relationship network | 4,790 nodes, 66,193 edges |
| `document_to_entities.json` | Document→entity index | 31,111 documents |
| `entity_to_documents.json` | Entity→document index | 12,152 entities |

## Command Line Options

```
usage: verify_relationships.py [-h] [--verbose] [--data-dir DATA_DIR] [--output OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  --verbose, -v         Enable verbose output (show detailed errors)
  --data-dir DATA_DIR   Data directory path (default: data/transformed)
  --output OUTPUT, -o OUTPUT
                        Output JSON report file
```

## Output Format

### Console Output

```
============================================================
RELATIONSHIP DATA INTEGRITY VERIFICATION
============================================================

1. Bidirectional Consistency Check
============================================================
✓ Bidirectional consistency verified

[... more checks ...]

============================================================
VERIFICATION SUMMARY
============================================================
Bidirectional Consistency............... PASSED
Network Integrity....................... PASSED
Coappearance Validity................... PASSED
Weight Consistency...................... FAILED
No Self Loops........................... FAILED
Bidirectional Edges..................... PASSED

Overall: 4/6 checks passed
Errors: 2
Warnings: 1
```

### JSON Output

```json
{
  "status": "passed|failed",
  "checks_passed": 6,
  "checks_total": 6,
  "results": {
    "bidirectional_consistency": true,
    "network_integrity": true,
    "coappearance_validity": true,
    "weight_consistency": true,
    "no_self_loops": true,
    "bidirectional_edges": true
  },
  "stats": {
    "bidirectional": {
      "missing_in_ent_to_doc": 0,
      "extra_in_doc_to_ent": 0,
      "missing_in_doc_to_ent": 0,
      "extra_in_ent_to_doc": 0
    },
    "network_integrity": {
      "total_nodes": 4790,
      "total_edges": 66193,
      "missing_sources": 0,
      "missing_targets": 0
    },
    ...
  },
  "errors": [],
  "warnings": [],
  "timestamp": "2025-12-06T18:27:14.036934"
}
```

## Exit Codes

- `0` - All checks passed
- `1` - One or more checks failed

## Integration with CI/CD

Add to your CI pipeline:

```yaml
# .github/workflows/verify-data.yml
name: Verify Data Integrity

on:
  push:
    paths:
      - 'data/transformed/**'

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Run verification
        run: |
          python3 scripts/verification/verify_relationships.py --output results.json
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: verification-results
          path: results.json
```

## Common Issues and Solutions

### Issue: Weight Mismatches

**Symptom:** Check 4 (Weight Consistency) fails with mismatched weights

**Cause:** Network includes flight log co-occurrences, while co-appearances only count documents

**Solution:** This is expected if data sources include both documents and flight logs. Document this in metadata.

### Issue: Self-Loops

**Symptom:** Check 5 (No Self-Loops) fails

**Cause:** Entity appears multiple times in same source document (e.g., duplicate passenger entry)

**Solution:** Filter self-loops during network generation:
```python
edges = [e for e in edges if e['source'] != e['target']]
```

### Issue: Missing Reverse Edges

**Symptom:** Check 6 (Bidirectional Edges) fails

**Cause:** Network generation didn't create both A→B and B→A edges

**Solution:** Ensure network generation creates bidirectional edges:
```python
edges.append({'source': a, 'target': b, 'weight': w})
edges.append({'source': b, 'target': a, 'weight': w})
```

## Performance

- **Runtime:** ~5-10 seconds for full verification
- **Memory:** ~500MB peak (loads all files in memory)
- **Disk I/O:** ~200MB read (4 JSON files)

## Development

### Adding New Checks

1. Add verification method to `RelationshipVerifier` class:
```python
def verify_new_check(self, data: dict) -> bool:
    """Verify new data constraint"""
    # Implement check logic
    if issue_found:
        self.log("Issue description", "ERROR")
        return False
    self.log("Check passed", "SUCCESS")
    return True
```

2. Add to `run_all_checks()`:
```python
results['new_check'] = self.verify_new_check(data)
```

3. Update documentation

### Testing

```bash
# Run with verbose output to see all details
python3 scripts/verification/verify_relationships.py --verbose

# Test with custom data directory
python3 scripts/verification/verify_relationships.py --data-dir /path/to/data
```

## Related Documentation

- [Relationship Integrity Report](../../docs/verification/relationship-integrity-report.md)
- [Data Model Documentation](../../docs/data-model.md)
- [Transformation Pipeline](../../docs/transformation-pipeline.md)

## Support

For issues or questions:
1. Check [relationship-integrity-report.md](../../docs/verification/relationship-integrity-report.md)
2. Review source code comments in `verify_relationships.py`
3. Open issue on GitHub

---

**Version:** 1.0.0
**Last Updated:** 2025-12-06
**Maintainer:** QA Team
