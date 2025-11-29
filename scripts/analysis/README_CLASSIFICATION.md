# Entity Relationship Classification System

AI-powered entity classification using Grok LLM to analyze relationships, roles, and significance in the Epstein archive.

## Quick Start

```bash
# 1. Set API key
export OPENROUTER_API_KEY="your-api-key-here"

# 2. Test with dry run
python3 classify_entity_relationships.py --dry-run --limit 10

# 3. Classify high-value entities
python3 classify_entity_relationships.py --tier 1 --limit 50 --import-db

# 4. Verify results
sqlite3 ../../data/metadata/entities.db \
  "SELECT entity_id, primary_role, significance_score
   FROM entity_classifications
   ORDER BY significance_score DESC
   LIMIT 10;"
```

## Features

- **Multi-dimensional classification**: Role, strength, category, temporal, significance
- **Batch processing**: Efficient processing with checkpointing
- **Quality validation**: Pydantic models ensure data consistency
- **Error recovery**: Retry logic with exponential backoff
- **Database integration**: Direct import to SQLite
- **Cost tracking**: Monitor token usage and estimated costs

## Classification Dimensions

### 1. Primary Role
Main relationship to Epstein:
- Close Associate
- Business Partner
- Political Figure
- Victim
- Law Enforcement
- Legal Team
- Social Contact
- Family Member

### 2. Connection Strength
Based on quantitative metrics:
- **Core Circle**: >50 flights or high centrality
- **Frequent Associate**: 10-50 flights
- **Occasional Contact**: 1-9 flights
- **Documented Only**: No flights, document mentions only

### 3. Professional Category
Primary occupation/role:
- Politician, Celebrity, Financier
- Scientist, Legal Professional, Socialite
- Academic, Artist, Pilot, Staff Member

### 4. Temporal Activity
Decades of involvement:
- 1970s, 1980s, 1990s, 2000s, 2010s, 2020s

### 5. Significance Score
1-10 rating based on centrality and context:
- **10**: Central figures (Epstein, Maxwell)
- **8-9**: Key network players
- **6-7**: Regular associates
- **4-5**: Occasional contacts
- **2-3**: Peripheral mentions
- **1**: Minimal involvement

## Command Reference

### Basic Usage

```bash
# Dry run (no API calls)
python3 classify_entity_relationships.py --dry-run --limit 10

# Classify Tier 1 (15+ connections)
python3 classify_entity_relationships.py --tier 1

# Classify Tier 2 (10+ connections)
python3 classify_entity_relationships.py --tier 2

# Classify with custom limit
python3 classify_entity_relationships.py --tier 1 --limit 50
```

### Advanced Options

```bash
# Create backup before processing
python3 classify_entity_relationships.py --tier 1 --backup

# Classify and import to database
python3 classify_entity_relationships.py --tier 1 --import-db

# Custom output file
python3 classify_entity_relationships.py \
  --tier 1 \
  --output ../../data/metadata/classifications_custom.json

# Export existing JSON to database
python3 classify_entity_relationships.py \
  --export ../../data/metadata/entity_classifications.json \
  --import-db
```

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
    "average_significance_score": 6.8
  },
  "classifications": {
    "entity_id": {
      "entity_id": "entity_id",
      "entity_name": "Display Name",
      "primary_role": "Close Associate",
      "connection_strength": "Core Circle",
      "professional_category": "Socialite",
      "temporal_activity": ["1990s", "2000s"],
      "significance_score": 10,
      "justification": "Brief explanation...",
      "metadata": {
        "classified_by": "grok-beta",
        "classification_date": "2025-11-25T12:05:30Z",
        "flight_count": 502,
        "document_count": 4421,
        "connection_count": 102
      }
    }
  }
}
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
```

## Database Queries

### View Classifications

```sql
-- Top 10 by significance
SELECT e.display_name, c.primary_role, c.significance_score
FROM entity_classifications c
JOIN entities e ON c.entity_id = e.id
ORDER BY c.significance_score DESC
LIMIT 10;

-- By role
SELECT e.display_name, c.connection_strength, c.significance_score
FROM entity_classifications c
JOIN entities e ON c.entity_id = e.id
WHERE c.primary_role = 'Close Associate';

-- By connection strength
SELECT e.display_name, c.primary_role, c.professional_category
FROM entity_classifications c
JOIN entities e ON c.entity_id = e.id
WHERE c.connection_strength = 'Core Circle';

