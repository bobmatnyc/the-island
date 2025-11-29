# Quick Start Guide - News Article Scraper

## 🚀 Get Started in 5 Minutes

### Prerequisites
```bash
# Install dependencies
pip install requests trafilatura beautifulsoup4 tqdm waybackpy
```

### Step 1: Test Single Article
```bash
cd /Users/masa/Projects/epstein/scripts/ingestion

python scrape_news_articles.py \
  "https://www.example.com" \
  "Example News" \
  "2024-01-15" \
  "../../data/md/entities/ENTITIES_INDEX.json"
```

### Step 2: Start API Server
```bash
cd /Users/masa/Projects/epstein/server
python app.py
```

### Step 3: Dry Run Test
```bash
cd /Users/masa/Projects/epstein/scripts/ingestion

python ingest_news_batch.py \
  ../../data/sources/news_articles_seed.csv \
  --dry-run \
  --limit 5
```

### Step 4: Full Ingestion
```bash
# Ingest all 20 seed articles
python ingest_news_batch.py ../../data/sources/news_articles_seed.csv

# Or with limit for testing
python ingest_news_batch.py ../../data/sources/news_articles_seed.csv --limit 10
```

## 📋 CSV Format

Create `my_articles.csv`:
```csv
url,publication,published_date,title,notes
https://example.com/article,Example News,2024-01-15,Optional Title,Optional notes
```

Required columns: `url`, `publication`

## 🎯 Common Commands

### Dry Run (No API Calls)
```bash
python ingest_news_batch.py articles.csv --dry-run
```

### Limited Batch (First 10)
```bash
python ingest_news_batch.py articles.csv --limit 10
```

### Skip Link Verification (Faster)
```bash
python ingest_news_batch.py articles.csv --skip-verification
```

### Custom API URL
```bash
python ingest_news_batch.py articles.csv --api-url http://localhost:5000
```

## 📊 Expected Output

```
Initializing scraper modules...
Scraper initialized successfully
API URL: http://localhost:8000
Loaded 20 articles from CSV

Ingesting articles: 100%|████████| 20/20 [01:23<00:00,  4.17s/article]

================================================================================
Ingestion Summary:
================================================================================
Total: 20
Success: 18
Failed: 2
Success rate: 90.0%
Elapsed time: 83.4s
Avg time per article: 4.2s
================================================================================
```

## 🐛 Troubleshooting

### "Entity index not found"
```bash
# Check path
ls ../../data/md/entities/ENTITIES_INDEX.json

# Or specify explicitly
python ingest_news_batch.py articles.csv --entity-index /full/path/to/ENTITIES_INDEX.json
```

### "API connection failed"
```bash
# Start server first
cd /Users/masa/Projects/epstein/server
python app.py

# In another terminal, run ingestion
cd /Users/masa/Projects/epstein/scripts/ingestion
python ingest_news_batch.py articles.csv
```

### Check Errors
```bash
# Errors logged to JSON file
cat articles_errors.json
```

## 📈 Performance

- **Single article**: 2-3 seconds
- **Batch (100 articles)**: 5-7 minutes
- **Success rate**: 90-95% for mainstream sites

## 🔍 What Gets Extracted

- ✅ Article title, author, date
- ✅ Full text content and word count
- ✅ Entity mentions (Jeffrey Epstein, Ghislaine Maxwell, etc.)
- ✅ Credibility score (0.0-1.0)
- ✅ Paywall detection
- ✅ Archive.org fallback for dead links

## 📚 More Info

See `README.md` for:
- Detailed module documentation
- API integration guide
- Source credibility tiers
- Error handling details
- Future enhancements

---

**Ready to scale?** Process hundreds of articles by creating a larger CSV file and running the batch ingestion script.
