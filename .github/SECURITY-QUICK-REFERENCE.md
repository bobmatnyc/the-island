# Security Scanning Quick Reference

## 🚀 Quick Start

### Before Every Commit

```bash
# Python (Backend)
cd server && pip-audit --requirement requirements.txt

# Node.js (Frontend)
cd frontend && npm audit
```

---

## 📋 Dependabot PRs: Quick Decision Guide

### 1. Security Updates (🔴 HIGH/CRITICAL)
- ✅ **Review changelog** → ✅ **Verify CI passes** → ✅ **Merge immediately**
- **SLA**: 24 hours (CRITICAL), 7 days (HIGH)

### 2. Patch Updates (1.2.3 → 1.2.4)
- ✅ **Check CI status** → ✅ **Merge** (usually safe)

### 3. Minor Updates (1.2.3 → 1.3.0)
- ⚠️ **Review changes** → ✅ **Local test** → ✅ **Merge**

### 4. Major Updates (1.2.3 → 2.0.0)
- 🔍 **Read migration guide** → 🧪 **Thorough testing** → ✅ **Schedule merge**

---

## 🤖 Dependabot Commands

Comment on any Dependabot PR:

```bash
@dependabot rebase          # Rebase on latest main
@dependabot merge           # Auto-merge after approval
@dependabot close           # Close without merging
@dependabot ignore this dependency  # Stop updates
```

---

## 🔍 Local Security Scanning

### Python (pip-audit)

```bash
# Install
pip install pip-audit

# Scan dependencies
pip-audit --requirement requirements.txt --desc

# JSON output
pip-audit --requirement requirements.txt --format json
```

### Node.js (npm audit)

```bash
# Scan dependencies
npm audit

# Auto-fix (safe updates only)
npm audit fix

# Show only high/critical
npm audit --audit-level=high
```

---

## 📊 CI/CD Security Workflow

**Triggers**:
- ✅ Pull requests to `main`/`develop`
- ✅ Pushes to `main`
- ✅ Weekly (Monday 2am UTC)
- ✅ Manual trigger via Actions tab

**Failure Criteria**: HIGH or CRITICAL vulnerabilities

**Artifacts**: Security reports (JSON) - retained 30 days

---

## 🔔 Severity & Response Times

| Severity | CVSS Score | Response SLA |
|----------|------------|--------------|
| 🔴 CRITICAL | 9.0 - 10.0 | 24 hours |
| 🟠 HIGH | 7.0 - 8.9 | 7 days |
| 🟡 MEDIUM | 4.0 - 6.9 | 30 days |
| 🟢 LOW | 0.1 - 3.9 | 90 days |

---

## 📚 Full Documentation

- **Security Policy**: `/SECURITY.md`
- **Developer Guide**: `/docs/SECURITY-SCANNING.md`
- **Dependabot Config**: `/.github/dependabot.yml`
- **CI/CD Workflow**: `/.github/workflows/security-scan.yml`

---

## 🆘 Troubleshooting

### "npm audit fix" doesn't fix everything
→ Try `npm audit fix --force` (caution: may break things)
→ Or manually update parent package

### pip-audit fails with missing package
→ Package not in PyPI (check requirements.txt)
→ Remove invalid packages or use private index

### Dependabot PR conflicts
→ Comment: `@dependabot rebase`

---

**Last Updated**: 2025-11-24
