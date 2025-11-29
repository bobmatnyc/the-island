# Deduplication System - Quick Start Guide

**Quick Summary**: Quick reference guide for rapid lookup of key information.

**Category**: Quick Reference
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Progress:** Current file / Total files (percentage)
- **Speed:** Emails processed per second
- **Duplicates:** Number of duplicates found
- **Errors:** Number of processing errors
- **Processing time:** 2-10 minutes

---

**Status:** ✅ System ready for House Oversight collection

**Note:** First-time users: The system will download a ~90MB sentence-transformers model (`all-MiniLM-L6-v2`) on first run. This requires an internet connection and will be cached locally. See [../user/getting-started.md#model-requirements](../user/getting-started.md#model-requirements) for details.

---

## One-Command Processing

When House Oversight emails arrive, run this single command:

```bash
python3 scripts/process_bulk_emails.py \
  /path/to/house_oversight_emails \
  --source-name "house_oversight" \
  --collection "oversight_2024" \
  --format pdf \
  --report processing_report.txt
```

**That's it!** Watch the progress bar and wait for completion.

---

## Common Commands

### Check System Status

```bash
python3 scripts/query_deduplication.py stats
```

### List Recent Documents

```bash
python3 scripts/query_deduplication.py recent 20
```

### Find Duplicates

```bash
python3 scripts/query_deduplication.py duplicates
```

### Search Documents

```bash
python3 scripts/query_deduplication.py search "epstein"
```

### Export Database

```bash
python3 scripts/query_deduplication.py export json output.json
```

---

## Real-Time Monitoring

During processing, you'll see:

```
Progress: 5432/20000 (27.2%) | 142.5 emails/sec | Duplicates: 567 | Errors: 3
```

**What it means:**
- **Progress:** Current file / Total files (percentage)
- **Speed:** Emails processed per second
- **Duplicates:** Number of duplicates found
- **Errors:** Number of processing errors

---

## Expected Results

For 20,000 emails:

- **Processing time:** 2-10 minutes
- **Duplicates found:** ~2,000 (10% typical)
- **Unique documents:** ~18,000
- **Database size:** ~100-500 MB

---

## File Locations

**Database:** `/Users/masa/Projects/Epstein/data/metadata/deduplication.db`

**Scripts:**
- `/Users/masa/Projects/Epstein/scripts/process_bulk_emails.py`
- `/Users/masa/Projects/Epstein/scripts/query_deduplication.py`

**Documentation:**
- `DEDUPLICATION_SYSTEM.md` - Full documentation
- `SYSTEM_READY_REPORT.md` - Verification report
- `QUICK_START.md` - This guide

---

## Troubleshooting

### Slow Processing

```bash
# Skip fuzzy matching for 2-3x speedup
python3 scripts/process_bulk_emails.py <dir> --skip-duplicates
```

### Memory Issues

```bash
# Reduce batch size
python3 scripts/process_bulk_emails.py <dir> --batch-size 50
```

### Database Not Found

```bash
# Re-initialize (safe to re-run)
python3 scripts/initialize_deduplication.py
```

---

## Need Help?

1. Check `DEDUPLICATION_SYSTEM.md` for detailed documentation
2. Run `python3 scripts/query_deduplication.py stats` to check system health
3. Review `processing_report.txt` for detailed processing results

---

**System Status:** ✅ Ready for production use
**Last verified:** 2025-11-16
