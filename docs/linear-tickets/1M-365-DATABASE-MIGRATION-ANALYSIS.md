# Linear Ticket: Database Migration vs JSON Optimization Analysis

**Created**: 2025-11-29
**Ticket ID**: 1M-365
**Type**: Epic (Parent Issue with 4 Sub-Tasks)
**Priority**: Medium
**Status**: Open

## Overview

Comprehensive Linear ticket documenting the database vs JSON architecture analysis and actionable optimization recommendations.

## Ticket Structure

### Parent Issue: 1M-365
**Title**: Evaluate Database Migration vs Optimized JSON Architecture

**URL**: https://linear.app/1m-hyperdev/issue/1M-365

**Key Points**:
- Current: 38,177 documents, 1,637 entities in JSON (~50 MB)
- Recommendation: Optimize JSON first (6 days effort, high impact)
- Decision framework for future SQLite migration
- Complete tradeoff analysis across deployment, performance, scalability

**Labels**: `architecture`, `performance`, `technical-debt`, `research`

**Research Document**: `docs/research/json-to-database-migration-analysis-2025-11-29.md`

---

## Sub-Tasks

### 1M-366: Add document ID index for O(1) lookups
**Priority**: High | **Effort**: 1 day | **Type**: Quick Win

**URL**: https://linear.app/1m-hyperdev/issue/1M-366

**Objective**: Eliminate O(n) linear search in DocumentService.get_by_id()

**Implementation**:
- Add `_document_index: Dict[str, dict]` to DocumentService
- Build index on startup
- Replace linear search with hash lookup

**Expected Gain**: 10x faster document retrieval

**Files**: `server/services/document_service.py`

---

### 1M-367: Pre-compute entity type classifications
**Priority**: High | **Effort**: 2 days | **Type**: LLM Optimization

**URL**: https://linear.app/1m-hyperdev/issue/1M-367

**Objective**: Pre-compute entity types to eliminate runtime LLM calls

**Implementation**:
- Create `scripts/analysis/precompute_entity_types.py`
- Batch process all 1,637 entities
- Add `entity_type` field to entity_biographies.json
- Remove runtime classification

**Expected Gain**: Eliminate 200-500ms blocking LLM calls

**Files**:
- `data/metadata/entity_biographies.json` (schema change)
- `server/services/entity_service.py`
- `scripts/analysis/precompute_entity_types.py` (new)

**Related**: 1M-364 (Entity type classification issues)

---

### 1M-368: Implement query caching layer
**Priority**: Medium | **Effort**: 2 days | **Type**: Performance

**URL**: https://linear.app/1m-hyperdev/issue/1M-368

**Objective**: Add LRU cache for frequent search queries

**Implementation**:
- Add `functools.lru_cache` to search methods
- Cache size: 100 queries
- TTL: 5 minutes
- Cache invalidation on updates

**Expected Gain**: 2-3x faster average search (40% hit rate)

**Files**:
- `server/services/document_service.py`
- `server/services/entity_service.py`

---

### 1M-369: Add performance monitoring for migration triggers
**Priority**: Low | **Effort**: 1 day | **Type**: Observability

**URL**: https://linear.app/1m-hyperdev/issue/1M-369

**Objective**: Track migration trigger conditions and alert when approaching thresholds

**Implementation**:
- Create `PerformanceMonitor` class
- Track p95 search latency
- Monitor document/entity counts
- Create `/api/performance/status` endpoint

**Migration Triggers** (any met → consider SQLite):
- Documents > 50,000
- Entities > 5,000
- p95 latency > 500ms

**Alert Thresholds** (80% of limits):
- Documents > 40,000
- Entities > 4,000
- p95 latency > 400ms

**Files**:
- `server/services/performance_monitor.py` (new)
- `server/performance_endpoints.py` (new)
- `server/app.py`

---

## Implementation Plan

### Phase 1: High-Priority Optimizations (3 days)
1. **Day 1**: 1M-366 - Document ID index
2. **Days 2-3**: 1M-367 - Pre-compute entity types

### Phase 2: Caching (2 days)
3. **Days 4-5**: 1M-368 - Query caching layer

### Phase 3: Monitoring (1 day)
4. **Day 6**: 1M-369 - Performance monitoring

**Total Timeline**: 6 days
**Expected Performance Gain**: 2-3x improvement

---

## Success Metrics

### Immediate (after implementation):
- Document lookup: <10ms (currently ~100ms)
- Entity detail page: <100ms (currently 200-500ms)
- Search response: <200ms average (currently ~300-500ms)

### Long-term (Q1 2026):
- Document count: Monitor vs 50K threshold
- Entity count: Monitor vs 5K threshold
- p95 search latency: Monitor vs 500ms threshold

---

## Decision Framework

### Stay on JSON if:
- Documents < 50,000
- Entities < 5,000
- p95 latency < 500ms
- Current: 38K docs, 1.6K entities, ~127ms latency → **Stay on JSON**

### Migrate to SQLite if ANY:
- Documents > 50,000
- Entities > 5,000
- p95 latency > 500ms

### Never migrate to PostgreSQL unless:
- Documents > 500,000 AND
- Need multi-tenant SaaS features

---

## Cost Estimates

- **JSON optimizations**: <$5K (1 week) ← **Current recommendation**
- **SQLite migration**: $20-30K (1 month)
- **PostgreSQL migration**: $40-60K (2 months) - Not recommended

---

## References

- Research document: `docs/research/json-to-database-migration-analysis-2025-11-29.md`
- Related ticket: 1M-364 (Entity type classification)
- Parent epic: Infrastructure improvements (f456fe9b-9ce1-4b05-adce-9a20f87ffd02)

---

## Notes

- Epic created successfully with all 4 sub-tasks linked
- Research document reference added to ticket comment
- All tickets assigned to bob@matsuoka.com
- Auto-detected labels applied based on content
- No blockers identified for immediate implementation
