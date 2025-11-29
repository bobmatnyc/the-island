# Seed Article Ingestion Guide

Production-ready script to expand the news archive from 3 → 100+ tier-1 articles.

## Quick Start

```bash
# Activate virtual environment
source ../../.venv/bin/activate

# Install dependencies (one-time)
pip install -r requirements.txt

# Dry run (test without saving)
python ingest_seed_articles.py --source miami-herald --limit 5 --dry-run

# Real ingestion - Miami Herald only
python ingest_seed_articles.py --source miami-herald

# Real ingestion - All tier-1 sources
python ingest_seed_articles.py --all --limit 100

# Resume interrupted run
python ingest_seed_articles.py --resume
```

## Features

### ✅ Data Quality Standards
- **Minimum word count**: 200 words (filters low-quality content)
- **Entity detection**: Must mention at least 1 known entity
- **Link verification**: 404 check with Archive.org fallback
- **Credibility scoring**: Tier-1 sources (0.90-0.98)

### ✅ Reliability
- **Resume capability**: Tracks scraped URLs (`.ingestion_progress.json`)
- **Retry logic**: 3 attempts with exponential backoff for network errors
- **Error isolation**: Individual failures don't stop batch
- **Graceful degradation**: Handles paywalls, 404s, timeouts

### ✅ Performance
- **Processing time**: ~3-5 seconds per article
- **Throughput**: ~15-20 articles per minute
- **100 articles**: ~5-7 minutes with retries
- **Rate limiting**: 1 second between articles (respectful scraping)

## Tier-1 Sources

| Source | Credibility | Priority | Target | Notes |
|--------|------------|----------|--------|-------|
| **Miami Herald** | 0.98 | 1 | 50 | Pulitzer finalist - Julie K. Brown |
| **Associated Press** | 0.95 | 2 | 30 | AP wire coverage |
| **Reuters** | 0.92 | 2 | 30 | Breaking news |
| **NPR** | 0.95 | 3 | 20 | Investigative reporting |

## CLI Reference

### Basic Usage

```bash
# Scrape specific source
python ingest_seed_articles.py --source <source_name>

# Scrape all sources
python ingest_seed_articles.py --all

# Resume previous run
python ingest_seed_articles.py --resume
```

### Options

| Option | Description | Example |
|--------|-------------|---------|
| `--source` | Scrape specific source | `--source miami-herald` |
| `--all` | Scrape all tier-1 sources | `--all` |
| `--resume` | Resume interrupted run | `--resume` |
| `--limit N` | Max articles per source | `--limit 10` |
| `--dry-run` | Test without saving | `--dry-run` |
| `--skip-verification` | Skip link checks (faster) | `--skip-verification` |

### Examples

```bash
# 1. Test with dry run (recommended first step)
python ingest_seed_articles.py --source miami-herald --limit 5 --dry-run

# 2. Scrape Miami Herald articles (high priority)
python ingest_seed_articles.py --source miami-herald

# 3. Scrape all tier-1 sources (limit to 25 each)
python ingest_seed_articles.py --all --limit 25

# 4. Resume interrupted run (automatic skip of scraped URLs)
python ingest_seed_articles.py --resume

# 5. Fast mode (skip verification, for testing)
python ingest_seed_articles.py --source npr --limit 5 --skip-verification
```

## Output

### Progress Tracking

```
Scraping miami-herald: 100%|████████| 10/10 [02:15<00:00, 13.5s/article]

================================================================================
Ingestion Summary:
================================================================================
Source: Miami Herald
Total: 10
Success: 8
Failed: 0
Skipped (already scraped): 2
Quality filtered: 0
Success rate: 80.0%
Elapsed time: 135.2s
Avg time per article: 13.5s
================================================================================
```

### Files Generated

1. **`news_articles_index.json`** (appended)
   - New articles added to existing index
   - Metadata updated (total_articles, date_range, sources)

2. **`.ingestion_progress.json`** (resume tracking)
   - Tracks scraped URLs to avoid re-scraping
   - Automatically created and updated

3. **Backup** (safety)
   - `news_articles_index.json.backup` (created before save)

## Data Quality Validation

### Articles are rejected if:
- ❌ Word count < 200 words
- ❌ No entities mentioned
- ❌ Title missing or < 10 characters
- ❌ Content excerpt < 50 characters
- ❌ Extraction failed (404, timeout, etc.)

### Articles are accepted if:
- ✅ Word count ≥ 200 words
- ✅ At least 1 entity mentioned
- ✅ Valid title and content
- ✅ Successful extraction

## Troubleshooting

### Issue: Connection timeouts
**Symptom**: `ReadTimeoutError` for multiple articles

