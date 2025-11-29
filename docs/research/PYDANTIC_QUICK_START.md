# Pydantic Schema Migration - Quick Start Guide

**Quick Summary**: Quick reference guide for rapid lookup of key information.

**Category**: Quick Reference
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- `EntitySource` enum
- `EntityType` enum
- `DocumentReference` model
- `TopConnection` model
- `Entity` model (main model)

---

**For Engineer Agent**: This is your implementation quick-start guide.

---

## 🚀 Quick Implementation Steps

### Step 1: Install Pydantic v2

```bash
cd /Users/masa/Projects/epstein
echo "pydantic==2.5.0" >> requirements.txt
pip install pydantic==2.5.0
```

### Step 2: Create Models Directory

```bash
mkdir -p server/models
touch server/models/__init__.py
```

### Step 3: Start with Entity Model (Phase 1)

**Create: `server/models/entity.py`**

Copy the Entity models from section 1 of `PYDANTIC_SCHEMA_DESIGN.md`:
- `EntitySource` enum
- `EntityType` enum
- `DocumentReference` model
- `TopConnection` model
- `Entity` model (main model)
- `EntityStatistics` model
- `EntityBiography` model
- `EntityTagInfo` model

### Step 4: Test Model Loading

**Create: `server/test_pydantic_models.py`**

```python
"""Test Pydantic models with real data"""

from pathlib import Path
import json
from models.entity import Entity, EntityStatistics

def test_load_entity_statistics():
    """Test loading entity_statistics.json"""

    path = Path("data/metadata/entity_statistics.json")

    with open(path) as f:
        data = json.load(f)

    # Validate with Pydantic
    stats = EntityStatistics.model_validate(data)

    print(f"✅ Loaded {stats.total_entities} entities")
    print(f"✅ Generated: {stats.generated}")

    # Test first entity
    first_entity = next(iter(stats.statistics.values()))
    print(f"✅ First entity: {first_entity.name}")
    print(f"   - Connections: {first_entity.connection_count}")
    print(f"   - Flights: {first_entity.flight_count}")

if __name__ == "__main__":
    test_load_entity_statistics()
```

Run test:
```bash
cd server
python test_pydantic_models.py
```

### Step 5: Update EntityService (Gradual)

**Modify: `server/services/entity_service.py`**

```python
# Add at top
from typing import Union
from models.entity import Entity, EntityStatistics

class EntityService:
    def __init__(self, data_path: Path, use_pydantic: bool = False):
        """
        Args:
            use_pydantic: If True, use Pydantic models. If False, use dicts (backward compatible)
        """
        self.use_pydantic = use_pydantic
        self.data_path = data_path
        self.metadata_dir = data_path / "metadata"

        # Load data
        self.load_data()

    def load_data(self):
        """Load entity data with optional Pydantic validation"""
        stats_path = self.metadata_dir / "entity_statistics.json"

        if not stats_path.exists():
            return

        with open(stats_path) as f:
            data = json.load(f)

        if self.use_pydantic:
            # Validate with Pydantic
            stats = EntityStatistics.model_validate(data)
            self.entity_stats = stats.statistics  # Dict[str, Entity]
        else:
            # Legacy: Use raw dict
            self.entity_stats = data.get("statistics", {})
```

### Step 6: Enable in API (Feature Flag)

**Modify: `server/api_routes.py`**

```python
import os

# Feature flag
USE_PYDANTIC = os.getenv("USE_PYDANTIC", "false").lower() == "true"

def init_services(data_path: Path):
    """Initialize services with Pydantic option"""
    global entity_service, flight_service, document_service, network_service

    entity_service = EntityService(data_path, use_pydantic=USE_PYDANTIC)
    # ... other services
```

### Step 7: Test with Feature Flag

```bash
# Test without Pydantic (backward compatible)
cd server
python app.py

# Test with Pydantic
USE_PYDANTIC=true python app.py
```

---

## 📋 Phase 1 Checklist (Week 1)

- [ ] Install Pydantic v2
- [ ] Create `server/models/` directory
- [ ] Create `server/models/entity.py` with:
  - [ ] `EntitySource` enum
  - [ ] `EntityType` enum
  - [ ] `DocumentReference` model
  - [ ] `TopConnection` model
  - [ ] `Entity` model
  - [ ] `EntityStatistics` model
  - [ ] `EntityBiography` model
  - [ ] `BiographyCollection` model
  - [ ] `EntityTag` enum
  - [ ] `EntityTagInfo` model
  - [ ] `TagCollection` model
