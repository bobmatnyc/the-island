# News Articles Deduplication - Implementation Summary

**Date**: 2025-11-25
**Type**: Data Cleanup
**Status**: ✅ Complete

## Overview

Successfully removed 19 duplicate news articles from the database, reducing the total from 245 to 226 unique articles. The deduplication script identifies exact duplicates based on (title, url, published_date) tuples and properly recalculates all metadata.

## Problem Statement

After running the news import script multiple times, the database accumulated duplicate entries. Articles were imported 2-3 times each, resulting in:
- **Original count**: 245 articles (including duplicates)
- **Duplicate count**: 19 duplicate entries
- **Expected after cleanup**: 226 unique articles

The import script lacked duplicate detection, causing re-imports to add the same articles multiple times.

## Solution

### Script Created: `deduplicate_news_articles.py`

**Location**: `/Users/masa/Projects/epstein/scripts/data/deduplicate_news_articles.py`

**Strategy**:
1. Group articles by (title, url, published_date) - unique identifier tuple
2. Keep first occurrence of each unique article
3. Remove all subsequent duplicates
4. Recalculate metadata (totals, date ranges, source counts)
5. Create backup before any modifications
6. Log all deletions for audit trail

**Design Decision**: Simple exact-match deduplication
- **Rationale**: Articles with identical title, URL, and publication date are definitively duplicates from re-imports
- **Trade-offs**:
  - Performance: O(n) single pass with dictionary lookup
  - Accuracy: 100% for exact duplicates, won't catch near-duplicates
  - Safety: Creates timestamped backup before modifications

## Duplicate Articles Removed

### Breakdown by Article (19 total duplicates)

1. **Appeals Court Rejects Ghislaine Maxwell's Bid to Overturn Sentence** (2 duplicates)
   - Washington Post, 2024-12-18

2. **Congressional Report Examines Failures in Epstein Case Oversight** (1 duplicate)
   - CNN, 2025-07-25

3. **Documentary Series Examines Epstein's Network and Enablers** (1 duplicate)
   - NPR, 2025-05-08

4. **Epstein Victim Compensation Fund Concludes After Distributing $125M** (2 duplicates)
   - Reuters, 2025-03-20

5. **FBI Releases Additional Files on Epstein Investigation Under FOIA** (2 duplicates)
   - Associated Press, 2025-04-15

6. **Five Years After Epstein's Death, Questions About Prison Security Remain** (1 duplicate)
   - BBC News, 2025-11-10

7. **Former Epstein Associate Faces New Civil Lawsuit in Florida** (1 duplicate)
   - Miami Herald, 2025-06-12

8. **French Authorities Expand Investigation Into Epstein's Paris Connections** (1 duplicate)
   - Le Monde, 2025-09-18

9. **Jeffrey Epstein's Estate Settles With U.S. Virgin Islands for $105M** (2 duplicates)
   - New York Times, 2024-11-30

10. **Legal Scholars Debate Privacy vs. Transparency in Unsealing Documents** (1 duplicate)
    - The Atlantic, 2025-10-05

11. **New York Strengthens Laws on Sex Trafficking Following Epstein Case** (1 duplicate)
    - Wall Street Journal, 2025-08-14

12. **Newly Released Epstein Documents Shed Light on Financial Network** (2 duplicates)
    - Bloomberg, 2025-01-09

13. **Prince Andrew Faces New Pressure to Testify in U.S. Civil Cases** (2 duplicates)
    - The Guardian, 2025-02-14

## Results

### Before Deduplication
- **Total articles**: 245
- **Total sources**: 26
- **Date range**: 2018-11-28 to 2025-11-10
- **Metadata status**: Stale (counted duplicates)

### After Deduplication
- **Total articles**: 226 unique articles
- **Total sources**: 26 (unchanged)
- **Date range**: 2018-11-28 to 2025-11-10 (unchanged)
- **Metadata status**: Accurate (recalculated from deduplicated data)
- **Duplicates removed**: 19 entries (7.8% reduction)

### Source Count Changes (Duplicates Removed)

Source counts decreased for publications that had duplicate articles:
- **NPR**: 31 → 30 (-1)
- **The Washington Post**: 14 → 12 (-2)
- **The Guardian**: 38 → 36 (-2)
- **CNN**: 11 → 10 (-1)
- **The New York Times**: 20 → 18 (-2)
- **BBC News**: 29 → 28 (-1)
- **The Wall Street Journal**: 5 → 4 (-1)
- **Reuters**: 20 → 18 (-2)
- **Associated Press**: 9 → 7 (-2)
- **Miami Herald**: 12 → 11 (-1)
- **Bloomberg**: 3 → 1 (-2)
- **Le Monde**: 2 → 1 (-1)
- **The Atlantic**: 2 → 1 (-1)

## Implementation Details

### Key Functions

```python
def find_duplicates(articles: list) -> tuple[list, list]:
    """
    Find duplicate articles based on (title, url, published_date).

    Time Complexity: O(n) - single pass through articles
    Space Complexity: O(n) - dictionary to track seen articles
    """
    # Groups articles by unique identifier tuple
    # Returns (unique_articles, duplicate_articles)
```

