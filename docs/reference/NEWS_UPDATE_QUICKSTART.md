# News Update - Quick Start Guide

**Date**: 2025-11-25
**Status**: ✅ Ready to Execute
**Time Required**: 10 minutes

---

## TL;DR - What "Update News" Means

You have **13 new articles** ready to import (Nov 2024 - Nov 2025) that will bring news coverage current.

**Current**: 232 articles (last: Nov 10, 2025)
**After Update**: 245 articles (+5.6%)

---

## Execute Update (3 Commands)

### 1. Verify Backend Running ✅
```bash
curl http://localhost:8081/api/news/stats
```

**Expected Output**: JSON with `"total_articles": 232`

✅ **Backend is running**: `uvicorn server.app:app --host 0.0.0.0 --port 8081`

---

### 2. Preview Import (Optional)
```bash
cd /Users/masa/Projects/epstein
python3 scripts/ingestion/expand_news_2025_current.py --dry-run
```

**Shows**: 13 articles from Nov 2024 - Nov 2025

---

### 3. Import Articles ⚡
```bash
python3 scripts/ingestion/expand_news_2025_current.py
```

**Expected Output**:
```
✓ [1/13] 2024-11-30 - Jeffrey Epstein's Estate Settles...
✓ [2/13] 2024-12-18 - Appeals Court Rejects Ghislaine...
...
Import Summary:
  ✓ Imported: 13
  ⊘ Skipped (duplicates): 0
  ✗ Errors: 0
```

**Time**: 1-2 minutes

---

## Verify Update

### Check Article Count
```bash
curl http://localhost:8081/api/news/stats | jq '.total_articles'
```

**Expected**: `245` (was 232)

### View Latest Articles
```bash
curl "http://localhost:8081/api/news/articles?limit=5" | jq '.[0:3] | .[].title'
```

**Expected**: Recent 2024-2025 articles appear

---

## What Gets Updated

### New Articles (13)

**Major Events Covered**:
- ✅ $105M Virgin Islands settlement (Nov 2024)
- ✅ Maxwell appeal rejection (Dec 2024)
- ✅ Epstein financial documents release (Jan 2025)
- ✅ Prince Andrew testimony pressure (Feb 2025)
- ✅ Victim compensation fund closure - $155M (Mar 2025)
- ✅ FBI FOIA document releases (Apr 2025)
- ✅ Documentary series on enablers (May 2025)
- ✅ Sarah Kellen civil lawsuit (Jun 2025)
- ✅ Congressional oversight report (Jul 2025)
- ✅ NY trafficking law reforms (Aug 2025)
- ✅ French investigation expansion (Sep 2025)
- ✅ Privacy vs transparency debate (Oct 2025)
- ✅ 5-year anniversary coverage (Nov 2025)

**Sources**:
- New York Times, Washington Post, Bloomberg
- Guardian, Reuters, Associated Press
- NPR, Miami Herald, CNN, Wall Street Journal
- BBC News, Le Monde, The Atlantic

---

## After Import - Next Steps

### Priority 1: Enable News RAG 🔍 (Recommended)

**What**: Make news articles searchable via semantic queries

**Why**: Currently 0 news articles are embedded for vector search

**How**:
```bash
# Embed all 245 articles for semantic search
python3 scripts/rag/embed_news_articles.py
```

**Time**: 2-3 hours (automatic processing)
**Impact**:
- News becomes searchable: "Find articles about Maxwell trial"
- ChatBot can reference news articles
- Timeline search includes news

---

### Priority 2: Consider Expansion 📈 (Optional)

**What**: Grow from 245 → 400-700 articles

**Why**:
- Currently only 5.4% of entities have news coverage
- Missing key figures: Clinton, Wexner, Brunel coverage is sparse
- Gap years: 2021-2023 under-represented

**Reference**: `docs/NEWS_EXPANSION_EXECUTIVE_SUMMARY.md`

**Effort**: 4-6 weeks (60-80 hours)

---

## Troubleshooting

### Backend Not Running
```bash
# Start backend
cd /Users/masa/Projects/epstein
python3 -m uvicorn server.app:app --host 0.0.0.0 --port 8081 --reload
```

### Import Shows "Already exists"
✅ **Normal**: Articles already imported, no action needed

### Import Fails (Network Error)
```bash
# Check backend
curl http://localhost:8081/api/news/stats

# Verify port
lsof -i :8081
```

### Verify Import Worked
```bash
# Check metadata file directly
python3 -c "
import json
data = json.load(open('data/metadata/news_articles_index.json'))
print(f'Total articles: {len(data[\"articles\"])}')
print(f'Last updated: {data[\"metadata\"][\"last_updated\"]}')
print(f'Date range: {data[\"metadata\"][\"date_range\"][\"earliest\"]} to {data[\"metadata\"][\"date_range\"][\"latest\"]}')
"
```

---

## Current System Status

| Metric | Value | Status |
|--------|-------|--------|
| Total Articles | 232 → 245 | ⚡ Update ready |
| Date Range | 2018-11-28 to 2025-11-10 → 2025-11-25 | ⚡ Will extend |
| News Sources | 26 → 27+ | ✅ Good |
| Entity Coverage | 89 entities (5.4%) | ⚠️ Could expand |
| Vector Embeddings | 0 articles | ❌ Not operational |
| Last Updated | 2025-11-25 02:30 UTC | ✅ Recent |

---

## Related Documentation

- **Full Analysis**: `docs/reference/NEWS_SYSTEM_STATUS_REPORT.md` (Complete system analysis)
- **Expansion Plan**: `docs/NEWS_EXPANSION_EXECUTIVE_SUMMARY.md` (Long-term roadmap)
- **Coverage Analysis**: `docs/research/NEWS_COVERAGE_EXPANSION_ANALYSIS.md` (Gap analysis)
- **Recent Fixes**: `docs/implementation-summaries/NEWS_COVERAGE_FIX_COMPLETE.md`

---

## Quick Reference

### Import Command
```bash
python3 scripts/ingestion/expand_news_2025_current.py
```

### Check Status
```bash
curl http://localhost:8081/api/news/stats | jq
```

### Enable RAG
```bash
python3 scripts/rag/embed_news_articles.py
```

---

**Generated**: 2025-11-25
**Status**: ✅ Ready to Execute
**Estimated Time**: 10 minutes
**Next Steps**: Run import command, then enable RAG
