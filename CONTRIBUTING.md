# Contributing to Epstein Document Archive

Thank you for your interest in contributing! This document provides guidelines for code quality, testing, and development workflow.

---

## Table of Contents

1. [Development Setup](#development-setup)
2. [Code Quality Standards](#code-quality-standards)
3. [Pre-Release Checklist](#pre-release-checklist)
4. [Linting and Formatting](#linting-and-formatting)
5. [Type Checking](#type-checking)
6. [Testing](#testing)
7. [Pull Request Process](#pull-request-process)
8. [Code Review Criteria](#code-review-criteria)

---

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Tesseract OCR (for document processing)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/epstein-document-archive.git
cd epstein-document-archive

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install ruff black isort mypy pytest pytest-cov pytest-asyncio

# Verify installation
python -m pytest --version
ruff --version
black --version
```

---

## Code Quality Standards

### Code Style

This project follows **PEP 8** with the following modifications:

- **Line Length**: 100 characters (not 79)
- **String Quotes**: Double quotes preferred (`"` not `'`)
- **Docstring Format**: Google style

### Design Principles

1. **Explicit over Implicit**: Clear, readable code over clever tricks
2. **Fail Fast**: Validate inputs early, propagate errors up
3. **Provenance Tracking**: All data must have source attribution
4. **No Global State**: Use dependency injection for configuration
5. **Type Hints**: All functions should have type annotations

### Forbidden Patterns

❌ **DON'T DO THIS**:

```python
# Bare except clauses
try:
    risky_operation()
except:
    pass

# Global mutable state
CACHE = {}

# Hardcoded paths
FILE_PATH = "/Users/username/Projects/data.json"

# Mock data in production
def get_user(user_id):
    return {"id": user_id, "name": "Mock User"}

# Silent failures
def load_config():
    try:
        return read_config()
    except Exception:
        return {}  # Silent failure!
```

✅ **DO THIS**:

```python
# Specific exception handling
try:
    risky_operation()
except (ValueError, KeyError) as e:
    logger.error(f"Operation failed: {e}")
    raise

# Dependency injection
@dataclass
class Service:
    cache: ICache

# Relative paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Fail fast if config missing
def load_config():
    try:
        return read_config()
    except FileNotFoundError as e:
        raise ConfigurationError("Config file not found") from e
```

---

## Pre-Release Checklist

Before submitting a pull request, run the pre-release script:

```bash
# Check code quality (no modifications)
./scripts/pre_release.sh

# Auto-fix linting and formatting issues
./scripts/pre_release.sh --fix

# Fast check (skip tests)
./scripts/pre_release.sh --fast
```

### Exit Codes

- `0` - All checks passed ✓
- `1` - Linting failures
- `2` - Type checking failures
- `3` - Test failures
- `4` - Coverage below threshold

---

## Linting and Formatting

### Ruff (Linter)

Ruff is a fast Python linter that replaces flake8, isort, and more.

```bash
# Check for linting issues
ruff check scripts/ server/

# Auto-fix issues
ruff check --fix scripts/ server/

# Check specific file
ruff check scripts/extraction/ocr_house_oversight.py
```

**Configuration**: `.ruff.toml`

### Black (Formatter)

Black is an opinionated code formatter with minimal configuration.

```bash
# Check formatting
black --check scripts/ server/

# Auto-format
black scripts/ server/

# Format specific file
black scripts/analysis/entity_network.py
```

**Configuration**: `pyproject.toml` under `[tool.black]`

### isort (Import Sorter)

isort sorts imports alphabetically and separates them into sections.

```bash
# Check import sorting
isort --check-only scripts/ server/

# Auto-sort imports
isort scripts/ server/

# Sort specific file
isort server/app.py
```

**Configuration**: `pyproject.toml` under `[tool.isort]`

---

## Type Checking

### mypy (Static Type Checker)

mypy performs static type checking to catch type errors before runtime.

```bash
# Type check all files
mypy scripts/ server/

# Type check specific file
mypy server/app.py

# Show error context
mypy --show-error-context scripts/core/deduplicator.py
```

**Configuration**: `pyproject.toml` under `[tool.mypy]`

### Type Hint Guidelines

1. **All function signatures** should have type hints
2. **Return types** are mandatory
3. **Use `Optional[T]`** for nullable values
4. **Use `List[T]`, `Dict[K, V]`** instead of `list`, `dict`
5. **Import from `typing`** for Python 3.9 compatibility

**Example**:

```python
from typing import List, Dict, Optional
from pathlib import Path

def process_documents(
    file_paths: List[Path],
    config: Dict[str, str]
) -> Optional[Dict[str, int]]:
    """Process documents and return statistics.

    Args:
        file_paths: List of paths to process
        config: Configuration dictionary

    Returns:
        Statistics dictionary, or None if processing fails
    """
    ...
```

---

## Testing

### pytest (Test Framework)

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=scripts --cov=server --cov-report=html

# Run specific test file
pytest tests/test_deduplicator.py

# Run tests matching pattern
pytest -k "test_entity"

# Run with verbose output
pytest -v

# Run only fast tests (skip slow integration tests)
pytest -m "not slow"
```

**Configuration**: `pyproject.toml` under `[tool.pytest.ini_options]`

### Writing Tests

#### Test File Structure

```
tests/
├── __init__.py
├── test_core/
│   ├── __init__.py
│   ├── test_deduplicator.py
│   ├── test_hasher.py
│   └── test_database.py
├── test_services/
│   ├── __init__.py
│   ├── test_entity_enrichment.py
│   └── test_suggestion_service.py
└── fixtures/
    ├── __init__.py
    └── sample_data.py
```

#### Test Example

```python
import pytest
from pathlib import Path
from scripts.core.hasher import DocumentHasher

class TestDocumentHasher:
    """Test suite for DocumentHasher"""

    @pytest.fixture
    def hasher(self):
        """Create hasher instance for tests"""
        return DocumentHasher()

    def test_hash_content_normalization(self, hasher):
        """Test that text normalization produces consistent hashes"""
        text1 = "This is a test"
        text2 = "This  is  a   test"  # Extra whitespace

        hash1 = hasher.hash_content(text1)
        hash2 = hasher.hash_content(text2)

        assert hash1 == hash2, "Normalized hashes should match"

    @pytest.mark.slow
    def test_hash_large_file(self, hasher, tmp_path):
        """Test hashing large file (integration test)"""
        # Create large temp file
        large_file = tmp_path / "large.txt"
        large_file.write_text("x" * 10_000_000)

        file_hash = hasher.hash_file(large_file)

        assert file_hash.startswith("sha256:")
        assert len(file_hash) == 71  # sha256: + 64 hex chars
```

### Test Markers

Use markers to categorize tests:

```python
@pytest.mark.unit
def test_simple_function():
    """Fast unit test"""
    pass

@pytest.mark.integration
def test_database_connection():
    """Integration test with external dependencies"""
    pass

@pytest.mark.slow
def test_large_dataset():
    """Slow test that processes large data"""
    pass
```

Run specific categories:

```bash
# Only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Integration tests only
pytest -m integration
```

---

## Pull Request Process

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code following style guidelines
- Add tests for new functionality
- Update documentation

### 3. Run Pre-Release Checks

```bash
# Auto-fix formatting
./scripts/pre_release.sh --fix

# Verify all checks pass
./scripts/pre_release.sh
```

### 4. Commit Changes

```bash
git add .
git commit -m "Add feature: brief description

Detailed description of changes:
- What was added/changed
- Why it was necessary
- Any breaking changes"
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with:
- Clear description of changes
- Link to related issues
- Screenshots/examples if applicable
- Checklist of completed tasks

---

## Code Review Criteria

Pull requests will be reviewed for:

### 1. **Code Quality** (Must Pass)
- ✅ All linting checks pass (`ruff`, `black`, `isort`)
- ✅ No type errors (`mypy`)
- ✅ Follows project style guidelines
- ✅ No hardcoded paths or credentials
- ✅ Proper error handling (no bare except)

### 2. **Testing** (Must Pass)
- ✅ New code has test coverage (≥80%)
- ✅ All tests pass
- ✅ Integration tests for API changes
- ✅ No flaky tests

### 3. **Documentation** (Must Pass)
- ✅ All public functions have docstrings
- ✅ Design decisions explained for complex logic
- ✅ README updated if API/usage changes
- ✅ CHANGELOG.md updated

### 4. **Performance** (Should Consider)
- ⚠️ No obvious performance regressions
- ⚠️ Algorithmic complexity documented
- ⚠️ Memory usage considerations
- ⚠️ Database query optimization

### 5. **Security** (Must Pass)
- ✅ No SQL injection risks
- ✅ Input validation on user inputs
- ✅ No hardcoded credentials
- ✅ Secure file handling (no path traversal)

---

## Development Workflow

### Daily Development

```bash
# 1. Pull latest changes
git pull origin main

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Make changes, run checks frequently
./scripts/pre_release.sh --fix

# 4. Commit and push
git add .
git commit -m "Description"
git push origin feature/my-feature
```

### Before Committing

```bash
# Auto-fix formatting
black scripts/ server/
isort scripts/ server/

# Check for issues
ruff check scripts/ server/
mypy scripts/ server/

# Run tests
pytest
```

### Before Creating PR

```bash
# Run full pre-release check
./scripts/pre_release.sh

# If all checks pass, create PR
# If checks fail, fix issues and re-run
```

---

## Common Development Tasks

### Add New Script

```bash
# 1. Create script in appropriate directory
touch scripts/analysis/new_analysis.py

# 2. Add shebang and docstring
cat > scripts/analysis/new_analysis.py << 'EOF'
#!/usr/bin/env python3
"""
Brief description of script purpose

Detailed description...
"""
EOF

# 3. Add to __init__.py if part of package
echo "from .new_analysis import main" >> scripts/analysis/__init__.py

# 4. Write tests
touch tests/test_analysis/test_new_analysis.py

# 5. Run pre-release checks
./scripts/pre_release.sh --fix
```

### Fix Linting Errors

```bash
# See what's wrong
ruff check scripts/your_file.py

# Auto-fix what's possible
ruff check --fix scripts/your_file.py

# Format code
black scripts/your_file.py
isort scripts/your_file.py

# Verify fixed
ruff check scripts/your_file.py
```

### Update Dependencies

```bash
# Update requirements.txt
pip install --upgrade package-name
pip freeze > requirements.txt

# Test that everything still works
pytest
./scripts/pre_release.sh
```

---

## Getting Help

- **Code Review Issues**: See [CODE_REVIEW_REPORT.md](CODE_REVIEW_REPORT.md)
- **Linting Errors**: Check [.ruff.toml](.ruff.toml) for rule explanations
- **Type Errors**: See [mypy documentation](https://mypy.readthedocs.io/)
- **Test Failures**: Run with `-v` flag for detailed output

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).
