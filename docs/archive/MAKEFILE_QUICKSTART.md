# Makefile Quick Start

**Quick Summary**: Historical documentation archived for reference purposes.

**Category**: Archive
**Status**: Historical
**Last Updated**: 2025-11-24

**Key Points**:
- Installation
- Common Commands
- Daily Development
- Version Management
- Code Quality

---

**One-page reference for the Epstein Document Archive Makefile**

## Installation

```bash
cd /Users/masa/Projects/Epstein
make install
```

## Common Commands

### Daily Development
| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make status` | Show project status summary |
| `make dev` | Start development server |
| `make clean` | Clean temporary files |

### Version Management
| Command | Description | Example |
|---------|-------------|---------|
| `make version` | Show current version | `0.1.0` |
| `make bump-patch` | Bug fixes | `0.1.0 → 0.1.1` |
| `make bump-minor` | New features | `0.1.0 → 0.2.0` |
| `make bump-major` | Breaking changes | `0.1.0 → 1.0.0` |
| `make tag-release` | Create git tag | `v0.1.0` |
| `make release` | Full release workflow | Bump + Tag |

### Code Quality
| Command | Description |
|---------|-------------|
| `make format` | Auto-format Python code |
| `make lint` | Run code linters |
| `make test` | Run test suite |

### Data Processing
| Command | Description |
|---------|-------------|
| `make ocr-status` | Check OCR progress |
| `make extract-emails` | Extract emails from OCR |
| `make classify-docs` | Classify all documents |
| `make build-network` | Rebuild entity network |

### Git Operations
| Command | Description |
|---------|-------------|
| `make commit` | Interactive commit helper |
| `make push` | Push to remote |

### Database
| Command | Description |
|---------|-------------|
| `make db-backup` | Backup databases |
| `make db-restore` | List backups |

### Logs
| Command | Description |
|---------|-------------|
| `make logs` | Tail OCR logs |
| `make logs-downloads` | Tail download logs |

## Typical Workflows

### Before Starting Work
```bash
make status          # Check project status
make install         # Update dependencies
```

### Before Committing
```bash
make format          # Format code
make lint            # Check code quality
make test            # Run tests
make commit          # Commit with helper
```

### Making a Release
```bash
# 1. Update changelog
# Edit CHANGELOG.md or use:
python3 scripts/update_changelog.py add Added "New feature"

# 2. Bump version
make bump-minor      # or bump-patch, bump-major

# 3. Review changes
git diff VERSION CHANGELOG.md

# 4. Tag and push
make tag-release
make push
git push --tags
```

### Data Processing Session
```bash
make ocr-status      # Check progress
make classify-docs   # Classify documents
make build-network   # Build network
make db-backup       # Backup results
```

## Direct Script Usage

### Version Management
```bash
# Bump version
python3 scripts/bump_version.py [patch|minor|major]

# Update changelog
python3 scripts/update_changelog.py release 0.2.0
python3 scripts/update_changelog.py add Added "Feature description"
python3 scripts/update_changelog.py validate

# Validate versions
python3 scripts/validate_version.py
```

### Git Helpers
```bash
# Interactive commit
python3 scripts/git_commit_helper.py

# Non-interactive commit
python3 scripts/git_commit_helper.py --type feat --message "Add feature"
```

## Environment Variables

```bash
# Override Python interpreter
PYTHON=/usr/local/bin/python3 make install

# Override project directory
PROJECT_DIR=/custom/path make status
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `make: command not found` | Install Xcode tools: `xcode-select --install` |
| Permission denied | Make scripts executable: `chmod +x scripts/*.py` |
| Virtual env issues | Recreate: `rm -rf .venv && make install` |
| Git tag exists | Delete: `git tag -d v0.1.0` then recreate |

## Color Output

The Makefile uses colored output:
- 🔵 **Blue**: Headers and informational messages
- 🟢 **Green**: Success messages and section titles
- 🟡 **Yellow**: Command names and processing messages
- 🔴 **Red**: Error messages

## Files Modified by Makefile

| Target | Files Modified |
|--------|----------------|
| `bump-*` | `VERSION`, `CHANGELOG.md` |
| `tag-release` | Git tags only |
| `install` | `.venv/` directory |
| `db-backup` | `data/backups/` directory |
| `clean` | Removes `__pycache__`, `*.pyc` |

## Configuration

Edit `.makerc` to customize behavior:
```bash
# Development server
DEV_PORT=8080

# OCR processing
OCR_WORKERS=16

# Database backups
BACKUP_RETENTION=60
```

## Complete Help Output

```bash
make help
```

Output:
```
═══════════════════════════════════════════════════════════════
  Epstein Document Archive - Makefile Commands
═══════════════════════════════════════════════════════════════

Version Management:
  make version        - Display current version (0.1.0)
  make bump-patch     - Increment patch version (X.Y.Z → X.Y.Z+1)
  make bump-minor     - Increment minor version (X.Y.Z → X.Y+1.0)
  make bump-major     - Increment major version (X.Y.Z → X+1.0.0)
  make tag-release    - Create git tag with current version

Development:
  make install        - Install Python dependencies
  make dev            - Start development server
  make test           - Run test suite
  make lint           - Run code linters
  make format         - Auto-format code
  make clean          - Clean temporary files

Data Processing:
  make ocr-status     - Check OCR processing status
  make extract-emails - Run email extraction pipeline
  make classify-docs  - Run document classification
  make build-network  - Rebuild entity network graph
  make status         - Show project status summary

Database:
  make db-backup      - Backup metadata databases
  make db-restore     - Restore from backup

Git Operations:
  make commit         - Stage and commit changes
  make push           - Push to remote repository
  make release        - Complete release workflow

Logs & Monitoring:
  make logs           - Tail OCR processing logs
  make logs-downloads - Tail download logs

═══════════════════════════════════════════════════════════════
```

## More Information

- Full documentation: `docs/MAKEFILE_GUIDE.md`
- Project guide: `CLAUDE.md`
- Project README: `README.md`

---

**Quick Start**: `make help` | **Status**: `make status` | **Full Docs**: `docs/MAKEFILE_GUIDE.md`
