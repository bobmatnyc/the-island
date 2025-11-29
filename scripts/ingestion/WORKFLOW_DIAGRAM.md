# Seed Article Ingestion - Workflow Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SEED ARTICLE INGESTION                      │
│                  Expand from 3 → 100+ articles                  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────┐
        │   INPUT: news_articles_seed.csv        │
        │   19 tier-1 articles (curated list)    │
        └────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────┐
        │   FILTER: Source Selection             │
        │   --source miami-herald OR --all       │
        └────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────┐
        │   CHECK: Resume Progress               │
        │   Skip already-scraped URLs            │
        └────────────────────────────────────────┘
                                 │
                                 ▼
                       ┌─────────────────┐
                       │  PER ARTICLE:   │
                       └─────────────────┘
                                 │
                ┌────────────────┼────────────────┐
                ▼                ▼                ▼
        [Verify URL]     [Extract Content]  [Extract Entities]
        • Check 404      • Trafilatura      • Match ENTITIES_INDEX
        • Archive.org    • Metadata         • Count mentions
        • Retry x3       • Detect paywall   • 1637 entities
                                 │
                                 ▼
                       [Calculate Credibility]
                       • Source-based score
                       • 0.90-0.98 tier-1
                                 │
                                 ▼
                       [Validate Quality]
                       • ≥200 words
                       • ≥1 entity
                       • Valid title
                                 │
                ┌────────────────┼────────────────┐
                ▼                                 ▼
         [✓ ACCEPT]                          [✗ REJECT]
                │                                 │
                ▼                                 ▼
    Append to index                    Quality filtered
                                       (logged for review)
                                 │
                                 ▼
        ┌────────────────────────────────────────┐
        │  OUTPUT: news_articles_index.json      │
        │  Updated with new articles             │
        └────────────────────────────────────────┘
                                 │
                                 ▼
        ┌────────────────────────────────────────┐
        │  PROGRESS: .ingestion_progress.json    │
        │  Track scraped URLs for resume         │
        └────────────────────────────────────────┘
```

## Detailed Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1: INITIALIZATION                                             │
├─────────────────────────────────────────────────────────────────────┤
│  • Load ENTITIES_INDEX.json (1637 entities)                         │
│  • Load news_articles_seed.csv (19 articles)                        │
│  • Load .ingestion_progress.json (resume tracker)                   │
│  • Load news_articles_index.json (current articles)                 │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 2: URL VERIFICATION (if enabled)                              │
├─────────────────────────────────────────────────────────────────────┤
│  1. HTTP HEAD request (timeout: 10s)                                │
│  2. If timeout: Retry with exponential backoff (3 attempts)         │
│  3. If 404: Query archive.org (waybackpy)                           │
│  4. If archived: Use archive URL for extraction                     │
│  5. If dead: Continue, mark as "removed"                            │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 3: CONTENT EXTRACTION (trafilatura + beautifulsoup)           │
├─────────────────────────────────────────────────────────────────────┤
│  • Extract full text (article body)                                 │
│  • Extract metadata (title, author, date)                           │
│  • Generate excerpt (first 200 chars)                               │
│  • Count words                                                      │
│  • Detect paywall (presence of paywall indicators)                  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 4: ENTITY EXTRACTION                                          │
├─────────────────────────────────────────────────────────────────────┤
│  • Match entities from ENTITIES_INDEX.json                          │
│  • Search full names (e.g., "Jeffrey Epstein")                      │
│  • Search aliases (e.g., "Epstein", "Jeff Epstein")                 │
│  • Count mentions per entity                                        │
│  • Return list of unique entities + mention counts                  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 5: CREDIBILITY SCORING                                        │
├─────────────────────────────────────────────────────────────────────┤
│  Source-based scores (tier-1):                                      │
│  • Miami Herald: 0.98 (Pulitzer finalist)                           │
│  • Associated Press: 0.95                                           │
│  • Reuters: 0.92                                                    │
│  • NPR: 0.95                                                        │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 6: QUALITY VALIDATION                                         │
├─────────────────────────────────────────────────────────────────────┤
│  ✓ ACCEPT if:                        ✗ REJECT if:                  │
│  • Word count ≥ 200                  • Word count < 200             │
│  • Entities mentioned ≥ 1            • No entities mentioned        │
│  • Title present (≥10 chars)         • Title missing or too short   │
│  • Content excerpt present           • Content missing              │
│  • Extraction successful             • Extraction failed            │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                ┌────────────────┼────────────────┐
                ▼                                 ▼
         [✓ ACCEPTED]                       [✗ REJECTED]
                │                                 │
                ▼                                 ▼
┌──────────────────────────┐          ┌──────────────────────────┐
│  APPEND TO INDEX         │          │  QUALITY FILTERED        │
│  • Generate article ID   │          │  • Log reason            │
│  • Convert to schema     │          │  • Track in stats        │
│  • Add to articles[]     │          │  • Mark as scraped       │
│  • Update metadata       │          │  • Continue to next      │
└──────────────────────────┘          └──────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 7: SAVE AND UPDATE                                            │
├─────────────────────────────────────────────────────────────────────┤
│  1. Create backup: news_articles_index.json.backup                  │
│  2. Update metadata:                                                │
│     • total_articles (increment)                                    │
│     • date_range (recalculate earliest/latest)                      │
│     • sources (article count by publication)                        │
│     • last_updated (current timestamp)                              │
│  3. Atomic write: temp file → replace original                      │
│  4. Update progress: add URL to .ingestion_progress.json            │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 8: RATE LIMITING & NEXT ARTICLE                               │
├─────────────────────────────────────────────────────────────────────┤
│  • Sleep 1 second (respectful scraping)                             │
│  • Continue to next article                                         │
│  • Repeat steps 2-8 until all articles processed                    │
└─────────────────────────────────────────────────────────────────────┘
```

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  ERROR SCENARIOS                                                    │
└─────────────────────────────────────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
  [NETWORK ERROR]         [EXTRACTION ERROR]      [QUALITY ERROR]
        │                        │                        │
        ▼                        ▼                        ▼
