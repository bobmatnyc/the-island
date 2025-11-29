# Security Scanning Guide

**Quick Summary**: This guide provides detailed information on the automated security scanning infrastructure for the Epstein Project.  All developers should familiarize themselves with these processes.

**Category**: Documentation
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Scans Python dependencies (`server/`, `scripts/ingestion/`)
- Scans Node.js dependencies (`frontend/`)
- Scans GitHub Actions workflows
- Creates PRs for security updates automatically
- Groups related updates to reduce noise

---

## Overview

This guide provides detailed information on the automated security scanning infrastructure for the Epstein Project. All developers should familiarize themselves with these processes.

## Quick Start

### Before Every Commit

```bash
# Python security scan (backend)
cd server
pip install pip-audit
pip-audit --requirement requirements.txt

# Node.js security scan (frontend)
cd frontend
npm audit
```

### Handling Security Alerts

1. Review Dependabot PRs in GitHub
2. Check CI/CD security scan results
3. Merge security updates promptly
4. Run local tests after updates

## Automated Scanning Infrastructure

### 1. Dependabot (Weekly Scans)

**Configuration**: `.github/dependabot.yml`

**What it does**:
- Scans Python dependencies (`server/`, `scripts/ingestion/`)
- Scans Node.js dependencies (`frontend/`)
- Scans GitHub Actions workflows
- Creates PRs for security updates automatically
- Groups related updates to reduce noise

**Schedule**:
- **Python**: Every Monday at 09:00 UTC
- **Node.js**: Every Monday at 10:00 UTC
- **GitHub Actions**: Every Monday at 11:00 UTC

**PR Labels**:
- `dependencies`: All dependency updates
- `security`: Security-related updates
- `python`, `javascript`: Language-specific
- `frontend`, `scripts`: Component-specific

### 2. GitHub Actions Security Workflow

**Configuration**: `.github/workflows/security-scan.yml`

**What it does**:
- Runs `pip-audit` for Python dependencies
- Runs `npm audit` for Node.js dependencies
- Fails build on HIGH/CRITICAL vulnerabilities
- Generates JSON security reports (retained 30 days)
- Posts summary to GitHub Actions UI

**Triggers**:
- Pull requests to `main` or `develop`
- Pushes to `main` branch
- Weekly schedule (Monday 2am UTC)
- Manual workflow dispatch

**Artifacts**:
- `python-security-report-server`: Backend scan results
- `python-security-report-scripts-ingestion`: Scripts scan results
- `nodejs-security-report`: Frontend scan results

## Local Security Scanning

### Python Dependencies

#### Using pip-audit (Recommended)

```bash
# Install pip-audit
pip install pip-audit

# Basic scan
pip-audit --requirement requirements.txt

# Detailed scan with descriptions
pip-audit --requirement requirements.txt --desc

# JSON output for parsing
pip-audit --requirement requirements.txt --format json

# Strict mode (fail on any vulnerability)
pip-audit --requirement requirements.txt --strict

# Fix vulnerabilities (where possible)
pip-audit --requirement requirements.txt --fix
```

#### Using safety (Alternative)

```bash
# Install safety
pip install safety

# Scan requirements.txt
safety check --file requirements.txt

# JSON output
safety check --file requirements.txt --json

# Ignore specific vulnerabilities
safety check --file requirements.txt --ignore 12345
```

### Node.js Dependencies

#### Using npm audit

```bash
cd frontend

# Basic audit
npm audit

# JSON output
npm audit --json

# Only show high/critical
npm audit --audit-level=high

# Automatically fix vulnerabilities
npm audit fix

# Fix including breaking changes (CAUTION)
npm audit fix --force

# Dry run (preview fixes)
npm audit fix --dry-run
```

#### Understanding npm audit output

```
┌───────────────┬──────────────────────────────────────────────────────────────┐
│ High          │ Prototype Pollution                                          │
├───────────────┼──────────────────────────────────────────────────────────────┤
│ Package       │ lodash                                                       │
├───────────────┼──────────────────────────────────────────────────────────────┤
│ Patched in    │ >=4.17.19                                                    │
├───────────────┼──────────────────────────────────────────────────────────────┤
│ Dependency of │ react-scripts                                                │
├───────────────┼──────────────────────────────────────────────────────────────┤
│ Path          │ react-scripts > webpack > lodash                             │
├───────────────┼──────────────────────────────────────────────────────────────┤
│ More info     │ https://npmjs.com/advisories/1523                            │
└───────────────┴──────────────────────────────────────────────────────────────┘
```

**Key fields**:
- **Severity**: Critical/High/Medium/Low
- **Package**: Vulnerable dependency name
- **Patched in**: Version that fixes the issue
- **Dependency of**: What requires this package
- **Path**: Full dependency chain

## Handling Dependabot PRs

### Standard Workflow

1. **Review PR Description**:
   - Check severity level
   - Read changelog/release notes
   - Note breaking changes

2. **Check CI/CD Status**:
   - Ensure security scan passes
   - Verify all tests pass
   - Review any new warnings

3. **Assess Impact**:
   - **Patch updates** (1.2.3 → 1.2.4): Usually safe
   - **Minor updates** (1.2.3 → 1.3.0): Review carefully
   - **Major updates** (1.2.3 → 2.0.0): Test thoroughly

4. **Merge Decision**:
   - **Security updates**: Merge immediately if tests pass
   - **Minor/patch**: Merge in next batch
   - **Major**: Schedule for dedicated testing

