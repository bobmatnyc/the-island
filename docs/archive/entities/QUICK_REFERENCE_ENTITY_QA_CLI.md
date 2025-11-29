# Entity QA Quick Reference - Ollama CLI Version

**Quick Summary**: Historical documentation archived for reference purposes.

**Category**: Archive
**Status**: Historical
**Last Updated**: 2025-11-24

**Key Points**:
- 🚀 Quick Start
- ✅ Prerequisites
- 📋 Command Options
- 📊 What It Checks
- 📄 Output

---

## 🚀 Quick Start

```bash
# Test with 5 entities
python3 scripts/analysis/comprehensive_entity_qa.py --max 5

# Process all entities (takes ~4-5 hours for 1639 entities)
python3 scripts/analysis/comprehensive_entity_qa.py

# Use different model
python3 scripts/analysis/comprehensive_entity_qa.py --model llama3.1:latest --max 5
```

## ✅ Prerequisites

1. **Ollama installed**
   ```bash
   # macOS
   brew install ollama

   # Linux
   curl https://ollama.ai/install.sh | sh
   ```

2. **Model pulled**
   ```bash
   ollama pull mistral-small3.2:latest
   ```

## 📋 Command Options

| Option | Description | Example |
|--------|-------------|---------|
| `--max N` | Analyze only N entities | `--max 10` |
| `--start N` | Start from entity N | `--start 100` |
| `--model NAME` | Use specific model | `--model llama3.1:latest` |
| `--skip-check` | Skip CLI validation | `--skip-check` (not recommended) |

## 📊 What It Checks

1. **Punctuation**: "LastName, FirstName" format
2. **Disambiguation**: Single names → full names
3. **Classification**: PERSON | ORGANIZATION | LOCATION | AIRCRAFT
4. **Duplicates**: Possible duplicate entries

## 📄 Output

**Report Location**: `data/metadata/comprehensive_entity_qa_report.json`

**Checkpoint**: Auto-saves every 100 entities to `.checkpoint.json`

## 🔍 Example Output

```bash
================================================================================
COMPREHENSIVE ENTITY QA
Disambiguation | Classification | Punctuation | Deduplication
Using Ollama CLI (no API server required)
================================================================================

Checking Ollama CLI availability...
✅ Ollama CLI available
✅ Model mistral-small3.2:latest is available

Analyzing 5 entities...

[1/5] Analyzing: Abby
[2/5] Analyzing: Adams, Kent
  💡 Disambiguation: Adams, Kent → Adams, Kent P.
     Reason: Full name in black book records
[3/5] Analyzing: Adriana, Ross
  ⚠️  Punctuation: Adriana, Ross → Ross, Adriana
[4/5] Analyzing: Alexander, Rika
[5/5] Analyzing: Allen, Woody
  🔄 Possible duplicate of: Allen, Heywood (Woody)

📊 Total entities analyzed: 5
📝 Punctuation errors: 1
🔍 Disambiguation needed: 1
🏷️  Classification suggestions: 0
🔄 Possible duplicates: 1
```

## 🛠️ Troubleshooting

### Ollama Not Found
```bash
# Check installation
which ollama

# Install if missing
brew install ollama  # macOS
```

### Model Not Available
```bash
# Check installed models
ollama list

# Pull the model
ollama pull mistral-small3.2:latest
```

### Timeout Issues
```bash
# Use smaller/faster model
python3 scripts/analysis/comprehensive_entity_qa.py --model mistral:latest

# Or edit timeout in code (line 118)
# Change: timeout=45  →  timeout=60
```

### Script Hangs
```bash
# Kill background ollama processes
pkill -f ollama

# Restart script
python3 scripts/analysis/comprehensive_entity_qa.py --max 5
```

## 📈 Performance

- **Per Entity**: ~10-15 seconds
- **100 Entities**: ~15-25 minutes
- **1639 Entities**: ~4-5 hours
- **Checkpoint**: Every 100 entities (auto-saves)

## 💡 Pro Tips

1. **Test First**: Always test with `--max 5` before full run
2. **Resume**: Use `--start N` to resume from checkpoint
3. **Batch Process**: Process in chunks during off-hours
4. **Monitor**: Watch for patterns in error messages
5. **Review**: Check report after each batch before continuing

## 🔄 Recovery

### Resume from Checkpoint
```bash
# If stopped at entity 237, resume:
python3 scripts/analysis/comprehensive_entity_qa.py --start 237
```

### Use Checkpoint File
```bash
# Checkpoint saved every 100 entities
cat data/metadata/comprehensive_entity_qa_report.checkpoint.json
```

## 📦 Dependencies

**NONE** - Uses only Python built-ins:
- ✅ `subprocess` (CLI execution)
- ✅ `json` (data processing)
- ✅ `pathlib` (file handling)
- ❌ No `requests` needed
- ❌ No external libraries

## 🎯 Common Workflows

### Test Run
```bash
python3 scripts/analysis/comprehensive_entity_qa.py --max 5
```

### Small Batch
```bash
python3 scripts/analysis/comprehensive_entity_qa.py --max 50
```

### Resume Processing
```bash
# Check how many processed
cat data/metadata/comprehensive_entity_qa_report.json | grep "total_analyzed"

# Resume from that point
python3 scripts/analysis/comprehensive_entity_qa.py --start 50
```

### Full Run (Background)
```bash
# Run in background with log
nohup python3 scripts/analysis/comprehensive_entity_qa.py > entity_qa.log 2>&1 &

# Monitor progress
tail -f entity_qa.log
```

## 📋 Report Format

```json
{
  "timestamp": "2025-11-18T01:59:50.572844",
  "model": "mistral-small3.2:latest",
  "total_analyzed": 1,
  "issues_found": {
    "punctuation": 0,
    "disambiguation": 0,
    "classification": 0,
    "duplicates": 0
  },
  "results": [
    {
      "name": "Abby",
      "punctuation_ok": true,
      "disambiguation_ok": true,
      "classification": "PERSON",
      "duplicate_of": null
    }
  ]
}
```

## 🚨 Important Notes

1. **No API Server**: Runs without Ollama server/app
2. **CLI Only**: Uses `ollama run` command directly
3. **Auto-Checkpoint**: Saves progress every 100 entities
4. **Interruption Safe**: Can resume from any point
5. **No State**: Each run is independent

## 🎓 Advanced Usage

### Custom Timeout
Edit line 118 in `comprehensive_entity_qa.py`:
```python
def call_ollama(self, prompt: str, timeout=60):  # Increase from 45
```

### Different Model
```bash
# List available models
ollama list

# Use different model
python3 scripts/analysis/comprehensive_entity_qa.py \
  --model llama3.1:latest \
  --max 10
```

### Parallel Processing
```bash
# Process different ranges in parallel
python3 scripts/analysis/comprehensive_entity_qa.py --start 0 --max 400 &
python3 scripts/analysis/comprehensive_entity_qa.py --start 400 --max 400 &
python3 scripts/analysis/comprehensive_entity_qa.py --start 800 --max 400 &

# WARNING: Merges reports manually after completion
```

## 📞 Support

**File**: `scripts/analysis/comprehensive_entity_qa.py`
**Documentation**: `OLLAMA_CLI_MIGRATION_COMPLETE.md`
**Issues**: Check error messages - they include solutions

---

**Last Updated**: 2025-11-18
**Version**: 2.0 (CLI-based)
**Status**: Production Ready ✅
