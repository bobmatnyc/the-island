# Pydantic Models - Quick Reference

**Quick Summary**: Quick reference guide for rapid lookup of key information.

**Category**: Quick Reference
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Quick Start
- Enable Pydantic Validation
- Import Models
- Common Patterns
- 1. Create Entity

---

**Last Updated**: 2025-11-18
**Phase**: 1 (Entity Models)
**Status**: ✅ Production Ready

## Quick Start

### Enable Pydantic Validation
```bash
# Enable globally
export USE_PYDANTIC=true

# Or per-script
USE_PYDANTIC=true python scripts/analysis/my_script.py
```

### Import Models
```python
from server.models import (
    Entity, EntityBiography, EntityTag,
    NetworkNode, NetworkEdge, NetworkGraph,
    EntityType, SourceType, DocumentType
)
```

## Common Patterns

### 1. Create Entity
```python
entity = Entity(
    name="Epstein, Jeffrey",
    connection_count=262,
    flight_count=8,
    sources=[SourceType.BLACK_BOOK, SourceType.FLIGHT_LOGS]
)

# Auto-populated fields:
# - normalized_name: "Epstein, Jeffrey" (from name)
# - entity_type: EntityType.PERSON (auto-detected)
# - top_connections: [] (default)
```

### 2. Load from Dict
```python
entity_data = {
    "name": "Maxwell, Ghislaine",
    "connection_count": 188,
    "sources": ["black_book", "flight_logs"]
}

entity = Entity(**entity_data)
```

### 3. Convert to Dict
```python
entity_dict = entity.model_dump()
# Or for JSON
entity_json = entity.model_dump_json()
```

### 4. Validate Network Graph
```python
nodes = [
    NetworkNode(id="A", name="Person A", connection_count=2),
    NetworkNode(id="B", name="Person B", connection_count=1)
]
edges = [
    NetworkEdge(source="A", target="B", weight=5)
]

# Validates: no self-loops, no orphaned edges
graph = NetworkGraph(nodes=nodes, edges=edges)

# Access helper methods
node = graph.get_node_by_id("A")
edges_for_a = graph.get_edges_for_node("A")
adj_list = graph.to_adjacency_list()
```

### 5. Handle Validation Errors
```python
from pydantic import ValidationError

try:
    entity = Entity(
        name="Test",
        connection_count=-1  # Invalid!
    )
except ValidationError as e:
    print(e.errors())
    # [{'loc': ('connection_count',), 'msg': 'greater than or equal to 0', ...}]
```

### 6. Use with EntityService
```python
from server.services.entity_service import EntityService
from pathlib import Path

service = EntityService(Path("data"))

# Get entity (Pydantic model if USE_PYDANTIC=true)
entity = service.get_entity_by_name("Epstein, Jeffrey")

# Convert to dict for API response
entity_dict = service.to_dict(entity)

# Get validation report
report = service.get_validation_report()
print(f"Success rate: {report['success_rate'] * 100:.2f}%")
```

## Field Defaults

### Entity Defaults
```python
Entity(
    name="Required",
    # Optional fields with defaults:
    normalized_name=None,        # Auto-populated from name
    entity_type=EntityType.UNKNOWN,
    in_black_book=False,
    is_billionaire=False,
    connection_count=0,
    flight_count=0,
    total_documents=0,
    sources=[],
    top_connections=[],
    documents=[]
)
```

### NetworkEdge Defaults
```python
NetworkEdge(
    source="Required",
    target="Required",
    weight=1,                   # Default: 1
    flight_count=None,          # Auto-synced with weight
    contexts=[]
)
```

## Validation Rules

### Entity Validation
- ✅ `name`: Required, min 1 character
- ✅ `normalized_name`: Auto-populated if missing
- ✅ `connection_count`: Must be ≥ 0
- ✅ `flight_count`: Must be ≥ 0
- ✅ `top_connections`: Auto-sorted, max 10
- ✅ `sources`: Auto-deduplicated

### Biography Validation
- ✅ `entity_name`: Required
- ✅ `biography`: Min 10 characters
- ✅ `last_updated`: ISO timestamp format

### Tag Validation
- ✅ `tags`: Min 1 tag, auto-normalized to lowercase
- ✅ `primary_tag`: Auto-added to tags if missing

### Network Validation
- ❌ Self-loops rejected
- ❌ Orphaned edges rejected (must reference existing nodes)
- ❌ Duplicate node IDs rejected
- ✅ Edge weight must be ≥ 1

## Auto-Transformations

### Name Normalization
```python
entity = Entity(
    name="Test",
    normalized_name="  Epstein,  Jeffrey  "
)
# Result: normalized_name = "Epstein, Jeffrey" (stripped, collapsed)
```

