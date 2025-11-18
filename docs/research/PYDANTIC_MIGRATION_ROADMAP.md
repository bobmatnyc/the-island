# Pydantic Migration Roadmap

**Project**: Epstein Data Platform - Type Safety Migration
**Timeline**: 3-4 weeks
**Goal**: Add Pydantic v2 validation to all data models

---

## 📅 Timeline Overview

```
Week 1: Entity Models       ████████████████░░░░░░░░░░░░  40% Complete
Week 2: Document Models     ░░░░░░░░░░░░░░░░████████████  40% Complete
Week 3: Flight & Network    ░░░░░░░░░░░░░░░░░░░░░░░░████  15% Complete
Week 4: Timeline & Polish   ░░░░░░░░░░░░░░░░░░░░░░░░░░░░   5% Complete
```

---

## 🎯 Week 1: Entity Models (Days 1-5)

**Goal**: Implement and validate all entity-related models

### Day 1: Setup & Core Entity Model

**Tasks**:
- [x] Install Pydantic v2: `pip install pydantic==2.5.0`
- [x] Create `server/models/` directory structure
- [ ] Create `server/models/__init__.py`
- [ ] Create `server/models/common.py` (shared enums)
- [ ] Create `server/models/entity.py`
- [ ] Implement `EntitySource` enum
- [ ] Implement `EntityType` enum
- [ ] Implement `DocumentReference` model
- [ ] Implement `TopConnection` model
- [ ] Implement `Entity` model (main)

**Files to Create**:
```
server/models/
├── __init__.py
├── common.py        # Shared types and enums
└── entity.py        # Entity models
```

**Validation Test**:
```bash
python -c "from models.entity import Entity; print('✅ Entity model works')"
```

**Time Estimate**: 3-4 hours

---

### Day 2: Entity Collections

**Tasks**:
- [ ] Implement `EntityStatistics` model
- [ ] Implement `EntityBiography` model
- [ ] Implement `BiographyCollection` model
- [ ] Add helper functions (`load_entity_statistics`, etc.)
- [ ] Create `server/test_pydantic_models.py`
- [ ] Test loading `entity_statistics.json`

**Validation Test**:
```bash
cd server
python test_pydantic_models.py
```

**Expected Output**:
```
✅ Loaded 1702 entities
✅ Generated: 2025-11-17T18:53:21.321883
✅ First entity: Dubin, Glenn
   - Connections: 24
   - Flights: 0
```

**Time Estimate**: 3-4 hours

---

### Day 3: Entity Tags & Biographies

**Tasks**:
- [ ] Implement `EntityTag` enum (13 values)
- [ ] Implement `EntityTagInfo` model
- [ ] Implement `TagCollection` model
- [ ] Test loading `entity_tags.json`
- [ ] Test loading `entity_biographies.json`
- [ ] Fix any validation errors in data

**Data Quality Checks**:
```bash
# Check for validation errors
python -c "
from models.entity import BiographyCollection, TagCollection
import json

# Test biographies
with open('data/metadata/entity_biographies.json') as f:
    bio_data = json.load(f)
    bios = BiographyCollection.model_validate(bio_data)
    print(f'✅ {len(bios.entities)} biographies validated')

# Test tags
with open('data/metadata/entity_tags.json') as f:
    tag_data = json.load(f)
    tags = TagCollection.model_validate(tag_data)
    print(f'✅ {len(tags.entities)} tagged entities validated')
"
```

**Time Estimate**: 4 hours

---

### Day 4: Update EntityService

**Tasks**:
- [ ] Backup `server/services/entity_service.py`
- [ ] Add `use_pydantic` parameter to `__init__`
- [ ] Update `load_data()` to support both dict and Pydantic modes
- [ ] Update `get_entities()` to work with Entity models
- [ ] Update `get_entity_by_name()` to return Entity model
- [ ] Test backward compatibility (dict mode)
- [ ] Test Pydantic mode

**Code Changes**:
```python
# Before
class EntityService:
    def __init__(self, data_path: Path):
        self.entity_stats = {}  # Dict

# After
class EntityService:
    def __init__(self, data_path: Path, use_pydantic: bool = False):
        self.use_pydantic = use_pydantic
        self.entity_stats = {}  # Dict or Dict[str, Entity]
```

