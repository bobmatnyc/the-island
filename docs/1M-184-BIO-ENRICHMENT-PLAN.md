# Priority-Based Biography Generation Plan (1M-184)

**Status**: Ready for Execution
**Created**: 2025-11-24
**Updated**: 2025-11-24
**Total Entities**: 1,637
**Existing Biographies**: 219
**Remaining**: 1,418 entities

## Executive Summary

This document outlines an intelligent, **priority-based strategy** for generating biographies for 1,637 entities in the Epstein Archive. Rather than processing entities randomly or alphabetically, we prioritize based on **importance and evidence strength**.

### Quick Stats
```
Total entities in archive: 1,637
Existing biographies: 219 (13.4%)
Remaining to generate: 1,418 (86.6%)

Priority breakdown:
  Tier 1 (High Priority):       ~81 entities   (~8 minutes)
  Tier 2 (Medium-High):         ~263 entities  (~26 minutes)
  Tier 3 (Medium):              ~293 entities  (~30 minutes)
  Tier 4 (Low):                 ~1,000 entities (~100 minutes)

Total estimated time: ~164 minutes (~2.7 hours)
```

## Current State Analysis

### Bio Coverage Statistics
```
Total entities: 1,637
With biographies: 219 (13.4%)
Without biographies: 1,418 (86.6%)

Data sources breakdown:
  - Black Book only: ~1,000 entities (61%)
  - Flight logs: ~400 entities (24%)
  - Document mentions: ~237 entities (14%)
  - Multiple sources: ~300 entities (18%)
```

## Priority Tier System

### Tier 1: High Priority (IMMEDIATE)
**Criteria**: Document mentions ≥ 2 OR multiple sources (>2)
**Expected Count**: ~81 entities
**Estimated Time**: ~8 minutes
**Rationale**: Primary subjects with substantial documentary evidence

**Examples**:
- Michael (82 document mentions)
- Sally (17 document mentions)
- Peter (13 document mentions)
- Entities appearing in multiple data sources (flights + documents + black book)

**Why Tier 1 First**:
- Highest public interest and research value
- Most complete source material for quality biographies
- Core figures in the investigation
- Immediate value to researchers and journalists

### Tier 2: Medium-High Priority (SHORT TERM)
**Criteria**: Flight logs OR network connections OR 1 document mention
**Expected Count**: ~263 entities
**Estimated Time**: ~26 minutes
**Rationale**: Direct evidence of involvement or proximity

**Examples**:
- Flight log passengers with multiple trips
- Entities with significant network connections (>5 connections)
- Single document mentions (still verified evidence)

**Why Tier 2 Second**:
- Direct, verifiable evidence of association
- Network analysis value (connection mapping)
- Corroborates Tier 1 relationships
- Flight logs are timestamped, valuable temporal data

### Tier 3: Medium Priority (MEDIUM TERM)
**Criteria**: Black Book + 1 other source
**Expected Count**: ~293 entities
**Estimated Time**: ~30 minutes
**Rationale**: Contact book entries with corroborating evidence

**Examples**:
- Black Book contacts who also appear in flights
- Black Book contacts mentioned in documents
- Addresses/phone numbers with secondary verification

**Why Tier 3 Third**:
- Black Book alone is limited (just contact info)
- Multiple sources increase biographical value
- Still significant for network analysis
- Corroborates other data points

### Tier 4: Low Priority (LONG TERM)
**Criteria**: Black Book only (single source)
**Expected Count**: ~1,000 entities
**Estimated Time**: ~100 minutes (batch across sessions)
**Rationale**: Address book contacts with minimal evidence

**Examples**:
- Phone numbers with no other context
- Addresses in contact book
- Names without additional verification

**Why Tier 4 Last**:
- Single-source data (weakest evidence)
- Limited biographical material available
- May include tangential contacts
- Better suited for batch processing across multiple sessions

## Infrastructure Ready

### Existing Bio Enrichment System
The project has a comprehensive bio enrichment script already built:

**Script**: `/scripts/analysis/enrich_bios_from_documents.py`

