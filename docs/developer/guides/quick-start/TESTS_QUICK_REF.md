# Tests Quick Reference

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- `test_api_v2.py` → `tests/api/`
- `uat_test*.py` → `tests/qa/`
- Browser test HTML/JS → `tests/browser/`
- `test_entity_models.py` → `tests/unit/`
- `test_endpoints.py` → `tests/server/`

---

**All test files are now in `tests/` directory**

## Quick Commands

```bash
# Run all Python tests
python -m pytest tests/ -v

# Run specific category
python -m pytest tests/unit/ -v      # Unit tests only
python -m pytest tests/api/ -v       # API tests only
python -m pytest tests/server/ -v    # Server tests only

# Run single test
python -m pytest tests/unit/test_entity_models.py -v

# Run with coverage
python -m pytest tests/ --cov=server --cov=scripts

# Run QA tests
python tests/qa/uat_test_v2.py --url http://localhost:8000

# Run script tests
./tests/scripts/test_server.sh
python tests/scripts/test_rag_system.py
```

## Directory Map

```
tests/
├── api/          → API endpoint tests (1 file)
├── browser/      → Browser UI tests (19 files)
├── integration/  → Integration tests (2 files)
├── qa/           → UAT tests (2 files)
├── scripts/      → Script tests (6 files)
├── server/       → Server tests (5 files)
└── unit/         → Unit tests (3 files)
```

## Test File Locations

**If you're looking for:**
- `test_api_v2.py` → `tests/api/`
- `uat_test*.py` → `tests/qa/`
- Browser test HTML/JS → `tests/browser/`
- `test_entity_models.py` → `tests/unit/`
- `test_endpoints.py` → `tests/server/`
- `test_rag_system.py` → `tests/scripts/`

## Full Documentation

See `tests/README.md` for comprehensive testing guide.

## Verification

```bash
# Verify structure
ls -la tests/

# Count test files
find tests -name "*.py" -o -name "*.html" -o -name "*.js" | wc -l
# Should show 39 files
```
