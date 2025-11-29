# Entity Extraction from OCR Documents

Comprehensive entity extraction script that processes 33,561 OCR documents using Ministral 8B via OpenRouter API.

## Overview

**Script**: `extract_entities_from_documents.py`
**Model**: `mistralai/ministral-8b` via OpenRouter
**Input**: 33,561 OCR text files in `data/sources/house_oversight_nov2025/ocr_text/`
**Output**: JSON files with extracted entities and document mappings
**Estimated Cost**: ~$2.20 for entire corpus (avg 734 tokens/doc)

## Features

### Entity Extraction
- **Person names**: Full names, handles initials and variations
- **Organizations**: Government agencies, companies, institutions
- **Locations**: Cities, addresses, properties
- **Name normalization**: Handles "J. Epstein" → "Jeffrey Epstein"
- **OCR error tolerance**: Gracefully handles corrupted text

### Batch Processing
- **Progress tracking**: Real-time progress bar with tqdm
- **Checkpointing**: Save progress every 1,000 documents (configurable)
- **Resume capability**: Restart from last checkpoint after interruption
- **Rate limiting**: 1 request/second to respect API limits
- **Error handling**: Retry logic and graceful error recovery

### Deduplication
- **Name normalization**: Case-insensitive, punctuation removal
- **Fuzzy matching**: Merge variations (initials, abbreviations)
- **Variation tracking**: Track all name forms for each entity
- **Cross-document merging**: Same entity across multiple documents

## Usage

### Basic Extraction

```bash
# Extract entities from all documents
python3 scripts/analysis/extract_entities_from_documents.py

# Dry run (no API calls)
python3 scripts/analysis/extract_entities_from_documents.py --dry-run --limit 10

# Test with first 100 documents
python3 scripts/analysis/extract_entities_from_documents.py --limit 100
```

### Advanced Options

```bash
# Custom input/output paths
python3 scripts/analysis/extract_entities_from_documents.py \
  --input-dir data/sources/house_oversight_nov2025/ocr_text \
  --output data/metadata/document_entities_raw.json \
  --batch-size 50 \
  --checkpoint-every 1000

# Resume from checkpoint after interruption
python3 scripts/analysis/extract_entities_from_documents.py --resume

# Custom API key
python3 scripts/analysis/extract_entities_from_documents.py --api-key sk-or-...
```

### Command-Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--input-dir` | `data/sources/house_oversight_nov2025/ocr_text` | OCR text files directory |
| `--output` | `data/metadata/document_entities_raw.json` | Output file path |
| `--batch-size` | `50` | Batch size for progress tracking |
| `--checkpoint-every` | `1000` | Save checkpoint every N documents |
| `--resume` | `False` | Resume from last checkpoint |
| `--limit` | `None` | Limit documents (for testing) |
| `--dry-run` | `False` | Test without API calls |
| `--api-key` | `$OPENROUTER_API_KEY` | OpenRouter API key |

## Output Files

### 1. Main Output: `document_entities_raw.json`

```json
{
  "extraction_metadata": {
    "total_documents": 33561,
    "documents_processed": 33561,
    "documents_failed": 0,
    "total_entities_found": 50000,
    "unique_entities": 2500,
    "extraction_date": "2025-11-28T21:00:00Z",
    "model": "mistralai/ministral-8b",
    "total_cost": "$2.20",
    "total_tokens_used": 24600000,
    "entity_type_counts": {
      "person": 1200,
      "organization": 800,
      "location": 500
    }
  },
  "entities": {
    "jeffrey_epstein": {
      "name": "Jeffrey Epstein",
      "type": "person",
      "normalized_name": "jeffrey epstein",
      "mention_count": 1250,
      "document_sources": ["DOJ-OGR-00000001", "DOJ-OGR-00000002", ...],
      "first_seen": "DOJ-OGR-00000001",
      "name_variations": ["Jeffrey Epstein", "J. Epstein", "Epstein, Jeffrey"]
    }
  }
}
```

### 2. Document Index: `document_entity_index.json`

```json
{
  "metadata": {
    "generated": "2025-11-28T21:00:00Z",
    "total_documents": 33561
  },
  "document_entities": {
    "DOJ-OGR-00000001": [
      "jeffrey epstein",
      "ghislaine maxwell",
      "fbi"
    ]
  }
}
```

### 3. Checkpoint File (temporary): `*_checkpoint.json`

Created during processing, removed on successful completion. Used for resume functionality.

## Entity Processing Pipeline

### 1. Extraction Prompt

```
System: You are an expert legal document entity extractor...

User: Extract all named entities from this legal document text:
[OCR text up to 3000 chars]

Return ONLY the JSON array, no additional text.
```

### 2. Name Normalization

- Lowercase conversion
- Remove titles: `Mr.`, `Mrs.`, `Dr.`, `Jr.`, `Sr.`
- Remove punctuation (except hyphens, apostrophes)
- Whitespace normalization

### 3. Fuzzy Matching

- Exact match on normalized name
- Substring matching for initials (min 3 chars)
- Prefer longer, more complete names

### 4. Deduplication

- Track all name variations per entity
- Maintain canonical name (first seen full form)
- Cross-document entity merging

## Performance Metrics

### From Test Runs

