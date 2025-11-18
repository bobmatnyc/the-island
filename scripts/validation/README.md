# Entity Validation Tools

Tools for validating data quality and formatting in the Epstein Archive database.

## Available Scripts

### validate_entity_names.py

Validates entity name formatting across the database.

**What it checks:**

1. **Trailing Commas** - Entity names ending with `,`
2. **Leading/Trailing Spaces** - Whitespace at start or end of names
3. **Multiple Consecutive Spaces** - Multiple spaces within names
4. **Unusual Ending Characters** - Names ending with invalid punctuation
5. **Duplicate Entities** - Case-insensitive duplicate detection
6. **Jeffrey Epstein Entity** - Verifies single canonical entity

**Usage:**

```bash
# Human-readable report
python scripts/validation/validate_entity_names.py

# JSON output (for automation/CI)
python scripts/validation/validate_entity_names.py --json

# Specify custom base path
python scripts/validation/validate_entity_names.py --base-path /path/to/project
```

**Exit Codes:**
- `0` - All validation checks passed
- `1` - Validation issues found
- `2` - Error (file not found, invalid JSON, etc.)

**Example Output:**

```
================================================================================
ENTITY NAME FORMATTING VALIDATION REPORT
================================================================================
Generated: 2025-11-17 21:29:19

ENTITIES DATABASE
----------------------------------------
Total entities: 1639

✅ Trailing Commas: No issues
✅ Leading/Trailing Spaces: No issues
✅ Multiple Spaces: No issues
✅ Unusual Endings: No issues
✅ Duplicate Names: No issues

✅ Jeffrey Epstein: Single entity
   - Name: "Epstein, Jeffrey"
   - Normalized: "Jeffrey Epstein"
   - Flights: 8

================================================================================
FLIGHT LOGS
----------------------------------------
Total flights: 1167
Unique passengers: 289

✅ Trailing Commas: No issues
✅ Leading/Trailing Spaces: No issues
✅ Unusual Characters: No issues

================================================================================
SUMMARY
================================================================================
✅ ALL CHECKS PASSED - No formatting issues found!
```

## Integration with CI/CD

You can integrate these validation scripts into your CI/CD pipeline:

```bash
#!/bin/bash
# In your CI script

# Run validation
python scripts/validation/validate_entity_names.py --json > validation_report.json

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ Validation passed"
    exit 0
else
    echo "❌ Validation failed"
    cat validation_report.json
    exit 1
fi
```

## Validation Standards

### Entity Name Format

**Valid Examples:**
- `"Epstein, Jeffrey"` - Last name first format
- `"John Doe"` - First name first
- `"Smith Jr., John"` - With suffix
- `"Dr. Jane Smith"` - With title

**Invalid Examples:**
- `"Epstein, Jeffrey,"` - Trailing comma ❌
- `" John Doe"` - Leading space ❌
- `"John  Doe"` - Multiple spaces ❌
- `"John Doe "` - Trailing space ❌

### Passenger Name Format (Flight Logs)

Same rules apply to passenger names in flight logs. Names must:
- Not have trailing commas
- Not have leading/trailing whitespace
- End with valid characters (letters, numbers, or valid punctuation)
- Be consistent with entity names in ENTITIES_INDEX.json

## Adding New Validation Checks

To add a new validation check:

1. Add a new issue category to `self.issues` in `EntityNameValidator.__init__()`
2. Implement the check in `validate_entities()` or `validate_flight_passengers()`
3. Update the report printing in `print_report()` and `get_json_report()`
4. Update this README with the new check description

Example:

```python
# In EntityNameValidator.__init__()
self.issues = {
    # ... existing checks ...
    'new_check': []
}

# In validate_entities()
for e in entities:
    if some_condition(e):
        self.issues['new_check'].append({
            'name': e['name'],
            'details': 'why this failed'
        })
```

## Troubleshooting

### File Not Found Error

```
❌ Error: Required file not found
```

**Solution**: Run from project root or specify `--base-path`:

```bash
cd /path/to/epstein
python scripts/validation/validate_entity_names.py
```

### Invalid JSON Error

```
❌ Error: Invalid JSON in data file
```

**Solution**: Check that the data files are valid JSON:

```bash
python3 -m json.tool data/md/entities/ENTITIES_INDEX.json
python3 -m json.tool data/md/entities/flight_logs_by_flight.json
```

## Current Validation Status

As of 2025-11-17, the database passes all validation checks:

- ✅ 1,639 entities validated
- ✅ 1,167 flights validated
- ✅ 289 unique passengers validated
- ✅ No formatting issues found
- ✅ Single canonical Jeffrey Epstein entity

See `ENTITY_NAME_VALIDATION_REPORT.md` for detailed validation results.
