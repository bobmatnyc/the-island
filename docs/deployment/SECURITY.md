# Security Guide - Epstein Archive

**Quick Summary**: **GOOD NEWS**: Security audit completed on 2025-11-20...

**Category**: Deployment
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- ✅ `.env.local` was NEVER committed to git history
- ✅ `.env.local` is properly listed in `.gitignore`
- ✅ No hardcoded secrets found in codebase
- ✅ Application properly uses `os.getenv()` for all secrets
- ✅ Documentation uses placeholder values only

---

## 🔴 CRITICAL: API Key Security

### Current Status Assessment

**GOOD NEWS**: Security audit completed on 2025-11-20
- ✅ `.env.local` was NEVER committed to git history
- ✅ `.env.local` is properly listed in `.gitignore`
- ✅ No hardcoded secrets found in codebase
- ✅ Application properly uses `os.getenv()` for all secrets
- ✅ Documentation uses placeholder values only

**ACTION REQUIRED**: API Key Rotation

Even though your key was never committed, as a security best practice when an API key is discovered during audit, it should be rotated.

---

## 🔄 API Key Rotation Instructions

### Step 1: Rotate OpenRouter API Key

1. **Login to OpenRouter**
   - Visit: https://openrouter.ai/keys
   - Sign in to your account

2. **Create New API Key**
   - Click "Create Key" or "+ New Key"
   - Give it a descriptive name (e.g., "Epstein Archive Production")
   - Copy the new key immediately (you won't see it again!)

3. **Revoke Old Key**
   - Find the old key in your key list
   - Click "Revoke" or "Delete"
   - Confirm revocation

4. **Update Local Environment**
   ```bash
   # Edit your .env.local file
   nano /Users/masa/Projects/epstein/.env.local

   # Replace the old key with your new key
   OPENROUTER_API_KEY=sk-or-v1-NEW_KEY_HERE
   ```

5. **Restart Application**
   ```bash
   # If server is running, restart it
   ./scripts/dev-stop.sh
   ./scripts/dev-start.sh
   ```

6. **Test New Key**
   ```bash
   # Test the chat endpoint
   python tests/scripts/test_openrouter.py
   ```

### Why Rotate?

- **Proactive Security**: Even without a breach, rotation is best practice
- **Audit Trail**: Establishes when key rotation occurred
- **Defense in Depth**: Limits exposure window if key was somehow compromised
- **Compliance**: Many security frameworks require periodic rotation

---

## 🔐 Production Secret Management

### Option A: Environment Variables (Simple Deployments)

**Best for**: VPS, single server deployments

```bash
# Set in server environment
export OPENROUTER_API_KEY="your_production_key"
export OPENROUTER_MODEL="openai/gpt-4o"

# Or add to ~/.bashrc or ~/.profile
echo 'export OPENROUTER_API_KEY="your_production_key"' >> ~/.bashrc
source ~/.bashrc
```

**Pros:**
- Simple to set up
- No additional services required
- Works on any platform

**Cons:**
- Keys visible in process list
- No built-in rotation
- Manual management

---

### Option B: Docker Secrets (Docker Deployments)

**Best for**: Docker Swarm, containerized deployments

```bash
# Create secret from file
echo "your_production_key" | docker secret create openrouter_key -

# Or from file
docker secret create openrouter_key ./openrouter_key.txt

# Use in docker-compose.yml
version: '3.8'
services:
  api:
    image: epstein-archive
    secrets:
      - openrouter_key
    environment:
      OPENROUTER_API_KEY_FILE: /run/secrets/openrouter_key

secrets:
  openrouter_key:
    external: true
```

**Pros:**
- Encrypted at rest and in transit
- Not visible in environment
- Native Docker integration

**Cons:**
- Requires Docker Swarm
- More complex setup

---

### Option C: Cloud Secret Managers (Cloud Deployments)

#### AWS Secrets Manager

**Best for**: AWS deployments

```bash
# Store secret
aws secretsmanager create-secret \
    --name epstein-archive/openrouter-key \
    --secret-string "your_production_key"

# Retrieve in application (Python)
import boto3
from botocore.exceptions import ClientError

def get_secret():
    secret_name = "epstein-archive/openrouter-key"
    region_name = "us-east-1"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        return get_secret_value_response['SecretString']
    except ClientError as e:
        raise e

# Use in app
OPENROUTER_API_KEY = get_secret()
```

**Pricing**: ~$0.40/month per secret + $0.05 per 10,000 API calls

**Pros:**
- Automatic rotation support
- Audit logging
- Fine-grained access control
- Encryption at rest

**Cons:**
- Additional cost
- AWS-specific
- More complex setup

---

#### Google Cloud Secret Manager

**Best for**: Google Cloud deployments

```bash
# Store secret
echo -n "your_production_key" | gcloud secrets create openrouter-key --data-file=-

# Grant access
gcloud secrets add-iam-policy-binding openrouter-key \
    --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

# Retrieve in application (Python)
from google.cloud import secretmanager

def get_secret():
    client = secretmanager.SecretManagerServiceClient()
    name = "projects/PROJECT_ID/secrets/openrouter-key/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

# Use in app
OPENROUTER_API_KEY = get_secret()
```

**Pricing**: $0.06 per 10,000 access operations (first 10,000 free/month)

**Pros:**
- Very affordable
- Automatic encryption
- Version management
- IAM integration

**Cons:**
- GCP-specific
- Requires service account setup

---

#### HashiCorp Vault

**Best for**: Multi-cloud, self-hosted, enterprise

```bash
# Store secret
vault kv put secret/epstein-archive/openrouter \
    api_key="your_production_key" \
    model="openai/gpt-4o"

# Retrieve in application (Python)
import hvac

client = hvac.Client(url='http://localhost:8200')
client.token = 'your-vault-token'

secret = client.secrets.kv.v2.read_secret_version(
    path='epstein-archive/openrouter'
)

OPENROUTER_API_KEY = secret['data']['data']['api_key']
```

**Pricing**: Free (open source) or Enterprise pricing

**Pros:**
- Cloud-agnostic
- Dynamic secrets
- Extensive auth methods
- Self-hosted option

**Cons:**
- Requires Vault infrastructure
- Operational overhead
- Steeper learning curve

---

#### Doppler (Third-Party Secret Manager)

**Best for**: Multi-environment, team collaboration

```bash
# Install Doppler CLI
brew install dopplerhq/cli/doppler  # macOS
# or: curl -Ls https://cli.doppler.com/install.sh | sh

# Login
doppler login

# Setup project
doppler setup

# Store secrets via UI or CLI
doppler secrets set OPENROUTER_API_KEY="your_production_key"

# Run application with Doppler
doppler run -- python server/app.py
```

**Pricing**: Free for personal use, $7/user/month for teams

**Pros:**
- Very easy to use
- Multi-environment support
- Team collaboration features
- Cloud-agnostic

**Cons:**
- Third-party dependency
- Paid for teams
- Requires network access

---

### Recommended Approach by Deployment Type

| Deployment Type | Recommended Solution | Why |
|----------------|---------------------|-----|
| **Local Development** | `.env.local` file | Simple, fast iteration |
| **Single VPS** | Environment variables | No extra dependencies |
| **Docker (single host)** | Docker Secrets | Native integration |
| **AWS** | AWS Secrets Manager | Cloud-native, rotation |
| **Google Cloud** | Secret Manager | Cost-effective |
| **Multi-cloud** | HashiCorp Vault or Doppler | Cloud-agnostic |
| **Team/Enterprise** | Doppler or Vault | Collaboration features |

---

## 🔍 Secret Scanning

### Pre-Commit Hook (Recommended)

Install `detect-secrets` to prevent committing secrets:

```bash
# Install
pip install detect-secrets

# Initialize baseline
detect-secrets scan > .secrets.baseline

# Add pre-commit hook
cat << 'EOF' > .git/hooks/pre-commit
#!/bin/bash
# Scan for secrets before commit
detect-secrets-hook --baseline .secrets.baseline $(git diff --cached --name-only)
if [ $? -ne 0 ]; then
    echo "⚠️  Potential secrets detected! Commit aborted."
    exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

### Manual Scanning

```bash
# Scan entire repository
detect-secrets scan

# Scan specific files
grep -r "sk-or-v1-" --exclude-dir=.venv --exclude-dir=node_modules

# Search for API key patterns
grep -r "api[_-]?key\s*=\s*['\"]" --exclude-dir=.venv --exclude-dir=node_modules
```

---

## ✅ Pre-Deployment Security Checklist

Before deploying to production, verify:

- [ ] **Environment Files**
  - [ ] `.env.local` is in `.gitignore`
  - [ ] `.env.example` exists with no real secrets
  - [ ] No `.env` files committed to git

- [ ] **API Keys**
  - [ ] All API keys rotated (if ever exposed)
  - [ ] Keys stored in secure secret manager (production)
  - [ ] No hardcoded secrets in codebase
  - [ ] API keys have appropriate scopes/permissions

- [ ] **Git History**
  - [ ] No secrets in git history (`git log --all -S "sk-or-v1"`)
  - [ ] `.gitignore` properly configured
  - [ ] Pre-commit hooks installed (optional but recommended)

- [ ] **Application Code**
  - [ ] All secrets loaded via `os.getenv()`
  - [ ] Fallback values are placeholders, not real secrets
  - [ ] Secrets not logged or exposed in error messages

- [ ] **Documentation**
  - [ ] Setup instructions use `.env.example`
  - [ ] No real credentials in documentation
  - [ ] Secret rotation process documented

- [ ] **Access Control**
  - [ ] Production secrets only accessible to authorized team members
  - [ ] Different keys for dev/staging/production
  - [ ] API key usage monitoring enabled (if available)

- [ ] **Monitoring**
  - [ ] API key usage alerts configured
  - [ ] Unauthorized access monitoring
  - [ ] Regular secret rotation scheduled (e.g., quarterly)

---

## 🚨 What to Do If a Secret Is Exposed

### Immediate Actions (within 1 hour)

1. **Rotate the compromised secret immediately**
   - Follow rotation instructions above
   - Do not wait for "business hours"

2. **Revoke the old secret**
   - Delete/disable in the service provider
   - Confirm revocation

3. **Check for unauthorized usage**
   - Review API usage logs
   - Look for unexpected activity
   - Check billing for abnormal usage

### Short-term Actions (within 24 hours)

4. **Update all deployments**
   - Update production with new key
   - Update staging/development environments
   - Verify all services are functional

5. **Remove from git history (if committed)**
   ```bash
   # Using BFG Repo-Cleaner (recommended)
   brew install bfg  # macOS
   bfg --replace-text passwords.txt  # File containing: API_KEY==>***REMOVED***
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive

   # Force push (coordinate with team!)
   git push --force --all
   ```

6. **Notify stakeholders**
   - Inform team of the incident
   - Document what happened
   - Review and improve processes

### Long-term Actions (within 1 week)

7. **Root cause analysis**
   - How did the exposure occur?
   - What processes failed?
   - How can we prevent recurrence?

8. **Implement preventive measures**
   - Install pre-commit hooks
   - Set up secret scanning
   - Review access controls
   - Schedule regular secret rotation

9. **Update documentation**
   - Document the incident (sanitized)
   - Update security procedures
   - Train team on secure practices

---

## 📚 Additional Resources

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [detect-secrets Documentation](https://github.com/Yelp/detect-secrets)
- [12 Factor App - Config](https://12factor.net/config)

---

## 🔒 Security Contact

For security concerns or to report vulnerabilities, please contact the project maintainer.

**Remember**: Security is everyone's responsibility. When in doubt, rotate the key!