**Features**:
- ✅ Grok AI integration (x-ai/grok-2-1212 free tier via OpenRouter)
- ✅ Document extraction and analysis
- ✅ Rate limiting (1 req/sec)
- ✅ Confidence scoring
- ✅ Batch processing with progress tracking
- ✅ Automatic backup creation
- ✅ Dry-run testing mode
- ✅ Comprehensive logging

**Architecture**:
1. Reads entity biographies and statistics
2. Finds documents mentioning each entity
3. Extracts relevant paragraphs (max 5 per document, 3 documents max)
4. Sends to Grok AI for contextual analysis
5. Extracts 2-3 specific factual details
6. Merges results back into biography JSON

## Implementation Workflow

### Step 1: Generate Tier Files

Use the priority script to classify all entities into tiers:

```bash
# Change to project directory
cd /Users/masa/Projects/epstein

# Generate all tier files at once
python3 scripts/analysis/generate_bios_by_priority.py --all-tiers

# Or generate individual tiers for review
python3 scripts/analysis/generate_bios_by_priority.py --tier 1 --dry-run
python3 scripts/analysis/generate_bios_by_priority.py --tier 2 --dry-run
python3 scripts/analysis/generate_bios_by_priority.py --tier 3 --dry-run
python3 scripts/analysis/generate_bios_by_priority.py --tier 4 --dry-run
```

**Output Files**:
- `data/metadata/entities_tier1.json` - High priority entities (~81)
- `data/metadata/entities_tier2.json` - Medium-high priority (~263)
- `data/metadata/entities_tier3.json` - Medium priority (~293)
- `data/metadata/entities_tier4.json` - Low priority (~1,000)

### Step 2: Generate Biographies by Tier

Process each tier sequentially, starting with highest priority:

```bash
# Tier 1: High Priority (IMMEDIATE - ~8 minutes)
python3 scripts/analysis/generate_entity_bios_grok.py \
  --source data/metadata/entities_tier1.json \
  --limit 100 \
  --backup

# Tier 2: Medium-High Priority (SHORT TERM - ~26 minutes)
python3 scripts/analysis/generate_entity_bios_grok.py \
  --source data/metadata/entities_tier2.json \
  --limit 300 \
  --backup

# Tier 3: Medium Priority (MEDIUM TERM - ~30 minutes)
python3 scripts/analysis/generate_entity_bios_grok.py \
  --source data/metadata/entities_tier3.json \
  --limit 300 \
  --backup

# Tier 4: Low Priority (LONG TERM - batch across sessions)
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

# Continue in batches of 200 until complete...
```

### Step 3: Merge Generated Biographies

After each tier generation, merge results into main biographies file:

```bash
# Merge Grok-generated biographies into main file
python3 scripts/analysis/merge_biographies.py \
  --source data/metadata/entity_biographies_grok.json \
  --target data/metadata/entity_biographies.json \
  --backup
```

### Step 4: Sync to Database

```bash
# Sync biographies to SQLite database
python3 scripts/analysis/sync_biographies_to_db.py
```

### Step 5: Verify in Frontend

```bash
# Check backend API returns enriched data
curl "http://localhost:8081/api/v2/entities/jeffrey_epstein" | jq '.bio'

# Test frontend display
# Navigate to: http://localhost:5173/entities
# Click on entities with new biographies
# Verify bio sections display correctly
```

## Priority Scoring Algorithm

The priority scoring system uses multiple factors to rank entities within each tier:

```python
base_score = (5 - tier) * 1000  # Tier 1 = 4000, Tier 4 = 1000

doc_weight = total_documents * 100
source_weight = num_sources * 50
connection_weight = connection_count * 10
flight_weight = flight_count * 5
billionaire_bonus = 200 (if applicable)
multi_source_bonus = 100 (if >1 source)

total_score = base_score + doc_weight + source_weight +
              connection_weight + flight_weight +
              billionaire_bonus + multi_source_bonus
```

