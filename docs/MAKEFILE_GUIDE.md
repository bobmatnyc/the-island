# Makefile Guide - Epstein Document Archive

Comprehensive guide to using the project Makefile for development, deployment, and version management.

## Table of Contents

- [Quick Start](#quick-start)
- [Version Management](#version-management)
- [Development Workflow](#development-workflow)
- [Data Processing](#data-processing)
- [Git Operations](#git-operations)
- [Database Management](#database-management)
- [Advanced Usage](#advanced-usage)

---

## Quick Start

### Display All Commands
```bash
make help
```

### Check Project Status
```bash
make status
```

### Install Dependencies
```bash
make install
```

---

## Version Management

The project follows **Semantic Versioning** (MAJOR.MINOR.PATCH).

### Display Current Version
```bash
make version
```
Output: `Current version: 0.1.0`

### Bump Patch Version
Use for backwards-compatible bug fixes:
```bash
make bump-patch
# 0.1.0 → 0.1.1
```

### Bump Minor Version
Use for new backwards-compatible features:
```bash
make bump-minor
# 0.1.0 → 0.2.0
```

### Bump Major Version
Use for breaking changes:
```bash
make bump-major
# 0.1.0 → 1.0.0
```

### What Happens During Version Bump
1. **VERSION file** is updated with new version
2. **CHANGELOG.md** is updated:
   - `[Unreleased]` section is moved to new version
   - New empty `[Unreleased]` section is created
   - Current date is added to version header
3. Changes are ready to commit

### Tag a Release
```bash
make tag-release
```
Creates a git tag: `v0.1.0`

To push tags:
```bash
git push origin v0.1.0
```

### Complete Release Workflow
```bash
make release
```
This will:
1. Bump minor version
2. Update CHANGELOG.md
3. Create git tag
4. Prompt to review and push

---

## Development Workflow

### Install Dependencies
```bash
make install
```
- Creates virtual environment (if needed)
- Upgrades pip
- Installs requirements.txt

### Start Development Server
```bash
make dev
```
Starts FastAPI server with auto-reload on port 8000.

### Run Tests
```bash
make test
```
Runs pytest test suite (when tests exist).

### Lint Code
```bash
make lint
```
Runs:
- `ruff` for linting
- `black` for format checking

### Auto-Format Code
```bash
make format
```
Formats all Python code in `scripts/` with black.

### Clean Temporary Files
```bash
make clean
```
Removes:
- `__pycache__` directories
- `.pyc` and `.pyo` files
- Large log files (>100MB)

---

## Data Processing

### Check OCR Status
```bash
make ocr-status
```
Shows:
- Processing progress (X / Y files)
- Current processing rate
- Estimated time remaining
- Output directory

### Extract Emails
```bash
make extract-emails
```
Runs email extraction pipeline on OCR results.

### Classify Documents
```bash
make classify-docs
```
Runs document classification on all PDFs:
- 11 category classification
- Confidence scoring
- Updates semantic index

### Build Entity Network
```bash
make build-network
```
Rebuilds entity relationship network from flight logs.

---

## Git Operations

### Interactive Commit
```bash
make commit
```
Interactive prompts for:
- Commit type (feat, fix, docs, etc.)
- Scope (optional)
- Commit message
- Auto-stages and commits with conventional commits format

Example commit message:
```
feat(ocr): add parallel processing for house oversight docs

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Push to Remote
```bash
make push
```
Pushes current branch to remote.

### Complete Release
```bash
make release
```
Full release workflow:
1. Bumps minor version
2. Updates CHANGELOG.md
3. Creates git tag
4. Prompts for review and push

---

## Database Management

### Backup Databases
```bash
make db-backup
```
Creates timestamped backups:
- `data/backups/deduplication_YYYYMMDD_HHMMSS.db`
- `data/backups/metadata_YYYYMMDD_HHMMSS.tar.gz`

### Restore from Backup
```bash
make db-restore
```
Lists available backups for manual restoration.

To restore manually:
```bash
cp data/backups/deduplication_20241116_230000.db data/canonical/deduplication.db
tar -xzf data/backups/metadata_20241116_230000.tar.gz -C data/
```

---

## Logs & Monitoring

### Tail OCR Logs
```bash
make logs
```
Real-time streaming of OCR processing logs.

### Tail Download Logs
```bash
make logs-downloads
```
Real-time streaming of download logs.

---

## Advanced Usage

### Using Scripts Directly

#### Bump Version Script
```bash
python3 scripts/bump_version.py patch
python3 scripts/bump_version.py minor
python3 scripts/bump_version.py major
```

#### Update Changelog
```bash
# Release a version
python3 scripts/update_changelog.py release 0.2.0

# Add entry to [Unreleased]
python3 scripts/update_changelog.py add Added "New feature description"
python3 scripts/update_changelog.py add Fixed "Bug fix description"

# Validate changelog format
python3 scripts/update_changelog.py validate
```

#### Git Commit Helper
```bash
# Interactive mode
python3 scripts/git_commit_helper.py

# Non-interactive mode
python3 scripts/git_commit_helper.py \
  --type feat \
  --scope ocr \
  --message "Add parallel processing"
```

---

## Workflow Examples

### Starting Development Session
```bash
# Check status
make status

# Install/update dependencies
make install

# Start dev server
make dev
```

### Before Committing Changes
```bash
# Format code
make format

# Lint code
make lint

# Test changes
make test

# Commit changes
make commit
```

### Releasing New Version
```bash
# 1. Complete all development work
make test

# 2. Update CHANGELOG.md manually or via script
python3 scripts/update_changelog.py add Added "New OCR pipeline"

# 3. Bump version (patch/minor/major)
make bump-minor

# 4. Review changes
git diff VERSION CHANGELOG.md

# 5. Commit version bump
git add VERSION CHANGELOG.md
git commit -m "chore: bump version to $(cat VERSION)"

# 6. Tag release
make tag-release

# 7. Push everything
git push && git push --tags
```

### Database Maintenance
```bash
# Create backup before major operations
make db-backup

# Run data processing
make classify-docs
make build-network

# If something goes wrong, restore
make db-restore
```

---

## Troubleshooting

### Make Command Not Found
```bash
# Install make on macOS
xcode-select --install

# Or use Homebrew
brew install make
```

### Python Virtual Environment Issues
```bash
# Remove and recreate venv
rm -rf .venv
make install
```

### Permission Denied on Scripts
```bash
# Make scripts executable
chmod +x scripts/*.py
chmod +x scripts/*/*.py
```

### Git Tag Already Exists
```bash
# Delete local tag
git tag -d v0.1.0

# Delete remote tag
git push origin :refs/tags/v0.1.0

# Recreate tag
make tag-release
```

---

## Configuration

### Customizing Makefile

Edit `/Users/masa/Projects/Epstein/Makefile`:

```makefile
# Change Python interpreter
PYTHON := /usr/local/bin/python3

# Change development server port
dev:
    $(PYTHON) -m uvicorn api.main:app --reload --port 8080

# Add custom targets
my-custom-task:
    @echo "Running custom task"
    @$(PYTHON) scripts/my_script.py
```

---

## Environment Variables

The Makefile uses these variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT_DIR` | `/Users/masa/Projects/Epstein` | Project root |
| `PYTHON` | `.venv/bin/python3` | Python interpreter |
| `PIP` | `.venv/bin/pip` | Pip package manager |
| `LOGS_DIR` | `logs/` | Log file directory |
| `DATA_DIR` | `data/` | Data directory |

Override in shell:
```bash
PROJECT_DIR=/custom/path make status
```

---

## Best Practices

### 1. Version Bumping
- **Patch**: Bug fixes, documentation updates
- **Minor**: New features, backwards-compatible changes
- **Major**: Breaking changes, API changes

### 2. Changelog Maintenance
- Update `[Unreleased]` section as you work
- Use clear, descriptive entries
- Group by category (Added, Changed, Fixed, Removed)

### 3. Git Workflow
- Commit frequently with descriptive messages
- Use conventional commit format
- Tag releases consistently

### 4. Database Backups
- Backup before major data processing
- Keep at least 3 recent backups
- Test restore process periodically

### 5. Code Quality
- Format before committing (`make format`)
- Lint regularly (`make lint`)
- Run tests before pushing (`make test`)

---

## Quick Reference

```bash
# Daily Development
make status              # Check project status
make install             # Update dependencies
make dev                 # Start dev server

# Before Committing
make format              # Format code
make lint                # Check code
make test                # Run tests
make commit              # Commit changes

# Releasing
make bump-patch          # Bump version
make tag-release         # Tag release
make push                # Push to remote

# Data Processing
make ocr-status          # Check OCR
make classify-docs       # Classify documents
make build-network       # Build entity network

# Maintenance
make clean               # Clean temp files
make db-backup           # Backup databases
make logs                # View logs
```

---

## Support

For issues or questions:
1. Check this guide
2. Run `make help` for command list
3. Review script help: `python3 scripts/bump_version.py`
4. See project documentation: `README.md`, `CLAUDE.md`