- [ ] Create `server/models/__init__.py` with exports
- [ ] Create test file `server/test_pydantic_models.py`
- [ ] Test loading `entity_statistics.json` ✓
- [ ] Test loading `entity_biographies.json` ✓
- [ ] Test loading `entity_tags.json` ✓
- [ ] Fix any validation errors in data
- [ ] Update `EntityService` with `use_pydantic` flag
- [ ] Add `USE_PYDANTIC` environment variable
- [ ] Test API with feature flag ON
- [ ] Test API with feature flag OFF (ensure backward compatibility)
- [ ] Performance benchmark (before/after)
- [ ] Code review
- [ ] Commit Phase 1

---

## 🧪 Validation Error Handling

If you encounter validation errors during testing:

### Error: Missing Required Field

```
ValidationError: Field required [type=missing]
```

**Fix**: Add default value or make optional
```python
# Before
name: str

# After (Option A: Default)
name: str = Field(default="Unknown")

# After (Option B: Optional)
name: Optional[str] = None
```

### Error: Type Mismatch

```
ValidationError: Input should be a valid integer [type=int_type]
```

**Fix**: Add type coercion validator
```python
@field_validator('connection_count', mode='before')
@classmethod
def coerce_int(cls, v):
    if isinstance(v, str):
        return int(v)
    return v
```

### Error: Extra Fields

```
ValidationError: Extra inputs are not permitted [type=extra_forbidden]
```

**Fix**: Allow extra fields
```python
model_config = ConfigDict(
    extra='ignore'  # Silently ignore extra fields
)
```

---

## 📊 Testing Checklist

Run these tests after each phase:

```bash
# 1. Test model creation
python -c "from models.entity import Entity; e = Entity(name='Test', normalized_name='Test'); print('✅ Model creation works')"

# 2. Test JSON loading
python test_pydantic_models.py

# 3. Test API endpoints
curl http://localhost:8000/api/v2/entities?limit=5

# 4. Test with invalid data (should fail gracefully)
python -c "from models.entity import Entity; Entity(name='', normalized_name='Test')"
```

---

## 🔧 Common Patterns

### Pattern 1: Loading Data with Validation

```python
from pathlib import Path
import json
from pydantic import ValidationError

def load_json_with_validation(path: Path, model_class):
    """Load JSON with Pydantic validation"""
    try:
        with open(path) as f:
            data = json.load(f)
        return model_class.model_validate(data)
    except ValidationError as e:
        print(f"❌ Validation errors in {path}:")
        for error in e.errors():
            print(f"  - {error['loc']}: {error['msg']}")
        raise
```

### Pattern 2: Optional Validation (Feature Flag)

```python
def load_data_optional_validation(path: Path, model_class, validate: bool):
    """Load with optional validation"""
    with open(path) as f:
        data = json.load(f)

    if validate:
        # Validate and return model
        return model_class.model_validate(data)
    else:
        # Return raw dict
        return data
```

### Pattern 3: Converting Models to JSON

```python
# Serialize model to JSON
entity = Entity(...)
json_str = entity.model_dump_json(indent=2)

# Serialize to dict
entity_dict = entity.model_dump()

# Exclude None values
entity_dict = entity.model_dump(exclude_none=True)

# Exclude certain fields
entity_dict = entity.model_dump(exclude={'internal_field'})
```

---

## 🎯 Success Criteria

Phase 1 is complete when:

✅ All entity models defined in `models/entity.py`
✅ All 3 entity JSON files load without validation errors:
  - `entity_statistics.json`
  - `entity_biographies.json`
  - `entity_tags.json`
✅ `EntityService` works with both Pydantic and dict modes
✅ API endpoints return same results with `USE_PYDANTIC=true` and `false`
✅ Unit tests pass
✅ Performance overhead < 20% (acceptable)
✅ Code reviewed and committed

---

## 📚 Reference

- **Full Design Doc**: `PYDANTIC_SCHEMA_DESIGN.md`
- **Pydantic Docs**: https://docs.pydantic.dev/latest/
- **Field Validation**: https://docs.pydantic.dev/latest/concepts/validators/
- **FastAPI Integration**: https://fastapi.tiangolo.com/tutorial/response-model/

---

## 🚨 Important Notes

1. **Don't break existing code**: Use feature flags during migration
2. **Test with real data**: Use actual JSON files, not mock data
3. **Fix data issues**: If validation fails, fix the data source
4. **Performance**: Benchmark before/after, aim for <20% overhead
5. **Incremental**: Complete Phase 1 fully before Phase 2

---

## 💡 Quick Commands

```bash
# Install
pip install pydantic==2.5.0

# Test models
python server/test_pydantic_models.py

# Run with Pydantic
USE_PYDANTIC=true python server/app.py

# Run without Pydantic (backward compatible)
python server/app.py

# Check for validation errors
python -m pytest server/tests/test_models.py -v
```

---

**Ready to implement?** Start with Step 1 and work through Phase 1 checklist!
