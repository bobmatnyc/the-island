# Entity Biography Enrichment from Documents

## Overview

The `enrich_bios_from_documents.py` script enriches entity biographies by extracting contextual information from documents using Grok AI.

**Status**: Script is ready but **requires document linking to be implemented first**. Currently, entities in `entity_statistics.json` do not have `documents` arrays populated.

## Prerequisites

### 1. Document Linking Required

Before this script can be effective, entities must be linked to documents. This requires:

- Running document entity extraction on all markdown files
- Populating the `documents` array in `entity_statistics.json`
- See: `scripts/rag/link_entities_to_docs.py` or similar

**Current Status**: ❌ No entities have documents linked (0 out of 1637)

**Required**: ✅ Entities must have populated `documents` arrays like:

```json
{
  "entity_id": {
    "documents": [
      {
        "path": "canonical/emails/some_email.md",
        "type": "email",
        "context": "Optional snippet"
      }
    ]
  }
}
```

### 2. OpenRouter API Key

The script uses OpenRouter's free Grok API:

```bash
# Add to .env.local
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
```

Get your key at: https://openrouter.ai/keys

### 3. Python Dependencies

```bash
pip install requests pydantic tqdm
```

## How It Works

### Workflow

1. **Read biographies** from `data/metadata/entity_biographies.json`
2. **For each entity with a biography**:
   - Find all documents mentioning the entity (from `entity_statistics.json`)
   - Extract relevant paragraphs containing entity name
   - Send excerpts to Grok AI for contextual analysis
3. **Grok extracts** 2-3 specific factual details from documents
4. **Results saved** to biography file with metadata

### Architecture

```
┌─────────────────────┐
│ entity_biographies  │  ← Input: Existing biographies
│      .json          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ entity_statistics   │  ← Source: Document references
│      .json          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Markdown Files    │  ← Read: Extract paragraphs
│   (data/md/...)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Grok AI (API)     │  ← Analyze: Extract context
│  (grok-2-1212)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Updated Bios with  │  ← Output: Enriched biographies
│  document_context   │
└─────────────────────┘
```

## Usage

### Dry Run (No API Calls)

Preview what would be processed:

```bash
# Test top 5 entities
python3 scripts/analysis/enrich_bios_from_documents.py --dry-run --limit 5

# Verbose output with debug logs
python3 scripts/analysis/enrich_bios_from_documents.py --dry-run --limit 10 --verbose
```

### Single Entity

Enrich a specific entity:

```bash
# With automatic backup
python3 scripts/analysis/enrich_bios_from_documents.py \
  --entity-id jeffrey_epstein \
  --backup

# Verbose mode
python3 scripts/analysis/enrich_bios_from_documents.py \
  --entity-id ghislaine_maxwell \
  --backup \
  --verbose
```

### Batch Processing

Enrich multiple entities:

```bash
# First 20 entities with biographies
python3 scripts/analysis/enrich_bios_from_documents.py --limit 20 --backup

# All entities with biographies (61 currently)
python3 scripts/analysis/enrich_bios_from_documents.py --limit 100 --backup

# Custom output file (doesn't modify original)
python3 scripts/analysis/enrich_bios_from_documents.py \
  --limit 50 \
  --output /tmp/enriched_biographies.json
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--entity-id <id>` | Process single entity by ID | None (all) |
| `--limit <n>` | Process first N entities | 10 |
| `--dry-run` | Preview without API calls | False |
| `--backup` | Create backup before modifying | False |
| `--output <path>` | Custom output file | Original file |
| `--verbose, -v` | Enable debug logging | False |

## Output Format

The script adds two new fields to each entity biography:

```json
{
  "entity_id": {
    "id": "jeffrey_epstein",
    "display_name": "Jeffrey Edward Epstein",
    "biography": "Existing biography text...",

    "document_context": [
      "Specific detail 1 extracted from documents",
      "Specific detail 2 extracted from documents"
    ],

    "context_metadata": {
      "extraction_date": "2025-11-22T16:00:00Z",
      "documents_analyzed": 5,
      "model": "x-ai/grok-2-1212",
      "confidence": 0.85
    }
  }
}
```

## Grok Prompt Strategy

### System Prompt

The script uses a carefully designed prompt to extract factual context:

```
You are analyzing documents from the Epstein archive to enrich entity biographies.

Your task: Extract 2-3 specific factual details from document excerpts.

Focus on:
- Specific events or dates mentioned
- Relationships or interactions described
- Roles, positions, or affiliations
- Notable activities documented

Requirements:
- Use ONLY information from excerpts
- Maintain factual tone
- Avoid speculation
- Return empty list if no useful context
```

### Response Format

Grok returns structured JSON:

```json
{
  "additional_context": [
    "Detail 1 from documents",
    "Detail 2 from documents"
  ],
  "confidence": 0.85
}
```

## Rate Limiting

- **Delay**: 1 second between API calls
- **Timeout**: 30 seconds per request
- **Max tokens**: 300 per response
- **Model**: `x-ai/grok-2-1212` (free tier)

**Estimated Time**:
- 10 entities: ~10 seconds (dry run: instant)
- 50 entities: ~50 seconds
- 100 entities: ~100 seconds (1.7 minutes)

## Error Handling

The script handles common errors gracefully:

### API Failures

- **Network errors**: Logged, entity skipped
- **Rate limits**: 1-second delay between requests
- **Invalid JSON**: Empty context returned
- **Timeouts**: Logged, entity marked as failed

### Data Issues

- **Missing biographies**: Warning logged, skipped
- **No documents**: Success with empty context
- **Missing files**: Warning logged, skipped
- **Parse errors**: Logged with details

