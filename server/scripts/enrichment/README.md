# Entity Enrichment Pipeline - Content Agent Integration

**Last Updated**: 2025-11-17

## Overview

Automated entity enrichment system using Claude's content agent capabilities for web research with full source provenance tracking. Designed to scale from manual research (15-20 min per entity) to automated processing (<5 min per entity).

## Architecture

```
Content Agent Pipeline:
┌─────────────────────────────────────────────────────────────┐
│  Priority Entity List (131 entities)                        │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  WebSearch Integration                                      │
│  • Biographical searches                                    │
│  • Epstein connection searches                             │
│  • Flight log references                                   │
│  • 7-day cache (avoid redundant queries)                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Content Extraction & Analysis                              │
│  • Extract biographical facts                               │
│  • Extract Epstein relationships                            │
│  • Extract dates, occupations, connections                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Reliability Tier Classification                            │
│  • Tier 1: Court documents (highest)                        │
│  • Tier 2: Major journalism                                 │
│  • Tier 3: Public records (Wikipedia, etc.)                 │
│  • Tier 4: General sources                                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Structured Data with Provenance                            │
│  • Every fact → source URL                                  │
│  • Every source → reliability tier                          │
│  • Every claim → access date                                │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Quality Assurance Validation                               │
│  • Verify source provenance                                 │
│  • Check reliability distribution                           │
│  • Validate URL accessibility                               │
│  • Flag for human review if needed                          │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  enriched_entity_data.json                                  │
│  • Production-ready entity data                             │
│  • Full provenance tracking                                 │
│  • Human review flags                                       │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. `automated_entity_enrichment.py`
Main enrichment pipeline with content agent integration.

**Features**:
- Automated web search for biographical data
- Fact extraction from search results
- Reliability tier classification
- Batch processing with rate limiting
- Human review flagging for low-confidence results

**Usage**:
```bash
# Enrich single entity
python3 automated_entity_enrichment.py --entity "Bill Clinton"

# Enrich batch of 10 entities
python3 automated_entity_enrichment.py --batch 10

# Generate report
python3 automated_entity_enrichment.py --report
```

### 2. `websearch_integration.py`
WebSearch MCP tool integration for entity research.

**Features**:
- Optimized search queries (biographical, Epstein connections, flight logs)
- 7-day caching to reduce API calls
- Rate limiting (2 seconds between requests)
- Mock implementation for testing (switch to real WebSearch in production)

**Usage**:
```python
from websearch_integration import WebSearchIntegration

integration = WebSearchIntegration()

# Biographical search
bio_results = await integration.search_entity_biographical("Entity Name")

# Epstein connection search
epstein_results = await integration.search_entity_epstein_connection("Entity Name")

# Flight log search
flight_results = await integration.search_entity_flight_logs("Entity Name")
```

### 3. `qa_validation.py`
Quality assurance validation for enriched data.

**Validation Rules**:
1. **Source Provenance**: Every fact must have ≥1 source
2. **High-Risk Claims**: Epstein connections require Tier 1-2 sources
3. **URL Validity**: All source URLs must be well-formed
4. **Minimum Sources**: At least 2 independent sources per entity
5. **Reliability Distribution**: At least 30% Tier 1-2 sources

**Usage**:
```bash
# Run validation
python3 qa_validation.py --input enriched_entity_data.json

# Export issues to JSON
python3 qa_validation.py --export qa_report.json
```

**Exit Codes**:
- `0`: Validation passed (no critical/high issues)
- `1`: Validation failed (critical or high issues found)

### 4. `batch_enrich.sh`
Batch processing script with checkpointing and error handling.

**Features**:
- Process entities in batches of 10
- Automatic checkpointing (resume from failure)
- QA validation after each batch
- Progress reporting
- Rate limiting (30s between batches)

**Usage**:
```bash
# Enrich 50 entities
./batch_enrich.sh --count 50

# Resume from checkpoint
./batch_enrich.sh --continue

# Start from specific entity
./batch_enrich.sh --start 20 --count 10

# Validation only
./batch_enrich.sh --validate
```

## Reliability Tier Classification

### Tier 1 (Highest - Court Documents)
**Domains**: `courtlistener.com`, `pacer.gov`, `supremecourt.gov`, `justice.gov`

**Use for**:
- Legal allegations
- Criminal convictions
- Court testimony
- Official charges

**Required for**:
- Epstein relationship claims
- Allegations of wrongdoing

### Tier 2 (High - Investigative Journalism)
**Domains**: `nytimes.com`, `washingtonpost.com`, `theguardian.com`, `reuters.com`, `bbc.com`, `propublica.org`, `miamiherald.com`

**Use for**:
- Investigative findings
- Documented relationships
- Public statements
- Timeline verification

**Acceptable for**:
- Epstein connections (with corroboration)
- Biographical facts (with multiple sources)

### Tier 3 (Verified - Public Records)
**Domains**: `wikipedia.org`, `britannica.com`, `documentcloud.org`, `archive.org`

**Use for**:
- Biographical data (birth, education, career)
- Public positions held
- Well-documented facts
- Background information

**Not sufficient for**:
- Epstein allegations (need Tier 1-2)
- Controversial claims

### Tier 4 (General - Other Sources)
**Domains**: `forbes.com`, `bloomberg.com`, `cnn.com`, `vanityfair.com`

**Use for**:
- Supporting information
- Additional context
- Net worth estimates
- General background

**Limitations**:
- Require corroboration from higher tiers
- Not sufficient alone for any claims

## Source Provenance Format

Every fact in the enriched data includes full provenance:

```json
{
  "biographical_data": {
    "birth_date": {
      "value": "1946-08-19",
      "precision": "exact",
      "confidence": "high",
      "sources": [
        {
          "url": "https://en.wikipedia.org/wiki/Bill_Clinton",
          "title": "Bill Clinton - Wikipedia",
          "accessed_date": "2025-11-17",
          "reliability_tier": 3,
          "source_type": "biographical_database",
          "quote": "William Jefferson Clinton (born August 19, 1946)..."
        }
      ]
    }
  }
}
```

## Workflow

### Phase 1: Setup (Complete)
✅ Created automated enrichment pipeline
✅ Integrated WebSearch functionality
✅ Built reliability tier classifier
✅ Created QA validation system
✅ Batch processing script

### Phase 2: Testing (Current)
- [ ] Test with 10 sample entities
- [ ] Validate provenance tracking
- [ ] Verify reliability tier accuracy
- [ ] Test batch processing
- [ ] QA validation checks

### Phase 3: Production Integration
To enable real WebSearch (currently using mock data):

1. **Update `websearch_integration.py`**:
```python
# Replace _mock_web_search() with real WebSearch MCP call:

