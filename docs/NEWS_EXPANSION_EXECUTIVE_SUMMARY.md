# News Coverage Expansion - Executive Summary

**Quick Summary**: **Research**: Coverage Gap Analysis Complete...

**Category**: Documentation
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **4 articles** covering 62 entities (3.8% of database)
- **3 publications** (Miami Herald, NPR, Reuters)
- **2-year span** (2018-2020)
- **Major gaps**: 2021-2025 events, 96% of entities, key figures
- **200 articles** covering 500 entities (30% of database)

---

**Date**: 2025-11-20  
**Research**: Coverage Gap Analysis Complete  
**Recommendation**: Expand from 4 → 200-500 articles

---

## The Bottom Line

**"Much more for news"** means: **+196 to +496 articles** (4,900-12,400% increase)

### Current State
- **4 articles** covering 62 entities (3.8% of database)
- **3 publications** (Miami Herald, NPR, Reuters)
- **2-year span** (2018-2020)
- **Major gaps**: 2021-2025 events, 96% of entities, key figures

### Recommended Target
- **200 articles** covering 500 entities (30% of database)
- **15+ publications** (tier-1 international sources)
- **17-year span** (2008-2025)
- **Effort**: 4-6 weeks, 60-80 hours

---

## What's Missing (Critical Gaps)

### Time Periods (100% Missing)
- ❌ 2021: Maxwell trial (0 articles)
- ❌ 2022-2024: Sentencing, lawsuits, document releases (0 articles)
- ❌ 2025: Ongoing litigation (0 articles)
- ❌ 2008-2017: First conviction era (0 articles)

### Key Entities (Zero Coverage)
- ❌ **Bill Clinton** (11 flights, major political figure)
- ❌ **Leslie Wexner** (primary financial backer, $500M+)
- ❌ **Jean-Luc Brunel** (30 flights, MC2 modeling agency)
- ❌ **Leon Black** (Apollo Global, $158M payments)
- ❌ **Maria Farmer** (first FBI complaint, 1996)

### Publications Not Represented
- ❌ BBC News (UK perspective, Prince Andrew)
- ❌ The Guardian (international, investigative)
- ❌ New York Times (trial coverage, legal analysis)
- ❌ ProPublica (financial investigations)
- ❌ Vanity Fair (historical profiles)

### Coverage Statistics
- **Top 20 frequent flyers**: Only 4/20 covered (20%)
- **2021-2025 events**: 0% coverage
- **International sources**: 0 articles
- **Long-form investigations**: 1 article (Miami Herald series)

---

## Expansion Plan Overview

### 🎯 Week 1: Quick Wins (4 → 50 articles)
**Days 1-2**: Fix Archive.org integration → +8-12 articles  
**Days 3-5**: Manual URL curation (2020-2025) → +30-40 articles
- Focus: Maxwell trial, document unsealing, recent lawsuits
- Sources: BBC, Guardian, NYT

**Result**: 1,150% increase

### 🎯 Week 2: Automation (50 → 100 articles)
**Days 1-3**: Build discovery pipeline  
**Days 4-5**: Entity-based discovery → +40-50 articles
- Focus: Clinton, Prince Andrew, Wexner, Brunel

**Result**: 2,400% increase

### 🎯 Week 3: Dataset Import (100 → 150 articles)
**Days 1-4**: Common Crawl + Hugging Face → +40-60 articles  
**Day 5**: Validation and ingestion

**Result**: 3,650% increase

### 🎯 Week 4: International (150 → 200 articles)
**Days 1-3**: UK sources (BBC, Guardian) → +30-40 articles  
**Days 4-5**: Long-form (Vanity Fair, ProPublica) → +15-20 articles

**Result**: 4,900% increase ✓ **TARGET ACHIEVED**

---

## Resource Requirements

### Time Investment
- **Week 1**: 16-20 hours (fix + manual curation)
- **Week 2**: 16-24 hours (build discovery pipeline)
- **Week 3**: 12-16 hours (dataset import)
- **Week 4**: 16-20 hours (international + long-form)
- **TOTAL**: 60-80 hours over 4 weeks

