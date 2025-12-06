# Entity Data Quality Audit Report

**Generated**: 2025-12-06T15:14:12.082345

## Executive Summary

Total entities audited: **2,954**

### Current State vs. Target Schema

**Critical Finding**: The current entity data structure does NOT match the target schema. A significant data transformation effort is required.

#### Current Structure
- **Biographies**: Uses `name` and `summary` fields
- **Locations/Organizations**: Uses `name`, `entity_type`, `mention_count`, and `documents` array

#### Target Schema (Required)
- `entity_id` (UUID)
- `entity_type` (person|place|organization)
- `canonical_name`
- `aliases` (array)
- `classifications` (array)
- `document_count`, `news_count`, `connection_count`
- `biography`
- `source_refs` (array of objects)

### Key Findings

**Biographies**: 1,637 entities
- UUID Coverage: 0.0%
- Classification Coverage: 0.0%
- Biography Coverage: 28.8%
- Isolated Entities (0 connections): 100.0%
- Potential Duplicates: 0

**Locations**: 429 entities
- UUID Coverage: 0.0%
- Classification Coverage: 0.0%
- Biography Coverage: 100.0%
- Isolated Entities (0 connections): 100.0%
- Potential Duplicates: 0

**Organizations**: 888 entities
- UUID Coverage: 0.0%
- Classification Coverage: 0.0%
- Biography Coverage: 100.0%
- Isolated Entities (0 connections): 100.0%
- Potential Duplicates: 0

## Biographies Analysis

**Total Count**: 1,637

### Field Coverage

| Field | Coverage | Count |
|-------|----------|-------|
| UUID | 0.0% | 0 |
| Classification | 0.0% | 0 |
| Biography | 28.8% | 471 |
| Aliases | 0.0% | 0 |

### Data Gaps

- **Zero Connections**: 1,637 (100.0%)
- **No Document References**: 1,637 (100.0%)
- **No News References**: 1,637 (100.0%)

### Missing Required Fields

- **entity_id**: 1,637 entities missing
- **canonical_name**: 1,637 entities missing

## Locations Analysis

**Total Count**: 429

### Field Coverage

| Field | Coverage | Count |
|-------|----------|-------|
| UUID | 0.0% | 0 |
| Classification | 0.0% | 0 |
| Biography | 100.0% | 429 |
| Aliases | 0.0% | 0 |

### Data Gaps

- **Zero Connections**: 429 (100.0%)
- **No Document References**: 429 (100.0%)
- **No News References**: 429 (100.0%)

### Missing Required Fields

- **entity_id**: 429 entities missing
- **canonical_name**: 429 entities missing

## Organizations Analysis

**Total Count**: 888

### Field Coverage

| Field | Coverage | Count |
|-------|----------|-------|
| UUID | 0.0% | 0 |
| Classification | 0.0% | 0 |
| Biography | 100.0% | 888 |
| Aliases | 0.0% | 0 |

### Data Gaps

- **Zero Connections**: 888 (100.0%)
- **No Document References**: 888 (100.0%)
- **No News References**: 888 (100.0%)

### Missing Required Fields

- **entity_id**: 888 entities missing
- **canonical_name**: 888 entities missing

## Cross-Type Misclassifications

- Found 1 names appearing in both PEOPLE and ORGANIZATIONS
-   - 
- Found 1 names appearing in both PEOPLE and LOCATIONS
-   - 
- Found 1 names appearing in both ORGANIZATIONS and LOCATIONS
-   - 

## Actual Data Structure Analysis

### Biographies (People) - 1,637 entities

**Current Fields**:
- `name`: Entity name (present in all)
- `summary`: Biography text (present in 471 entities, 28.8%)

**Missing Fields** (from target schema):
- `entity_id`: 100% missing (0 UUIDs)
- `canonical_name`: 100% missing
- `aliases`: 100% missing
- `classifications`: 100% missing
- `document_count`: 100% missing
- `news_count`: 100% missing
- `connection_count`: 100% missing
- `source_refs`: 100% missing

### Locations - 429 entities

**Current Fields**:
- `name`: Location name (present in all)
- `entity_type`: Always "location"
- `mention_count`: Number of mentions in documents
- `documents`: Array of document file paths

**Mapping to Target Schema**:
- `name` → `canonical_name` ✓ (straightforward mapping)
- `mention_count` → `document_count` (partial - need to count unique docs)
- `documents` → `source_refs` (needs transformation)

**Missing Fields**:
- `entity_id`: 100% missing (0 UUIDs)
- `aliases`: 100% missing
- `classifications`: 100% missing
- `news_count`: 100% missing
- `connection_count`: 100% missing
- `biography`: 0% missing (but needs to be populated with context)

### Organizations - 888 entities

**Current Fields**:
- `name`: Organization name (present in all)
- `entity_type`: Always "organization"
- `mention_count`: Number of mentions in documents
- `documents`: Array of document file paths

**Mapping to Target Schema**:
- Same as Locations (identical structure)

**Missing Fields**:
- Same as Locations

## Schema Transformation Requirements

### Phase 1: Field Mapping (Low Complexity)

1. **Name Normalization**:
   - `name` → `canonical_name` (all entity types)
   - Add `entity_type` field for biographies (all = "person")

2. **Document Reference Transformation**:
   - Count unique documents from `documents` array → `document_count`
   - Transform `documents` paths into `source_refs` format:
     ```json
     {"type": "document", "id": "extracted_from_path"}
     ```

### Phase 2: UUID Generation (Medium Complexity)

Generate UUIDs for all 2,954 entities using deterministic approach:
- Use hash of `name` + `entity_type` to ensure consistency
- Store mapping of old names to new UUIDs

### Phase 3: Classification (High Complexity)

