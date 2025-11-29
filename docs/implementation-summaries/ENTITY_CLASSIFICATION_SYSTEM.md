# Entity Relationship Classification System

**Status**: ✅ Implemented
**Created**: 2025-11-25
**Script**: `scripts/analysis/classify_entity_relationships.py`

## Overview

AI-powered entity classification system using Grok LLM to analyze and categorize entities based on their relationships, connections, and roles in the Epstein archive.

## Features

### Multi-Dimensional Classification

1. **Primary Role**: Main relationship to Epstein
   - Close Associate
   - Business Partner
   - Political Figure
   - Victim
   - Law Enforcement
   - Legal Team
   - Social Contact
   - Family Member

2. **Connection Strength**: Based on quantitative metrics
   - **Core Circle**: >50 flights or high network centrality
   - **Frequent Associate**: 10-50 flights
   - **Occasional Contact**: 1-9 flights
   - **Documented Only**: No flights, only document mentions

3. **Professional Category**: Primary occupation/role
   - Politician
   - Celebrity
   - Financier
   - Scientist
   - Legal Professional
   - Socialite
   - Academic
   - Artist

4. **Temporal Activity**: Decades of involvement
   - 1970s, 1980s, 1990s, 2000s, 2010s, 2020s

5. **Significance Score**: 1-10 rating based on:
   - Network centrality
   - Document mentions
   - Flight frequency
   - Context from biography

## Technical Architecture

### Input Data Sources

1. **Entity Statistics** (`data/metadata/entity_statistics.json`)
   - Flight counts
   - Document mentions
   - Network connections
   - Top co-passengers

2. **Entity Biographies** (`data/metadata/entity_biographies.json`)
   - Context for role interpretation
   - Background information
   - Relationship descriptions

3. **SQLite Database** (`data/metadata/entities.db`)
   - Entity metadata
   - Existing classifications (to skip)

### Processing Pipeline

```
Entity Statistics
       ↓
Context Building
       ↓
Grok LLM Analysis
       ↓
JSON Validation (Pydantic)
       ↓
Quality Checks
       ↓
Database Storage
```

### Database Schema

```sql
CREATE TABLE entity_classifications (
    entity_id TEXT PRIMARY KEY,
    primary_role TEXT NOT NULL,
    connection_strength TEXT NOT NULL,
    professional_category TEXT NOT NULL,
    temporal_activity TEXT,  -- JSON array
    significance_score INTEGER NOT NULL CHECK (significance_score BETWEEN 1 AND 10),
    justification TEXT NOT NULL,
    classified_by TEXT,
    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,  -- JSON object
    FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
);

CREATE INDEX idx_classification_role ON entity_classifications(primary_role);
CREATE INDEX idx_classification_strength ON entity_classifications(connection_strength);
CREATE INDEX idx_classification_significance ON entity_classifications(significance_score DESC);
```

## Usage

### Basic Commands

```bash
# Dry run with top 10 entities (no API calls)
python3 scripts/analysis/classify_entity_relationships.py --dry-run --limit 10

# Classify Tier 1 entities (15+ connections)
python3 scripts/analysis/classify_entity_relationships.py --tier 1 --limit 50

# Classify Tier 2 entities (10+ connections)
python3 scripts/analysis/classify_entity_relationships.py --tier 2 --limit 100

# Classify all entities without existing classifications
python3 scripts/analysis/classify_entity_relationships.py --tier all --limit 500
```

### Advanced Options

```bash
# Create backup before processing
python3 scripts/analysis/classify_entity_relationships.py --tier 1 --backup

# Classify and import to database in one step
python3 scripts/analysis/classify_entity_relationships.py --tier 1 --import-db

# Export specific JSON file to database
python3 scripts/analysis/classify_entity_relationships.py \
    --export data/metadata/entity_classifications.json \
    --import-db

# Custom output file
python3 scripts/analysis/classify_entity_relationships.py \
    --tier 2 \
    --output data/metadata/classifications_batch2.json
```

### Tier System

- **Tier 1**: High-value entities (15+ connections)
  - Core network members
  - Frequently mentioned individuals
  - High priority for classification

- **Tier 2**: Medium-value entities (10-14 connections)
  - Regular associates
  - Documented relationships

- **Tier 3**: Lower-value entities (5-9 connections)
  - Occasional contacts
  - Peripheral network members

- **All**: All entities (0+ connections)
  - Complete coverage
  - Includes minimal mentions

## Output Format

### JSON Structure

```json
{
  "metadata": {
    "generated": "2025-11-25T12:00:00Z",
    "classifier": "grok-beta",
    "total_entities": 50,
    "successful": 48,
    "failed": 2,
    "statistics": {
      "total_processed": 50,
      "successful": 48,
      "failed": 2,
      "retries": 5,
      "total_tokens_used": 125000,
      "total_api_calls": 50
    },
    "average_significance_score": 6.8,
    "connection_strength_distribution": {
      "Core Circle": 8,
      "Frequent Associate": 15,
      "Occasional Contact": 20,
      "Documented Only": 5
    }
  },
  "classifications": {
    "ghislaine_maxwell": {
      "entity_id": "ghislaine_maxwell",
      "entity_name": "Maxwell, Ghislaine",
      "primary_role": "Close Associate",
      "connection_strength": "Core Circle",
      "professional_category": "Socialite",
      "temporal_activity": ["1990s", "2000s", "2010s"],
      "significance_score": 10,
      "justification": "Most frequent flight companion (502 flights) and central network figure with 102 direct connections and extensive document mentions.",
      "metadata": {
        "classified_by": "grok-beta",
        "classification_date": "2025-11-25T12:05:30Z",
        "flight_count": 502,
        "document_count": 4421,
        "connection_count": 102,
        "tokens_used": 2500,
        "attempt": 1
      }
    }
  }
}
```