┌──────────────┐         ┌──────────────┐        ┌──────────────┐
│ Retry Logic  │         │ Skip Article │        │ Filter + Log │
│ • 3 attempts │         │ • Log error  │        │ • Continue   │
│ • Exp. back. │         │ • Mark fail  │        │ • Track stat │
│ • Archive.org│         │ • Continue   │        │ • No retry   │
└──────────────┘         └──────────────┘        └──────────────┘
        │                        │                        │
        └────────────────────────┴────────────────────────┘
                                 │
                                 ▼
                         [LOG AND CONTINUE]
                         • Individual failures
                           don't stop batch
                         • All errors logged
                         • Stats tracked
```

## Data Flow Diagram

```
INPUT FILES                    PROCESSING                   OUTPUT FILES
─────────────────────────────────────────────────────────────────────────

news_articles_seed.csv ───┐
                          │
ENTITIES_INDEX.json ──────┼───► [SCRAPER] ──────┐
                          │         │           │
.ingestion_progress.json ─┘         │           ├─► news_articles_index.json
                                    │           │   (3 → 100+ articles)
                                    │           │
                                    │           └─► .ingestion_progress.json
                                    │               (updated with scraped URLs)
                                    │
                                    ▼
                            [LOGGING OUTPUT]
                            • Progress bars (tqdm)
                            • Success/failure stats
                            • Error messages
                            • Quality filter reasons
```

## Resume Capability Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  RESUME WORKFLOW                                                    │
└─────────────────────────────────────────────────────────────────────┘

  [START INGESTION]
         │
         ▼
  Load .ingestion_progress.json
         │
         ▼
  For each article URL:
         │
         ├─► URL in scraped_urls? ──YES─► Skip (logged)
         │                          │
         NO                         │
         │                          │
         ▼                          │
  Scrape article                    │
         │                          │
         ▼                          │
  Add URL to scraped_urls           │
         │                          │
         ▼                          │
  Save progress                     │
         │                          │
         └──────────────────────────┘
                    │
                    ▼
         [ALL ARTICLES PROCESSED]

BENEFIT: If interrupted (Ctrl+C, error, crash), resume with:
         python ingest_seed_articles.py --resume
         → Skips already-scraped URLs automatically
```

## Performance Characteristics

