# News Coverage Expansion - Quick Reference

**Quick Summary**: Quick reference guide for rapid lookup of key information.

**Category**: Quick Reference
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Effort**: 2-3 weeks, 40-60 hours
- **Coverage**: Major events 2019-2024, top 50 entities
- **Impact**: Basic news context for RAG queries
- **Effort**: 4-6 weeks, 60-80 hours
- **Coverage**: Comprehensive 2008-2025, top 100 entities

---

**Date**: 2025-11-20
**Status**: Research Complete

---

## Current State vs. Target

```
CURRENT:           TARGET:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Articles:          4              →    200-500      (+4,900%)
Publications:      3              →    15-20        (+400%)
Date Range:        2 years        →    17 years     (+750%)
Entity Coverage:   62 (3.8%)      →    500 (30%)    (+690%)
Top 20 Flyers:     4 (20%)        →    18 (90%)     (+350%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## What "Much More" Means

### 🎯 Minimum Viable (50-100 articles)
- **Effort**: 2-3 weeks, 40-60 hours
- **Coverage**: Major events 2019-2024, top 50 entities
- **Impact**: Basic news context for RAG queries

### 🎯 Recommended Target (200-300 articles)
- **Effort**: 4-6 weeks, 60-80 hours
- **Coverage**: Comprehensive 2008-2025, top 100 entities
- **Impact**: Rich historical context, 30% entity coverage

### 🎯 Aspirational (500+ articles)
- **Effort**: 2-3 months, 100-120 hours
- **Coverage**: Near-complete, international perspectives
- **Impact**: Authoritative news archive, 50%+ entities

---

## Critical Gaps Identified

### 📅 **TIME PERIODS (100% Missing)**
- 2008-2017: First conviction era → **0 articles**
- 2021: Maxwell trial → **0 articles**
- 2022-2024: Recent developments → **0 articles**
- 2025: Ongoing litigation → **0 articles**

### 👤 **KEY ENTITIES (Zero Coverage)**
- **Bill Clinton** (11 flights) - CRITICAL
- **Leslie Wexner** (primary backer, $500M+)
- **Jean-Luc Brunel** (30 flights, MC2 modeling)
- **Leon Black** ($158M payments)
- **Maria Farmer** (first FBI complaint)

### 📰 **MISSING PUBLICATIONS**
- BBC News (Prince Andrew coverage)
- The Guardian (UK perspective)
- New York Times (trial coverage)
- ProPublica (investigations)
- Vanity Fair (profiles)

---

## Expansion Strategy Overview

### Week 1: Quick Wins (→ 50 articles)
```
Day 1-2:  Fix Archive.org API          → +8-12 articles
Day 3-5:  Manual URL curation (2020+)  → +30-40 articles
          Focus: BBC, Guardian, NYT
          Events: Maxwell trial, doc unsealing

RESULT: 4 → 50 articles (1,150% increase)
```

### Week 2: Automation (→ 100 articles)
```
Day 1-3:  Build discovery pipeline     → Discovery tool
Day 4-5:  Entity-based discovery       → +40-50 articles
          Focus: Clinton, Andrew, Wexner, Brunel

RESULT: 50 → 100 articles (2,400% increase)
```

### Week 3: Datasets (→ 150 articles)
```
Day 1-2:  Common Crawl import          → +30-40 articles
Day 3-4:  Hugging Face + Archive.org   → +20-30 articles
Day 5:    Validation + ingestion       → Quality check

RESULT: 100 → 150 articles (3,650% increase)
```

### Week 4: International (→ 200 articles)
```
Day 1-3:  UK sources (BBC, Guardian)   → +30-40 articles
Day 4-5:  Long-form (Vanity Fair, etc) → +15-20 articles

RESULT: 150 → 200 articles (4,900% increase) ✓ TARGET
```

---

## Infrastructure Status

### ✅ **Working**
- Scraper pipeline (3-5s/article)
- Entity extraction (1,637 entities)
- Quality filtering (≥200 words, entities)
- Resume capability
- Vector embedding (5.94 articles/sec)

### ⚠️ **Needs Fixing**
- Archive.org API (CDX format mismatch)
- Processing speed (47s/article → parallelize)

### ❌ **Missing**
- Automated discovery pipeline
- RSS feed monitoring
- Common Crawl integration

---

## Immediate Action Items (This Week)

### Priority 1: Fix Archive.org (Day 1-2)
```bash
# Fix CDX API format handling
cd /Users/masa/Projects/epstein/scripts/ingestion
# Edit link_verifier.py to handle 5-property snapshots
# Re-run: python ingest_seed_articles.py --resume

GAIN: +8-12 articles
```

### Priority 2: Curate Fresh URLs (Day 3-5)
```bash
# Use MCP Browser to find current articles
Search: "Jeffrey Epstein" site:bbc.com after:2020
Search: "Ghislaine Maxwell trial" site:theguardian.com
Search: "Epstein documents unsealed" site:nytimes.com after:2023

# Manually verify 50 URLs
# Add to data/sources/news_articles_seed.csv
# Run: python ingest_seed_articles.py --all