## Logging

All operations logged to:

```
logs/enrich_bios_YYYYMMDD_HHMMSS.log
```

### Log Levels

- **DEBUG** (`--verbose`): All operations, API responses
- **INFO** (default): Progress, summary stats
- **WARNING**: Skipped entities, missing data
- **ERROR**: API failures, exceptions

## Summary Statistics

After processing, the script prints:

```
======================================================================
ENRICHMENT SUMMARY
======================================================================
Total entities processed: 20
Successful: 18
With additional context: 12
Total details extracted: 36
Average details per entity: 1.80

Grok API Statistics:
  Total requests: 18
  Successful: 18
  Failed: 0
  Total tokens used: 5,420
  Entities with context: 12
  Entities without context: 6
======================================================================
```

## Backup Strategy

### Automatic Backups

When using `--backup`:

```
data/metadata/entity_biographies.backup_20251122_160000.json
```

### Manual Backups

The script also creates a backup when saving (if modifying original):

```
data/metadata/entity_biographies.backup_20251122_160130.json
```

## Next Steps

### Before Production Use

1. **Implement Document Linking**
   - Run entity extraction on all markdown files
   - Populate `documents` arrays in `entity_statistics.json`
   - Verify with: `scripts/analysis/verify_entity_filtering.py`

2. **Test with Sample Entities**
   - Run dry run: `--dry-run --limit 5 --verbose`
   - Test single entity: `--entity-id <entity_with_docs> --backup`
   - Verify output format and quality

3. **Batch Processing**
   - Start with `--limit 10` to test API integration
   - Gradually increase to `--limit 50`, `--limit 100`
   - Monitor token usage and API rate limits

### Quality Validation

After enrichment, verify results:

```python
# Check enriched biographies
import json
from pathlib import Path

bio_path = Path("data/metadata/entity_biographies.json")
with open(bio_path) as f:
    data = json.load(f)
    entities = data.get("entities", data)

# Count enriched entities
enriched = sum(
    1 for e in entities.values()
    if "document_context" in e and e["document_context"]
)

print(f"Enriched entities: {enriched}/{len(entities)}")
```

## Troubleshooting

### "No entities have documents"

**Problem**: `entity_statistics.json` doesn't have `documents` arrays populated.

**Solution**: Run document entity extraction first:

```bash
# Link entities to documents
python3 scripts/rag/link_entities_to_docs.py

# Verify linking
python3 scripts/analysis/verify_entity_filtering.py
```

### "API key not set"

**Problem**: `OPENROUTER_API_KEY` environment variable missing.

**Solution**: Add to `.env.local`:

```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
```

### "Too many API failures"

**Problem**: Rate limiting or network issues.

**Solution**:
- Reduce batch size: `--limit 10`
- Check network connectivity
- Verify API key is valid
- Check OpenRouter status

### "Invalid JSON response from Grok"

**Problem**: Grok didn't return valid JSON.

**Solution**:
- Check logs for raw response
- Verify prompt format
- May be temporary API issue - retry

## Cost Estimation

**Model**: `x-ai/grok-2-1212` (Free tier on OpenRouter)

**Token Usage**:
- ~200 tokens per entity (prompt)
- ~100 tokens per response
- **Total**: ~300 tokens per entity

**Free Tier Limits**:
- Check OpenRouter for current limits
- Typically allows thousands of requests/day

**Example**:
- 100 entities ≈ 30,000 tokens
- 1,000 entities ≈ 300,000 tokens

## Future Enhancements

### Potential Improvements

1. **Multi-Model Support**
   - Add support for GPT-4, Claude, other models
   - Model selection via `--model` flag
   - Compare quality across models

2. **Enhanced Context Extraction**
   - Use vector similarity for relevance ranking
   - Extract more sophisticated relationships
   - Cross-reference multiple documents

3. **Quality Scoring**
   - Automated fact-checking against biography
   - Confidence scoring based on document quality
   - Flag low-quality extractions for review

4. **Batch Optimization**
   - Parallel API calls with rate limiting
   - Caching to avoid re-processing
   - Resume from checkpoint on failure

## Examples

### Complete Workflow

```bash
# 1. Dry run to preview
python3 scripts/analysis/enrich_bios_from_documents.py --dry-run --limit 5 --verbose

# 2. Test single entity
python3 scripts/analysis/enrich_bios_from_documents.py \
  --entity-id jeffrey_epstein \
  --backup \
  --verbose

# 3. Batch process (small)
python3 scripts/analysis/enrich_bios_from_documents.py --limit 10 --backup

# 4. Check results
cat data/metadata/entity_biographies.json | jq '.entities.jeffrey_epstein.document_context'

# 5. Full batch (if successful)
python3 scripts/analysis/enrich_bios_from_documents.py --limit 100 --backup
```

### Verify Enrichment

```bash
# Count enriched entities
jq '[.entities | to_entries[] | select(.value.document_context != null)] | length' \
  data/metadata/entity_biographies.json

# View specific entity
jq '.entities.ghislaine_maxwell' data/metadata/entity_biographies.json
```

## References

- **OpenRouter API**: https://openrouter.ai/docs
- **Grok Model**: https://openrouter.ai/models/x-ai/grok-2-1212
- **Biography Format**: `server/models/entity.py` → `EntityBiography`
- **Entity Statistics**: `data/metadata/entity_statistics.json`

## Support

For issues or questions:

1. Check logs: `logs/enrich_bios_*.log`
2. Run with `--verbose` for detailed output
3. Test with `--dry-run` first
4. Verify prerequisites are met

---

**Last Updated**: 2025-11-22
**Script Version**: 1.0
**Status**: Ready (pending document linking)
