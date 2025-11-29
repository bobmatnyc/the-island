# Tests Directory

All test files, scripts, and QA artifacts for the Epstein project.

## Directory Structure

```
tests/
├── README.md              # This file
├── __init__.py           # Python package marker
├── api/                  # API endpoint tests
│   └── test_api_v2.py   # API v2 endpoint tests
├── browser/              # Browser-based UI tests
│   ├── markdown-test.html
│   ├── test_browser_console.js
│   ├── test_buttons_simple.html
│   ├── test_flight_fixes.html
│   ├── test_flight_loading_performance.html
│   ├── test_nav_buttons.js
│   ├── test_page_load.js
│   ├── test_stats.html
│   ├── test_timeline_*.html/js
│   ├── test-modules-*.html/mjs
│   └── test-refactoring-phase1.html
├── integration/          # Integration tests
│   ├── test_timeline_playwright.py
│   └── test_timeline_scroll.py
├── qa/                   # User Acceptance Testing
│   ├── uat_test.py
│   └── uat_test_v2.py
├── scripts/              # Script tests
│   ├── test_audit_logging.py
│   ├── test_disambiguation_setup.py
│   ├── test_openrouter.py
│   ├── test_rag_system.py
│   ├── test_server.sh
│   └── test_tunnel_failover.sh
├── server/               # Server-side tests
│   ├── test_auth_flow.py
│   ├── test_auth.py
│   ├── test_endpoints.py
│   ├── test_enrichment.py
│   └── test_hot_reload.py
└── unit/                 # Unit tests
    ├── test_document_categories.py
    ├── test_entity_models.py
    └── test_suggestions.py
```

## Running Tests

### Python Tests

```bash
# Run all unit tests
python -m pytest tests/unit/

# Run specific unit test
python -m pytest tests/unit/test_entity_models.py

# Run all server tests
python -m pytest tests/server/

# Run all API tests
python -m pytest tests/api/

# Run integration tests
python -m pytest tests/integration/

# Run with verbose output
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=server --cov=scripts
```

### Browser Tests

Browser test files (HTML/JS) need to be served through a web server:

```bash
# Start the development server
cd /Users/masa/Projects/epstein
python server/app.py

# Then open browser tests:
# http://localhost:5000/static/tests/browser/test_timeline_navigation.html
# http://localhost:5000/static/tests/browser/test_flight_fixes.html
# etc.
```

Or use a simple HTTP server:

```bash
cd tests/browser
python -m http.server 8000
# Visit http://localhost:8000/test_timeline_navigation.html
```

### Script Tests

```bash
# Run shell script tests
cd tests/scripts
./test_server.sh
./test_tunnel_failover.sh

# Run Python script tests
python tests/scripts/test_rag_system.py
python tests/scripts/test_audit_logging.py
```

### QA/UAT Tests

```bash
# Run UAT tests
python tests/qa/uat_test.py
python tests/qa/uat_test_v2.py
```

## Test Categories

### Unit Tests (`tests/unit/`)
- Test individual functions and classes in isolation
- Fast, no external dependencies
- Use mocking for database/API calls

### Integration Tests (`tests/integration/`)
- Test interaction between components
- May use test database or external services
- Includes Playwright browser automation tests

### API Tests (`tests/api/`)
- Test REST API endpoints
- Verify request/response formats
- Test authentication and authorization

### Server Tests (`tests/server/`)
- Test server-side functionality
- Authentication flows
- Hot reload functionality
- Data enrichment

### Browser Tests (`tests/browser/`)
- Interactive HTML test pages
- JavaScript functionality tests
- Timeline visualization tests
- UI component tests
- Performance tests

### Scripts Tests (`tests/scripts/`)
- Test utility scripts
- Data processing scripts
- RAG system tests
- Tunnel/network tests

### QA Tests (`tests/qa/`)
- User acceptance testing
- End-to-end workflows
- Production-like scenarios

## Adding New Tests

### Python Tests

1. Create test file in appropriate directory
2. Name file starting with `test_`
3. Use pytest conventions:
   ```python
   def test_feature_name():
       # Arrange
       # Act
       # Assert
       pass
   ```

### Browser Tests

1. Create HTML file in `tests/browser/`
2. Include test framework (if needed)
3. Document test purpose in HTML comments

### Script Tests

1. Add to `tests/scripts/`
2. Make executable: `chmod +x tests/scripts/test_your_script.sh`
3. Document usage in file header

## Test Data

Test data should be:
- Stored in `tests/fixtures/` (create if needed)
- Small and focused
- Not include production data
- Use mocking for external services

## Continuous Integration

Tests are run automatically on:
- Pull requests
- Commits to main branch
- Nightly builds (full test suite)

## Coverage Goals

- Unit tests: >80% coverage
- Integration tests: Critical paths covered
- API tests: All endpoints tested
- Browser tests: Key UI workflows tested

## Troubleshooting

### Import Errors in Moved Tests

If tests fail with import errors, update the Python path:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Browser Tests Not Loading

1. Check server is running
2. Verify file paths in HTML
3. Check browser console for errors

### Database Connection Errors

Tests should use test database or mocks. If seeing connection errors:

```bash
# Set test database environment
export DATABASE_URL=sqlite:///test.db
```

## Best Practices

1. **Keep tests fast**: Unit tests should run in milliseconds
2. **Make tests independent**: No test should depend on another
3. **Use descriptive names**: `test_user_login_with_valid_credentials()`
4. **Clean up after tests**: Remove test data, close connections
5. **Mock external services**: Don't hit real APIs in tests
6. **Test edge cases**: Not just happy paths
7. **Update tests with code**: Keep tests in sync with implementation

## Test Utilities

Common test utilities can be added to:
- `tests/conftest.py` - pytest fixtures
- `tests/helpers.py` - test helper functions
- `tests/mocks.py` - mock objects and data

## Documentation

Each test file should include:
- Module docstring explaining what it tests
- Function docstrings for complex tests
- Comments for non-obvious assertions
- Links to related documentation

## Related Files

- `Makefile` - test running shortcuts
- `.github/workflows/` - CI/CD test configurations
- `pytest.ini` or `pyproject.toml` - pytest configuration
- `.coveragerc` - coverage configuration