## Quality Assurance

### Validation Checks

1. **JSON Schema Validation**: Pydantic models enforce structure
2. **Enum Validation**: Connection strength must match predefined values
3. **Range Validation**: Significance score must be 1-10
4. **Temporal Validation**: Decades must be from valid list
5. **Completeness Check**: All required fields must be present

### Error Handling

- **Retry Logic**: 3 attempts with exponential backoff (1s, 2s, 4s)
- **Rate Limiting**: 1.5 seconds between API requests
- **Checkpoint Saving**: Every 10 entities
- **Graceful Degradation**: Failed classifications don't stop batch
- **Error Logging**: Detailed error messages for debugging

### Output Quality Metrics

- Success rate tracking
- Token usage monitoring
- Significance score distribution
- Connection strength distribution
- Classification consistency checks

## API Integration

### Grok LLM Configuration

```python
model = "x-ai/grok-beta"
base_url = "https://openrouter.ai/api/v1"
temperature = 0.2  # Low for structured output
max_tokens = 600
response_format = {"type": "json_object"}  # Force JSON response
```

### Rate Limits

- **Conservative**: 1.5 seconds between requests
- **Free tier**: Available until December 3, 2025
- **Post-free pricing**: ~$0.50/M input, ~$1.50/M output tokens

### Cost Estimation

For 100 entities:
- Estimated tokens: ~250,000 total
- Current cost: **FREE** (until Dec 3, 2025)
- Future cost: ~$0.20-0.40 per 100 entities

## Integration with Existing Systems

### Entity Pages

Classifications enhance entity detail pages with:
- Role badges (visual indicators)
- Connection strength indicators
- Significance ratings
- Temporal activity timeline

### API Endpoints

```python
# Get classification for entity
GET /api/entities/{entity_id}/classification

# List entities by classification
GET /api/entities/classifications?role=Close+Associate
GET /api/entities/classifications?strength=Core+Circle
GET /api/entities/classifications?significance=8-10

# Classification statistics
GET /api/classifications/stats
```

### Search & Filtering

- Filter entities by primary role
- Sort by significance score
- Filter by connection strength
- Filter by temporal activity

## Performance Characteristics

### Processing Speed

- **Dry Run**: Instant (no API calls)
- **Live Processing**: ~2 seconds per entity (with rate limiting)
- **Batch of 50**: ~2 minutes
- **Batch of 100**: ~4 minutes
- **Tier 1 (319 entities)**: ~11 minutes

### Checkpointing

- Saves progress every 10 entities
- Resume capability (checkpoint file)
- Automatic cleanup on successful completion
- Manual recovery from failures

## Best Practices

### Before Running

1. **Verify API Key**: Set `OPENROUTER_API_KEY` environment variable
2. **Backup Existing Data**: Use `--backup` flag
3. **Test with Dry Run**: Always test with `--dry-run` first
4. **Check Tier Appropriateness**: Start with Tier 1, expand as needed

### During Processing

1. **Monitor Progress**: Watch for failed classifications
2. **Check Quality**: Review sample results for accuracy
3. **Verify Checkpoints**: Ensure checkpoints are being saved
4. **Track Token Usage**: Monitor costs (for post-free period)

### After Processing

1. **Review Results**: Check output JSON for quality
2. **Import to Database**: Use `--import-db` flag
3. **Validate Database**: Query database to verify imports
4. **Archive Checkpoint**: Remove or archive checkpoint files

## Troubleshooting

### Common Issues

**API Key Not Found**
```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

**Classification Failures**
- Check internet connection
- Verify API key validity
- Review error messages in output
- Check Grok API status

**Database Import Errors**
- Ensure database exists
- Verify table was created
- Check entity_id references are valid
- Review foreign key constraints

**Checkpoint Recovery**
```bash
# Resume from checkpoint
python3 scripts/analysis/classify_entity_relationships.py --resume

# Or start fresh (remove checkpoint)
rm data/metadata/entity_classifications_checkpoint.json
```

## Future Enhancements

### Planned Features

1. **Multi-Model Comparison**: Compare Grok vs Claude classifications
2. **Confidence Scores**: Add confidence rating to classifications
3. **Batch Re-classification**: Update existing classifications
4. **Manual Override**: UI for manual classification adjustments
5. **Classification History**: Track changes over time
6. **Consensus Classification**: Combine multiple AI judgments

### Integration Roadmap

1. **Phase 1**: Core classification system ✅
2. **Phase 2**: API endpoint integration
3. **Phase 3**: Frontend UI components
4. **Phase 4**: Search and filtering
5. **Phase 5**: Advanced analytics and insights

## Related Documentation

- [Entity Biography Generation](ENTITY_BIOGRAPHY_GENERATION.md)
- [Entity Statistics System](../data/ENTITY_ANALYSIS_EXECUTIVE_SUMMARY.md)
- [Database Schema](../developer/api/ENTITY_ID_SCHEMA.md)
- [Grok API Integration](../features/MISTRAL_INTEGRATION_SUMMARY.md)

## Success Metrics

- ✅ Script successfully classifies entities using Grok LLM
- ✅ Database schema updated with classifications table
- ✅ Batch processing with checkpoints works correctly
- ✅ All 319 entities with biographies can be classified
- ✅ Output includes primary role, connection strength, and significance
- ✅ Results stored in SQLite for API access
- ✅ Comprehensive error handling and retry logic
- ✅ Quality validation and verification
- ✅ Production-ready code with full documentation

## Contact & Support

For issues or questions about the classification system:
1. Review this documentation
2. Check script help: `python3 classify_entity_relationships.py --help`
3. Review error logs in console output
4. Check OpenRouter API status
5. Consult related documentation above