```python
def recalculate_metadata(articles: list) -> dict:
    """
    Recalculate metadata from deduplicated articles.

    Updates:
    - total_articles: Actual count of unique articles
    - sources: Per-publication article counts
    - date_range: Earliest to latest publication dates
    - last_updated: Timestamp of metadata recalculation

    Complexity: O(n) - single pass through articles
    """
```

### Metadata Recalculation

**Critical Fix**: The original script removed duplicate articles but didn't update the metadata, causing the API to report stale counts. The updated script now:

1. Recounts total articles from deduplicated list
2. Recalculates source counts (articles per publication)
3. Recomputes date range from remaining articles
4. Updates last_updated timestamp

**Why This Matters**: The backend's `NewsService` reads metadata from the JSON file for API responses. Without recalculation, the API would continue reporting old counts even after deduplication.

### Backup Strategy

**Automatic Backups**: Every run creates timestamped backup
- **Format**: `news_articles_index_backup_YYYYMMDD_HHMMSS.json`
- **Location**: `data/metadata/`
- **Example**: `news_articles_index_backup_20251125_091233.json`

**Recovery**: Restore from any backup
```bash
cp data/metadata/news_articles_index_backup_20251125_091233.json \
   data/metadata/news_articles_index.json
```

## Backend Integration

### Caching Behavior

The backend's `NewsService` class caches the news index in memory:

```python
class NewsService:
    def load_news_index(self) -> NewsArticlesIndex:
        if self._index is not None:
            return self._index  # Returns cached index
```

**Important**: After running deduplication, restart the backend to clear the cache:

```bash
pkill -9 -f "uvicorn server.app:app"
uvicorn server.app:app --host 0.0.0.0 --port 8081 --reload
```

### Verification

After restart, verify the API reflects deduplicated counts:

```bash
curl -s "http://localhost:8081/api/news/stats" | python3 -m json.tool
```

Expected output:
```json
{
  "total_articles": 226,
  "total_sources": 26,
  "date_range": {
    "earliest": "2018-11-28",
    "latest": "2025-11-10"
  }
}
```

## Lessons Learned

### Root Cause: Import Script Lacks Duplicate Detection

The original import script didn't check for existing articles before adding new ones:

```python
# Import script behavior (needs fixing)
def import_article(article_data):
    # ❌ No check for existing article
    articles.append(article_data)  # Adds blindly
```

**Future Prevention**: The import script should be updated to:
1. Check if article with same (title, url, date) already exists
2. Skip import if duplicate detected
3. Log skipped duplicates for visibility

### Metadata Consistency

**Lesson**: When modifying article data, always recalculate metadata. The metadata serves as an index/cache for the API and must stay synchronized with the actual article count.

**Implementation**: Any script that modifies the articles array must:
```python
data["articles"] = modified_articles
data["metadata"] = recalculate_metadata(modified_articles)  # Critical!
```

## Usage

### Running Deduplication

```bash
cd /Users/masa/Projects/epstein
python3 scripts/data/deduplicate_news_articles.py
```

### Script Output

The script provides detailed logging:
- Original article count
- Number of duplicates found
- Detailed list of each duplicate removed
- Backup file location
- New metadata calculations
- Completion summary

### Idempotent Operation

The script is safe to run multiple times:
- If no duplicates exist, it exits without modifications
- Creates new backup each run for safety
- Validates counts before and after deduplication

## Files Modified

### Created
- `/Users/masa/Projects/epstein/scripts/data/deduplicate_news_articles.py` - Deduplication script

### Modified
- `/Users/masa/Projects/epstein/data/metadata/news_articles_index.json` - Deduplicated articles + updated metadata

### Backups Created
- `/Users/masa/Projects/epstein/data/metadata/news_articles_index_backup_20251125_091002.json` - First backup
- `/Users/masa/Projects/epstein/data/metadata/news_articles_index_backup_20251125_091233.json` - Final backup

## Success Criteria

- ✅ Backup created before modifications
- ✅ 19 duplicate entries removed
- ✅ 226 unique articles remain
- ✅ No data loss (only duplicates removed)
- ✅ Metadata recalculated and synchronized
- ✅ API stats reflect correct count (226)
- ✅ Date range preserved (2018-11-28 to 2025-11-10)
- ✅ All 26 sources still represented
- ✅ Backend successfully restarted and cache cleared

## Next Steps

### Immediate
- ✅ Deduplication complete
- ✅ Backend restarted
- ✅ API verified

### Future Improvements

1. **Update Import Script**: Add duplicate detection to prevent future duplicates
2. **Add Pre-Import Validation**: Check for existing articles before import
3. **Implement Article Fingerprinting**: Consider fuzzy matching for near-duplicates
4. **Add Monitoring**: Track import statistics (new, skipped, duplicate)
5. **Document Import Process**: Create guidelines for adding new articles

## References

- **Script**: `/Users/masa/Projects/epstein/scripts/data/deduplicate_news_articles.py`
- **Data File**: `/Users/masa/Projects/epstein/data/metadata/news_articles_index.json`
- **News Service**: `/Users/masa/Projects/epstein/server/services/news_service.py`
- **API Endpoint**: `GET /api/news/stats`

---

**Completion Date**: 2025-11-25
**Net LOC Impact**: +175 lines (new deduplication script)
**Data Impact**: -19 duplicate articles (7.8% reduction)
**Status**: ✅ Complete and verified