**Within each tier**, entities are sorted by this score to prioritize:
1. **Document mentions** (strongest evidence) - 100 points each
2. **Multiple sources** (cross-validation) - 50 points each + 100 bonus
3. **Network connections** (relationship context) - 10 points each
4. **Flight count** (temporal data) - 5 points each
5. **Notable figures** (billionaires, public figures) - 200 bonus points

## Expected Outcomes by Tier

### Tier 1 Biographies (High Quality)
- **Length**: 150-300 words
- **Source Material**: Rich, multiple data points
- **Fact Density**: High (dates, numbers, specific details)
- **Quality Score**: 0.8-1.0
- **Example**: "Michael appears in 82 documents spanning 1995-2005, primarily related to property transactions and financial records. Flight logs show 15 trips between New York and Palm Beach..."

### Tier 2 Biographies (Good Quality)
- **Length**: 100-250 words
- **Source Material**: Good, clear role/relationship
- **Fact Density**: Moderate (some dates, numbers)
- **Quality Score**: 0.6-0.8
- **Example**: "Listed in flight logs for 8 trips between 2001-2003, primarily on routes connecting New York, Florida, and the Virgin Islands. Connected to 12 other passengers..."

### Tier 3 Biographies (Acceptable Quality)
- **Length**: 75-200 words
- **Source Material**: Limited but verified
- **Fact Density**: Basic (minimal temporal data)
- **Quality Score**: 0.5-0.7
- **Example**: "Listed in Epstein's contact book with Florida phone number. Also appears in flight logs for 2 trips in 2002. Connected to 3 other entities..."

### Tier 4 Biographies (Basic Quality)
- **Length**: 50-150 words
- **Source Material**: Minimal (single source)
- **Fact Density**: Contact-level information
- **Quality Score**: 0.4-0.6
- **Example**: "Listed in Epstein's contact book with New York address and phone number. No additional data available in flight logs or documents..."

## Time and Cost Estimates

### Processing Time

Based on ~6 seconds per biography (with API rate limiting):

| Tier | Count | Time (minutes) | Time (hours) | Sessions |
|------|-------|----------------|--------------|----------|
| 1    | ~81   | ~8             | ~0.13        | 1        |
| 2    | ~263  | ~26            | ~0.43        | 1        |
| 3    | ~293  | ~30            | ~0.50        | 1-2      |
| 4    | ~1000 | ~100           | ~1.67        | 5-10     |
| **Total** | **1,637** | **~164** | **~2.73** | **8-14** |

### Cost Estimates

Using **Grok-4.1-fast** via OpenRouter:

**Current (FREE until December 3, 2025)**:
- Total cost: **$0.00**
- Rate limiting: 1 second between requests
- No usage limits on free tier

**Post-December 3, 2025**:
- Input tokens: ~150-200 per bio × $0.20/M = ~$0.03-0.04 per 1000 bios
- Output tokens: ~200-300 per bio × $0.50/M = ~$0.10-0.15 per 1000 bios
- **Estimated total cost for 1,637 biographies**: ~$0.25-0.30

## Success Criteria

### Tier 1: COMPLETE
- ✓ All ~81 high-priority entities have biographies
- ✓ Average quality score ≥ 0.7
- ✓ All biographies ≥ 100 words
- ✓ Manual review completed for key figures (optional)

### Tier 2: COMPLETE
- ✓ All ~263 medium-high priority entities have biographies
- ✓ Average quality score ≥ 0.6
- ✓ All biographies ≥ 75 words

### Tier 3: COMPLETE
- ✓ All ~293 medium priority entities have biographies
- ✓ Average quality score ≥ 0.5
- ✓ All biographies ≥ 50 words

### Tier 4: COMPLETE
- ✓ All ~1,000 low priority entities have biographies
- ✓ Average quality score ≥ 0.4
- ✓ All biographies ≥ 50 words

### Overall Project: COMPLETE
- ✓ All 1,637 entities have biographies
- ✓ Biographies synced to SQLite database
- ✓ Frontend displays all biographies correctly
- ✓ Quality assurance review completed
- ✓ Linear ticket 1M-184 marked as COMPLETE

## Technical Specifications