**Validation Tests**:
```bash
# Test dict mode (backward compatible)
python -c "
from services.entity_service import EntityService
from pathlib import Path
service = EntityService(Path('data'), use_pydantic=False)
print('✅ Dict mode works')
"

# Test Pydantic mode
python -c "
from services.entity_service import EntityService
from pathlib import Path
service = EntityService(Path('data'), use_pydantic=True)
print('✅ Pydantic mode works')
"
```

**Time Estimate**: 4 hours

---

### Day 5: API Integration & Testing

**Tasks**:
- [ ] Add `USE_PYDANTIC` environment variable to `api_routes.py`
- [ ] Update `init_services()` to pass `use_pydantic` flag
- [ ] Test API endpoints with feature flag OFF
- [ ] Test API endpoints with feature flag ON
- [ ] Verify identical responses in both modes
- [ ] Performance benchmark (before/after)
- [ ] Write unit tests
- [ ] Code review
- [ ] Commit Phase 1

**Testing Script**:
```bash
# Test without Pydantic (baseline)
python server/app.py &
SERVER_PID=$!
sleep 2

curl -s "http://localhost:8000/api/v2/entities?limit=5" | jq . > /tmp/response_dict.json

kill $SERVER_PID

# Test with Pydantic
USE_PYDANTIC=true python server/app.py &
SERVER_PID=$!
sleep 2

curl -s "http://localhost:8000/api/v2/entities?limit=5" | jq . > /tmp/response_pydantic.json

kill $SERVER_PID

# Compare (should be identical)
diff /tmp/response_dict.json /tmp/response_pydantic.json
echo "✅ Responses match" || echo "❌ Responses differ"
```

**Performance Benchmark**:
```bash
# Benchmark dict mode
time curl "http://localhost:8000/api/v2/entities?limit=100" > /dev/null

# Benchmark Pydantic mode
USE_PYDANTIC=true time curl "http://localhost:8000/api/v2/entities?limit=100" > /dev/null

# Acceptable: <20% slower
```

**Time Estimate**: 4-5 hours

---

## 🎯 Week 2: Document Models (Days 6-10)

**Goal**: Implement document, email, and PDF models

### Day 6: Core Document Model

**Tasks**:
- [ ] Create `server/models/document.py`
- [ ] Implement `DocumentType` enum
- [ ] Implement `DocumentClassification` enum
- [ ] Implement `DocumentMetadata` model
- [ ] Implement `Document` model (base)
- [ ] Add field validators (ID generation, type inference)

**Time Estimate**: 4 hours

---

### Day 7: Specialized Document Models

**Tasks**:
- [ ] Implement `EmailDocument` model (extends Document)
- [ ] Implement `PDFDocument` model (extends Document)
- [ ] Implement `DocumentIndex` model (collection)
- [ ] Test model creation
- [ ] Test field validation

**Time Estimate**: 3-4 hours

---

### Day 8: Document Data Loading

**Tasks**:
- [ ] Test loading `all_documents_index.json`
- [ ] Handle large file (11MB) - use streaming if needed
- [ ] Fix validation errors in document data
- [ ] Verify all documents validate successfully
- [ ] Performance test (loading time)

**Large File Strategy**:
```python
import json
from pathlib import Path

def load_documents_in_chunks():
    """Load large document index in chunks"""
    path = Path("data/metadata/all_documents_index.json")

    with open(path) as f:
        data = json.load(f)

    # Validate in chunks to reduce memory
    docs = data.get("documents", [])
    chunk_size = 1000

    validated_docs = []
    for i in range(0, len(docs), chunk_size):
        chunk = docs[i:i+chunk_size]
        validated_chunk = [Document.model_validate(doc) for doc in chunk]
        validated_docs.extend(validated_chunk)

    return DocumentIndex(
        documents=validated_docs,
        total_count=len(validated_docs)
    )
```

**Time Estimate**: 5 hours

---

### Day 9: Update DocumentService

**Tasks**:
- [ ] Backup `server/services/document_service.py`
- [ ] Add `use_pydantic` parameter
- [ ] Update `load_data()` for Document models
- [ ] Update `search_documents()` to work with models
- [ ] Test backward compatibility
- [ ] Test Pydantic mode