-- High significance entities
SELECT e.display_name, c.primary_role, c.justification
FROM entity_classifications c
JOIN entities e ON c.entity_id = e.id
WHERE c.significance_score >= 8
ORDER BY c.significance_score DESC;
```

## Performance

### Processing Speed
- **1 entity**: ~2 seconds (with rate limiting)
- **50 entities**: ~2 minutes
- **100 entities**: ~4 minutes
- **319 entities** (all with biographies): ~11 minutes

### Checkpointing
- Saves progress every 10 entities
- Automatic recovery on restart
- Cleanup after successful completion

## API Costs

### Free Period (Until Dec 3, 2025)
- **Model**: x-ai/grok-beta (free)
- **Rate**: Conservative 1.5s between requests

### Post-Free Pricing
- **Input**: ~$0.50 per million tokens
- **Output**: ~$1.50 per million tokens
- **Estimate**: ~$0.20-0.40 per 100 entities

## Tier Selection Guide

| Tier | Connections | Description | Count | Time |
|------|-------------|-------------|-------|------|
| 1 | 15+ | High-value entities | ~319 | ~11 min |
| 2 | 10-14 | Regular associates | ~150-200 | ~5-7 min |
| 3 | 5-9 | Occasional contacts | ~300-400 | ~10-13 min |
| All | 0+ | All entities | ~1600+ | ~53 min |

**Recommendation**: Start with Tier 1 for high-priority entities.

## Error Handling

### Common Issues

**API Key Not Set**
```bash
export OPENROUTER_API_KEY="your-key-here"
```

**No Entities Match Criteria**
```bash
# Use lower tier or "all"
python3 classify_entity_relationships.py --tier all
```

**Classification Failures**
- Check internet connection
- Verify API key validity
- Check Grok API status
- Review error messages

### Recovery

```bash
# Resume from checkpoint
python3 classify_entity_relationships.py --resume

# Start fresh (remove checkpoint)
rm ../../data/metadata/entity_classifications_checkpoint.json
```

## Validation

After classification, verify:

- [ ] Success rate >95%
- [ ] Sample classifications are accurate
- [ ] Database import completed
- [ ] Significance scores are reasonable
- [ ] Connection strength aligns with metrics
- [ ] Output files are backed up

## Integration

### Python Example

```python
import sqlite3
import json

# Query classifications
conn = sqlite3.connect('data/metadata/entities.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT e.display_name, c.primary_role, c.significance_score
    FROM entity_classifications c
    JOIN entities e ON c.entity_id = e.id
    WHERE c.significance_score >= 8
    ORDER BY c.significance_score DESC
""")

for name, role, score in cursor.fetchall():
    print(f"{name}: {role} (Score: {score})")

conn.close()
```

### REST API Example

```python
from fastapi import APIRouter
import sqlite3

@router.get("/api/entities/{entity_id}/classification")
async def get_classification(entity_id: str):
    conn = sqlite3.connect('data/metadata/entities.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT primary_role, connection_strength,
               significance_score, justification
        FROM entity_classifications
        WHERE entity_id = ?
    """, (entity_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"error": "Classification not found"}

    return {
        "primary_role": row[0],
        "connection_strength": row[1],
        "significance_score": row[2],
        "justification": row[3]
    }
```

## Documentation

- **Full Documentation**: `../../docs/implementation-summaries/ENTITY_CLASSIFICATION_SYSTEM.md`
- **Quick Reference**: `../../docs/reference/ENTITY_CLASSIFICATION_QUICK_REFERENCE.md`
- **Help Command**: `python3 classify_entity_relationships.py --help`

## Related Files

- **Database**: `data/metadata/entities.db`
- **Statistics**: `data/metadata/entity_statistics.json`
- **Biographies**: `data/metadata/entity_biographies.json`
- **Output**: `data/metadata/entity_classifications.json`

## Support

For issues or questions:
1. Check `--help` output
2. Review error messages
3. Test with `--dry-run`
4. Verify API key is set
5. Check Grok API status

## Example Session

```bash
# Complete workflow
export OPENROUTER_API_KEY="sk-or-v1-..."

# Test first
python3 classify_entity_relationships.py --dry-run --limit 5

# Classify Tier 1
python3 classify_entity_relationships.py --tier 1 --backup --import-db

# Verify results
sqlite3 ../../data/metadata/entities.db <<EOF
SELECT
    e.display_name,
    c.primary_role,
    c.connection_strength,
    c.significance_score
FROM entity_classifications c
JOIN entities e ON c.entity_id = e.id
ORDER BY c.significance_score DESC
LIMIT 10;
EOF
```

## Success Metrics

✅ Script successfully classifies entities using Grok LLM
✅ Database schema created and populated
✅ Batch processing with checkpoints works correctly
✅ Quality validation and error handling implemented
✅ Comprehensive documentation provided
✅ Production-ready code with Pydantic V2 compatibility
