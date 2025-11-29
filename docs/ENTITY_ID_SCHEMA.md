# Entity ID Schema Specification

**Quick Summary**: This document specifies the deterministic entity ID schema for migrating from name-based identifiers to stable, URL-safe slug identifiers across all Epstein archive data files. .

**Category**: Documentation
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Inconsistent name formatting across data files
- Difficulty handling special characters in URLs
- Ambiguity with name variations (e.g., "Jeffrey Epstein" vs "Epstein, Jeffrey")
- Complex lookups requiring exact string matching
- **URL-safe**: Only lowercase letters, numbers, and underscores

---

**Version**: 1.0
**Created**: 2025-11-20
**Status**: Design Phase

## Overview

This document specifies the deterministic entity ID schema for migrating from name-based identifiers to stable, URL-safe slug identifiers across all Epstein archive data files.

## Design Rationale

**Problem**: Current system uses entity names as primary keys, causing:
- Inconsistent name formatting across data files
- Difficulty handling special characters in URLs
- Ambiguity with name variations (e.g., "Jeffrey Epstein" vs "Epstein, Jeffrey")
- Complex lookups requiring exact string matching

**Solution**: Deterministic snake_case slug generation
- **URL-safe**: Only lowercase letters, numbers, and underscores
- **Deterministic**: Same name always generates same ID
- **Human-readable**: `"Jeffrey Epstein"` → `"jeffrey_epstein"`
- **Collision-resistant**: Numeric suffixes for duplicates
- **Backward compatible**: Follows existing pattern in `enriched_entity_data.json`

## ID Generation Algorithm

### Core Transformation Rules

```python
def generate_entity_id(name: str) -> str:
    """
    Generate deterministic snake_case entity ID from name.

    Examples:
        "Jeffrey Epstein" → "jeffrey_epstein"
        "Maxwell, Ghislaine" → "maxwell_ghislaine"
        "Trump, Donald" → "trump_donald"
        "O'Brien, Michael" → "obrien_michael"
        "Müller, Hans" → "muller_hans"
    """
    1. Normalize Unicode (NFD decomposition)
    2. Convert to lowercase
    3. Remove accents/diacritics
    4. Replace special characters with space
    5. Remove commas (name inversion markers)
    6. Collapse multiple spaces to single space
    7. Strip leading/trailing whitespace
    8. Replace spaces with underscores
    9. Remove consecutive underscores
    10. Validate format (must match ^[a-z0-9_]+$)
```

### Character Mapping Rules

| Character Type | Transformation | Example |
|----------------|----------------|---------|
| Uppercase A-Z | Lowercase | `Jeffrey` → `jeffrey` |
| Accented chars | Remove accent | `Müller` → `muller` |
| Comma | Remove | `Maxwell, Ghislaine` → `maxwell ghislaine` |
| Space | Underscore | `Jeffrey Epstein` → `jeffrey_epstein` |
| Hyphen | Underscore | `Jean-Luc` → `jean_luc` |
| Apostrophe | Remove | `O'Brien` → `obrien` |
| Period | Remove | `Dr. Smith` → `dr smith` |
| Multiple spaces | Single underscore | `John   Doe` → `john_doe` |
| Numbers | Preserve | `Bond 007` → `bond_007` |

### Edge Cases

#### 1. Name Inversions (Last, First)
```python
"Epstein, Jeffrey" → "epstein_jeffrey"
"Maxwell, Ghislaine" → "maxwell_ghislaine"
```
**Rule**: Commas removed, preserving natural word order

#### 2. Unicode and Special Characters
```python
"Müller, Hans" → "muller_hans"
"José García" → "jose_garcia"
"Françoise Bettencourt" → "francoise_bettencourt"
```
**Rule**: NFD normalization + accent removal

#### 3. Abbreviated Names
```python
"Dr. Smith" → "dr_smith"
"J.P. Morgan" → "jp_morgan"
```
**Rule**: Periods removed, letters preserved