**Time Estimate**: 4 hours

---

### Day 10: Document API & Testing

**Tasks**:
- [ ] Update document API endpoints
- [ ] Test with feature flag OFF/ON
- [ ] Verify response consistency
- [ ] Write unit tests
- [ ] Performance benchmark
- [ ] Code review
- [ ] Commit Phase 2

**Time Estimate**: 4-5 hours

---

## 🎯 Week 3: Flight & Network Models (Days 11-15)

**Goal**: Implement flight logs and network graph models

### Day 11: Flight Model

**Tasks**:
- [ ] Create `server/models/flight.py`
- [ ] Implement `Flight` model
- [ ] Add field validators (route parsing, passenger count)
- [ ] Implement `FlightCollection` model
- [ ] Test loading `flight_logs_by_flight.json`

**Route Parsing Validator**:
```python
@field_validator('from_airport', 'to_airport', mode='before')
@classmethod
def parse_route(cls, v: Optional[str], info) -> Optional[str]:
    """Auto-parse FROM-TO from route field"""
    if v:
        return v
    route = info.data.get('route', '')
    if '-' in route:
        from_code, to_code = route.split('-', 1)
        if info.field_name == 'from_airport':
            return from_code
        return to_code
    return None
```

**Time Estimate**: 4 hours

---

### Day 12: Airport Locations

**Tasks**:
- [ ] Implement `AirportLocation` model
- [ ] Implement `RouteStatistics` model
- [ ] Test loading location data (if exists)
- [ ] Verify coordinates validation (-90 to 90, -180 to 180)

**Time Estimate**: 3 hours

---

### Day 13: Network Models

**Tasks**:
- [ ] Create `server/models/network.py`
- [ ] Implement `NetworkNode` model
- [ ] Implement `NetworkEdge` model
- [ ] Add validator: prevent self-loops
- [ ] Add validator: verify nodes exist for edges
- [ ] Implement `NetworkGraph` model
- [ ] Test loading `entity_network.json`

**Self-Loop Prevention**:
```python
@field_validator('target', mode='after')
@classmethod
def validate_not_self_loop(cls, v: str, info) -> str:
    """Prevent edge from node to itself"""
    source = info.data.get('source', '')
    if v == source:
        raise ValueError("Edge cannot connect node to itself")
    return v
```

**Time Estimate**: 4-5 hours

---

### Day 14: Update Services

**Tasks**:
- [ ] Update `FlightService` with Pydantic support
- [ ] Update `NetworkService` with Pydantic support
- [ ] Test backward compatibility
- [ ] Test Pydantic mode

**Time Estimate**: 4 hours

---

### Day 15: API Integration & Testing

**Tasks**:
- [ ] Update flight API endpoints
- [ ] Update network API endpoints
- [ ] Test with feature flags
- [ ] Write unit tests
- [ ] Performance benchmark
- [ ] Code review
- [ ] Commit Phase 3

**Time Estimate**: 4-5 hours

---

## 🎯 Week 4: Timeline, Response Models & Polish (Days 16-20)

**Goal**: Complete remaining models and polish implementation

### Day 16: Timeline Model

**Tasks**:
- [ ] Create `server/models/timeline.py`
- [ ] Implement `TimelineCategory` enum
- [ ] Implement `TimelineEvent` model
- [ ] Add date format validator
- [ ] Add URL validator
- [ ] Implement `TimelineCollection` model
- [ ] Add auto-sorting of events by date
- [ ] Test loading `timeline.json`

**Date Sorting**:
```python
@field_validator('events', mode='after')
@classmethod
def sort_events(cls, v: List[TimelineEvent]) -> List[TimelineEvent]:
    """Sort events chronologically by date"""
    return sorted(v, key=lambda e: e.date)
```

**Time Estimate**: 3-4 hours

---

### Day 17: API Response Models

**Tasks**:
- [ ] Create `server/models/responses.py`
- [ ] Implement `PaginatedResponse` (generic)
- [ ] Implement `EntityListResponse`
- [ ] Implement `DocumentListResponse`
- [ ] Implement `FlightListResponse`
- [ ] Implement `SearchResult` model
- [ ] Implement `ErrorDetail` model
- [ ] Implement `ErrorResponse` model

