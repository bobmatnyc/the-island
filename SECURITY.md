# Security Policy

## Overview

The Epstein Project maintains automated security scanning for all dependencies to identify and remediate vulnerabilities promptly. This document outlines our security practices, vulnerability reporting process, and update workflow.

## Automated Security Scanning

### Dependabot Configuration

We use GitHub Dependabot for automated dependency vulnerability scanning:

- **Scan Frequency**: Weekly (every Monday)
- **Scope**:
  - Python dependencies (`server/requirements.txt`, `scripts/ingestion/requirements.txt`)
  - Node.js dependencies (`frontend/package.json`)
  - GitHub Actions workflows
- **Auto-PR Creation**: Enabled for security updates
- **Severity Prioritization**: Security updates are grouped and prioritized

### CI/CD Security Checks

Our GitHub Actions workflow (`security-scan.yml`) performs continuous security monitoring:

- **Triggers**:
  - Pull requests to `main` or `develop` branches
  - Pushes to `main` branch
  - Weekly scheduled scan (Monday 2am UTC)
  - Manual workflow dispatch

- **Tools**:
  - **Python**: `pip-audit` (OSV vulnerability database)
  - **Node.js**: `npm audit` (npm advisory database)

- **Failure Criteria**:
  - Build fails on **HIGH** or **CRITICAL** severity vulnerabilities
  - Security reports uploaded as workflow artifacts (retained 30 days)

## Vulnerability Severity Classification

We follow industry-standard CVSS (Common Vulnerability Scoring System) severity ratings:

| Severity | CVSS Score | Response Time | Action Required |
|----------|------------|---------------|-----------------|
| **CRITICAL** | 9.0 - 10.0 | 24 hours | Immediate patch/update |
| **HIGH** | 7.0 - 8.9 | 7 days | Priority update |
| **MEDIUM** | 4.0 - 6.9 | 30 days | Scheduled update |
| **LOW** | 0.1 - 3.9 | 90 days | Opportunistic update |

## Handling Dependabot Pull Requests

### Reviewing Security PRs

1. **Automatic Review** (Security updates):
   - Review Dependabot PR description and changelog
   - Check CI/CD pipeline status (must pass all tests)
   - Verify no breaking changes in upgrade
   - Merge if tests pass and changes are non-breaking

2. **Manual Testing** (Major version updates):
   - Pull PR branch locally
   - Run full test suite
   - Test critical application paths
   - Review breaking changes documentation
   - Merge after thorough validation

### Merge Priority

1. **CRITICAL/HIGH security patches**: Merge within SLA (24h/7d)
2. **Grouped security updates**: Review and merge weekly
3. **Minor/patch updates**: Review during sprint planning
4. **Major version updates**: Allocate dedicated development time

### Commands for Dependabot PRs

You can interact with Dependabot using PR comments:

```bash
@dependabot rebase          # Rebase PR on latest base branch
@dependabot recreate        # Recreate PR (discard local changes)
@dependabot merge           # Merge PR (after approval)
@dependabot squash and merge # Squash commits and merge
@dependabot cancel merge    # Cancel scheduled merge
@dependabot close           # Close PR without merging
@dependabot ignore this dependency # Stop updates for this dependency
@dependabot ignore this major version # Ignore this major version
```

## Local Security Scanning

### Python (Backend/Scripts)

Run security scan before committing code:

```bash
# Install pip-audit
pip install pip-audit

# Scan server dependencies
cd server
pip-audit --requirement requirements.txt --desc

# Scan ingestion scripts dependencies
cd scripts/ingestion
pip-audit --requirement requirements.txt --desc

# Alternative: Use safety (another popular tool)
pip install safety
safety check --file requirements.txt
```

### Node.js (Frontend)

Run security scan before committing code:

```bash
cd frontend

# Run npm audit
npm audit

# Fix automatically fixable vulnerabilities
npm audit fix

# Fix including breaking changes (use with caution)
npm audit fix --force

# Generate detailed JSON report
npm audit --json > security-report.json
```

## Update Workflow Best Practices

### For Developers

1. **Before starting work**:
   - Pull latest changes from `main`
   - Review and merge any pending security PRs
   - Run local security scan

2. **During development**:
   - Avoid adding dependencies with known vulnerabilities
   - Check vulnerability status before adding new packages:
     - Python: `pip-audit` or safety check
     - Node.js: `npm audit` after install

3. **Before creating PR**:
   - Run full security scan locally
   - Ensure no new vulnerabilities introduced
   - Update dependencies if needed

### For Maintainers

1. **Weekly security review**:
   - Review Dependabot PRs (Monday mornings)
   - Merge non-breaking security updates
   - Schedule major updates for sprint planning

2. **Quarterly dependency audit**:
   - Review all dependencies for alternatives
   - Remove unused dependencies
   - Update locked versions
   - Test full application after updates

3. **Emergency security patches**:
   - Monitor GitHub Security Advisories
   - Apply critical patches within 24 hours
   - Create hotfix branch if necessary
   - Deploy to production immediately

## Reporting Security Vulnerabilities

### Found a vulnerability in our dependencies?

If automated scanning hasn't caught it yet:

1. **Do NOT** create a public GitHub issue
2. Contact maintainers privately via:
   - GitHub Security Advisories (preferred)
   - Direct message to project maintainer
   - Email: [security contact - add if available]

### Found a vulnerability in our code?

1. Create a **private security advisory** on GitHub
2. Provide:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested remediation (if any)

### Disclosure Timeline

- **Day 0**: Vulnerability reported privately
- **Day 1-7**: Maintainers assess and confirm issue
- **Day 7-30**: Develop and test fix
- **Day 30**: Public disclosure and patch release
- **Extended timeline**: If patch requires significant refactoring

## Security Exceptions

In rare cases, we may accept known vulnerabilities temporarily:

**Requirements for security exceptions**:
1. Documented risk assessment
2. Mitigation controls in place
3. Remediation plan with timeline
4. Approval from project maintainer
5. Regular review (monthly)

**Process**:
1. Create GitHub issue documenting exception
2. Use `@dependabot ignore` to suppress alerts
3. Link issue in code comments
4. Schedule review in project board

## Resources

- [GitHub Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [pip-audit Documentation](https://github.com/pypa/pip-audit)
- [npm audit Documentation](https://docs.npmjs.com/cli/v8/commands/npm-audit)
- [CVSS Severity Ratings](https://nvd.nist.gov/vuln-metrics/cvss)
- [OWASP Dependency Check](https://owasp.org/www-project-dependency-check/)

## Changelog

- **2025-11-24**: Initial security policy created
  - Configured Dependabot for Python and Node.js
  - Implemented GitHub Actions security scanning
  - Established vulnerability response SLAs