### Technical Needs
- ✅ Existing scraper infrastructure (operational)
- ⚠️ Archive.org API fix (4-6 hours)
- ⚠️ Discovery pipeline script (16-24 hours)
- ⚠️ MCP Browser for URL discovery (available)

### Infrastructure Status
- ✅ Scraping: 3-5 seconds/article
- ✅ Entity extraction: 1,637 entities loaded
- ✅ Quality filtering: ≥200 words, entity mentions
- ✅ Vector embedding: 5.94 articles/second
- ⚠️ Archive.org: Needs CDX API fix

---

## Immediate Next Steps (This Week)

### Priority 1: Fix Archive.org (6 hours)
```bash
# Fix CDX API format handling in link_verifier.py
# Re-run ingestion on existing seed CSV
GAIN: +8-12 articles
```

### Priority 2: Curate Fresh URLs (10 hours)
```bash
# MCP Browser searches:
- "Jeffrey Epstein" site:bbc.com after:2020
- "Ghislaine Maxwell trial" site:theguardian.com
- "Epstein documents unsealed" site:nytimes.com after:2023

# Manually verify 50 URLs → Add to seed CSV → Run ingestion
GAIN: +30-40 articles
```

### Priority 3: Discovery Pipeline (8 hours)
```python
# Create scripts/ingestion/discover_news_articles.py
# Test on 5 entities: Clinton, Andrew, Wexner, Brunel, Dershowitz
GAIN: +10-15 articles + automation foundation
```

**Week 1 Target**: 4 → 50 articles

---

## Success Criteria (200-Article Target)

### Quantitative Metrics
| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Total Articles | 4 | 200 | ❌ 2% |
| Publications | 3 | 15+ | ❌ 20% |
| Date Range | 2 years | 10+ years | ❌ 20% |
| Entity Coverage | 62 (3.8%) | 500 (30%) | ❌ 12% |
| Top 20 Flyers | 4 (20%) | 18 (90%) | ❌ 22% |

### Qualitative Goals
- ✓ Maxwell trial coverage (2021)
- ✓ Document unsealing (2024)
- ✓ Bill Clinton coverage
- ✓ Leslie Wexner coverage
- ✓ UK/international perspectives
- ✓ Long-form investigative pieces

---

## Risk Assessment

### High Risk
**URL Accessibility**: 56% of old URLs fail → **Solution**: Focus on 2020-2025  
**Manual Curation**: Finding URLs is time-intensive → **Solution**: Automate discovery

### Medium Risk
**Paywall Restrictions**: NYT/WaPo require subscriptions → **Solution**: Archive.org, open-access  
**Quality vs. Quantity**: Pressure to hit numbers → **Solution**: Maintain quality filters

### Low Risk
**Processing Speed**: 47s/article → **Solution**: Parallelize (future optimization)  
**Storage**: Minimal (~1 GB for 500 articles) → **No action needed**

---

## Key Entities Priority List

### Must Cover (Top 10)
1. **Bill Clinton** (11 flights) - CRITICAL
2. **Prince Andrew** (18+ allegations)
3. **Leslie Wexner** ($500M+ to Epstein)
4. **Jean-Luc Brunel** (30 flights, MC2)
5. **Leon Black** ($158M payments)
6. **Maria Farmer** (first FBI complaint)
7. **Sarah Kellen** (assistant, lawsuits)
8. **Nadia Marcinkova** (125 flights)
9. **Glenn Dubin** (hedge fund connections)
10. **Annie Farmer** (trial witness)

### Should Cover (Next 10)
11. Donald Trump (social connections)
12. George Mitchell (Senate, flights)
13. Courtney Wild (CVRA lawsuit)
14. Sarah Ransome (2024 memoir)
15. Alan Dershowitz (legal, allegations)
16. Adriana Ross (assistant)
17. Lesley Groff (executive assistant)
18. Ken Starr (defense team)
19. Brad Edwards (victim attorney)
20. Vicky Ward (journalist, 2003 profile)

---

## Publication Target List

### Tier 1: Must-Have (100+ articles total)
- Miami Herald (Perversion of Justice) - **PRIORITY 1**
- BBC News (UK perspective, Prince Andrew)
- The Guardian (investigative, international)
- New York Times (trial, legal analysis)
- ProPublica (financial investigations)