**Time Estimate**: 3 hours

---

### Day 18: Update All API Endpoints

**Tasks**:
- [ ] Update entity endpoints with `response_model`
- [ ] Update document endpoints with `response_model`
- [ ] Update flight endpoints with `response_model`
- [ ] Update network endpoints with `response_model`
- [ ] Update timeline endpoints with `response_model`
- [ ] Test OpenAPI docs generation
- [ ] Verify all type hints are correct

**FastAPI Type Hints**:
```python
@router.get("/entities", response_model=EntityListResponse)
async def get_entities(...) -> EntityListResponse:
    """Get entities with type-safe response"""
    return entity_service.get_entities(...)
```

**Time Estimate**: 4 hours

---

### Day 19: Comprehensive Testing

**Tasks**:
- [ ] Run full test suite
- [ ] Test all endpoints with Pydantic ON
- [ ] Test all endpoints with Pydantic OFF
- [ ] Verify identical responses
- [ ] Performance benchmarks (all endpoints)
- [ ] Load testing (1000 requests)
- [ ] Memory profiling
- [ ] Fix any performance issues

**Load Test Script**:
```bash
# Install Apache Bench
brew install httpd

# Test entity endpoint (100 requests, 10 concurrent)
ab -n 100 -c 10 http://localhost:8000/api/v2/entities

# Test with Pydantic
USE_PYDANTIC=true python server/app.py &
ab -n 100 -c 10 http://localhost:8000/api/v2/entities
```

**Time Estimate**: 5-6 hours

---

### Day 20: Documentation & Deployment

**Tasks**:
- [ ] Update `README.md` with Pydantic info
- [ ] Update API documentation
- [ ] Update developer documentation
- [ ] Create migration guide for contributors
- [ ] Code review (full codebase)
- [ ] Create PR with all changes
- [ ] Deploy to staging environment
- [ ] Monitor for errors
- [ ] Deploy to production (with feature flag)
- [ ] Monitor performance in production
- [ ] Enable Pydantic by default (if all good)

**Deployment Checklist**:
```
✓ All tests passing
✓ Performance acceptable (<20% overhead)
✓ No validation errors in production data
✓ Backward compatibility verified
✓ Documentation updated
✓ Code reviewed
✓ Staging deployment successful
✓ Production deployment (with flag)
✓ Monitoring in place
```

**Time Estimate**: 4-5 hours

---

## 📊 Progress Tracking

### Overall Progress

| Phase | Status | Completion | Time Spent | Time Remaining |
|-------|--------|------------|------------|----------------|
| Week 1: Entities | 🟡 In Progress | 0% | 0h | 18-20h |
| Week 2: Documents | ⚪ Not Started | 0% | 0h | 18-20h |
| Week 3: Flight/Network | ⚪ Not Started | 0% | 0h | 18-20h |
| Week 4: Timeline/Polish | ⚪ Not Started | 0% | 0h | 18-20h |

**Total Estimated Time**: 72-80 hours (3-4 weeks @ 20h/week)

---

## 🎯 Success Metrics

### Week 1 Success Criteria

✅ All entity models defined
✅ All 3 entity JSON files validate successfully
✅ EntityService supports both dict and Pydantic modes
✅ API endpoints work with feature flag ON/OFF
✅ Performance overhead < 20%
✅ Unit tests pass
✅ Code reviewed and committed

### Week 2 Success Criteria

✅ All document models defined
✅ Document index (11MB) loads successfully
✅ DocumentService supports both modes
✅ Document API endpoints work correctly
✅ Performance acceptable
✅ Tests pass

### Week 3 Success Criteria

✅ Flight and Network models defined
✅ Both JSON files validate successfully
✅ Services updated
✅ API endpoints work correctly
✅ Tests pass

### Week 4 Success Criteria

✅ Timeline models complete
✅ API response models complete
✅ All endpoints use proper type hints
✅ OpenAPI docs complete and accurate
✅ Full test suite passes
✅ Performance benchmarks acceptable
✅ Deployed to production

