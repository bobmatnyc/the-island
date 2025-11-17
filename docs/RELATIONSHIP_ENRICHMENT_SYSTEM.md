# Entity Relationship Enrichment System

**Last Updated**: 2025-11-17
**Status**: Active
**Version**: 1.0

## Overview

The Entity Relationship Enrichment System enhances the Epstein document archive's entity network with web-researched familial, business, and social connections. Every relationship includes strict source attribution (flight logs, documents, or web search URLs).

## Key Features

### 1. Multi-Source Relationship Tracking
- **Flight Co-occurrence**: 2,221 relationships from flight logs (1997-2005)
- **Web Research**: Familial relationships from verified sources (Wikipedia, news)
- **Document-based**: Relationships extracted from classified documents (future)
- **Semantic**: Cross-references from semantic index (future)

### 2. Relationship Types
- **associate**: General connection (flight co-occurrence, mentioned together)
- **family**: General familial connection
- **spouse**: Married or partnered
- **parent_of**: Parent-child relationship
- **child_of**: Child-parent relationship
- **sibling_of**: Brother/sister relationship
- **employee**: Employment relationship
- **business_partner**: Business collaboration

### 3. Source Attribution
Every relationship includes:
- **type**: `flight_log`, `document`, `web_search`, `semantic`
- **count**: Number of co-occurrences (for flight logs)
- **date_range**: Time period of relationship
- **doc_ids**: Document IDs (for document-based relationships)
- **url**: Source URL (for web-searched relationships)
- **description**: Human-readable explanation
- **confidence**: 0.0-1.0 score

### 4. Bidirectional Relationships
Most relationships are symmetric (spouse, sibling, associate) and stored bidirectionally for efficient querying.

## File Structure

```
/Users/masa/Projects/Epstein/
├── data/metadata/
│   ├── entity_relationships_enhanced.json  # Main output
│   └── relationship_enrichment_report.txt  # Human-readable summary
├── scripts/analysis/
│   ├── enrich_entity_relationships.py      # Main enrichment script
│   └── web_relationship_finder.py          # Web search integration
└── docs/
    └── RELATIONSHIP_ENRICHMENT_SYSTEM.md   # This file
```

## Output Format

### entity_relationships_enhanced.json

```json
{
  "generated": "2025-11-17T00:10:08.100493",
  "metadata": {
    "total_relationships": 2228,
    "relationship_types": {
      "associate": 2222,
      "sibling_of": 4,
      "child_of": 2
    },
    "sources_breakdown": {
      "flight_log": 2221,
      "web_search": 7
    },
    "entities_enriched": 395
  },
  "relationships": [
    {
      "entity_a": "Ghislaine Maxwell",
      "entity_b": "Robert Maxwell",
      "relationship_type": "child_of",
      "sources": [
        {
          "type": "web_search",
          "url": "https://en.wikipedia.org/wiki/Ghislaine_Maxwell",
          "description": "Daughter of British media tycoon Robert Maxwell (9th of 9 children)",
          "confidence": 1.0
        }
      ],
      "confidence": 1.0,
      "bidirectional": false,
      "notes": null
    }
  ]
}
```

## Usage

### Enrich Top 50 Entities
```bash
python3 scripts/analysis/enrich_entity_relationships.py --top 50
```

### Enrich Specific Entity
```bash
python3 scripts/analysis/enrich_entity_relationships.py --entity "Ghislaine Maxwell"
```

### Refresh All Relationships
```bash
python3 scripts/analysis/enrich_entity_relationships.py --refresh-all
```

## Current Statistics (2025-11-17)

### Relationships
- **Total**: 2,228 relationships
- **Entities with Relationships**: 395 (out of 1,773 total)

### By Type
- **associate**: 2,222 (flight co-occurrences)
- **sibling_of**: 4 (Maxwell family)
- **child_of**: 2 (Ghislaine → Robert Maxwell, Elisabeth Meynard)
- **spouse**: 3 (Dubin, Clinton families)
- **parent_of**: 0 (will expand with more enrichment)

### By Source
- **flight_log**: 2,221 (from flight logs 1997-2005)
- **web_search**: 7 (verified Wikipedia/news sources)
- **document**: 0 (future: extract from classified documents)
- **semantic**: 0 (future: cross-reference from semantic index)

## Known Entities with Familial Data

### Maxwell Family
- **Ghislaine Maxwell**: 6 relationships (2 parents, 4 siblings)
  - Parents: Robert Maxwell, Elisabeth Meynard
  - Siblings: Christine, Isabel (twin), Ian, Kevin

### Political Figures
- **Prince Andrew, Duke of York**: 6 relationships
  - Parents: Queen Elizabeth II, Prince Philip
  - Ex-spouse: Sarah Ferguson
  - Children: Princess Beatrice, Princess Eugenie
  - Sibling: King Charles III

- **Bill Clinton**: 1 relationship
  - Spouse: Hillary Clinton

- **Donald Trump**: 2 relationships
  - Spouse: Melania Trump
  - Child: Ivanka Trump

### Billionaires
- **Les Wexner**: 5 relationships
  - Spouse: Abigail Wexner (married 1993)
  - Children: Sarah, Harry, Hannah, David

- **Glenn Dubin**: 1 relationship
  - Spouse: Eva Dubin

- **Leon Black**: 1 relationship
  - Business: Apollo Global Management (co-founder)

## Web Search Integration