| Metric | Value |
|--------|-------|
| Average tokens/doc | 734 tokens |
| Average cost/doc | $0.0001 |
| Processing speed | ~0.5 docs/sec (with rate limiting) |
| Estimated total time | ~18 hours for 33,561 docs |
| Estimated total cost | ~$2.20 |

### Entity Extraction Quality (Sample of 5 docs)

- **Total entities extracted**: 31
- **Unique entities**: 27
- **Entity types**:
  - Persons: 14 (52%)
  - Organizations: 7 (26%)
  - Locations: 6 (22%)

**Sample extracted entities**:
- Persons: Jeffrey Epstein, Ghislaine Maxwell, David Oscar Markus
- Organizations: FBI, Department of Justice, United States of America
- Locations: Miami Florida, New York, Washington DC, Southern District of New York

## Cost Calculation

**Ministral 8B Pricing** (via OpenRouter):
- Input: $0.10 / 1M tokens
- Output: $0.10 / 1M tokens

**Estimate for 33,561 documents**:
- Average input: ~500 tokens/doc × 33,561 = 16.78M tokens
- Average output: ~234 tokens/doc × 33,561 = 7.85M tokens
- Total tokens: ~24.63M tokens
- **Total cost**: (24.63M × $0.10) / 1M = **$2.46**

## Error Handling

### API Errors
- Request timeouts: 30-second timeout per request
- HTTP errors: Detailed error messages with status codes
- Rate limiting: Automatic 1-second delay between requests

### OCR Errors
- Invalid JSON responses: Regex extraction fallback
- Malformed entity data: Skip invalid entries
- File read errors: Log and continue processing

### Recovery
- Checkpoint every 1,000 documents
- Resume with `--resume` flag
- Skip already-processed documents

## Integration with Existing System

### Entity Matching

Match extracted entities with existing `entity_biographies.json`:

```python
# Load existing entities
with open('data/metadata/entity_biographies.json') as f:
    existing_entities = json.load(f)['entities']

# Load extracted entities
with open('data/metadata/document_entities_raw.json') as f:
    extracted_entities = json.load(f)['entities']

# Find matches
for norm_name, entity_data in extracted_entities.items():
    # Check if entity exists in biographies
    if norm_name in existing_entities:
        print(f"Match found: {entity_data['name']}")
```

### Document-Entity Graph

Use `document_entity_index.json` to build document-entity relationships:

```python
# Load document index
with open('data/metadata/document_entity_index.json') as f:
    doc_index = json.load(f)['document_entities']

# Find all documents mentioning specific entity
entity_name = "jeffrey epstein"
related_docs = [
    doc_id for doc_id, entities in doc_index.items()
    if entity_name in entities
]
```

## Next Steps

### 1. Run Full Extraction

```bash
# Start full extraction (33,561 documents)
nohup python3 scripts/analysis/extract_entities_from_documents.py \
  --output data/metadata/document_entities_raw.json \
  --checkpoint-every 1000 \
  > extraction.log 2>&1 &

# Monitor progress
tail -f extraction.log
```

### 2. Merge with Existing Entities

Create merge script to:
- Match extracted entities with existing entity records
- Add document sources to entity profiles
- Identify new entities not in current database
- Generate entity enrichment candidates

### 3. Entity Enrichment

Use extracted entities to:
- Enhance entity biographies with document context
- Build document-entity relationship graph
- Identify co-occurrence patterns
- Generate semantic search embeddings

## Troubleshooting

### Common Issues

**Problem**: `API key required`
**Solution**: Set `OPENROUTER_API_KEY` environment variable or use `--api-key`

**Problem**: `Input directory not found`
**Solution**: Verify OCR files are in `data/sources/house_oversight_nov2025/ocr_text/`

**Problem**: Rate limit errors
**Solution**: Script includes 1-second delay; OpenRouter free tier should handle this

**Problem**: Checkpoint not resuming
**Solution**: Ensure checkpoint file exists and use `--resume` flag

### Debug Mode

```bash
# Test with first 10 documents
python3 scripts/analysis/extract_entities_from_documents.py --limit 10

# Dry run (no API calls)
python3 scripts/analysis/extract_entities_from_documents.py --dry-run --limit 10
```

## Validation

### Sample Extraction Verification

```bash
# Extract entities from 100 documents
python3 scripts/analysis/extract_entities_from_documents.py --limit 100

# Check output
cat data/metadata/document_entities_raw.json | jq '.extraction_metadata'
cat data/metadata/document_entities_raw.json | jq '.entities | keys | length'

# View sample entities
cat data/metadata/document_entities_raw.json | jq '.entities | to_entries | .[0:5]'
```

### Quality Metrics

- **Entity name quality**: Check for nonsensical names or OCR artifacts
- **Type accuracy**: Verify person/organization/location classification
- **Deduplication**: Check that variations are merged correctly
- **Coverage**: Ensure major entities (Epstein, Maxwell) are extracted

## File Organization

Per project organization rules, all related files are in proper locations:

- **Script**: `scripts/analysis/extract_entities_from_documents.py`
- **Documentation**: `scripts/analysis/README_ENTITY_EXTRACTION.md`
- **Output**: `data/metadata/document_entities_raw.json`
- **Index**: `data/metadata/document_entity_index.json`
- **Checkpoints**: `data/metadata/*_checkpoint.json` (temporary)

---

**Created**: 2025-11-28
**Author**: Entity Extraction Enhancement System
**Related**: Entity Biography Enhancement System, Document Processing Pipeline