```
┌─────────────────────────────────────────────────────────────────────┐
│  PROCESSING TIMELINE (per article)                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  0s ──────────► 1s ──────────► 3s ──────────► 3.2s ────► 3.5s      │
│   │             │               │               │         │         │
│   │             │               │               │         │         │
│   Start    Verify URL    Extract Content  Entities  Credibility    │
│              (1s)           (1-2s)         (0.2s)    (<0.01s)      │
│                                                                      │
│  Timeline:                                                           │
│  ┌────┬─────────────┬───────┬──┬┐                                  │
│  │ V  │      E      │   EN  │C ││  = 3-5 seconds per article       │
│  └────┴─────────────┴───────┴──┴┘                                  │
│                                                                      │
│  V  = Verify URL (1s)                                               │
│  E  = Extract content (1-2s)                                        │
│  EN = Extract entities (0.2s)                                       │
│  C  = Calculate credibility (<0.01s)                                │
│                                                                      │
│  + 1s rate limiting between articles                                │
└─────────────────────────────────────────────────────────────────────┘

THROUGHPUT:
  • 1 article: ~4-6 seconds (with rate limit)
  • 10 articles: ~40-60 seconds (~1 minute)
  • 50 articles: ~200-300 seconds (~4-5 minutes)
  • 100 articles: ~400-600 seconds (~7-10 minutes)

BOTTLENECKS:
  1. Network requests (URL verification + content fetch)
  2. Archive.org lookups (when URLs dead)
  3. Rate limiting (1s between articles)

OPTIMIZATION OPTIONS:
  --skip-verification: Skip URL checks (~2-3s per article, 40% faster)
  Future: asyncio parallel processing (3-5x speedup potential)
```

## Quality Metrics

```
┌─────────────────────────────────────────────────────────────────────┐
│  EXPECTED OUTCOMES (100 articles)                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  INPUT: 100 articles                                                │
│    │                                                                 │
│    ├─► 77-85 ACCEPTED ─┐                                            │
│    │                   │                                            │
│    │                   ├─► ✓ Word count ≥ 200                       │
│    │                   ├─► ✓ Entities ≥ 1                           │
│    │                   ├─► ✓ Valid metadata                         │
│    │                   └─► ✓ Successfully scraped                   │
│    │                                                                 │
│    └─► 15-23 REJECTED ─┐                                            │
│                        │                                            │
│                        ├─► 404 errors (10-15%)                      │
│                        ├─► Low word count (2-5%)                    │
│                        ├─► No entities (1-3%)                       │
│                        └─► Extraction failures (2-5%)               │
│                                                                      │
│  SUCCESS RATE: 77-85%                                               │
│  QUALITY FILTER RATE: 15-23%                                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  EPSTEIN ARCHIVE ECOSYSTEM                                          │
└─────────────────────────────────────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
┌──────────────┐         ┌──────────────┐        ┌──────────────┐
│  INGEST      │         │  STORAGE     │        │  API         │
│              │         │              │        │              │
│ • Scraper    │────────►│ • JSON Index │───────►│ • /articles  │
│ • Entities   │         │ • Metadata   │        │ • /search    │
│ • Quality    │         │ • Progress   │        │ • /sources   │
└──────────────┘         └──────────────┘        └──────────────┘
                                                         │
                                                         ▼
                                                  ┌──────────────┐
                                                  │  RAG         │
                                                  │              │
                                                  │ • Embedding  │
                                                  │ • Semantic   │
                                                  │   Search     │
                                                  └──────────────┘
```

## CLI Usage Visual

```
┌─────────────────────────────────────────────────────────────────────┐
│  COMMAND LINE INTERFACE                                             │
└─────────────────────────────────────────────────────────────────────┘

BASIC:
  python ingest_seed_articles.py --source miami-herald
                                  └──────┬──────┘
                                  Source selection

WITH LIMIT:
  python ingest_seed_articles.py --all --limit 100
                                  └─┬─┘  └───┬───┘
                                    │        │
                              All sources  Max per source

WITH RESUME:
  python ingest_seed_articles.py --resume
                                  └───┬───┘
                                      │
                              Continue previous run

DRY RUN (TESTING):
  python ingest_seed_articles.py --source npr --limit 5 --dry-run
                                  └──┬───┘  └──┬──┘  └───┬───┘
                                     │         │          │
                                  Source    Limit    No changes

FAST MODE:
  python ingest_seed_articles.py --all --skip-verification
                                  └─┬─┘  └────────┬────────┘
                                    │              │
                               All sources    Skip URL checks
                                              (40% faster)
```

## Summary

**Input**: 19 curated tier-1 articles (seed CSV)
**Processing**: Scrape → Extract → Validate → Score → Save
**Output**: 100-110 articles (77-85% success rate)
**Time**: 7-10 minutes for full run
**Quality**: Tier-1 sources, 0.90-0.98 credibility, entity-linked
**Reliability**: Resume capability, error handling, atomic saves
