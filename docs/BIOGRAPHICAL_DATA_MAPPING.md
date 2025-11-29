# Biographical Data Mapping Reference

**Quick Summary**: entities. yaml (Source of Truth).

**Category**: Documentation
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- Data Flow Architecture
- Field Mapping
- Core Identity Fields
- Biographical Content
- Temporal Data

---

## Data Flow Architecture

```
entities.yaml (Source of Truth)
         ↓
  sync_yaml_to_json_biographies.py
         ↓
entity_biographies.json (Backend Data)
         ↓
   EntityService.py (API Layer)
         ↓
   EntityBio.tsx (Frontend Display)
```

## Field Mapping

### Core Identity Fields

| entities.yaml | entity_biographies.json | Display Component |
|---------------|------------------------|-------------------|
| `id` | `id` | Entity identifier |
| `display_name` | `display_name` | Entity heading |
| `full_name` | `full_name` | Full legal name |
| `born` | `born` | Birth date (ISO format) |
| `died` | `died` | Death date (ISO format) |
| `birth_place` | `birth_place` | Birth location |
| `nationality` | `nationality` | Nationality |
| `occupation` | `occupation` | Primary occupation |

### Biographical Content

| entities.yaml | entity_biographies.json | EntityBio Component |
|---------------|------------------------|---------------------|
| `summary` | `summary` | Fallback display (`entity.bio?.summary`) |
| `full_biography` | `biography` | Primary display (`entity.bio?.biography`) |

**Display Logic:**
```typescript
entity.bio?.biography || entity.bio?.summary
```

### Temporal Data

| entities.yaml | entity_biographies.json | Frontend Format |
|---------------|------------------------|-----------------|
| `timeline_events` (array) | `timeline` (array) | Timeline component |
| `timeline_events[].date` | `timeline[].date` | ISO date string |
| `timeline_events[].event` | `timeline[].event` | Event description |

### Relationship Data

| entities.yaml | entity_biographies.json | Usage |
|---------------|------------------------|-------|
| `relationships` (array) | `relationships` (array) | Network graph |
| `relationships[].name` | `relationships[].entity` | Related entity name |
| `relationships[].nature` | `relationships[].nature` | Relationship type |
| `relationships[].description` | `relationships[].description` | Context |

### Document References

| entities.yaml | entity_biographies.json | Purpose |
|---------------|------------------------|---------|
| `document_references` (array) | `document_references` (array) | Source attribution |

## Backend Integration

### EntityService.py

```python
# Load biographies
bio_path = self.metadata_dir / "entity_biographies.json"
if bio_path.exists():
    with open(bio_path) as f:
        data = json.load(f)
        self.entity_bios = data.get("entities", {})
```

### API Response Format

```json
{
  "id": "jeffrey_epstein",
  "display_name": "Jeffrey Edward Epstein",
  "bio": {
    "biography": "Full 500-800 word biography text...",
    "summary": "Brief 2-3 sentence summary...",
    "timeline": [...],
    "relationships": [...]
  }
}
```

## Frontend Display

### EntityBio Component (Fix 1M-108)

```typescript
// Fixed to check BOTH biography and summary fields
{(entity.bio?.biography || entity.bio?.summary) ? (
  <div className="entity-bio-content">
    {entity.bio.biography || entity.bio.summary}
  </div>
) : (
  <div className="no-bio-fallback">
    No biographical information available.
  </div>
)}
```

**Why Both Fields?**
- 81 entities have `biography` field (AI-generated, 150-250 words)
- 17 entities have `summary` field (manually curated, 2-3 sentences)
- 8 primary entities NOW have BOTH fields (500-800 word biography + summary)

## Data Quality Standards

### Biography Content
- **Length:** 500-800 words
- **Tone:** Factual, neutral, unbiased
- **Sources:** Minimum 2 verifiable public sources per fact
- **Format:** Plain text with proper paragraph breaks

### Timeline Events
- **Date Format:** ISO 8601 (YYYY-MM-DD)
- **Precision:** Match available source precision (year, month, or day)
- **Content:** Brief factual description
- **Order:** Chronological

