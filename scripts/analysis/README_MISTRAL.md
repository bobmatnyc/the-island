# Mistral Entity Disambiguation - Quick Reference

## Quick Start

### 1. Install (One-Time Setup)
```bash
cd /Users/masa/Projects/Epstein
bash scripts/analysis/setup_mistral.sh
```

### 2. Test the System
```bash
python3 scripts/analysis/mistral_entity_disambiguator.py
```

### 3. Disambiguate High-Priority Entities
```bash
python3 scripts/analysis/batch_entity_disambiguation.py --priority high --max-count 10
```

## Common Commands

### Preview Without Saving (Dry Run)
```bash
python3 scripts/analysis/batch_entity_disambiguation.py --dry-run
```

### Process Specific Entities
```bash
python3 scripts/analysis/batch_entity_disambiguation.py --entities "Ghislaine" "Nadia"
```

### Process All Ambiguous Entities
```bash
python3 scripts/analysis/batch_entity_disambiguation.py --priority all
```

## Priority Levels

- `--priority high`: Single names with 10+ flights (20 entities)
- `--priority medium`: Single names with <10 flights (24 entities)
- `--priority all`: All ambiguous entities (44 entities)

## Current Ambiguous Entities (Top 10)

| Name | Flights | Priority | Suggested Fix |
|------|---------|----------|--------------|
| Ghislaine | 520 | HIGH | Maxwell, Ghislaine |
| Female (1) | 120 | HIGH | [Needs identification] |
| Nadia | 125 | HIGH | [Need full name] |
| Didier | 32 | HIGH | [Need full name] |
| Gramza | 20 | HIGH | [Need full name] |
| Lang | 18 | MEDIUM | [Need full name] |
| Casey | 10 | MEDIUM | [Need full name] |
| Teal | 6 | MEDIUM | [Need full name] |
| Elizabeth | 3 | LOW | [Need full name] |
| Nicole | 3 | LOW | [Need full name] |

## Interactive Workflow

When you run batch processing:

1. **System shows entity**:
   ```
   Entity: Ghislaine
   Flights: 520
   Sources: ['flight_logs']
   ```

2. **Mistral suggests name** (2-5 seconds):
   ```
   Suggested: Maxwell, Ghislaine
   Confidence: 0.95
   Reasoning: Court documents confirm...
   ```

3. **You decide**:
   - Type `y` to accept
   - Type `n` to reject
   - Type `skip` to skip

4. **System saves**:
   - Updates entity index
   - Creates automatic backup
   - Logs change with timestamp

## Data Safety

- ✅ Automatic backups before every save
- ✅ Complete changelog of all changes
- ✅ Human confirmation required
- ✅ Easy rollback if needed

### Backups Location
```
data/metadata/entity_index_backups/ENTITIES_INDEX_[timestamp].json
```

### Changelog Location
```
data/metadata/disambiguation_changelog.json
```

## Performance

| Hardware | Speed | Batch Rate |
|----------|-------|------------|
| M1 Mac | 2-3 sec/entity | ~150/hour |
| M2 Mac | 1-2 sec/entity | ~200/hour |
| RTX 3090 | 0.5-1 sec/entity | ~400/hour |
| CPU-only | 5-10 sec/entity | ~50/hour |

*Batch rate includes user confirmation time*

## Troubleshooting

### Model won't load
```bash
# Check RAM usage
free -h  # Linux
vm_stat  # macOS

# If low on RAM, close other apps
```

### Slow performance
```python
# Check if GPU/MPS is being used
python3 -c "
from scripts.analysis.mistral_entity_disambiguator import MistralEntityDisambiguator
d = MistralEntityDisambiguator()
print(f'Device: {d.device}')  # Should be 'cuda' or 'mps', not 'cpu'
"
```

### Import errors
```bash
pip install transformers torch accelerate
```

## Next Steps

1. **Start small**: Process 10 high-priority entities
   ```bash
   python3 scripts/analysis/batch_entity_disambiguation.py --priority high --max-count 10
   ```

2. **Review results**: Check changelog
   ```bash
   cat data/metadata/disambiguation_changelog.json | python3 -m json.tool
   ```

3. **Continue**: Process remaining entities
   ```bash
   python3 scripts/analysis/batch_entity_disambiguation.py --priority high
   ```

## Help

For detailed documentation, see:
- `docs/MISTRAL_DISAMBIGUATION.md` - Full documentation
- `scripts/analysis/mistral_entity_disambiguator.py` - Source code with docstrings

For command help:
```bash
python3 scripts/analysis/batch_entity_disambiguation.py --help
```