#### 4. Hyphenated Names
```python
"Jean-Luc Brunel" → "jean_luc_brunel"
"Al-Saud, Turki" → "al_saud_turki"
```
**Rule**: Hyphens converted to underscores

#### 5. Single Names
```python
"Ghislaine" → "ghislaine"
"Madonna" → "madonna"
```
**Rule**: Single word becomes single slug

#### 6. Empty/Invalid Results
```python
"###" → ValueError("Invalid name produces empty slug")
"" → ValueError("Empty name cannot generate ID")
```
**Rule**: Must produce non-empty alphanumeric slug

### Collision Resolution

When duplicate slugs are detected:

```python
Base slug: "john_smith"

First entity: "john_smith"      # Original
Second entity: "john_smith_2"   # Collision counter
Third entity: "john_smith_3"    # Incremental
```

**Implementation**:
1. Generate base slug using core algorithm
2. Check if slug exists in ID registry
3. If exists, append `_2` and check again
4. Increment counter until unique slug found
5. Log collision for manual review

**Collision Report Example**:
```json
{
  "collisions": [
    {
      "base_slug": "john_smith",
      "entities": [
        {"name": "John Smith", "id": "john_smith", "sources": ["black_book"]},
        {"name": "Smith, John", "id": "john_smith_2", "sources": ["flight_logs"]}
      ],
      "manual_review": true,
      "reason": "Possible duplicate entity, requires merge decision"
    }
  ]
}
```

## Data Structure Updates

### 1. Entity Statistics (`entity_statistics.json`)

**BEFORE** (Name-keyed):
```json
{
  "statistics": {
    "Jeffrey Epstein": {
      "name": "Jeffrey Epstein",
      "name_variations": ["Jeffrey Epstein", "Epstein, Jeffrey"],
      "flight_count": 0,
      "connection_count": 262
    }
  }
}
```

**AFTER** (ID-keyed):
```json
{
  "statistics": {
    "jeffrey_epstein": {
      "id": "jeffrey_epstein",
      "name": "Jeffrey Epstein",
      "name_variations": ["Jeffrey Epstein", "Epstein, Jeffrey"],
      "flight_count": 0,
      "connection_count": 262
    }
  }
}
```

**Changes**:
- Root key changed from `name` to `id`
- Added explicit `id` field to entity object
- `name` field preserved as primary display name

### 2. Entity Network (`entity_network.json`)

**BEFORE** (Name-based references):
```json
{
  "nodes": [
    {"id": "Jeffrey Epstein", "name": "Jeffrey Epstein"}
  ],
  "edges": [
    {"source": "Jeffrey Epstein", "target": "Ghislaine Maxwell", "weight": 150}
  ]
}
```

**AFTER** (ID-based references):
```json
{
  "nodes": [
    {"id": "jeffrey_epstein", "name": "Jeffrey Epstein"}
  ],
  "edges": [
    {"source": "jeffrey_epstein", "target": "ghislaine_maxwell", "weight": 150}
  ]
}
```

**Changes**:
- Node `id` uses slug instead of name
- Edge `source` and `target` reference slugs
- `name` field added for display purposes

### 3. Entity Biographies (`entity_biographies.json`)

**BEFORE**:
```json
{
  "entities": {
    "Epstein, Jeffrey": {
      "full_name": "Jeffrey Edward Epstein",
      "born": "1953-01-20"
    }
  }
}
```

**AFTER**:
```json
{
  "entities": {
    "jeffrey_epstein": {
      "id": "jeffrey_epstein",
      "full_name": "Jeffrey Edward Epstein",
      "display_name": "Jeffrey Epstein",
      "born": "1953-01-20"
    }
  }
}
```

**Changes**:
- Root key uses slug
- Added `id` field
- Added `display_name` field for consistent rendering

### 4. Entity Name Mappings (`entity_name_mappings.json`)

**BEFORE**:
```json
{
  "Alan    Alan Dershowitz": "Alan Dershowitz",
  "Alan   Alan Dershowitz": "Alan Dershowitz"
}
```

