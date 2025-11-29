# Audit Logging Quick Start Guide

**Quick Summary**: Quick reference guide for rapid lookup of key information.

**Category**: Quick Reference
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- ✅ Username, timestamp, IP (hashed)
- ✅ Success/failure status
- ✅ Browser, OS, device type
- ✅ Screen resolution, timezone
- ✅ TOS acceptance, remember me

---

## 🚀 Quick Access

**Dashboard**: `http://localhost:8000/static/audit.html`

**Database**: `/Users/masa/Projects/Epstein/data/logs/audit.db`

**Status**: ✅ Active and Logging

## 📊 What's Logged

Every login attempt captures:
- ✅ Username, timestamp, IP (hashed)
- ✅ Success/failure status
- ✅ Browser, OS, device type
- ✅ Screen resolution, timezone
- ✅ TOS acceptance, remember me
- ✅ Session token generated

## 🔍 Quick Commands

### View Recent Logins
```bash
sqlite3 data/logs/audit.db "SELECT timestamp, username, success FROM login_events ORDER BY timestamp DESC LIMIT 10;"
```

### Check Security Events
```bash
sqlite3 data/logs/audit.db "SELECT * FROM security_events ORDER BY timestamp DESC;"
```

### Count Failed Logins
```bash
sqlite3 data/logs/audit.db "SELECT COUNT(*) FROM login_events WHERE success = 0;"
```

### Browser Distribution
```bash
sqlite3 data/logs/audit.db "SELECT browser, COUNT(*) as count FROM browser_profiles GROUP BY browser ORDER BY count DESC;"
```

## 🛡️ Security Alerts

**Automatic Triggers**:
- 5+ failed logins (same user, 5 min) → High severity
- 10+ failed logins (same IP, 5 min) → Critical severity

**Check Alerts**:
```bash
sqlite3 data/logs/audit.db "SELECT event_type, severity, details FROM security_events WHERE severity IN ('high', 'critical');"
```

## 🔧 API Quick Reference

**Get Logs** (last 100):
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/admin/audit-logs?limit=100
```

**Get Statistics**:
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/admin/login-statistics
```

**Anonymize Old Records** (90+ days):
```bash
curl -X POST -H "Authorization: Bearer <token>" http://localhost:8000/api/admin/anonymize-logs?days=90
```

## 📈 Dashboard Features

1. **Statistics Cards**: Total logins, success rate, unique users
2. **Charts**: Browser, OS, device distribution (last 30 days)
3. **Security Events**: Real-time alerts with severity levels
4. **Audit Logs**: Full login history with filtering
5. **GDPR Controls**: One-click anonymization

## 🧪 Test the System

```bash
python3 scripts/test_audit_logging.py
```

Expected output: `ALL TESTS PASSED! ✅`

## 📝 Common Tasks

### Export Logs to CSV
```bash
sqlite3 -header -csv data/logs/audit.db "SELECT * FROM login_events;" > audit_export.csv
```

### Backup Database
```bash
cp data/logs/audit.db data/logs/audit_backup_$(date +%Y%m%d).db
```

### Check Database Size
```bash
du -h data/logs/audit.db
```

### Vacuum (Reclaim Space)
```bash
sqlite3 data/logs/audit.db "VACUUM;"
```

## 🔐 Privacy Features

- **IP Hashing**: SHA256 (irreversible)
- **90-Day Retention**: Auto-anonymization
- **No Cookies**: Privacy-first design
- **GDPR Compliant**: Data minimization

## 📞 Support

- **Full Documentation**: `AUDIT_LOGGING_IMPLEMENTATION.md`
- **Test Suite**: `scripts/test_audit_logging.py`
- **Database Schema**: `scripts/database/init_audit_db.py`

---

**Need Help?** Check the comprehensive implementation doc for detailed information.
