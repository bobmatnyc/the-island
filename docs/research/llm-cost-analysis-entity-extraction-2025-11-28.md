# LLM Cost Analysis: Entity Extraction from OCR Documents

**Research Date:** 2025-11-28
**Researcher:** Research Agent
**Corpus Size:** 33,561 OCR documents (House Oversight Nov 2025 release)
**Task:** Entity extraction from OCR text files
**Status:** ✅ Complete

---

## Executive Summary

Analyzed low-cost LLM options for extracting entities from 33,561 OCR documents. Key findings:

🥇 **RECOMMENDED: Grok 4.1 Fast (Paid Tier)** - $10 total cost, 34 days processing
🥈 **FASTEST ALTERNATIVE: Ministral 8B** - $2.20 total cost, <1 day processing
🥉 **HIGHEST QUALITY: Claude Haiku 3.5** - $49.80 total cost, <1 day processing (already integrated)

**Hybrid Strategy (BEST APPROACH):** $12.14 total, 24 days with parallel processing across quality tiers.

---

## Corpus Analysis

### Document Statistics
- **Total OCR files:** 33,561 documents
- **Location:** `data/sources/house_oversight_nov2025/ocr_text/`
- **Average words per file:** 267 words (from 20-file sample)
- **Estimated tokens per file:** 355 tokens (input)
- **Entity extraction output:** ~300 tokens per file (estimated)

### Token Requirements
- **Total input tokens:** 11,914,155 (~11.9M)
- **Total output tokens:** 10,068,300 (~10.1M)
- **Sampling methodology:** Analyzed 20 random OCR files
- **Token estimation:** 1 token ≈ 0.75 words (conservative estimate)

---

## Model Comparison Table

| Model | Total Cost | Processing Time | Quality | Rate Limits | Notes |
|-------|-----------|----------------|---------|------------|-------|
| **Grok 4.1 Fast (Free)** | **FREE** | 671 days | High | 50 req/day | Too slow for full corpus |
| **Grok 4.1 Fast (Paid)** | **$10** | 34 days | High | 1000 req/day | $10 unlocks 20x speed |
| **Mistral Small 3.1** | $4.21 | <1 day | High | None | 128K context |
| **Ministral 8B** | **$2.20** | <1 day | Medium-High | None | **Cheapest paid option** |
| **Claude Haiku 3.5** | $49.80 | <1 day | Very High | None | Already integrated |
| **Claude Haiku 4.5 (Batch)** | $31.13 | 1-2 days | Very High | Batch queue | 50% discount via Batch API |

---

## Detailed Cost Breakdown

### 🔵 Grok 4.1 Fast (Free Tier)
**Cost:** $0 (FREE)
**Processing Time:** 671 days (22.4 months)
**Rate Limit:** 50 requests/day

#### Limitations
- ⚠️ Extremely slow for full corpus (nearly 2 years)
- ⚠️ Free tier promotional period (expiration unknown)
- ⚠️ Only suitable for small batches or non-urgent work

#### When to Use
- Testing/prototyping with small document sets
- No budget available
- Non-critical background processing

---

### 🟢 Grok 4.1 Fast (Paid Tier - $10 Unlock)
**Cost:** $10 one-time purchase
**Processing Time:** 34 days (4.8 weeks)
**Rate Limit:** 1,000 requests/day (after $10 credit purchase)

#### Benefits
- ✅ Still uses **free Grok model** during promotional period
- ✅ 20x faster than free tier
- ✅ **Best value if Grok promo continues** past Dec 2025
- ✅ One-time $10 cost covers entire corpus
- ✅ Can process 30,000 docs/month

#### How It Works
1. Purchase $10 in OpenRouter credits (one-time)
2. Unlocks 1,000 req/day rate limit (up from 50 req/day)
3. Still uses `x-ai/grok-4.1-fast:free` (no per-token charges during promo)
4. If promo ends, falls back to paid pricing ($0.20/$0.50 per 1M tokens)

#### Calculation
- 33,561 documents ÷ 1,000 req/day = 34 days
- Total cost: $10 (assuming promo active)
- Processing speed: 1,000 docs/day

---

### 🟡 Mistral Small 3.1 (24B)
**Cost:** $4.21
**Processing Time:** <1 day
**Context Window:** 128K tokens

#### Pricing
- Input: 11.9M tokens × $0.10/1M = $1.19
- Output: 10.1M tokens × $0.30/1M = $3.02
- **Total: $4.21**