### Relationships
- **Entity Names:** Must match display_name of related entity
- **Nature:** Brief label (e.g., "Associate", "Client", "Accuser")
- **Description:** 1-2 sentence context explaining relationship

## Migration Script Usage

### Basic Sync
```bash
python3 scripts/migration/sync_yaml_to_json_biographies.py
```

### Dry Run (Preview Changes)
```bash
python3 scripts/migration/sync_yaml_to_json_biographies.py --dry-run
```

### Output
```
📖 Reading YAML entities from: data/entities.yaml
📖 Reading JSON biographies from: data/metadata/entity_biographies.json

✓ Loaded 8 entities from YAML
✓ Loaded 98 entities from JSON

🔄 Syncing biographical data...

============================================================
UPDATES SUMMARY
============================================================
  • jeffrey_epstein: born, died, biography, timeline, relationships
  • ghislaine_maxwell: born, biography, timeline, relationships
  ...

✅ SYNC COMPLETE
```

## Validation Checks

### Pre-Sync Validation
1. ✅ YAML file exists and is valid
2. ✅ JSON file exists and is valid
3. ✅ All entity IDs in YAML match expected format

### Post-Sync Validation
1. ✅ JSON syntax valid
2. ✅ All biographies >= 500 words
3. ✅ All timeline dates in ISO format
4. ✅ All relationships properly structured
5. ✅ Backend can load JSON successfully
6. ✅ No data loss from original entities

## Troubleshooting

### Biography Not Displaying

**Check 1: Does entity have biography data?**
```bash
python3 -c "
import json
data = json.load(open('data/metadata/entity_biographies.json'))
entity = data['entities']['entity_id']
print('Has biography:', 'biography' in entity)
print('Has summary:', 'summary' in entity)
"
```

**Check 2: Is backend loading the data?**
```bash
# Check server logs for:
# "Loaded N entity biographies"
```

**Check 3: Is frontend checking both fields?**
```typescript
// Should be:
entity.bio?.biography || entity.bio?.summary

// NOT just:
entity.bio?.biography
```

### Sync Script Errors

**"Entity not found in YAML"**
- Check entity ID matches exactly (case-sensitive)
- Verify entity exists in entities.yaml

**"JSON validation failed"**
- Check for syntax errors in generated JSON
- Script automatically restores backup on failure

**"No changes detected"**
- Verify entities.yaml has updated data
- Run with `--dry-run` to see what would change

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-23 | 1.0 | Initial sync of 8 primary entities |

## Related Files

- `/data/entities.yaml` - YAML source data
- `/data/metadata/entity_biographies.json` - JSON backend data
- `/scripts/migration/sync_yaml_to_json_biographies.py` - Migration script
- `/server/services/entity_service.py` - Backend loader
- `/frontend/src/components/entity/EntityBio.tsx` - Frontend display
- `/IMPLEMENTATION_SUMMARY_BIOGRAPHY_SYNC.md` - Implementation summary

## Metadata Tracking

The sync script updates metadata in entity_biographies.json:

```json
{
  "metadata": {
    "last_updated": "2025-11-23T22:05:17.809870",
    "yaml_sync_date": "2025-11-23T22:05:17.809865",
    "yaml_sync_entities": 8,
    "total_entities": 98
  }
}
```

This allows tracking:
- When last sync occurred
- How many entities were synced
- Total entities in system

## Best Practices

### Adding New Biographies

1. Add comprehensive biography to `data/entities.yaml`
2. Follow existing format (500-800 words)
3. Include timeline events with ISO dates
4. Document relationships
5. Run sync script with `--dry-run` first
6. Review changes before final sync
7. Validate in frontend

### Updating Existing Biographies

1. Edit `data/entities.yaml` directly
2. Maintain existing structure
3. Re-run sync script
4. Script merges changes automatically
5. Backup created automatically

### Quality Control

- Always run `--dry-run` first
- Check word count (500-800 target)
- Verify all dates in ISO format
- Ensure relationships reference valid entities
- Test frontend display after sync
- Review backup if rollback needed