### Grok AI Configuration
```python
Model: x-ai/grok-2-1212 (free tier)
API: OpenRouter (https://openrouter.ai/api/v1)
Temperature: 0.2 (factual extraction)
Max Tokens: 300
Rate Limit: 1 request/second
```

### Prompt Design
The script uses a carefully crafted prompt that:
- Focuses on specific factual details from documents
- Avoids speculation beyond document content
- Maintains investigative journalism tone
- Cites what's found in archive materials
- Returns 2-3 concrete details per entity

### Data Structure
Enriched biography format:
```json
{
  "entity_id": {
    "display_name": "...",
    "summary": "...",
    "biography": "...",
    "document_context": [
      "Specific detail 1 from documents",
      "Specific detail 2 from documents"
    ],
    "context_metadata": {
      "extraction_date": "2025-11-24T...",
      "documents_analyzed": 3,
      "model": "x-ai/grok-2-1212",
      "confidence": 0.85
    }
  }
}
```

## Estimated Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| 1. Testing & Validation | 30 mins | ⏳ Pending |
| 2. Batch Enrichment (Tier 1) | 30 mins | ⏳ Pending |
| 3. Batch Enrichment (Tier 2) | 45 mins | ⏳ Pending |
| 4. UI Verification | 15 mins | ⏳ Pending |
| 5. Bio Button Fix | 30 mins | ⏳ Pending |
| **Total** | **~2.5 hours** | |

## Risks & Mitigation

### Risk 1: API Rate Limiting
- **Impact**: Slow enrichment process (1 req/sec)
- **Mitigation**: Run in batches, schedule during off-hours
- **Workaround**: Free tier has no hard limits, just slow

### Risk 2: Poor Quality AI Responses
- **Impact**: Generated context may not be useful
- **Mitigation**: Low temperature (0.2), specific prompt, confidence scoring
- **Fallback**: Manual review of top 20, adjust prompt if needed

### Risk 3: Missing Document Context
- **Impact**: Many entities have few/no document mentions
- **Mitigation**: Filter by document_count first, focus on well-documented entities
- **Acceptance**: Some entities will remain without enrichment

## Quality Assurance

### Validation Checks

Each biography is validated for:
1. **Length**: 50-500 words (warnings if outside range)
2. **Entity mention**: Name appears in text
3. **Epstein relationship**: Explicit mention of connection
4. **Speculation level**: Limit on speculative language (<3 instances)
5. **Fact density**: Dates, numbers, specific details present
6. **Vague language**: Minimize "appears to", "possibly", etc. (<3 instances)

### Quality Metrics

- **Quality Score**: 0.0-1.0 (calculated from validation checks)
- **Word Count**: Actual biography length
- **Has Dates**: Boolean (temporal context present)
- **Has Numbers**: Boolean (quantitative facts present)
- **Speculation Count**: Number of speculative terms
- **Vague Language Count**: Number of vague terms

### Manual Review Triggers

Biographies flagged for manual review if:
- Quality score < 0.5
- Word count < 50 words
- No Epstein mention
- High speculation count (>3 instances)
- Excessive vague language (>3 instances)

## Monitoring Progress

### Check Current Status

```bash
# Overall summary (all tiers)
python3 scripts/analysis/generate_bios_by_priority.py --all-tiers --dry-run

# Specific tier details
python3 scripts/analysis/generate_bios_by_priority.py --tier 1 --dry-run

# Database count
sqlite3 data/metadata/entities.db "SELECT COUNT(*) FROM entity_biographies"

# JSON count
python3 -c "import json; data = json.load(open('data/metadata/entity_biographies.json')); print(len(data['entities']))"
```

### Progress Tracking File

Create: `data/metadata/biography_generation_progress.json`

```json
{
  "last_updated": "2025-11-24T15:30:00Z",
  "total_entities": 1637,
  "total_generated": 219,
  "remaining": 1418,
  "tiers": {
    "tier_1": {
      "total": 81,
      "generated": 75,
      "remaining": 6,
      "status": "in_progress",
      "avg_quality_score": 0.82
    },
    "tier_2": {
      "total": 263,
      "generated": 0,
      "remaining": 263,
      "status": "pending"
    },
    "tier_3": {
      "total": 293,
      "generated": 0,
      "remaining": 293,
      "status": "pending"
    },
    "tier_4": {
      "total": 1000,
      "generated": 0,
      "remaining": 1000,
      "status": "pending"
    }
  }
}
```