### Connection Sorting
```python
entity = Entity(
    name="Test",
    top_connections=[
        TopConnection(name="A", flights_together=5),
        TopConnection(name="B", flights_together=10),
        TopConnection(name="C", flights_together=3)
    ]
)
# Auto-sorted: [B(10), A(5), C(3)]
```

### Tag Normalization
```python
tags = EntityTag(
    entity_name="Test",
    tags=["Politics", "  Business  ", "politics"]
)
# Result: tags = ["politics", "business"] (lowercase, deduplicated)
```

### Source Deduplication
```python
entity = Entity(
    name="Test",
    sources=[
        SourceType.BLACK_BOOK,
        SourceType.FLIGHT_LOGS,
        SourceType.BLACK_BOOK  # Duplicate
    ]
)
# Result: sources = [BLACK_BOOK, FLIGHT_LOGS]
```

## Performance Tips

### Bulk Loading
```python
# For trusted data, skip validation
entities = []
for entity_data in large_dataset:
    # Use model_construct (no validation)
    entity = Entity.model_construct(**entity_data)
    entities.append(entity)

# Validate afterward if needed
for entity in entities:
    entity.model_validate(entity)
```

### Caching Results
```python
# Cache validation results
validated_entities = {}

for name, data in entity_data.items():
    try:
        entity = Entity(**data)
        validated_entities[name] = entity
    except ValidationError as e:
        logger.warning(f"Skipping invalid entity {name}: {e}")
```

## Common Errors

### Missing Required Field
```python
# ERROR: Field required
Entity()  # Missing 'name'

# FIX: Provide required field
Entity(name="Test")
```

### Negative Count
```python
# ERROR: greater than or equal to 0
Entity(name="Test", connection_count=-1)

# FIX: Use non-negative value
Entity(name="Test", connection_count=0)
```

### Self-Loop Edge
```python
# ERROR: Self-loops not allowed
NetworkEdge(source="A", target="A", weight=1)

# FIX: Use different source and target
NetworkEdge(source="A", target="B", weight=1)
```

### Orphaned Edge
```python
nodes = [NetworkNode(id="A", name="A", connection_count=0)]
edges = [NetworkEdge(source="A", target="B", weight=1)]  # B doesn't exist

# ERROR: Edge target 'B' not in nodes
NetworkGraph(nodes=nodes, edges=edges)

# FIX: Add missing node
nodes.append(NetworkNode(id="B", name="B", connection_count=0))
NetworkGraph(nodes=nodes, edges=edges)
```

## Testing

### Run Unit Tests
```bash
# All tests
pytest tests/test_entity_models.py -v

# Specific test class
pytest tests/test_entity_models.py::TestEntity -v

# Single test
pytest tests/test_entity_models.py::TestEntity::test_entity_minimal_valid -v
```

### Run Validation Audit
```bash
# Full audit with report
python scripts/validation/run_pydantic_audit.py

# Verbose mode (shows errors)
python scripts/validation/run_pydantic_audit.py --verbose
```

## Configuration

### Environment Variables
```bash
# Enable Pydantic validation
export USE_PYDANTIC=true

# Disable Pydantic validation (default)
export USE_PYDANTIC=false
```

### Feature Flag in Code
```python
import os

# Check if enabled
use_pydantic = os.getenv('USE_PYDANTIC', 'false').lower() == 'true'

if use_pydantic:
    entity = Entity(**data)  # Validated
else:
    entity = data  # Raw dict
```

## Migration Checklist

### Enabling Pydantic in Production
- [ ] Set `USE_PYDANTIC=true`
- [ ] Run validation audit: `python scripts/validation/run_pydantic_audit.py`
- [ ] Verify 100% success rate
- [ ] Test API endpoints with Pydantic models
- [ ] Monitor performance (should be <20% overhead)
- [ ] Check logs for validation warnings
- [ ] Roll back if issues: `USE_PYDANTIC=false`

## Resources

### Documentation
- **Full Design**: `PYDANTIC_SCHEMA_DESIGN.md`
- **Implementation Summary**: `PYDANTIC_PHASE1_COMPLETE.md`
- **Migration Roadmap**: `PYDANTIC_MIGRATION_ROADMAP.md`
- **Validation Report**: `PYDANTIC_VALIDATION_REPORT.md`

### Code
- **Models**: `server/models/entity.py`, `server/models/network.py`
- **Service**: `server/services/entity_service.py`
- **Tests**: `tests/test_entity_models.py`
- **Audit**: `scripts/validation/run_pydantic_audit.py`

### Pydantic Docs
- **Official Docs**: https://docs.pydantic.dev/
- **Migration Guide**: https://docs.pydantic.dev/2.12/migration/
- **Validation**: https://docs.pydantic.dev/2.12/concepts/validators/

---

**Questions?** Check `PYDANTIC_PHASE1_COMPLETE.md` for detailed implementation notes.