### Tier 2: Important (30-50 articles)
- Washington Post (political connections)
- Wall Street Journal (financial investigation)
- Vanity Fair (historical profiles)
- Bloomberg (business, money trail)
- Associated Press (wire coverage)

### Tier 3: Nice-to-Have (10-20 articles)
- Le Monde (French perspective, Brunel)
- Daily Mail (UK, Prince Andrew)
- New Yorker (long-form features)
- Reuters (international wire)
- NPR (investigative reporting)

---

## Comparison: Current vs. Target State

```
METRIC                CURRENT         TARGET (200)    GAIN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Articles              4               200             +4,900%
Publications          3               15              +400%
Date Range            2018-2020       2008-2025       +750%
Entity Coverage       62 (3.8%)       500 (30%)       +690%
Top 20 Flyers         4 (20%)         18 (90%)        +350%
Avg Word Count        2,477           1,500+          Quality maintained
Credibility Avg       0.96            0.85+           Tier-1/2 sources
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Event Coverage Comparison

### Currently Covered (4 articles)
- ✅ 2008 plea agreement (Miami Herald)
- ✅ 2018 Perversion of Justice (Miami Herald)
- ✅ 2019 arrest (NPR)
- ✅ 2020 Maxwell arrest (Reuters)

### Missing Coverage (0 articles)
- ❌ 2019 death investigation
- ❌ 2021 Maxwell trial verdict
- ❌ 2022 Maxwell sentencing
- ❌ 2023 JPMorgan lawsuit ($290M)
- ❌ 2024 document unsealing (Jan 2024)
- ❌ 2024 Sarah Ransome memoir (Feb 2024)
- ❌ 2025 ongoing litigation

---

## Conclusion

### What Success Looks Like

**Minimum Viable** (50-100 articles):
- Major events 2019-2024 covered
- Top 50 entities represented
- 10+ publications
- **Effort**: 2-3 weeks

**Recommended Target** (200-300 articles):
- Comprehensive timeline 2008-2025
- Top 100 entities covered
- 15-20 publications
- 30-50% entity coverage
- **Effort**: 4-6 weeks ← **RECOMMENDED**

**Aspirational** (500+ articles):
- Near-complete coverage
- International perspectives
- 50%+ entity coverage
- **Effort**: 2-3 months

### Recommended Action

**START THIS WEEK**:
1. Fix Archive.org integration (6 hours)
2. Curate 50 fresh URLs from BBC, Guardian, NYT (10 hours)
3. Build discovery pipeline prototype (8 hours)

**WEEK 1 GOAL**: 4 → 50 articles (1,150% increase)

### ROI Analysis

**Time Investment**: 60-80 hours over 4 weeks  
**Output**: +196 articles (4,900% increase)  
**Impact**: 
- Rich RAG context for queries
- Comprehensive entity coverage (30%)
- Historical timeline 2008-2025
- Multi-source verification
- International perspectives

**Cost per Article**: 18-24 minutes of effort  
**Value**: Essential for comprehensive archive context

---

## Documentation

**Full Analysis**: `docs/research/NEWS_COVERAGE_EXPANSION_ANALYSIS.md` (16,000+ words)  
**Quick Reference**: `docs/research/NEWS_EXPANSION_QUICK_REF.md`  
**This Summary**: `NEWS_EXPANSION_EXECUTIVE_SUMMARY.md`

**Ingestion Tools**:
- `scripts/ingestion/ingest_seed_articles.py` (production-ready)
- `scripts/ingestion/scrape_news_articles.py` (core scraper)
- `scripts/rag/embed_news_articles.py` (vector embedding)

**Data Files**:
- `data/sources/news_articles_seed.csv` (20 seed URLs)
- `data/metadata/news_articles_index.json` (4 articles currently)
- `data/metadata/.ingestion_progress.json` (resume tracker)

---

**Generated**: 2025-11-20  
**Research Type**: Coverage Gap Analysis  
**Status**: Ready for Implementation  
**Recommendation**: Proceed with 4-week expansion plan → 200 articles