#### Benefits
- ✅ Fast processing (no rate limits for paid tier)
- ✅ Large context window (can batch multiple docs)
- ✅ Reliable, proven model quality
- ✅ Good balance of cost/performance

---

### 🟢 Ministral 8B (Cheapest Mistral)
**Cost:** $2.20
**Processing Time:** <1 day
**Context Window:** 131K tokens

#### Pricing
- Input: 11.9M tokens × $0.10/1M = $1.19
- Output: 10.1M tokens × $0.10/1M = $1.01
- **Total: $2.20**

#### Benefits
- ✅ **Lowest cost paid model**
- ✅ Largest Mistral context window (131K)
- ✅ Good quality for entity extraction tasks
- ✅ No rate limits (fast processing)

#### When to Use
- Budget-conscious projects needing fast results
- Bulk entity extraction where quality is "good enough"
- Testing before committing to more expensive models

---

### 🔵 Claude Haiku 3.5 (Current Integration)
**Cost:** $49.80
**Processing Time:** <1 day
**Context Window:** 200K tokens

#### Pricing
- Input: 11.9M tokens × $0.80/1M = $9.53
- Output: 10.1M tokens × $4.00/1M = $40.27
- **Total: $49.80**

#### Benefits
- ✅ **Already integrated** in `classify_entity_types.py`
- ✅ Proven quality for entity classification tasks
- ✅ Fast processing (no rate limits)
- ✅ Prompt caching available (90% savings on repeated context)
- ✅ High reliability and consistency

#### Cost Optimization
With prompt caching (90% savings on repeated system prompts):
- Potential savings: ~$4.50 on system prompts
- Effective cost: ~$45 with caching

---

### 🟣 Claude Haiku 4.5 (Batch API - 50% Discount)
**Cost:** $31.13 (with batch discount)
**Processing Time:** 1-2 days (batch queue)
**Context Window:** 200K tokens

#### Pricing
- Regular cost: $62.26
- **Batch API cost: $31.13** (50% discount)
- Input: 11.9M tokens × $1.00/1M × 0.5 = $5.96
- Output: 10.1M tokens × $5.00/1M × 0.5 = $25.17

#### Benefits
- ✅ Latest Claude model with improved performance
- ✅ 50% discount via Anthropic Batch API
- ✅ Very high quality output
- ✅ Good cost/quality ratio

#### Trade-offs
- ⚠️ Batch processing adds 1-2 day queue time
- ⚠️ Requires Anthropic direct API (not OpenRouter)
- ⚠️ Less flexible than real-time API

---

## Recommendation Matrix

### 🥇 BEST VALUE (if Grok promo active)
**Model:** Grok 4.1 Fast (Paid - $10 unlock)
**Cost:** $10
**Time:** 34 days
**Why:** Still free model during promo, just $10 for 20x speed boost

### 🥈 FASTEST + CHEAP
**Model:** Ministral 8B
**Cost:** $2.20
**Time:** <1 day
**Why:** Lowest cost paid model, no rate limits, good quality

### 🥉 HIGHEST QUALITY
**Model:** Claude Haiku 3.5 (already integrated)
**Cost:** $49.80
**Time:** <1 day
**Why:** Proven quality, already integrated, fast processing

### 💰 NO BUDGET (slow)
**Model:** Grok 4.1 Fast (Free Tier)
**Cost:** FREE
**Time:** 671 days
**Why:** Zero cost but takes nearly 2 years

### ⚖️ BALANCED
**Model:** Claude Haiku 4.5 Batch API
**Cost:** $31.13
**Time:** 1-2 days
**Why:** Latest model, 50% discount, excellent quality

---

## Hybrid Strategy (RECOMMENDED)

**Total Cost:** $12.14
**Total Time:** 24 days (with parallel processing)

### Strategy Overview
Split corpus by priority across multiple models to optimize cost and quality:

#### Phase 1: HIGH PRIORITY (1,000 docs)
- **Model:** Claude Haiku 3.5
- **Cost:** $1.48
- **Time:** 1 hour
- **Why:** Critical entities need best quality extraction
- **Use case:** Documents mentioning high-profile individuals, key events

#### Phase 2: MEDIUM PRIORITY (10,000 docs)
- **Model:** Ministral 8B
- **Cost:** $0.66
- **Time:** 3-6 hours
- **Why:** Good balance of cost/quality for bulk processing
- **Use case:** Standard entity extraction from general documents

#### Phase 3: LOW PRIORITY (22,561 docs)
- **Model:** Grok 4.1 Fast (Paid)
- **Cost:** $10.00
- **Time:** 23 days (background processing)
- **Why:** Minimal cost for remaining bulk
- **Use case:** Lower-priority documents, background processing