GAIN: +30-40 articles
```

### Priority 3: Build Discovery Tool (Day 6-7)
```python
# Create scripts/ingestion/discover_news_articles.py
# Implement MCP Browser integration for automated search
# Test on: Bill Clinton, Prince Andrew

GAIN: +10-15 articles + automation foundation
```

---

## Resource Requirements Summary

| Phase | Duration | Effort | Outcome |
|-------|----------|--------|---------|
| Week 1 | 5 days | 16-20h | +46 articles (→ 50 total) |
| Week 2 | 5 days | 16-24h | +50 articles (→ 100 total) |
| Week 3 | 5 days | 12-16h | +50 articles (→ 150 total) |
| Week 4 | 5 days | 16-20h | +50 articles (→ 200 total) |
| **TOTAL** | **4 weeks** | **60-80h** | **+196 articles (4,900%)** |

---

## Success Metrics (200-Article Target)

### Quantitative
- [x] **Articles**: 4 → 200 (5,000% increase)
- [x] **Publications**: 3 → 15+ (diverse sources)
- [x] **Date Range**: 2 years → 10+ years (2008-2025)
- [x] **Entity Coverage**: 62 → 500 (30% of database)
- [x] **Top 20 Flyers**: 4 → 18 (90% coverage)

### Qualitative
- [x] Maxwell trial coverage (2021)
- [x] Document unsealing (2024)
- [x] Bill Clinton coverage
- [x] Leslie Wexner coverage
- [x] UK/international perspectives
- [x] Long-form investigative pieces

---

## Risk Mitigation

### URL Accessibility Risk
**Problem**: 56% of old URLs fail (404, paywall)
**Solution**: Focus on 2020-2025 articles (higher success)

### Manual Curation Bottleneck
**Problem**: Finding URLs is time-intensive
**Solution**: Build automated discovery pipeline

### Paywall Restrictions
**Problem**: NYT/WaPo require subscriptions
**Solution**: Archive.org fallback, open-access focus

### Quality vs. Quantity
**Problem**: Pressure to hit numbers
**Solution**: Maintain 200-word, entity-mention filters

---

## Key Entities Needing Coverage

### Political (High Priority)
1. **Bill Clinton** (11 flights) - CRITICAL
2. **Prince Andrew** (18+ allegations)
3. **Donald Trump** (social connections)
4. **George Mitchell** (Senate, flights)

### Financial (High Priority)
5. **Leslie Wexner** ($500M+ to Epstein)
6. **Leon Black** ($158M payments)
7. **Glenn Dubin** (hedge fund, connections)

### Associates (High Priority)
8. **Jean-Luc Brunel** (30 flights, MC2)
9. **Sarah Kellen** (assistant, lawsuits)
10. **Nadia Marcinkova** (125 flights)

### Accusers (Medium Priority)
11. **Maria Farmer** (first FBI report)
12. **Annie Farmer** (trial witness)
13. **Courtney Wild** (CVRA lawsuit)
14. **Sarah Ransome** (2024 memoir)

---

## Publication Priority List

### Tier 1: Must-Have (100+ articles)
- **Miami Herald** (Perversion of Justice)
- **BBC News** (UK perspective)
- **The Guardian** (investigative)
- **New York Times** (trial, legal)
- **ProPublica** (financial)

### Tier 2: Important (30-50 articles)
- **Washington Post** (political)
- **Wall Street Journal** (financial)
- **Vanity Fair** (profiles)
- **Bloomberg** (business)

### Tier 3: Nice-to-Have (10-20 articles)
- **Le Monde** (French perspective)
- **Daily Mail** (UK royal coverage)
- **New Yorker** (long-form)

---

## Next Steps Checklist

### This Week
- [ ] Fix Archive.org CDX API handling
- [ ] Re-run ingestion on existing seed CSV
- [ ] MCP Browser search: BBC, Guardian, NYT (2020-2025)
- [ ] Manually verify 50 URLs
- [ ] Add URLs to seed CSV
- [ ] Run ingestion
- [ ] **Target**: 4 → 50 articles

### Next Week
- [ ] Build discovery pipeline script
- [ ] Test entity-based discovery (5 entities)
- [ ] Run automated discovery
- [ ] Ingest discovered articles
- [ ] **Target**: 50 → 100 articles

### Weeks 3-4
- [ ] Import Common Crawl dataset
- [ ] Import Hugging Face datasets
- [ ] Scrape UK publications
- [ ] Add long-form investigative pieces
- [ ] **Target**: 100 → 200 articles

---

## Contact Points

**Full Analysis**: `docs/research/NEWS_COVERAGE_EXPANSION_ANALYSIS.md`
**Ingestion Script**: `scripts/ingestion/ingest_seed_articles.py`
**Seed Data**: `data/sources/news_articles_seed.csv`
**Progress Tracker**: `data/metadata/.ingestion_progress.json`

---

**Generated**: 2025-11-20
**Type**: Quick Reference
**Status**: Ready for Implementation