---

## 🚨 Risk Management

### Risk 1: Data Validation Failures

**Likelihood**: Medium
**Impact**: High

**Mitigation**:
- Run validation audits early (Day 1-2)
- Fix data quality issues proactively
- Use `extra='ignore'` for unknown fields
- Add type coercion validators where needed

**Contingency**:
- If >10% of data fails validation, pause and fix data
- Create data cleaning scripts
- Document all data quality issues

---

### Risk 2: Performance Degradation

**Likelihood**: Low
**Impact**: Medium

**Mitigation**:
- Benchmark early and often
- Use `model_validate_json()` for better performance
- Lazy load large datasets
- Cache validated objects

**Contingency**:
- If overhead >20%, optimize validators
- Disable validation for trusted data
- Use async loading for large files

---

### Risk 3: Breaking Changes

**Likelihood**: Low
**Impact**: High

**Mitigation**:
- Use feature flags throughout migration
- Maintain backward compatibility
- Test both modes extensively
- Gradual rollout to production

**Contingency**:
- If breaking changes found, revert to dict mode
- Fix issues in separate branch
- Re-test before re-enabling

---

## 📋 Daily Checklist Template

Use this for each day:

```
Day X: [Phase Name]
Date: ___________
Developer: ___________

Morning (9am-12pm):
□ Review tasks for the day
□ Pull latest code
□ Run existing tests
□ Start implementation
□ [Specific task 1]
□ [Specific task 2]

Afternoon (1pm-5pm):
□ [Specific task 3]
□ [Specific task 4]
□ Write unit tests
□ Run all tests
□ Performance check

End of Day:
□ Code review (self)
□ Commit changes
□ Update progress tracker
□ Document any issues
□ Plan next day

Blockers/Issues:
-
-

Notes:
-
-
```

---

## 🎓 Learning Resources

### Essential Reading (Before Starting)

1. **Pydantic Docs**: https://docs.pydantic.dev/latest/
   - Read: Concepts → Models
   - Read: Concepts → Validators
   - Read: Concepts → JSON Schema

2. **FastAPI + Pydantic**: https://fastapi.tiangolo.com/tutorial/response-model/
   - Response models
   - Request body validation
   - Nested models

3. **Migration Guide**: https://docs.pydantic.dev/latest/migration/
   - v1 to v2 changes
   - Breaking changes
   - New features

### Reference During Development

- **Field Types**: https://docs.pydantic.dev/latest/concepts/types/
- **Validators**: https://docs.pydantic.dev/latest/concepts/validators/
- **Config**: https://docs.pydantic.dev/latest/concepts/config/
- **Performance**: https://docs.pydantic.dev/latest/concepts/performance/

---

## 🏁 Final Checklist (After Week 4)

### Code Quality

- [ ] All models defined and documented
- [ ] All services updated
- [ ] All API endpoints type-hinted
- [ ] No validation errors in production data
- [ ] Code coverage >80%
- [ ] No linting errors
- [ ] No type errors (mypy clean)

### Testing

- [ ] Unit tests for all models
- [ ] Integration tests for all services
- [ ] API endpoint tests
- [ ] Performance benchmarks
- [ ] Load testing
- [ ] Memory profiling

### Documentation

- [ ] README updated
- [ ] API docs complete
- [ ] Migration guide written
- [ ] Code comments added
- [ ] OpenAPI schema complete
- [ ] Examples provided

### Deployment

- [ ] Feature flags implemented
- [ ] Staging deployment successful
- [ ] Production deployment successful
- [ ] Monitoring in place
- [ ] Rollback plan documented
- [ ] Team trained on new system

---

## 📞 Support & Questions

**Primary Contact**: Development Team Lead
**Documentation**: `PYDANTIC_SCHEMA_DESIGN.md`
**Quick Start**: `PYDANTIC_QUICK_START.md`
**Visual Guide**: `PYDANTIC_SCHEMA_VISUAL_SUMMARY.md`

**Get Help**:
1. Check documentation first
2. Search Pydantic docs: https://docs.pydantic.dev
3. Ask in team chat
4. Create issue in project tracker

---

**Ready to start?** Begin with Week 1, Day 1 tasks!