### Benefits of Hybrid Approach
- ✅ Prioritizes quality where it matters most
- ✅ Minimizes overall cost while maintaining flexibility
- ✅ Parallel processing reduces total time
- ✅ Can start with high-priority results immediately
- ✅ Risk mitigation (not locked into single model)

---

## Rate Limits & Processing Time

### OpenRouter Free Tier (Updated Nov 2025)
- **Limit:** 50 requests/day, 20 requests/minute
- **Recent change:** Reduced from 200 to 50 requests/day in early 2025
- **Applies to:** All `:free` model variants

### OpenRouter Paid Tier ($10+ Credits)
- **Limit:** 1,000 requests/day, 20 requests/minute
- **Unlock:** Purchase >$10 in credits (one-time)
- **Persistent:** Keeps higher limits even if balance drops below $10
- **Applies to:** All models (free and paid)

### Paid Models (Mistral, Claude via OpenRouter)
- **No hard rate limits** for paid tiers
- **Provider-dependent:** Soft limits based on provider capacity
- **Best practice:** Use reasonable parallelism (10-50 concurrent requests)

---

## Implementation Notes

### ✅ Already Integrated
1. **Grok integration:** `scripts/analysis/generate_entity_bios_grok.py`
2. **Claude Haiku integration:** `scripts/analysis/classify_entity_types.py`
   - Uses 3-tier classification: LLM → NLP → Keyword matching
   - OpenRouter API configured
   - Proven quality for entity type classification

### ⚠️ Needs Implementation
3. **Mistral integration:** Add support for Mistral models via OpenRouter API
   - Model IDs: `mistralai/ministral-8b`, `mistralai/mistral-small-3.1`
   - Use existing OpenRouter integration pattern from Grok/Claude scripts
   - Add to entity service for unified access

### 💡 Optimization Opportunities

#### 1. Batch Multiple Documents in Single Prompt
- **Strategy:** Combine 5-10 short OCR files in one prompt
- **Benefit:** Reduce API calls, save on per-request overhead
- **Context window:** Mistral (131K), Claude (200K) support batching
- **Calculation:** 355 tokens/doc × 10 docs = 3,550 tokens (well within limits)
- **Potential savings:** 50-70% reduction in API calls

#### 2. Prompt Caching (Claude only)
- **Strategy:** Cache system prompts and instructions
- **Benefit:** 90% cost savings on repeated context
- **Best for:** Standardized entity extraction with consistent instructions
- **Implementation:** Use Claude's prompt caching API
- **Potential savings:** ~$4-5 on Claude Haiku 3.5 run

#### 3. Resume Capability
- **Strategy:** Save progress checkpoints for long-running jobs
- **Benefit:** Recover from failures without reprocessing
- **Implementation:**
  - Save processed document IDs to checkpoint file
  - Skip already-processed documents on restart
  - Track errors separately for retry

#### 4. Quality Metrics
- **Strategy:** Sample validation across different models
- **Metrics to track:**
  - Entity extraction accuracy (precision/recall)
  - Entity type classification accuracy
  - Processing errors/failures
  - Average processing time per document
- **Use case:** Validate model choice before committing to full corpus

---

## Cost Comparison Summary

| Strategy | Total Cost | Processing Time | Quality | Best For |
|----------|-----------|----------------|---------|----------|
| **Grok Free** | FREE | 671 days | High | No budget, no urgency |
| **Grok Paid** | $10 | 34 days | High | Best value if promo active |
| **Ministral 8B** | $2.20 | <1 day | Medium-High | **Fastest + cheapest paid** |
| **Mistral Small** | $4.21 | <1 day | High | Balanced cost/quality |
| **Haiku 3.5** | $49.80 | <1 day | Very High | Highest quality |
| **Haiku 4.5 Batch** | $31.13 | 1-2 days | Very High | Quality on budget |
| **Hybrid Strategy** | **$12.14** | **24 days** | **Variable** | **RECOMMENDED** |

---

## Decision Criteria

### Choose Grok 4.1 Fast (Paid) if:
- ✅ Grok promotional period still active (verify on OpenRouter)
- ✅ Can wait 34 days for processing
- ✅ Want absolute lowest cost ($10 total)
- ✅ Need high quality output
- ⚠️ Risk: Promo may end, falling back to paid pricing