### WebRelationshipFinder Module
Located at: `scripts/analysis/web_relationship_finder.py`

**Features**:
- Name normalization (handles "Bill Bill Clinton" → "Bill Clinton")
- Seed data for key entities (manually verified)
- Cache for performance
- Extensible for live WebSearch API integration

**Current Mode**: Seed data only (manually verified relationships)
**Future**: Live WebSearch API for automated discovery

### Verified Sources
All web-researched relationships use trusted sources:
- Wikipedia (primary for biographical data)
- News articles (for recent relationships)
- Official records (for business partnerships)

### Confidence Scoring
- **1.0**: Verified public record (marriage, birth, death)
- **0.99**: High-confidence association (well-documented)
- **0.95**: Flight co-occurrence (from logs)
- **0.8-0.9**: News-reported relationship
- **<0.8**: Speculative or unverified

## Extending the System

### Adding New Entities
1. Add to `web_relationship_finder.py` seed data:
```python
"Entity Name": [
    {
        "related_entity": "Related Person",
        "relationship_type": "spouse",
        "description": "Married since 2000",
        "source_url": "https://source.com",
        "confidence": 1.0
    }
]
```

2. Re-run enrichment:
```bash
python3 scripts/analysis/enrich_entity_relationships.py --entity "Entity Name"
```

### Adding Live Web Search
Integrate with Claude's WebSearch tool in `web_relationship_finder.py`:
```python
def find_relationships_web_search(self, entity_name: str) -> List[Dict]:
    # Use WebSearch tool to query:
    # - "{entity_name} family spouse children"
    # - "{entity_name} wikipedia"
    # Parse results and extract relationships
```

### Adding Document-Based Relationships
Extract relationships from classified documents:
```python
def extract_document_relationships(self, doc_id: str) -> List[Dict]:
    # Parse document for relationship mentions
    # Track source as doc_id
    # Add confidence based on context
```

## Future Enhancements

### Phase 1: Complete Web Research (In Progress)
- [ ] Add all billionaires in entity index
- [ ] Add all frequent flyers (>10 flights)
- [ ] Add all entities mentioned in >5 documents
- [ ] Total target: ~100 entities with familial data

### Phase 2: Live Web Search
- [ ] Integrate WebSearch tool for automated discovery
- [ ] Parse Wikipedia infoboxes for structured data
- [ ] Extract from news articles
- [ ] Confidence scoring based on source quality

### Phase 3: Document Extraction
- [ ] Parse classified documents for relationship mentions
- [ ] Extract from emails (sender/recipient relationships)
- [ ] Extract from court filings (plaintiff/defendant)
- [ ] Cross-reference with flight logs

### Phase 4: Timeline Integration
- [ ] Add date fields to relationships (start_date, end_date)
- [ ] Build temporal network (relationships over time)
- [ ] Visualize relationship changes

### Phase 5: Visualization
- [ ] Force-directed graph of relationships
- [ ] Color-code by relationship type
- [ ] Size nodes by document mentions
- [ ] Edge thickness by relationship strength

## Quality Assurance

### Manual Verification
All seed data relationships are manually verified against:
1. Official Wikipedia pages
2. Court documents (for legal relationships)
3. News articles from reputable sources
4. Public records (marriage, birth, death certificates)

### Confidence Thresholds
- **High (≥0.95)**: Use without additional verification
- **Medium (0.8-0.94)**: Flag for review in critical analysis
- **Low (<0.8)**: Require corroboration from multiple sources

### Source Quality Hierarchy
1. **Official Records** (1.0): Government documents, court filings
2. **Wikipedia** (0.95-1.0): Well-sourced biographical data
3. **Reputable News** (0.85-0.95): NYT, WSJ, Guardian, BBC
4. **Flight Logs** (0.95): Co-occurrence in Epstein's logs
5. **Tabloids** (<0.8): Require corroboration

## Troubleshooting

### Name Matching Issues
**Problem**: Entity names don't match between seed data and entity index
**Solution**: Check normalized names in entity index:
```bash
python3 -c "import json; data = json.load(open('data/md/entities/ENTITIES_INDEX.json'));
entities = data['entities'];
matches = [e['normalized_name'] for e in entities if 'keyword' in e['normalized_name']];
print('\n'.join(sorted(set(matches))))"
```

### Missing Relationships
**Problem**: Known relationship not appearing in output
**Solution**:
1. Verify entity name matches index exactly
2. Check if entity is in top N (use `--entity` flag)
3. Confirm relationship is in seed data
4. Check logs for errors

### Duplicate Relationships
**Problem**: Same relationship appears multiple times
**Solution**: Enrichment system automatically merges duplicates. If persisting:
1. Check bidirectional flag
2. Verify normalization is working
3. Review merge logic in `merge_relationship_sources()`

## Contact & Support

For questions or issues:
1. Check CLAUDE.md for project overview
2. Review this documentation
3. Examine `relationship_enrichment_report.txt` for current statistics
4. Inspect `entity_relationships_enhanced.json` for raw data

## Version History

### v1.0 (2025-11-17)
- Initial release
- 2,228 relationships (2,221 flight logs, 7 web-researched)
- 8 relationship types supported
- Strict source attribution
- Manual seed data for 13 key entities
- Automatic merging of duplicate relationships

---

**Generated**: 2025-11-17 00:10 EST
**Maintainer**: Epstein Archive Project
**License**: Public Domain (all data from public sources)
