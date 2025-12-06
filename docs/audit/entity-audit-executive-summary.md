# Entity Data Quality Audit - Executive Summary

**Date**: 2025-12-06
**Auditor**: Research Agent
**Scope**: All entity metadata files (2,954 total entities)

## Critical Finding: Schema Mismatch

🚨 **BLOCKER**: Current entity data structure is incompatible with target schema. Transformation required before data can be used.

## Entity Inventory

| Entity Type | Count | Status |
|-------------|-------|--------|
| People (Biographies) | 1,637 | Schema mismatch |
| Locations | 429 | Schema mismatch |
| Organizations | 888 | Schema mismatch |
| **TOTAL** | **2,954** | **Requires transformation** |

## Current vs. Target Schema Gap

### Target Schema Requirements
```json
{
  "entity_id": "uuid",                    // 0% coverage
  "entity_type": "person|place|org",      // Partial
  "canonical_name": "string",             // 0% coverage
  "aliases": ["string"],                  // 0% coverage
  "classifications": ["category"],        // 0% coverage
  "document_count": 0,                    // Partial (locations/orgs only)
  "news_count": 0,                        // 0% coverage
  "connection_count": 0,                  // 0% coverage (all show 0)
  "biography": "string|null",             // 60.5% coverage
  "source_refs": [{"type": "", "id": ""}] // 0% coverage
}
```

### Current Schema (Varies by Type)

**Biographies**:
- `name` ✓
- `summary` (28.8% populated)

**Locations/Organizations**:
- `name` ✓
- `entity_type` ✓
- `mention_count` ✓
- `documents` (array of paths) ✓

## Data Quality Score: 20.2%

| Metric | Coverage |
|--------|----------|
| UUID Coverage | 0.0% ❌ |
| Classification Coverage | 0.0% ❌ |
| Biography Coverage | 60.5% ⚠️ |
| Connection Graph | 0.0% ❌ |
| Source References | 0.0% ❌ |

## Critical Path to Production

### Phase 1: Schema Transformation (4-6 days) - BLOCKING

**Must complete before any other work**:

1. **Field Mapping** (1-2 days)
   - `name` → `canonical_name` for all 2,954 entities
   - Add `entity_type` to biographies
   - Transform `documents` → `source_refs`
   - Calculate `document_count` from unique docs

2. **UUID Generation** (2-3 days)
   - Generate deterministic UUIDs for all entities
   - Create UUID mapping file

3. **Initialize Missing Fields** (1 day)
   - Add empty `aliases`, `classifications` arrays
   - Set `connection_count` = 0, `news_count` = 0

**Deliverable**: Entity files matching target schema with minimal data

### Phase 2: Classification (2-4 weeks) - HIGH PRIORITY

4. **Entity Classification**
   - 1,637 people: victim/associate/employee/witness/etc.
   - 429 locations: residence/office/island/airport/etc.
   - 888 organizations: government/business/nonprofit/media/etc.
   - **Approach**: LLM-assisted + human validation

5. **Biography Enrichment**
   - Enhance 1,166 missing biographies
   - Use document context for generation

### Phase 3: Relationships (3-4 weeks) - MEDIUM PRIORITY

6. **Connection Graph Building**
   - Analyze document co-occurrences
   - Build entity relationship graph
   - Populate `connection_count`

7. **Alias Extraction**
   - Extract from documents
   - Validate and add to records

## Known Issues

1. **Cross-Type Misclassifications**: 3 entities found
   - 1 name in both People and Organizations
   - 1 name in both People and Locations
   - 1 name in both Organizations and Locations

2. **Missing Biographies**: 1,166 people (71.2%) lack biographical data

3. **Zero Connections**: 100% of entities show 0 connections
   - Likely: connection graph not yet built
   - **Not**: actual isolated entities

## Recommendations

### Immediate Actions (This Sprint)

1. ✅ **Approve Schema Transformation Plan**
2. ✅ **Allocate 4-6 days for Phase 1 transformation**
3. ✅ **Create transformation script with validation**
4. ⚠️ **Backup existing entity files before transformation**

### Next Sprint

5. **Begin Entity Classification** (LLM-assisted workflow)
6. **Build Biography Enrichment Pipeline**
7. **Design Connection Graph Strategy**

### Risk Mitigation

- **Data Loss Risk**: Create backups before transformation
- **Quality Risk**: Implement validation checks in transformation script
- **Timeline Risk**: Phase 1 is critical path - prioritize over features

## Estimated Total Effort

| Phase | Effort | Priority |
|-------|--------|----------|
| Phase 1: Schema Transformation | 4-6 days | 🔴 CRITICAL |
| Phase 2: Classification | 2-4 weeks | 🟡 HIGH |
| Phase 3: Relationships | 3-4 weeks | 🟢 MEDIUM |

**Total**: 8-14 weeks to full data quality

## Decision Required

**Should we proceed with schema transformation?**

- [ ] **Yes** - Proceed with Phase 1 transformation (4-6 days)
- [ ] **No** - Revise target schema to match current structure
- [ ] **Defer** - Continue with current schema, plan migration later

**Recommendation**: Proceed with transformation. Current schema is unusable for target system.

---

**Full Report**: See `docs/audit/entity-data-quality.md` for detailed analysis

**Audit Script**: `scripts/analysis/audit_entity_quality.py`
