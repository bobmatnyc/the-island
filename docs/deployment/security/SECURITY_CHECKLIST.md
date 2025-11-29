# 🔒 Security Deployment Checklist

**Quick Summary**: **Use this checklist before deploying to production**...

**Category**: Deployment
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- [x] `.env.local` is in `.gitignore`
- [x] `.env.example` exists (safe to commit)
- [x] No `.env` files in git history
- [ ] Production uses secret manager (not `.env` files)
- [ ] **OpenRouter API key rotated** (REQUIRED)

---

**Use this checklist before deploying to production**

---

## Pre-Deployment Security Verification

### 1. Environment Files ✅

- [x] `.env.local` is in `.gitignore`
- [x] `.env.example` exists (safe to commit)
- [x] No `.env` files in git history
- [ ] Production uses secret manager (not `.env` files)

**Quick Check**:
```bash
# Verify gitignore
cat .gitignore | grep -E "\.env"

# Check git history
git log --all --full-history -- "*.env*"
```

---

### 2. API Keys & Secrets 🔑

- [ ] **OpenRouter API key rotated** (REQUIRED)
  - [ ] New key created at https://openrouter.ai/keys
  - [ ] `.env.local` updated with new key
  - [ ] Old key revoked
  - [ ] Application tested with new key

- [ ] Production uses different keys than development
- [ ] API keys scoped to minimum required permissions
- [ ] Billing alerts configured (detect abuse)

**Quick Check**:
```bash
# Verify no hardcoded secrets
grep -r "sk-or-v1-" --exclude-dir=.venv --exclude-dir=node_modules
# Should return: No results
```

---

### 3. Code Security ✅

- [x] All secrets loaded via `os.getenv()`
- [x] No hardcoded credentials in codebase
- [x] No secrets in error messages or logs
- [x] Documentation uses placeholder values only

**Quick Check**:
```bash
# Scan for potential secrets
grep -r "api[_-]?key\s*=\s*['\"']" --exclude-dir=.venv --exclude-dir=node_modules
# Should only return environment variable assignments
```

---

### 4. Production Secret Management 🏭

Choose one based on your deployment:

#### Option A: VPS/Single Server
- [ ] Environment variables set in server profile
- [ ] Variables exported in systemd service file
- [ ] Server access restricted to authorized users

#### Option B: Docker
- [ ] Using Docker Secrets
- [ ] Secrets not in docker-compose.yml
- [ ] Runtime injection configured

#### Option C: AWS
- [ ] AWS Secrets Manager configured
- [ ] IAM roles properly scoped
- [ ] Automatic rotation enabled (optional)

#### Option D: Google Cloud
- [ ] Secret Manager configured
- [ ] Service account has minimal permissions
- [ ] Version management enabled

#### Option E: Multi-cloud
- [ ] HashiCorp Vault or Doppler configured
- [ ] Access policies defined
- [ ] Backup/recovery tested

**See**: `docs/deployment/SECURITY.md` for detailed setup instructions

---

### 5. Access Control 👥

- [ ] Production secrets accessible only to authorized team
- [ ] Service accounts use least privilege principle
- [ ] API key access logged (if available)
- [ ] Team members trained on security procedures

---

### 6. Monitoring & Alerts 📊

- [ ] API usage monitoring enabled
- [ ] Billing alerts configured
- [ ] Unauthorized access detection active
- [ ] Security logs reviewed regularly

---

### 7. Documentation 📚

- [x] Security procedures documented (`docs/deployment/SECURITY.md`)
- [x] Key rotation process documented
- [x] `.env.example` template available
- [ ] Team trained on security practices
- [ ] Incident response plan defined

---

### 8. Optional Enhancements (Recommended) ⭐

- [ ] Pre-commit hooks installed (`detect-secrets`)
- [ ] Secret scanning in CI/CD pipeline
- [ ] Quarterly key rotation scheduled
- [ ] Security audit scheduled (every 6 months)
- [ ] Dependency vulnerability scanning enabled