### Testing Dependabot PRs Locally

```bash
# Fetch PR branch
git fetch origin pull/123/head:dependabot-pr-123
git checkout dependabot-pr-123

# For Python updates
cd server
pip install -r requirements.txt
# Run tests
pytest

# For Node.js updates
cd frontend
npm install
npm run build
npm test
```

### Dependabot Commands

Comment on PRs to control Dependabot:

```bash
@dependabot rebase          # Rebase on latest base branch
@dependabot recreate        # Recreate PR from scratch
@dependabot merge           # Auto-merge after approval
@dependabot squash and merge # Squash commits before merge
@dependabot close           # Close without merging
@dependabot ignore this dependency # Stop updates for this package
@dependabot ignore this major version # Ignore major version updates
@dependabot ignore this minor version # Ignore minor version updates
```

## CI/CD Integration Details

### Security Scan Workflow Steps

1. **Checkout**: Pulls latest code
2. **Setup**: Installs Python 3.11 or Node.js 20
3. **Install Tools**: Installs `pip-audit` or uses `npm audit`
4. **Scan**: Runs vulnerability scan
5. **Report**: Generates JSON report
6. **Check**: Fails if HIGH/CRITICAL found
7. **Upload**: Saves report as artifact

### Accessing Scan Reports

```bash
# Via GitHub CLI
gh run list --workflow=security-scan.yml
gh run view <run-id>
gh run download <run-id>

# Via web UI
# Navigate to Actions → Security Scan → Latest run → Artifacts
```

### Manual Workflow Trigger

```bash
# Via GitHub CLI
gh workflow run security-scan.yml

# Via web UI
# Navigate to Actions → Security Scan → Run workflow
```

## Troubleshooting

### Common Issues

#### 1. "No matching distribution found"

**Problem**: `pip-audit` can't find package in PyPI

**Solution**:
```bash
# Check if package exists
pip search package-name

# Update pip and retry
pip install --upgrade pip
pip-audit --requirement requirements.txt
```

#### 2. "Cannot fix all vulnerabilities"

**Problem**: `npm audit fix` cannot resolve all issues

**Cause**: Dependencies locked by parent packages

**Solution**:
```bash
# Check dependency tree
npm ls vulnerable-package

# Force update (may break things)
npm audit fix --force

# Or manually update parent package
npm install parent-package@latest
```

#### 3. "Dependency has no available fixes"

**Problem**: Vulnerability exists but no patch available

**Solutions**:
1. **Find alternative package**: Research replacements
2. **Wait for fix**: Monitor package repository
3. **Fork and patch**: Create custom fix (last resort)
4. **Accept risk**: Document in SECURITY.md exceptions

#### 4. "Build fails due to transitive dependencies"

**Problem**: Indirect dependency has vulnerability

**Solution**:
```bash
# Python: Override transitive dependency
# Add to requirements.txt:
vulnerable-package>=1.2.3  # Forces minimum version

# Node.js: Use resolutions in package.json
{
  "resolutions": {
    "vulnerable-package": ">=1.2.3"
  }
}
```

## Best Practices

### Development Workflow

1. **Start of sprint**:
   - Review and merge pending security PRs
   - Run full security scan locally
   - Update dependencies

2. **Adding new dependencies**:
   ```bash
   # Python: Check before adding
   pip install new-package
   pip-audit

   # Node.js: Check after adding
   npm install new-package
   npm audit
   ```

3. **Before creating PR**:
   - Run security scan locally
   - Ensure no new vulnerabilities
   - Document any accepted risks

4. **After merge**:
   - Monitor CI/CD security scan results
   - Address any new findings immediately

### Maintenance Schedule

- **Daily**: Review Dependabot PR notifications
- **Weekly**: Merge non-breaking security updates
- **Monthly**: Review security exceptions and risks
- **Quarterly**: Full dependency audit and cleanup

## Security Severity Response Times

| Severity | Response SLA | Example Actions |
|----------|-------------|-----------------|
| **CRITICAL** | 24 hours | Immediate hotfix, emergency deploy |
| **HIGH** | 7 days | Priority PR, scheduled deploy |
| **MEDIUM** | 30 days | Regular update cycle |
| **LOW** | 90 days | Opportunistic updates |

## Additional Resources

### Tools

- **pip-audit**: [GitHub Repository](https://github.com/pypa/pip-audit)
- **safety**: [Safety DB](https://pyup.io/safety/)
- **npm audit**: [npm Docs](https://docs.npmjs.com/cli/v8/commands/npm-audit)
- **Dependabot**: [GitHub Docs](https://docs.github.com/en/code-security/dependabot)

### Vulnerability Databases

- **Python**: [PyPI Advisory Database](https://github.com/pypa/advisory-database)
- **Node.js**: [npm Security Advisories](https://www.npmjs.com/advisories)
- **OSV**: [Open Source Vulnerabilities](https://osv.dev/)
- **CVE**: [National Vulnerability Database](https://nvd.nist.gov/)

### Learning Resources

- [OWASP Dependency Check](https://owasp.org/www-project-dependency-check/)
- [Snyk Security 101](https://snyk.io/learn/)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security/getting-started/securing-your-repository)

## Support

For questions or issues with security scanning:

1. Check this documentation
2. Review SECURITY.md policy
3. Search GitHub Issues
4. Contact project maintainers

---

**Last Updated**: 2025-11-24
**Maintained By**: Epstein Project Team
