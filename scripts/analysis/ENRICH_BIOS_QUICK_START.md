# Entity Biography Enrichment - Quick Start

## TL;DR

Extract contextual information from documents to enhance entity biographies using Grok AI.

## Prerequisites Checklist

- [ ] OpenRouter API key in `.env.local` (`OPENROUTER_API_KEY=sk-or-v1-...`)
- [ ] Entities have `documents` arrays populated in `entity_statistics.json`
- [ ] Python dependencies: `requests`, `pydantic`, `tqdm`

## Quick Commands

### Test the Script

```bash
# Run unit tests
python3 tests/scripts/test_enrich_bios.py

# Dry run (no API calls)
python3 scripts/analysis/enrich_bios_from_documents.py --dry-run --limit 5 --verbose
```

### Single Entity

```bash
python3 scripts/analysis/enrich_bios_from_documents.py \
  --entity-id jeffrey_epstein \
  --backup \
  --verbose
```

### Batch Process

```bash
# First 20 entities with backup
python3 scripts/analysis/enrich_bios_from_documents.py --limit 20 --backup

# Custom output (doesn't modify original)
python3 scripts/analysis/enrich_bios_from_documents.py \
  --limit 50 \
  --output /tmp/enriched_bios.json
```

## What It Does

1. **Reads** entity biographies from `data/metadata/entity_biographies.json`
2. **Finds** documents mentioning each entity (from `entity_statistics.json`)
3. **Extracts** relevant paragraphs from markdown files
4. **Sends** to Grok AI for contextual analysis
5. **Saves** enriched biographies with `document_context` field

## Output Format

```json
{
  "entity_id": {
    "biography": "Original biography...",
    "document_context": [
      "Detail 1 from documents",
      "Detail 2 from documents"
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

## Rate Limiting

- **1 request per second** to Grok API
- **Free tier**: `x-ai/grok-2-1212` model
- **Estimated time**: ~1 second per entity

## Common Options

| Option | Description |
|--------|-------------|
| `--entity-id <id>` | Process single entity |
| `--limit <n>` | Process first N entities (default: 10) |
| `--dry-run` | Preview without API calls |
| `--backup` | Create backup before modifying |
| `--verbose, -v` | Enable debug logging |

## Error Handling

- **No documents**: Success with empty context
- **API failure**: Logged, entity skipped
- **Missing files**: Warning logged, skipped

## Verification

```bash
# Check enriched count
jq '[.entities | to_entries[] | select(.value.document_context != null)] | length' \
  data/metadata/entity_biographies.json

# View specific entity
jq '.entities.jeffrey_epstein.document_context' \
  data/metadata/entity_biographies.json
```

## Important Notes

⚠️ **Current Status**: No entities have documents linked yet. Run document entity extraction first.

✅ **Safe**: Always creates backups when modifying original file

📝 **Logs**: All operations logged to `logs/enrich_bios_*.log`

## Full Documentation

See: `scripts/analysis/README_ENRICH_BIOS.md`

---

**Created**: 2025-11-22
**Status**: Ready for use (pending document linking)