**Biographies (People)**: Classify into categories
- Potential categories: victim, associate, employee, investigator, witness, etc.
- Requires: Document context analysis or manual review
- Estimated effort: High (1,637 entities)

**Locations**: Classify into categories
- Potential categories: residence, office, island, airport, etc.
- Can be partially automated from document context

**Organizations**: Classify into categories
- Potential categories: government, business, nonprofit, media, etc.
- Can be partially automated from document context

### Phase 4: Connection Graph Building (High Complexity)

Build relationship graph to populate:
- `connection_count`: Count of related entities
- Requires: Co-occurrence analysis in documents
- Estimated effort: High (requires graph database or similar)

### Phase 5: Data Enrichment (Medium Complexity)

1. **Biographies**: Enhance 1,166 entities missing summaries
2. **Aliases**: Extract from documents or external sources
3. **News References**: Link to news articles (requires news data integration)

## Recommendations

### Priority 1: Schema Transformation (CRITICAL - Blocking)

**Without schema transformation, the entity data cannot be used in the target system.**

1. **Field Mapping (Quick Win - 1-2 days)**:
   - Map `name` → `canonical_name` for all entities (2,954)
   - Add `entity_type` field to biographies
   - Transform `documents` arrays into `source_refs` format
   - Calculate `document_count` from unique documents

2. **UUID Generation (Medium - 2-3 days)**:
   - Generate deterministic UUIDs for all 2,954 entities
   - Create UUID mapping file for reference
   - Update all entity records with UUIDs

3. **Initialize Missing Fields (Quick - 1 day)**:
   - Add empty arrays for `aliases`, `classifications`
   - Set `connection_count` = 0 (will populate in Phase 4)
   - Set `news_count` = 0 (will populate when news data available)

**Estimated Total Effort**: 4-6 days for basic schema compliance

### Priority 2: Data Quality & Classification (HIGH)

4. **Entity Classification (High Effort - 2-4 weeks)**:
   - **People (1,637)**: Classify as victim/associate/employee/etc.
     - Option A: LLM-assisted classification using document context
     - Option B: Manual review with UI tool
     - Option C: Hybrid approach (LLM + human validation)
   - **Locations (429)**: Classify as residence/office/island/etc.
   - **Organizations (888)**: Classify as government/business/nonprofit/etc.

5. **Biography Enrichment (Medium - 1-2 weeks)**:
   - Enhance 1,166 biographies missing summary text
   - Use document context to generate summaries
   - Quality review for accuracy

### Priority 3: Relationship & Enrichment (MEDIUM)

6. **Connection Graph Building (High Effort - 3-4 weeks)**:
   - Analyze document co-occurrences to identify entity relationships
   - Build connection graph (may require graph database)
   - Populate `connection_count` for all entities
   - Current state: 100% of entities show 0 connections (likely data issue)

7. **Alias Extraction (Medium - 1-2 weeks)**:
   - Extract aliases from documents
   - Review and validate aliases
   - Add to entity records

8. **Data Quality Fixes (Low - 2-3 days)**:
   - Fix cross-type misclassifications (3 identified)
   - Standardize naming (capitalization, whitespace)
   - Validate entity type assignments

### Priority 4: Future Enhancements (LOW)

9. **News Integration**: Link entities to news articles (requires news data source)
10. **External Data Enrichment**: Augment with public records, LinkedIn, etc.
11. **Duplicate Resolution**: Merge duplicate entities (currently 0 detected)

## Data Completeness Score

**Overall Completeness**: 20.2%

| Metric | Score |
|--------|-------|
| UUID Coverage | 0.0% |
| Classification Coverage | 0.0% |
| Biography Coverage | 60.5% |

**Note**: This score reflects compliance with target schema. The actual completeness is much lower when considering all required fields.

## Transformation Roadmap Summary

| Phase | Task | Entities Affected | Complexity | Estimated Effort |
|-------|------|-------------------|------------|------------------|
| 1 | Field Mapping | 2,954 | Low | 1-2 days |
| 1 | UUID Generation | 2,954 | Medium | 2-3 days |
| 1 | Initialize Missing Fields | 2,954 | Low | 1 day |
| 2 | Entity Classification | 2,954 | High | 2-4 weeks |
| 2 | Biography Enrichment | 1,166 | Medium | 1-2 weeks |
| 3 | Connection Graph Building | 2,954 | High | 3-4 weeks |
| 3 | Alias Extraction | 2,954 | Medium | 1-2 weeks |
| 3 | Data Quality Fixes | ~10 | Low | 2-3 days |

**Total Estimated Effort**: 8-14 weeks (with Phase 1 being critical path)

## Critical Blocker

**SCHEMA MISMATCH**: The current entity data structure is incompatible with the target schema.

**Impact**:
- Entity data cannot be imported into target system without transformation
- API endpoints expecting target schema will fail
- Frontend components expecting target fields will break

**Required Action**: Execute Priority 1 (Schema Transformation) before any other work can proceed.

## Data Quality Metrics Summary

| Entity Type | Count | UUID | Classification | Biography | Aliases | Connections | Duplicates |
|-------------|-------|------|----------------|-----------|---------|-------------|------------|
| **People** | 1,637 | 0% | 0% | 28.8% | 0% | 0% | 0 |
| **Locations** | 429 | 0% | 0% | 100%* | 0% | 0% | 0 |
| **Organizations** | 888 | 0% | 0% | 100%* | 0% | 0% | 0 |
| **TOTAL** | **2,954** | **0%** | **0%** | **60.5%** | **0%** | **0%** | **0** |

\* Locations and Organizations have `mention_count` data that can serve as biography context, but not formatted as biographical text.

---

*Report generated by `scripts/analysis/audit_entity_quality.py`*