**Install Pre-commit Hooks**:
```bash
pip install detect-secrets
detect-secrets scan > .secrets.baseline

# Create pre-commit hook
cat << 'EOF' > .git/hooks/pre-commit
#!/bin/bash
detect-secrets-hook --baseline .secrets.baseline $(git diff --cached --name-only)
if [ $? -ne 0 ]; then
    echo "⚠️  Potential secrets detected! Commit aborted."
    exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

---

## Quick Start: Rotate API Key (5 minutes)

### Step 1: Create New Key
1. Visit: https://openrouter.ai/keys
2. Click "Create Key"
3. Name it: "Epstein Archive Production"
4. **Copy the key immediately!**

### Step 2: Update Local Environment
```bash
# Edit .env.local
nano /Users/masa/Projects/epstein/.env.local

# Replace:
OPENROUTER_API_KEY=sk-or-v1-NEW_KEY_HERE
```

### Step 3: Restart & Test
```bash
# Restart server
./scripts/dev-stop.sh
./scripts/dev-start.sh

# Test
python tests/scripts/test_openrouter.py
```

### Step 4: Revoke Old Key
1. Go back to: https://openrouter.ai/keys
2. Find the old key
3. Click "Revoke" or "Delete"

### Step 5: Document
```bash
echo "$(date): API key rotated" >> SECURITY_LOG.md
```

**✅ Done!**

---

## Production Deployment Commands

### Before First Deployment

```bash
# 1. Verify security
./scripts/security-check.sh  # (create this script)

# 2. Set production environment variables
export OPENROUTER_API_KEY="your_production_key"
export OPENROUTER_MODEL="openai/gpt-4o"

# 3. Test configuration
python -c "import os; print('Key loaded:', 'sk-' in os.getenv('OPENROUTER_API_KEY', ''))"

# 4. Deploy
./scripts/deploy.sh  # (your deployment script)
```

---

## Emergency Response: If Secret Is Exposed

### Immediate Actions (< 1 hour)

1. **Rotate immediately**
   ```bash
   # Follow "Quick Start: Rotate API Key" above
   ```

2. **Revoke old key**
   - Do NOT wait
   - Revoke at provider immediately

3. **Check for abuse**
   - Review API usage logs
   - Check billing for unexpected charges

### Within 24 Hours

4. **Update all environments**
   - Production
   - Staging
   - Development
   - CI/CD

5. **If committed to git**
   ```bash
   # Use BFG Repo-Cleaner
   brew install bfg
   bfg --replace-text passwords.txt
   git push --force --all
   ```

6. **Notify team**
   - Document incident
   - Review security procedures

### Within 1 Week

7. **Root cause analysis**
   - How did it happen?
   - What failed?
   - How to prevent?

8. **Implement prevention**
   - Pre-commit hooks
   - Secret scanning
   - Team training

---

## Verification Commands

### Check Git Security
```bash
# No env files in history
git log --all --full-history -- "*.env*"
# Should return: empty

# No secrets in current commit
git diff --cached | grep -i "api[_-]key"
# Should return: empty
```

### Check Code Security
```bash
# No hardcoded secrets
grep -r "sk-or-v1-" --exclude-dir=.venv --exclude-dir=node_modules
# Should return: empty or only in .env.local

# Proper env var usage
grep -r "os.getenv" --include="*.py" | wc -l
# Should return: multiple occurrences
```

### Check Configuration
```bash
# Gitignore configured
cat .gitignore | grep -E "\.env"
# Should show: .env, .env.local, etc.

# Example file exists
ls -la .env.example
# Should exist

# Local config not tracked
git status | grep ".env.local"
# Should show: nothing to commit (if gitignored correctly)
```

---

## Security Metrics

Track these over time:

| Metric | Target | Current |
|--------|--------|---------|
| **Days Since Last Key Rotation** | < 90 | 🔄 Rotate now |
| **Secrets in Git History** | 0 | ✅ 0 |
| **Hardcoded Secrets** | 0 | ✅ 0 |
| **Pre-commit Hooks Installed** | Yes | ⏳ Pending |
| **Production Secret Manager** | Yes | ⏳ When deploying |
| **Team Members Trained** | 100% | ⏳ As needed |

---

## Resources

- **Full Security Guide**: `docs/deployment/SECURITY.md`
- **Audit Report**: `SECURITY_AUDIT_REPORT.md`
- **Environment Template**: `.env.example`
- **OWASP Secrets Management**: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html

---

## Sign-off

Before deploying to production, verify:

```
[ ] All checklist items completed
[ ] API key rotated
[ ] Production secret manager configured
[ ] Team trained on security procedures
[ ] Monitoring and alerts active

Signed: ________________  Date: __________
```

---

*Keep this checklist updated as your security posture evolves*