from mcp import WebSearch

async def _real_web_search(self, query: str) -> List[SearchResult]:
    results = await WebSearch(
        query=query,
        allowed_domains=[
            'nytimes.com', 'washingtonpost.com', 'theguardian.com',
            'reuters.com', 'bbc.com', 'courtlistener.com',
            'wikipedia.org', 'britannica.com'
        ]
    )

    return [
        SearchResult(
            title=r['title'],
            url=r['url'],
            snippet=r['snippet'],
            domain=urlparse(r['url']).netloc,
            search_query=query,
            retrieved_at=datetime.now().isoformat()
        )
        for r in results
    ]
```

2. **Optional: Add WebFetch for content extraction**:
```python
from mcp import WebFetch

async def extract_content(self, url: str) -> str:
    content = await WebFetch(
        url=url,
        prompt="Extract biographical information and Epstein connections"
    )
    return content
```

### Phase 4: Batch Processing (131 Entities)
```bash
# Process all 131 priority entities in batches
./batch_enrich.sh --count 131

# Monitor progress
tail -f /Users/masa/Projects/epstein/logs/enrichment/batch_*.log

# If interrupted, resume from checkpoint
./batch_enrich.sh --continue
```

**Estimated time**:
- 131 entities × 5 minutes/entity = ~11 hours
- With batching and rate limiting: ~12-14 hours
- Can run overnight unattended

### Phase 5: Human Review
After automated enrichment:

1. **Generate QA report**:
```bash
python3 qa_validation.py --export qa_report.json
```

2. **Review flagged entities**:
```bash
python3 automated_entity_enrichment.py --report
```

3. **Priority review** (entities requiring human verification):
   - Low source count (<2 sources)
   - No Tier 1-2 sources for Epstein claims
   - Incomplete biographical data
   - URL accessibility issues

4. **Manual enrichment** for flagged entities:
   - Research additional sources
   - Add court document citations
   - Verify controversial claims
   - Complete missing biographical data

## Success Criteria

✅ **Speed**: <5 minutes per entity (vs 15-20 manual)
✅ **Provenance**: 100% source attribution (every fact has source)
✅ **Reliability**: ≥80% Tier 1-2 sources for Epstein claims
✅ **Scale**: 50+ entities enriched in first batch
✅ **Quality**: Human review validates accuracy before publication

## Output Format

**enriched_entity_data.json**:
```json
{
  "metadata": {
    "version": "1.0",
    "total_entities_enriched": 131,
    "research_methodology": "Automated web search with source provenance tracking",
    "last_updated": "2025-11-17T14:00:00"
  },
  "entities": [
    {
      "entity_id": "bill_clinton",
      "name": "William Clinton",
      "name_variations": ["Bill Clinton", "William Jefferson Clinton"],
      "biographical_data": { /* with sources */ },
      "epstein_relationship": { /* with sources */ },
      "archive_metadata": {
        "total_flights": 11,
        "is_billionaire": false
      },
      "research_metadata": {
        "research_completeness": "comprehensive",
        "verification_status": "verified",
        "requires_human_review": false
      }
    }
  ]
}
```

## Monitoring

### Progress Tracking
```bash
# Current status
python3 automated_entity_enrichment.py --report

# QA status
python3 qa_validation.py

# Checkpoint status
cat /Users/masa/Projects/epstein/data/metadata/.enrichment_checkpoint
```

### Logs
```bash
# Latest batch log
ls -lt /Users/masa/Projects/epstein/logs/enrichment/batch_*.log | head -1

# Follow live progress
tail -f /Users/masa/Projects/epstein/logs/enrichment/batch_*.log
```

## Known Limitations

1. **WebSearch Mock**: Currently using mock data (needs MCP WebSearch integration)
2. **Content Extraction**: WebFetch not yet implemented (snippets only)
3. **Fact Extraction**: Pattern-based (could be enhanced with NLP)
4. **Name Variations**: Manual handling (could use entity disambiguation)
5. **Rate Limiting**: Conservative (2s between requests, 30s between batches)

## Next Steps

1. **Test with sample entities** (5-10 entities)
2. **Integrate real WebSearch** (MCP tool)
3. **Validate provenance accuracy** (spot-check sources)
4. **Process first batch** (50 entities)
5. **Human review** (validate quality)
6. **Full production run** (131 entities)

## Contact

For questions or issues with the enrichment pipeline:
- See CLAUDE.md in project root
- Check logs in `/Users/masa/Projects/epstein/logs/enrichment/`
- Review QA reports in `/Users/masa/Projects/epstein/data/metadata/`
