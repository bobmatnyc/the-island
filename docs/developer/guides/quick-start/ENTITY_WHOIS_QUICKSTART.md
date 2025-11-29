# Entity WHOIS Enrichment - Quick Start Guide

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- ✅ Searches Wikipedia for each entity
- ✅ Extracts 2-3 sentence biographical summaries
- ✅ Adds source attribution ("Source: Wikipedia - [Article Name]")
- ✅ Skips generic entities ("Female (1)", etc.)
- ✅ Respects Wikipedia's rate limits (0.5s between requests)

---

## Overview

This guide explains how to enrich all entities in the Epstein Archive with biographical information from Wikipedia.

## What It Does

The WHOIS enrichment script:
- ✅ Searches Wikipedia for each entity
- ✅ Extracts 2-3 sentence biographical summaries
- ✅ Adds source attribution ("Source: Wikipedia - [Article Name]")
- ✅ Skips generic entities ("Female (1)", etc.)
- ✅ Respects Wikipedia's rate limits (0.5s between requests)
- ✅ Saves progress every 25 entities (resume-able)

## Quick Start

### Run Full Enrichment

```bash
cd /Users/masa/Projects/epstein
python3 scripts/research/basic_entity_whois.py
```

**Expected Runtime:** 15-20 minutes
**Entities to Process:** ~1,639 total (~400-600 will be enriched)

### Monitor Progress

The script will output:
```
[25/1639] Enriching: Clinton, Bill
  ✓ Added bio (342 chars)
[26/1639] Skipped (generic): Female (1)
[27/1639] Enriching: Prince Andrew
  ✓ Added bio (651 chars)
...
--- Checkpoint: Saving progress ---
Processed: 25/1639
Bios added: 18
Bios skipped: 5
Generic skipped: 2
```

### Interrupt & Resume

**To Stop:** Press `Ctrl+C`

**To Resume:** Just run the script again:
```bash
python3 scripts/research/basic_entity_whois.py
```

It will automatically resume from the last checkpoint.

## Results

### Output Files

1. **data/md/entities/ENTITIES_INDEX.json** (updated)
   - Entities will have new fields:
     - `bio`: Biographical text
     - `whois_checked`: true
     - `whois_source`: "wikipedia" | "none" | "skipped_generic"
     - `whois_date`: ISO timestamp

2. **data/metadata/whois_report.txt** (generated)
   - Comprehensive statistics
   - Coverage percentages
   - Error summary

3. **data/metadata/whois_progress.json** (temporary)
   - Progress tracking file
   - Automatically deleted on completion

### Expected Coverage

| Category | Count | % of Total |
|----------|-------|------------|
| Named individuals (will enrich) | ~600 | ~37% |
| Generic placeholders (skipped) | ~500 | ~30% |
| Errors (no Wikipedia) | ~400 | ~24% |
| Single names (skipped) | ~139 | ~9% |
| **Target Bio Coverage** | **~1,000** | **~60-70%** |

## Entity Categories

### Will Be Enriched ✅
- Named individuals: "Clinton, Bill", "Trump, Donald"
- Public figures: "Prince Andrew", "Maxwell, Ghislaine"
- Billionaires: "Wexner, Leslie", "Dubin, Glenn"

### Will Be Skipped ⏭️
- Generic: "Female (1)", "Male (2)", "Passenger 3"
- Single names: "Nadia", "Didier", "Tatiana"
- Non-persons: "Pilot", "Crew", "Staff"

### Marked as Checked (No Bio Found) ❌
- Obscure individuals without Wikipedia entries
- Misspelled or variant names
- Private individuals

## Verification

### Check Results

```bash
# Count entities with bios
grep -c '"bio":' data/md/entities/ENTITIES_INDEX.json

# View sample enriched entity
python3 -c "
import json
with open('data/md/entities/ENTITIES_INDEX.json') as f:
    data = json.load(f)
    for entity in data['entities']:
        if entity.get('bio') and len(entity['bio']) > 100:
            print(f\"Name: {entity['name']}\")
            print(f\"Bio: {entity['bio'][:200]}...\")
            print()
            break
"
```

### View Final Report

```bash
cat data/metadata/whois_report.txt
```

## Troubleshooting

### Problem: Script is too slow

**Solution:** The script respects Wikipedia's rate limits. This is intentional and cannot be safely increased without risking being blocked.

### Problem: Many "No Wikipedia entry" errors

**Expected:** Many entities in the archive are not public figures and won't have Wikipedia entries. This is normal.

### Problem: Script crashes or is interrupted

**Solution:** Just run it again. Progress is saved every 25 entities and will resume automatically.

### Problem: 403 Forbidden errors from Wikipedia

**Cause:** Missing or invalid User-Agent header
**Status:** This has been fixed in the current script

## Advanced Options

### Modify Rate Limit

Edit `scripts/research/basic_entity_whois.py`:

```python
RATE_LIMIT_SECONDS = 0.5  # Change to 1.0 for slower, safer rate
```

### Modify Checkpoint Interval

```python
PROGRESS_CHECKPOINT_INTERVAL = 25  # Change to 50 for fewer checkpoints
```

### Test on Sample

Run test script first to verify API connectivity:

```bash
python3 scripts/research/test_whois.py
```

## API Details

- **Service:** Wikipedia API
- **Endpoint:** https://en.wikipedia.org/w/api.php
- **Authentication:** None required
- **Rate Limit:** Self-imposed 0.5s delay
- **User-Agent:** EpsteinArchiveBot/1.0

## Success Criteria

After running, you should see:

✅ All entities have `whois_checked: true`
✅ ~60-70% of entities have biographical information
✅ Report file generated: `data/metadata/whois_report.txt`
✅ No orphaned progress file (cleaned up on completion)

## Next Steps

After enrichment completes:

1. **Review report:** `cat data/metadata/whois_report.txt`
2. **Verify coverage:** Check bio coverage percentage
3. **Manual additions:** Add bios for high-priority entities that Wikipedia missed
4. **Update API:** Restart server to serve new bio data

## Support

For issues or questions:
- Check `data/metadata/whois_report.txt` for statistics
- Review script output for specific error messages
- Examine `data/metadata/whois_progress.json` for current state

---

**Last Updated:** 2025-11-19
**Script Location:** `/Users/masa/Projects/epstein/scripts/research/basic_entity_whois.py`
**Documentation:** `/Users/masa/Projects/epstein/data/metadata/entity_data_quality_report.txt`