## Batch Processing Strategy (Tier 4)

For **Tier 4** (1,000 entities), use batch processing across multiple sessions:

```bash
# Session 1: First 200
python3 scripts/analysis/generate_entity_bios_grok.py \
  --source data/metadata/entities_tier4.json \
  --limit 200 --backup

# Session 2: Next 200
python3 scripts/analysis/generate_entity_bios_grok.py \
  --source data/metadata/entities_tier4.json \
  --limit 200 --backup

# Session 3-5: Continue until complete...
```

**Why batch Tier 4?**
- 100+ minutes is long for single session
- Allows for quality review between batches
- Reduces risk of API failures affecting all entities
- Can adjust generation parameters between batches
- Easier to manage checkpoints

## Error Handling

### API Failures

If generation fails:
1. Check checkpoint file: `data/metadata/entity_biographies_grok_checkpoint.json`
2. Review error messages in console output
3. Resume from checkpoint by re-running command with same parameters

### Quality Issues

If biographies have low quality scores:
1. Review validation warnings in output
2. Adjust prompt in `generate_entity_bios_grok.py` (line 129)
3. Re-generate specific low-quality entities
4. Consider manual enrichment for key public figures

### Rate Limiting

If rate limited by API:
1. Increase sleep time in `generate_entity_bios_grok.py` (currently 1 second at line 256)
2. Reduce batch size with `--limit` parameter
3. Spread generation across more sessions

## Next Steps (Quick Start)

### 1. Generate All Tier Files (2 minutes)
```bash
cd /Users/masa/Projects/epstein
python3 scripts/analysis/generate_bios_by_priority.py --all-tiers
```

### 2. Start with Tier 1 (8 minutes)
```bash
python3 scripts/analysis/generate_entity_bios_grok.py \
  --source data/metadata/entities_tier1.json \
  --limit 100 \
  --backup
```

### 3. Review Quality
Check output quality scores and sample a few biographies before proceeding.

### 4. Process Remaining Tiers
Continue with Tier 2, 3, and batch Tier 4 across multiple sessions.

### 5. Mark Complete
Update Linear ticket 1M-184 when all tiers are complete.

## Related Documentation

- **Priority Script**: `/scripts/analysis/generate_bios_by_priority.py`
- **Generation Script**: `/scripts/analysis/generate_entity_bios_grok.py`
- **Entity Statistics**: `/data/metadata/entity_statistics.json`
- **Entity Biographies**: `/data/metadata/entity_biographies.json`
- **Bio Component**: `/frontend/src/components/entity/EntityBio.tsx`
- **Linear Ticket**: https://linear.app/1m-hyperdev/issue/1M-184/bio-enrichment

## Appendix: Command Reference

### Dry Run Examples
```bash
# See what entities are in Tier 1
python3 scripts/analysis/generate_bios_by_priority.py --tier 1 --dry-run

# See all tier summaries
python3 scripts/analysis/generate_bios_by_priority.py --all-tiers --dry-run

# Test generation (no API calls)
python3 scripts/analysis/generate_entity_bios_grok.py \
  --source data/metadata/entities_tier1.json \
  --limit 10 \
  --dry-run
```

### Production Examples
```bash
# Generate Tier 1 with backup
python3 scripts/analysis/generate_entity_bios_grok.py \
  --source data/metadata/entities_tier1.json \
  --limit 100 \
  --backup

# Continue from checkpoint after failure
# Just re-run the same command - it will resume from checkpoint

# Check progress
sqlite3 data/metadata/entities.db \
  "SELECT COUNT(*) FROM entity_biographies"
```

---

**Status**: Ready for Execution
**Deliverable**: Priority-based generation workflow for 1,637 entities
**Last Updated**: 2025-11-24