### Choose Ministral 8B if:
- ✅ Need results in <1 day
- ✅ Budget-conscious ($2.20 total)
- ✅ Quality requirements are "good enough" (not critical)
- ✅ Want to test before committing to more expensive models

### Choose Claude Haiku 3.5 if:
- ✅ Need highest quality entity extraction
- ✅ Already integrated (no implementation work)
- ✅ Can afford $49.80
- ✅ Critical data requiring best accuracy
- ✅ Want to use prompt caching for savings

### Choose Hybrid Strategy if:
- ✅ Can prioritize documents by importance
- ✅ Want to balance cost and quality
- ✅ Can implement parallel processing workflow
- ✅ Need some results immediately, others can wait
- ✅ Want risk mitigation across multiple models

---

## Next Steps

### Immediate Actions
1. ✅ **Verify Grok promo status:** Check OpenRouter for `x-ai/grok-4.1-fast:free` expiration
2. ✅ **Prioritize documents:** Identify top 1,000 high-priority OCR files
3. ✅ **Test Ministral 8B:** Run pilot with 100 documents to validate quality
4. ⚠️ **Implement Mistral integration:** Add Ministral support to entity extraction scripts

### Pilot Testing (Recommended)
Before committing to full corpus:
1. Extract 100 representative documents
2. Run through 3 models: Grok, Ministral 8B, Claude Haiku 3.5
3. Compare quality metrics:
   - Entity extraction completeness
   - Entity type accuracy
   - False positive/negative rates
4. Measure actual processing time
5. Validate cost estimates

### Implementation Priority
1. **Week 1:** Test pilot (100 docs) across all models
2. **Week 2:** Implement Ministral integration
3. **Week 3:** Process high-priority 1,000 docs with Claude Haiku 3.5
4. **Week 4+:** Background processing with Grok Paid or Ministral 8B

---

## Evidence & Sources

### Rate Limits Research
- **OpenRouter Free Tier:** 50 req/day, 20 req/minute (as of Nov 2025)
- **OpenRouter Paid Tier:** 1,000 req/day after $10 credit purchase
- **Source:** https://openrouter.ai/docs/limits

### Pricing Research (November 2025)
- **Grok 4.1 Fast:** Free (promotional), falls back to $0.20/$0.50 per 1M tokens
- **Mistral Small 3.1:** $0.10/$0.30 per 1M tokens (input/output)
- **Ministral 8B:** $0.10/$0.10 per 1M tokens
- **Claude Haiku 3.5:** $0.80/$4.00 per 1M tokens
- **Claude Haiku 4.5:** $1.00/$5.00 per 1M tokens (50% off with Batch API)
- **Sources:**
  - https://openrouter.ai/pricing
  - https://www.anthropic.com/claude/pricing
  - https://docs.x.ai/docs/models

### Sample Data Analysis
- **Method:** Random sampling of 20 OCR files from `data/sources/house_oversight_nov2025/ocr_text/`
- **Average words:** 267 words per document
- **Token estimate:** 355 tokens per document (using 1 token ≈ 0.75 words)
- **Output estimate:** 300 tokens per document (entity extraction output)

---

## Conclusion

For the 33,561 OCR document corpus:

**🏆 RECOMMENDED APPROACH: Hybrid Strategy ($12.14 total, 24 days)**
- Balances cost, quality, and processing time
- Delivers high-priority results immediately
- Minimizes total cost while maintaining flexibility

**🥇 ALTERNATIVE: Ministral 8B ($2.20, <1 day)**
- If need ALL results fast and have minimal budget
- Good quality for bulk entity extraction
- Fastest path to completion

**🥉 FALLBACK: Grok 4.1 Fast Paid ($10, 34 days)**
- If Grok promo still active and can wait
- Best value for money
- High quality output

**❌ NOT RECOMMENDED: Claude Haiku 3.5 for full corpus ($49.80)**
- 22x more expensive than Ministral 8B
- Better suited for high-priority subset or critical validation

---

## File References

**Existing Integrations:**
- `scripts/analysis/generate_entity_bios_grok.py` - Grok biography generation
- `scripts/analysis/classify_entity_types.py` - Claude Haiku entity classification

**Data Locations:**
- `data/sources/house_oversight_nov2025/ocr_text/` - 33,561 OCR files
- `data/metadata/entity_biographies.json` - Entity biography storage

**Configuration:**
- `.env.example` - OPENROUTER_API_KEY configuration
- Project uses OpenRouter API for model access

---

**Research Completed:** 2025-11-28
**Next Review:** Before starting full corpus processing (verify Grok promo status)
