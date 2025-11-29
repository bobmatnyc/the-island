# Entity Extraction - Quick Start Guide

Extract entities from 33,561 OCR documents using Ministral 8B.

## Quick Commands

### Test Run (Recommended First Step)
```bash
# Test with first 10 documents (dry run, no API calls)
python3 scripts/analysis/extract_entities_from_documents.py --dry-run --limit 10

# Test with real API on 100 documents
python3 scripts/analysis/extract_entities_from_documents.py --limit 100
```

### Full Production Run
```bash
# Run full extraction (33,561 documents, ~18 hours, ~$2.46)
nohup python3 scripts/analysis/extract_entities_from_documents.py \
  --output data/metadata/document_entities_raw.json \
  --checkpoint-every 1000 \
  > extraction.log 2>&1 &

# Monitor progress
tail -f extraction.log

# Check for errors
grep -i error extraction.log
```

### Resume After Interruption
```bash
# Resume from last checkpoint
python3 scripts/analysis/extract_entities_from_documents.py --resume
```

## Expected Output

```
Extracting entities: 100%|██████████| 33561/33561 [18:00:00<00:00, 0.52doc/s, entities=2500, cost=$2.46]

======================================================================
EXTRACTION COMPLETE
======================================================================
Total documents: 33,561
Documents processed: 33,561
Unique entities: 2,500
Total cost: $2.46
```

## Output Files

- **Main**: `data/metadata/document_entities_raw.json` (all entities with metadata)
- **Index**: `data/metadata/document_entity_index.json` (document → entity mapping)

## Performance

- **Speed**: ~0.5 docs/sec (with rate limiting)
- **Cost**: ~$0.0001 per document
- **Total**: ~$2.46 for all 33,561 documents
- **Time**: ~18 hours for full corpus

## Verification

```bash
# Check extraction metadata
cat data/metadata/document_entities_raw.json | jq '.extraction_metadata'

# Count unique entities
cat data/metadata/document_entities_raw.json | jq '.entities | keys | length'

# View sample entities
cat data/metadata/document_entities_raw.json | jq '.entities | to_entries | .[0:5]'

# Find documents mentioning specific entity
cat data/metadata/document_entity_index.json | \
  jq '.document_entities | to_entries | map(select(.value | contains(["jeffrey epstein"]))) | .[0:10]'
```

## Troubleshooting

**Issue**: API key required
**Fix**: `export OPENROUTER_API_KEY=sk-or-...`

**Issue**: Rate limit errors
**Fix**: Script includes 1-second delay, should not hit limits

**Issue**: Checkpoint not resuming
**Fix**: Ensure checkpoint file exists and use `--resume` flag

## Documentation

- **Full Guide**: `scripts/analysis/README_ENTITY_EXTRACTION.md`
- **Implementation**: `docs/implementation-summaries/ENTITY_EXTRACTION_FROM_OCR_DOCS.md`
- **Script**: `scripts/analysis/extract_entities_from_documents.py`

---

**Quick Start**: `python3 scripts/analysis/extract_entities_from_documents.py --limit 100`
