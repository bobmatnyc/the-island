# Entity Enrichment - Quick Start Guide

## 5-Minute Setup

### 1. Test the Pipeline (Mock Data)
Test the enrichment pipeline with mock search results:

```bash
cd /Users/masa/Projects/epstein/server/scripts/enrichment

# Test single entity
python3 automated_entity_enrichment.py --entity "Band, Doug"

# Test WebSearch integration
python3 websearch_integration.py

# Test QA validation
python3 qa_validation.py
```

### 2. Run Small Batch (10 Entities)
Process first 10 priority entities:

```bash
# Batch enrichment
./batch_enrich.sh --count 10

# Check results
python3 automated_entity_enrichment.py --report

# Validate quality
python3 qa_validation.py --export qa_report.json
```

### 3. Review Results
```bash
# View enriched data
cat /Users/masa/Projects/epstein/data/metadata/enriched_entity_data.json | jq '.entities[] | {name, research_completeness: .research_metadata.research_completeness}'

# View QA report
cat /Users/masa/Projects/epstein/data/metadata/qa_report.json | jq '.by_severity'
```

## Production Setup (Real WebSearch)

### 1. Enable WebSearch MCP Tool

**Option A: Use existing MCP WebSearch** (already configured)
```python
# In websearch_integration.py, replace _mock_web_search() with:

from mcp import WebSearch  # This is already available!

async def _real_web_search(self, query: str) -> List[SearchResult]:
    # Call Claude's WebSearch MCP tool
    results = await WebSearch(
        query=query,
        allowed_domains=[
            'nytimes.com', 'washingtonpost.com', 'theguardian.com',
            'reuters.com', 'bbc.com', 'npr.org',
            'courtlistener.com', 'pacer.gov',
            'wikipedia.org', 'britannica.com'
        ]
    )

    return [SearchResult(...) for r in results]
```

**Option B: Use Brave Search API** (free tier: 2000 req/month)
1. Get API key: https://brave.com/search/api/
2. Set environment variable: `export BRAVE_SEARCH_API_KEY=your_key`
3. Update `websearch_integration.py` to use Brave API

### 2. Production Run
```bash
# Process all 131 entities
./batch_enrich.sh --count 131

# Monitor progress
tail -f /Users/masa/Projects/epstein/logs/enrichment/batch_*.log

# Resume if interrupted
./batch_enrich.sh --continue
```

## Common Tasks

### Enrich Specific Entity
```bash
python3 automated_entity_enrichment.py --entity "Bill Clinton"
```

### Check Progress
```bash
# How many entities enriched?
jq '.metadata.total_entities_enriched' /Users/masa/Projects/epstein/data/metadata/enriched_entity_data.json

# Which entities need review?
jq '.entities[] | select(.research_metadata.requires_human_review == true) | .name' /Users/masa/Projects/epstein/data/metadata/enriched_entity_data.json
```

### Resume From Checkpoint
```bash
# See current checkpoint
cat /Users/masa/Projects/epstein/data/metadata/.enrichment_checkpoint

# Resume from checkpoint
./batch_enrich.sh --continue
```

### Validate Quality
```bash
# Run QA checks
python3 qa_validation.py

# Export issues for review
python3 qa_validation.py --export qa_issues.json

# View critical issues
jq '.issues[] | select(.severity == "critical")' qa_issues.json
```

## Expected Output

### After 10-Entity Batch:
```
✅ VALIDATION PASSED
   No critical or high-severity issues found

Total Issues: 3
  Critical: 0
  High:     0
  Medium:   2  (insufficient sources)
  Low:      1  (incomplete Epstein info)

Enrichment complete:
  - Total sources per entity: 5.2 average
  - Tier 1 (court docs): 15%
  - Tier 2 (journalism): 40%
  - Requires review: 20%
```

### enriched_entity_data.json Structure:
```json
{
  "metadata": {
    "total_entities_enriched": 10,
    "last_updated": "2025-11-17T14:30:00"
  },
  "entities": [
    {
      "entity_id": "band_doug",
      "name": "Band, Doug",
      "biographical_data": {
        "occupation": {
          "primary": "Political advisor, Clinton Foundation executive",
          "sources": [
            {
              "url": "https://en.wikipedia.org/wiki/Doug_Band",
              "reliability_tier": 3,
              "accessed_date": "2025-11-17"
            }
          ]
        }
      },
      "epstein_relationship": {
        "documented_interactions": [
          {
            "date": "2002-2003",
            "type": "flights",
            "description": "13 flights on Epstein's aircraft",
            "sources": [
              {
                "url": "https://www.theguardian.com/us-news/epstein-flight-logs",
                "reliability_tier": 2,
                "source_type": "journalism"
              }
            ]
          }
        ]
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

## Troubleshooting

### "Entity not found in priority list"
**Solution**: Check entity name exactly matches priority list:
```bash
jq '.entities[] | .name' /Users/masa/Projects/epstein/data/metadata/priority_entities_for_research.json | grep -i "entity name"
```

### "Validation failed"
**Solution**: View specific issues:
```bash
python3 qa_validation.py --export issues.json
jq '.issues[] | {entity: .entity_name, issue: .description, fix: .suggested_fix}' issues.json
```

### "WebSearch not available"
**Current**: Pipeline uses mock data (safe for testing)
**Solution**: Enable real WebSearch (see Production Setup above)

### "Rate limit exceeded"
**Solution**: Increase delay in websearch_integration.py:
```python
self.rate_limit_delay = 5.0  # seconds (default: 2.0)
```

## Performance Metrics

### Target Performance:
- **Speed**: <5 minutes per entity (vs 15-20 manual)
- **Throughput**: ~12 entities/hour (with rate limiting)
- **Quality**: ≥80% Tier 1-2 sources for Epstein claims
- **Coverage**: 100% source provenance

### Expected Timeline:
- 10 entities: ~1 hour
- 50 entities: ~4-5 hours
- 131 entities: ~11-12 hours

## Next Steps

1. ✅ **Test pipeline** (10 entities)
2. **Enable WebSearch** (production integration)
3. **Process batch** (50 entities)
4. **Human review** (QA validation)
5. **Full run** (131 entities)
6. **Publication** (add to web interface)

## Files Created

```
/Users/masa/Projects/epstein/server/scripts/enrichment/
├── automated_entity_enrichment.py  # Main pipeline
├── websearch_integration.py        # WebSearch MCP integration
├── qa_validation.py                # Quality assurance
├── batch_enrich.sh                 # Batch processing script
├── README.md                       # Full documentation
└── QUICKSTART.md                   # This file
```

## Support

For issues or questions:
1. Check logs: `/Users/masa/Projects/epstein/logs/enrichment/`
2. Review README.md for detailed documentation
3. Run QA validation to identify specific problems
4. See CLAUDE.md in project root for project context
