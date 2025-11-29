# Biography Generation Quick Start Guide

**Goal**: Generate biographies for 1,418 remaining entities using priority-based strategy

## TL;DR (2 Minutes to Start)

```bash
# 1. Generate tier files (30 seconds)
python3 scripts/analysis/generate_bios_by_priority.py --all-tiers

# 2. Start with Tier 1 (3-5 minutes)
python3 scripts/analysis/generate_entity_bios_grok.py \
  --source data/metadata/entities_tier1.json \
  --limit 50 \
  --backup
```

## Current Status

- **Total entities**: 1,637
- **With biographies**: 219 (13.4%)
- **Remaining**: 1,418 (86.6%)

## Priority Breakdown (Actual Counts)

| Tier | Priority | Count | Time | Rationale |
|------|----------|-------|------|-----------|
| 1 | High | 33 | ~3 min | Document mentions ≥ 2 OR multiple sources |
| 2 | Medium-High | 70 | ~7 min | Flight logs OR connections OR 1 doc mention |
| 3 | Medium | 0 | ~0 min | Black Book + 1 other source |
| 4 | Low | 1,315 | ~132 min | Black Book only (single source) |
| **Total** | - | **1,418** | **~142 min** | **~2.4 hours** |

## Quick Commands

### Dry Run (Test First)

```bash
# See what's in each tier (no files created)
python3 scripts/analysis/generate_bios_by_priority.py --all-tiers --dry-run

# Check specific tier
python3 scripts/analysis/generate_bios_by_priority.py --tier 1 --dry-run
```

### Generate Tier Files

```bash
# Generate all at once
python3 scripts/analysis/generate_bios_by_priority.py --all-tiers

# Or generate individually
python3 scripts/analysis/generate_bios_by_priority.py --tier 1
python3 scripts/analysis/generate_bios_by_priority.py --tier 2
python3 scripts/analysis/generate_bios_by_priority.py --tier 4
```

### Generate Biographies

```bash
# Tier 1: High Priority (33 entities, ~3 minutes)
python3 scripts/analysis/generate_entity_bios_grok.py \
  --source data/metadata/entities_tier1.json \
  --limit 50 \
  --backup

# Tier 2: Medium-High Priority (70 entities, ~7 minutes)
python3 scripts/analysis/generate_entity_bios_grok.py \
  --source data/metadata/entities_tier2.json \
  --limit 100 \
  --backup

# Tier 4: Low Priority (1,315 entities - batch across sessions)
# Session 1: First 200
python3 scripts/analysis/generate_entity_bios_grok.py \
  --source data/metadata/entities_tier4.json \
  --limit 200 \
  --backup

# Session 2: Next 200
python3 scripts/analysis/generate_entity_bios_grok.py \
  --source data/metadata/entities_tier4.json \
  --limit 200 \
  --backup

# Continue in batches until complete...
```

## Monitoring Progress

```bash
# Check database count
sqlite3 data/metadata/entities.db "SELECT COUNT(*) FROM entity_biographies"

# Check JSON count
python3 -c "import json; data = json.load(open('data/metadata/entity_biographies.json')); print(len(data['entities']))"

# See tier summary
python3 scripts/analysis/generate_bios_by_priority.py --all-tiers --dry-run
```

## Error Recovery

### If Generation Fails

1. **Check checkpoint**: `data/metadata/entity_biographies_grok_checkpoint.json`
2. **Resume**: Re-run the same command - it will continue from checkpoint
3. **Review errors**: Check console output for error messages

### If Quality is Low

1. **Check validation warnings** in output
2. **Review sample biographies** in output file
3. **Adjust prompt** in `generate_entity_bios_grok.py` (line 129)
4. **Re-generate** specific entities if needed

## Expected Quality by Tier

### Tier 1 (High Quality)
- **Length**: 150-300 words
- **Quality Score**: 0.8-1.0
- **Content**: Rich, multiple data points, specific details

### Tier 2 (Good Quality)
- **Length**: 100-250 words
- **Quality Score**: 0.6-0.8
- **Content**: Clear role/relationship, moderate details

### Tier 4 (Basic Quality)
- **Length**: 50-150 words
- **Quality Score**: 0.4-0.6
- **Content**: Contact-level information, minimal details

## Success Criteria

- ✓ All 1,418 remaining entities have biographies
- ✓ Average quality scores meet tier expectations
- ✓ Biographies synced to database
- ✓ Frontend displays all biographies correctly

## Cost Estimate

**Using Grok-4.1-fast (currently FREE until Dec 3, 2025)**:
- Total cost: **$0.00**
- Post-Dec 3: ~$0.25-0.30 for all 1,418 bios

## Related Files

- **Priority Script**: `scripts/analysis/generate_bios_by_priority.py`
- **Generation Script**: `scripts/analysis/generate_entity_bios_grok.py`
- **Full Plan**: `docs/1M-184-BIO-ENRICHMENT-PLAN.md`
- **Linear Ticket**: [1M-184](https://linear.app/1m-hyperdev/issue/1M-184/bio-enrichment)

---

**Last Updated**: 2025-11-24