**Solution**:
```bash
# Use skip-verification for faster processing
python ingest_seed_articles.py --source miami-herald --skip-verification
```

### Issue: Archive.org errors
**Symptom**: `Snapshot returned by CDX API has 5 properties instead of expected 7`

**Solution**: This is a waybackpy bug. The script continues and tries direct extraction.

### Issue: 404 errors
**Symptom**: `HTTP error 404 for URL`

**Solution**: Expected for old/removed articles. Script automatically filters them.

### Issue: Progress not saving
**Symptom**: Re-scrapes same articles on resume

**Solution**:
```bash
# Check progress file exists
ls -la ../../data/metadata/.ingestion_progress.json

# If missing, it will be created on next run
```

### Issue: All articles quality filtered
**Symptom**: `Quality filtered: 10, Success: 0`

**Solution**: Check entity index is loaded correctly:
```bash
ls -la ../../data/md/entities/ENTITIES_INDEX.json
```

## Advanced Usage

### Custom Entity Index Path

```bash
python ingest_seed_articles.py \
  --source miami-herald \
  --entity-index /path/to/ENTITIES_INDEX.json
```

### Custom Data Directory

```bash
python ingest_seed_articles.py \
  --source reuters \
  --data-dir /path/to/data
```

### Combining Options

```bash
# Production run: All sources, resume, 50 articles each
python ingest_seed_articles.py \
  --all \
  --resume \
  --limit 50
```

## Expected Results

### Miami Herald (Priority 1)
- **Target**: 50 articles
- **Expected success rate**: 70-80%
- **Common issues**: Paywalls, 404s on old articles

### AP/Reuters (Priority 2)
- **Target**: 30 articles each
- **Expected success rate**: 80-90%
- **Common issues**: URL format changes, redirects

### NPR (Priority 3)
- **Target**: 20 articles
- **Expected success rate**: 85-95%
- **Common issues**: Rare, high-quality source

### Overall
- **Total target**: 130 articles
- **Expected ingestion**: ~100-110 articles (77-85% success)
- **Time estimate**: ~7-10 minutes for full run

## Data Flow

```
1. Read news_articles_seed.csv
   ↓
2. Filter by source (optional)
   ↓
3. Check .ingestion_progress.json (skip if scraped)
   ↓
4. Verify URL (check live, fallback to archive.org)
   ↓
5. Extract content (trafilatura + beautifulsoup)
   ↓
6. Extract entities (match against ENTITIES_INDEX.json)
   ↓
7. Calculate credibility (source-specific score)
   ↓
8. Validate quality (word count, entities)
   ↓
9. Append to news_articles_index.json
   ↓
10. Update progress tracker
```

## Integration

### With News API Endpoints
The ingested articles are automatically available via:
- `GET /api/news/articles` - List articles with filters
- `GET /api/news/articles/{id}` - Get article details
- `GET /api/news/search` - Search articles by entity/date

### With RAG System
Ingested articles can be embedded for semantic search:
```bash
# After ingestion, embed articles
cd ../rag
python embed_news_articles.py
```

## Best Practices

### 1. Start with Dry Run
Always test with `--dry-run` first:
```bash
python ingest_seed_articles.py --source miami-herald --limit 5 --dry-run
```

### 2. Use Resume for Large Batches
For 100+ articles, use `--resume` to avoid re-scraping on errors:
```bash
python ingest_seed_articles.py --all --limit 100
# If interrupted, resume with:
python ingest_seed_articles.py --resume
```

### 3. Monitor Progress
Watch for quality filtering - if >50% filtered, investigate:
```bash
# Check entity index is valid
python -c "import json; print(len(json.load(open('../../data/md/entities/ENTITIES_INDEX.json'))['entities']))"
```

### 4. Backup Before Large Runs
Backup is automatic, but you can manually backup:
```bash
cp ../../data/metadata/news_articles_index.json \
   ../../data/metadata/news_articles_index.json.manual_backup
```

## Success Criteria

### ✅ Script succeeds if:
- At least 70% success rate
- Quality validation filters < 30%
- Network errors < 20%
- Progress tracking works (resume skips scraped)

### ❌ Investigate if:
- Success rate < 50%
- Quality filtered > 50%
- All articles fail (check dependencies, entity index)
- Progress not saving (check file permissions)

## Support

For issues or questions:
1. Check logs for specific error messages
2. Run with `--dry-run` to test without changes
3. Verify dependencies installed: `pip list | grep -E "trafilatura|requests|tqdm"`
4. Check entity index: `ls -la ../../data/md/entities/ENTITIES_INDEX.json`