**AFTER**:
```json
{
  "name_to_id": {
    "Alan    Alan Dershowitz": "alan_dershowitz",
    "Alan   Alan Dershowitz": "alan_dershowitz",
    "Alan Dershowitz": "alan_dershowitz"
  },
  "id_to_canonical_name": {
    "alan_dershowitz": "Alan Dershowitz"
  }
}
```

**Changes**:
- Split into bidirectional mappings
- All name variations map to single ID
- ID maps to single canonical display name

### 5. Entity Tags (`entity_tags.json`)

**BEFORE**:
```json
{
  "entities": {
    "Jeffrey Epstein": {
      "tags": ["Financier", "Associate"]
    }
  }
}
```

**AFTER**:
```json
{
  "entities": {
    "jeffrey_epstein": {
      "id": "jeffrey_epstein",
      "name": "Jeffrey Epstein",
      "tags": ["Financier", "Associate"]
    }
  }
}
```

**Changes**:
- Root key uses slug
- Added `id` and `name` fields

## Validation Rules

### ID Format Validation

All entity IDs MUST:
- Match regex: `^[a-z0-9_]+$`
- Be between 2-100 characters
- Not start or end with underscore
- Not contain consecutive underscores

**Valid IDs**:
- `jeffrey_epstein`
- `ghislaine_maxwell`
- `trump_donald`
- `john_smith_2`

**Invalid IDs**:
- `Jeffrey_Epstein` (uppercase)
- `jeffrey-epstein` (hyphen)
- `jeffrey__epstein` (consecutive underscores)
- `_jeffrey_epstein` (leading underscore)
- `jeffrey_epstein_` (trailing underscore)
- `a` (too short, <2 chars)

### Data Integrity Validation

Post-migration checks:
1. **Entity Count**: Total entities unchanged
2. **ID Uniqueness**: No duplicate IDs
3. **Reference Integrity**: All edge references exist in nodes
4. **Data Preservation**: All original fields retained
5. **Name Mappings**: All name variations map correctly

## Performance Characteristics

### ID Lookup Performance

| Operation | Before (Names) | After (IDs) | Improvement |
|-----------|---------------|-------------|-------------|
| Dict lookup | O(n) string compare | O(1) hash lookup | 10-100x faster |
| URL routing | Encoding required | Direct use | Simpler |
| Database indexing | Variable-length | Fixed format | More efficient |
| API queries | Case-sensitive | Normalized | Consistent |

### Expected Metrics

- **ID Generation**: <1ms per entity
- **ID Lookup**: <0.1ms (O(1) dict access)
- **Name→ID Translation**: <5ms (indexed lookup)
- **Migration Runtime**: <5 minutes for 1,637 entities

### Memory Impact

- **ID Storage**: ~30 bytes per ID (vs ~50 bytes for full name)
- **Memory Reduction**: ~40% for ID-only references
- **Network graph edges**: 1,624 edges × 20 bytes saved = ~32KB saved

## Migration Strategy

### Phase 1: ID Generation
1. Generate IDs for all 1,637 entities
2. Detect and resolve collisions
3. Create `entity_id_mappings.json`
4. Manual review of collision report

### Phase 2: Data File Migration
1. Backup all data files
2. Migrate `entity_statistics.json`
3. Migrate `entity_network.json`
4. Migrate `entity_biographies.json`
5. Migrate `entity_name_mappings.json`
6. Migrate `entity_tags.json`

### Phase 3: Validation
1. Verify entity counts
2. Validate reference integrity
3. Test API endpoints
4. Performance benchmarks

### Phase 4: Frontend Updates
1. Update API calls to use IDs
2. Update URL routing
3. Add name→ID translation layer
4. Deploy with backward compatibility

## Backward Compatibility

### Transition Period

Support both name and ID lookups during migration:

```python
def get_entity(identifier: str) -> Entity:
    """Lookup by ID or name during transition."""
    # Try ID first (new system)
    if entity := entity_db.get(identifier):
        return entity

    # Fall back to name lookup (legacy)
    entity_id = name_to_id_mapping.get(identifier)
    if entity_id:
        return entity_db.get(entity_id)

    raise EntityNotFoundError(identifier)
```

