# Release Process Documentation

**Last Updated**: 2025-11-17

---

## Overview

This document describes the automated release process for the Epstein Document Archive, including roadmap linting, semantic versioning, and pre-release quality gates.

---

## Table of Contents

- [Pre-Release Quality Gate](#pre-release-quality-gate)
- [Roadmap Linting](#roadmap-linting)
- [Semantic Versioning](#semantic-versioning)
- [CHANGELOG Updates](#changelog-updates)
- [Release Workflow](#release-workflow)
- [Troubleshooting](#troubleshooting)

---

## Pre-Release Quality Gate

The `scripts/pre_release.sh` script runs a comprehensive suite of checks before any release:

### Running the Script

```bash
# Run all checks (includes tests)
./scripts/pre_release.sh

# Run with auto-fix enabled
./scripts/pre_release.sh --fix

# Run in fast mode (skip tests)
./scripts/pre_release.sh --fast

# Get help
./scripts/pre_release.sh --help
```

### Checks Performed

1. **Tool Verification**
   - Ensures all required linting tools are installed
   - Checks: ruff, black, isort, mypy, pytest

2. **Ruff Linting**
   - Code quality checks
   - 100+ linting rules
   - Auto-fix available with `--fix`

3. **Black Formatting**
   - Code formatting consistency
   - Line length: 100 characters
   - Auto-format available with `--fix`

4. **isort Import Sorting**
   - Import statement organization
   - Consistent ordering across codebase
   - Auto-sort available with `--fix`

5. **mypy Type Checking**
   - Static type analysis
   - Non-blocking (warnings only)
   - Gradual adoption approach

6. **pytest Test Suite**
   - Unit and integration tests
   - Coverage threshold: 80%
   - Skipped in `--fast` mode

7. **Roadmap Validation** (NEW)
   - Structure validation
   - Required sections check
   - Link integrity verification
   - Date format validation

8. **Version Bump Analysis** (NEW)
   - Analyzes changes in ROADMAP.md
   - Suggests semantic version bump
   - Non-blocking (informational)

9. **CHANGELOG Check** (NEW)
   - Identifies completed items
   - Reminds to update CHANGELOG.md
   - Non-blocking (informational)

### Exit Codes

- `0` - All checks passed, ready for release
- `1` - Linting failures (ruff, black, isort, roadmap)
- `2` - Type checking failures (mypy)
- `3` - Test failures (pytest)
- `4` - Coverage below threshold

---

## Roadmap Linting

The roadmap linting system ensures ROADMAP.md maintains proper structure and quality.

### Required Sections

The following sections must be present in ROADMAP.md:

1. **Completed Recently**
   - Recently finished features
   - Moved from "Current Sprint" when done
   - Used for version bump analysis

2. **Current Sprint**
   - Active development work
   - Features currently in progress
   - Updated regularly during sprints

3. **Next Up**
   - Prioritized backlog
   - Planned features with targets
   - Organized by priority (High/Medium/Low)

4. **Future Enhancements**
   - Long-term feature ideas
   - Lower priority improvements
   - Exploratory concepts

### Validation Rules

#### 1. File Existence and Size
```bash
# ROADMAP.md must exist
if [ ! -f "ROADMAP.md" ]; then
    ERROR: "ROADMAP.md not found"
fi

# ROADMAP.md must be non-empty
if [ ! -s "ROADMAP.md" ]; then
    ERROR: "ROADMAP.md is empty"
fi
```

#### 2. Section Structure
All required sections must be present as H2 headers (`## Section Name`):
- `## Completed Recently`
- `## Current Sprint`
- `## Next Up`
- `## Future Enhancements`

#### 3. TODO/FIXME Comments
Warns if TODO or FIXME comments are found:
```bash
# Check for unfinished work
grep -n "TODO\|FIXME" ROADMAP.md
```

#### 4. Date Format Validation
"Last Updated" field must use YYYY-MM-DD format:
```bash
# Valid: **Last Updated**: 2025-11-17
# Invalid: **Last Updated**: Nov 17, 2025
```

#### 5. Internal Link Integrity
Validates all markdown internal links:
```markdown
# Valid links (must have corresponding header)
[Overview](#overview)               → ## Overview
[Current Sprint](#current-sprint)  → ## Current Sprint

# Invalid links (will generate warning)
[Missing Section](#nonexistent)    → WARNING: broken link
```

### Roadmap Update Workflow

When completing a feature:

1. **Move to "Completed Recently"**
   ```markdown
   ## Completed Recently

   ### Feature Name ✅
   - Brief description
   - Key accomplishments
   - Version number (if applicable)
   ```

2. **Remove from "Current Sprint"**
   - Delete or move the feature from active development

3. **Update "Last Updated" Date**
   ```markdown
   **Last Updated**: 2025-11-17
   ```

4. **Run Validation**
   ```bash
   ./scripts/pre_release.sh --fast
   ```

---

## Semantic Versioning

The project follows [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH (e.g., 1.2.3)
```

### Version Components

- **MAJOR** (X.0.0): Breaking changes, incompatible API changes
- **MINOR** (0.X.0): New features, backwards-compatible additions
- **PATCH** (0.0.X): Bug fixes, small improvements

### Automated Version Analysis

The pre-release script analyzes ROADMAP.md to suggest version bumps:

#### Detection Keywords

**Breaking Changes** (MAJOR bump):
- "breaking change"
- "incompatible"
- "removed"
- "deprecated"

**New Features** (MINOR bump):
- "new feature"
- "added"
- "implemented"

**Bug Fixes** (PATCH bump):
- "fixed"
- "bug fix"
- "patched"
- "corrected"

#### Suggestion Logic

```bash
if BREAKING_COUNT > 0; then
    SUGGEST: MAJOR bump (X+1.0.0)
elif FEATURE_COUNT > 5; then
    SUGGEST: MINOR bump (0.X+1.0)
elif BUGFIX_COUNT > 0 or FEATURE_COUNT > 0; then
    SUGGEST: PATCH bump (0.0.X+1)
else
    SUGGEST: No version bump needed
fi
```

#### Example Output

```
Current version: 1.0.0

Change Analysis:
  - Breaking changes: 0
  - New features: 7
  - Bug fixes: 2

Suggested version: 1.1.0 (MINOR bump - new features detected)

To update version, run:
  sed -i '' 's/version = "1.0.0"/version = "1.1.0"/' pyproject.toml
```

### Manual Version Update

If you agree with the suggestion:

```bash
# Update pyproject.toml
sed -i '' 's/version = "1.0.0"/version = "1.1.0"/' pyproject.toml

# Verify change
grep 'version = ' pyproject.toml
```

---

## CHANGELOG Updates

The CHANGELOG.md file tracks all notable changes following [Keep a Changelog](https://keepachangelog.com/) format.

### Automated Analysis

The pre-release script:
1. Counts completed items in ROADMAP.md
2. Suggests updating CHANGELOG.md
3. Provides manual update reminder

### Manual CHANGELOG Update Process

1. **Extract Completed Items from ROADMAP.md**
   ```markdown
   ## Completed Recently

   ### Document Deduplication System ✅
   - Content-based deduplication
   - 38,177 unique documents identified
   ```

2. **Add to CHANGELOG.md under [Unreleased]**
   ```markdown
   ## [Unreleased]

   ### Added
   - Document deduplication system with quality scoring
   - Content-based hash comparison for duplicates
   ```

3. **Before Release, Update Version Section**
   ```markdown
   ## [1.1.0] - 2025-11-17

   ### Added
   - Document deduplication system with quality scoring
   - Email classification (305 emails extracted)
   - Entity normalization (296 entities)

   ### Changed
   - Improved timeline page with 92 events
   - Enhanced network visualization

   ### Fixed
   - Login page session handling
   - Icon system integration issues
   ```

---

## Release Workflow

Complete step-by-step release process:

### 1. Complete Feature Development

```bash
# Develop feature
git checkout -b feature/new-feature
# ... make changes ...
git commit -m "Add new feature"
git push origin feature/new-feature
```

### 2. Update ROADMAP.md

```markdown
## Completed Recently

### New Feature Name ✅
- Feature description
- Key accomplishments
- Version: v1.1.0

## Current Sprint
(Remove completed feature from here)
```

### 3. Run Pre-Release Checks

```bash
# Run with auto-fix
./scripts/pre_release.sh --fix

# Review version suggestion
# Example output:
#   Suggested version: 1.1.0 (MINOR bump)
```

### 4. Update Version

```bash
# Update pyproject.toml
sed -i '' 's/version = "1.0.0"/version = "1.1.0"/' pyproject.toml
```

### 5. Update CHANGELOG.md

```markdown
## [1.1.0] - 2025-11-17

### Added
- New feature name and description
- Another feature

### Changed
- Improvements to existing features

### Fixed
- Bug fixes
```

### 6. Final Validation

```bash
# Run full checks (including tests)
./scripts/pre_release.sh

# Should see:
# ✓ All checks passed!
# ┌─────────────────────────────────────┐
# │  READY FOR RELEASE                  │
# └─────────────────────────────────────┘
```

### 7. Create Release Commit

```bash
git add ROADMAP.md pyproject.toml CHANGELOG.md
git commit -m "Release v1.1.0

- Updated roadmap with completed features
- Bumped version to 1.1.0
- Updated CHANGELOG.md

Release notes: See CHANGELOG.md for details."
```

### 8. Tag Release

```bash
# Create annotated tag
git tag -a v1.1.0 -m "Release v1.1.0

New features:
- Feature 1
- Feature 2

See CHANGELOG.md for full details."

# Push tag
git push origin v1.1.0
```

### 9. Create GitHub Release (when repository is public)

```bash
# Using GitHub CLI
gh release create v1.1.0 \
  --title "Release v1.1.0" \
  --notes-file CHANGELOG.md
```

---

## Troubleshooting

### Common Issues

#### 1. Roadmap Validation Fails

**Error**: Missing required sections

```bash
ERROR: Missing required sections: Current Sprint
```

**Solution**: Add missing H2 section to ROADMAP.md:
```markdown
## Current Sprint

### Active Development 🔄
(Content here)
```

---

#### 2. Broken Internal Links

**Warning**: Potentially broken link

```bash
WARNING: Potentially broken link: [Overview](#overview)
```

**Solution**: Ensure corresponding header exists:
```markdown
[Overview](#overview)    # Link
## Overview              # Corresponding header (must exist)
```

---

#### 3. TODO/FIXME Comments

**Warning**: Found TODO/FIXME comments

```bash
WARNING: Found 3 TODO/FIXME comment(s) in roadmap
```

**Solution**: Either:
- Complete the TODO items
- Remove TODO comments
- Move to issues/backlog

---

#### 4. Linting Failures

**Error**: Ruff/Black/isort failures

```bash
ERROR: Failed checks: ruff black isort
```

**Solution**: Run with auto-fix:
```bash
./scripts/pre_release.sh --fix
```

---

#### 5. Version Suggestion Incorrect

**Issue**: Script suggests wrong version bump

**Solution**: Manually specify version:
```bash
# Ignore suggestion, update manually
sed -i '' 's/version = "1.0.0"/version = "2.0.0"/' pyproject.toml

# Reason: Script bases suggestion on keywords in ROADMAP.md
# You have final judgment on versioning
```

---

#### 6. Test Failures

**Error**: Tests failed or coverage below 80%

```bash
ERROR: Tests failed or coverage below 80%
```

**Solution**:
```bash
# Run tests directly to see details
pytest --cov=scripts --cov=server --cov-report=term-missing

# Fix failing tests
# Add tests to improve coverage
```

---

## Best Practices

### 1. Regular Roadmap Updates

- Update ROADMAP.md after completing each feature
- Move items from "Current Sprint" to "Completed Recently"
- Keep "Next Up" prioritized and current

### 2. Meaningful Commit Messages

```bash
# Good
git commit -m "Add email classification system

- Extracted 305 emails from OCR results
- Pattern-based detection with confidence scoring
- Organized in /data/md/.../emails/

Closes #123"

# Bad
git commit -m "updates"
```

### 3. Version Bump Timing

- Bump version BEFORE creating release commit
- Include version in commit message
- Tag commit with same version number

### 4. CHANGELOG Maintenance

- Update CHANGELOG.md with every notable change
- Use [Keep a Changelog](https://keepachangelog.com/) format
- Include migration notes for breaking changes

### 5. Pre-Release Checks

Always run before:
- Creating pull requests
- Merging to main branch
- Tagging releases

---

## Continuous Improvement

### Future Enhancements

1. **Automated CHANGELOG Updates**
   - Auto-extract from ROADMAP.md
   - Generate CHANGELOG entries
   - Reduce manual work

2. **Git Hook Integration**
   - Run pre-release checks on commit
   - Prevent commits with linting errors
   - Auto-format on commit

3. **Release Automation**
   - GitHub Actions workflow
   - Automated version bumping
   - Automatic tag creation

4. **Enhanced Version Analysis**
   - Parse git commits for conventional commits
   - More sophisticated change detection
   - Breaking change detection from code

---

## References

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)

---

**Maintained By**: Epstein Archive Development Team
**Last Updated**: 2025-11-17
**Next Review**: 2025-12-01