### API Versioning

- **v1 API**: Accept names, return with IDs
- **v2 API**: Require IDs, return IDs
- Deprecation notice: 6 months before removing name support

## Risk Mitigation

### Data Loss Prevention
- **Backup Strategy**: Timestamped backups before each migration step
- **Rollback Plan**: Automated rollback scripts
- **Validation Gates**: Stop migration if validation fails

### Collision Handling
- **Automatic Resolution**: Numeric suffix for duplicates
- **Manual Review**: All collisions logged for review
- **Merge Tool**: UI for resolving duplicate entities

### Reference Integrity
- **Pre-Migration Check**: Validate all references exist
- **Post-Migration Validation**: Ensure no broken links
- **Orphan Detection**: Identify and fix orphaned references

## Testing Strategy

### Unit Tests

```python
def test_id_generation():
    assert generate_entity_id("Jeffrey Epstein") == "jeffrey_epstein"
    assert generate_entity_id("Maxwell, Ghislaine") == "maxwell_ghislaine"
    assert generate_entity_id("O'Brien, Michael") == "obrien_michael"
    assert generate_entity_id("Müller, Hans") == "muller_hans"

def test_collision_resolution():
    registry = {}
    id1 = register_entity("John Smith", registry)  # "john_smith"
    id2 = register_entity("Smith, John", registry)  # "john_smith_2"
    assert id1 != id2
    assert id2.startswith(id1)

def test_validation():
    assert is_valid_id("jeffrey_epstein") == True
    assert is_valid_id("Jeffrey_Epstein") == False  # uppercase
    assert is_valid_id("jeffrey-epstein") == False  # hyphen
```

### Integration Tests

1. **End-to-End Migration**: Test full migration pipeline
2. **Reference Integrity**: Validate all network edges
3. **API Compatibility**: Test both ID and name lookups
4. **Performance Benchmarks**: Measure lookup times

## Future Considerations

### Potential Enhancements

1. **UUID Fallback**: Add UUID for absolute uniqueness guarantee
2. **Versioning**: Track entity ID changes over time
3. **Aliases**: Support multiple IDs for same entity
4. **Internationalization**: Enhanced Unicode handling

### Schema Evolution

```json
{
  "id": "jeffrey_epstein",
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "slug": "jeffrey_epstein",
  "version": 1,
  "created_at": "2025-11-20T00:00:00Z",
  "updated_at": "2025-11-20T00:00:00Z"
}
```

## Appendix: Example Transformations

### Real Entity Names from Dataset

| Original Name | Generated ID | Notes |
|---------------|--------------|-------|
| Jeffrey Epstein | `jeffrey_epstein` | Standard case |
| Epstein, Jeffrey | `epstein_jeffrey` | Comma removed |
| Maxwell, Ghislaine | `maxwell_ghislaine` | Comma removed |
| Trump, Donald | `trump_donald` | Comma removed |
| Clinton, William | `clinton_william` | Comma removed |
| Prince Andrew | `prince_andrew` | Title preserved |
| Ghislaine Maxwell | `ghislaine_maxwell` | Standard case |
| Bill Clinton | `bill_clinton` | Nickname form |
| Donald Trump | `donald_trump` | Standard case |
| Alan Dershowitz | `alan_dershowitz` | Standard case |
| Les Wexner | `les_wexner` | Standard case |
| Glenn Dubin | `glenn_dubin` | Standard case |
| Eva Dubin | `eva_dubin` | Standard case |
| Jean-Luc Brunel | `jean_luc_brunel` | Hyphen to underscore |
| Virginia Giuffre | `virginia_giuffre` | Standard case |
| Sarah Kellen | `sarah_kellen` | Standard case |

## References

- Research Analysis: `/docs/ENTITY_ID_RESEARCH_ANALYSIS.md`
- Migration Plan: `/docs/ENTITY_ID_MIGRATION_PLAN.md`
- Migration Scripts: `/scripts/migration/`
