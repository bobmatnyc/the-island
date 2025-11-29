# House Oversight OCR Processing

## Overview
Automated OCR processing system for 33,572 House Oversight Committee PDF documents with parallel processing, email detection, and comprehensive progress tracking.

---

## Quick Status Check

```bash
# Check current processing status
cd /Users/masa/Projects/Epstein
source .venv/bin/activate
python scripts/extraction/check_ocr_status.py
```

---

## Processing Details

### Source Data
- **Location**: `/Users/masa/Projects/Epstein/data/sources/house_oversight_nov2025/epstein-pdf/`
- **File Count**: 33,572 single-page PDF files
- **File Type**: Scanned images (no text layer)
- **Naming Pattern**: `DOJ-OGR-00000001.pdf` through `DOJ-OGR-00033572.pdf`

### OCR Configuration
- **Engine**: Tesseract OCR
- **DPI**: 300 (balance between quality and speed)
- **Parallel Workers**: 10 concurrent processes
- **Batch Size**: 1,000 files per batch
- **Tesseract Mode**: LSTM OCR engine (--oem 3) with uniform text block assumption (--psm 6)

### Performance Metrics
- **Average Processing Time**: ~0.14 seconds per file
- **Estimated Total Time**: ~1.5-2 hours for all 33,572 files
- **Processing Rate**: ~7-8 files/second
- **Batch Processing Rate**: ~2.5 minutes per 1,000 files

---

## Output Structure

### OCR Text Output
**Location**: `/Users/masa/Projects/Epstein/data/sources/house_oversight_nov2025/ocr_text/`

Each PDF generates two files:
1. **Text File** (`DOJ-OGR-00000001.txt`): Extracted OCR text
2. **Metadata File** (`DOJ-OGR-00000001.json`): Processing metadata

**Metadata Format**:
```json
{
  "source_pdf": "DOJ-OGR-00000001.pdf",
  "ocr_date": "2025-11-16T20:48:39.123456",
  "text_length": 757,
  "is_email": false,
  "email_confidence": 0.0,
  "email_addresses": []
}
```

### Progress Tracking
**Location**: `/Users/masa/Projects/Epstein/data/sources/house_oversight_nov2025/ocr_progress.json`

Tracks:
- Completed files
- Failed files
- Email candidates
- Processing statistics

### Email Detection Index
**Location**: `/Users/masa/Projects/Epstein/data/sources/house_oversight_nov2025/email_candidates.jsonl`

JSONL format (one JSON object per line):
```json
{"file": "DOJ-OGR-00012345.pdf", "confidence": 0.85, "email_addresses": ["someone@example.com"]}
```

### Logs
**Location**: `/Users/masa/Projects/Epstein/logs/ocr_house_oversight.log`

Contains:
- Processing progress
- Batch completion statistics
- Estimated time remaining
- Error messages

---

## Background Processing

### Starting OCR Processing

```bash
# Start background processing
/Users/masa/Projects/Epstein/scripts/extraction/start_ocr_background.sh
```

The script will output:
- Process ID (PID)
- Log file location
- Status check command
- Stop command

### Checking Process Status

```bash
# Quick status check
cd /Users/masa/Projects/Epstein
source .venv/bin/activate
python scripts/extraction/check_ocr_status.py

# View live log
tail -f /Users/masa/Projects/Epstein/logs/ocr_house_oversight.log

# Check if process is running
ps aux | grep ocr_house_oversight.py | grep -v grep
```

### Stopping Processing

```bash
# Stop the background process
kill $(cat /Users/masa/Projects/Epstein/logs/ocr_process.pid)

# Force stop if needed
pkill -f ocr_house_oversight.py
```

### Resuming Processing

The system has **automatic resume capability**. If processing is interrupted:

```bash
# Simply restart - it will resume from last checkpoint
/Users/masa/Projects/Epstein/scripts/extraction/start_ocr_background.sh
```

The script automatically:
- Loads previous progress
- Skips already-processed files
- Continues from where it left off

---

## Email Detection

### Detection Logic

The system uses a multi-factor confidence scoring system to identify emails:

**Email Indicators**:
1. **Email Addresses** (40% confidence): Pattern `name@domain.com`
2. **Email Headers** (30% confidence): From:, To:, Subject:, Date:, etc.
3. **Email Keywords** (20% confidence): "original message", "forwarded message", "replied", etc.

**Confidence Threshold**: 0.5 (50%)
- Files with confidence >= 0.5 are flagged as email candidates

### Email Detection Patterns

```python
# Email address pattern
r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

# Email header patterns
r'^(From|To|Cc|Bcc|Subject|Date):\s*'
r'\b(sent|received|forwarded):\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
r'\b(original message|forwarded message)\b'
```

### Accessing Email Candidates

```bash
# View email candidates
cat /Users/masa/Projects/Epstein/data/sources/house_oversight_nov2025/email_candidates.jsonl

# Count email candidates
wc -l /Users/masa/Projects/Epstein/data/sources/house_oversight_nov2025/email_candidates.jsonl

# Extract emails with high confidence
cat email_candidates.jsonl | jq 'select(.confidence > 0.7)'
```

---

## Scripts Reference

### Main OCR Processing Script
**Location**: `/Users/masa/Projects/Epstein/scripts/extraction/ocr_house_oversight.py`

**Usage**:
```bash
python ocr_house_oversight.py [OPTIONS]

Options:
  --workers N        Number of parallel workers (default: 10)
  --batch-size N     Batch size for processing (default: 1000)
  --resume           Resume from previous progress (default: false)
  --test N           Process only N files for testing
```

**Examples**:
```bash
# Test with 100 files
python ocr_house_oversight.py --test 100 --workers 10

# Full processing with resume
python ocr_house_oversight.py --workers 10 --batch-size 1000 --resume

# Smaller batches (more frequent checkpoints)
python ocr_house_oversight.py --workers 10 --batch-size 500 --resume
```

### Status Monitor Script
**Location**: `/Users/masa/Projects/Epstein/scripts/extraction/check_ocr_status.py`

**Usage**:
```bash
python check_ocr_status.py
```

**Output**:
- Progress percentage and progress bar
- Files completed/failed
- Email candidates found
- Elapsed time and estimated completion
- Processing rate
- Last update timestamp

### Background Start Script
**Location**: `/Users/masa/Projects/Epstein/scripts/extraction/start_ocr_background.sh`

**Usage**:
```bash
./start_ocr_background.sh
```

Automatically handles:
- Virtual environment activation
- Background process spawning
- PID tracking
- Log file setup

---

## Current Status

### Processing Information
- **Start Time**: 2025-11-16 20:49:01
- **Background Process ID**: 29722
- **Current Progress**: Check with `python check_ocr_status.py`
- **Expected Completion**: ~1.5-2 hours from start

### Monitoring Commands

```bash
# Full status dashboard
python scripts/extraction/check_ocr_status.py

# Watch log in real-time
tail -f logs/ocr_house_oversight.log

# Check files processed
find data/sources/house_oversight_nov2025/ocr_text -name "*.txt" | wc -l

# Check process is running
ps aux | grep ocr_house_oversight.py | grep -v grep

# Check memory usage
ps aux | grep ocr_house_oversight.py | grep -v grep | awk '{print $3, $4, $11}'
```

---

## Error Handling

### Resume on Failure

If processing crashes or is interrupted:

```bash
# Simply restart - automatic resume
/Users/masa/Projects/Epstein/scripts/extraction/start_ocr_background.sh
```

### Manual Recovery

If progress file is corrupted:

```bash
# Backup current progress
cp data/sources/house_oversight_nov2025/ocr_progress.json ocr_progress.backup.json

# Check what's been processed
find data/sources/house_oversight_nov2025/ocr_text -name "*.txt" | wc -l

# Start fresh (will skip existing files)
python scripts/extraction/ocr_house_oversight.py --workers 10 --resume
```

### Failed Files

Check failed files in progress JSON:

```bash
# View failed files
cat data/sources/house_oversight_nov2025/ocr_progress.json | jq '.failed'

# Count failures
cat data/sources/house_oversight_nov2025/ocr_progress.json | jq '.failed | length'
```

---

## Performance Optimization

### Current Settings (Optimized)
- **Workers**: 10 (optimal for most systems)
- **Batch Size**: 1,000 files (good checkpoint frequency)
- **DPI**: 300 (balance quality/speed)

### Tuning Guidelines

**If System is Slow**:
```bash
# Reduce workers
python ocr_house_oversight.py --workers 5 --resume
```

**If System Has More Resources**:
```bash
# Increase workers (test first)
python ocr_house_oversight.py --workers 15 --resume
```

**For More Frequent Checkpoints**:
```bash
# Smaller batches
python ocr_house_oversight.py --batch-size 500 --resume
```

---

## Next Steps After OCR Completion

1. **Verify Completion**:
   ```bash
   python scripts/extraction/check_ocr_status.py
   # Should show 33,572 / 33,572 files (100%)
   ```

2. **Check Email Candidates**:
   ```bash
   wc -l data/sources/house_oversight_nov2025/email_candidates.jsonl
   ```

3. **Quality Checks**:
   ```bash
   # Check for empty files
   find data/sources/house_oversight_nov2025/ocr_text -name "*.txt" -size 0

   # Check sample files
   head -20 data/sources/house_oversight_nov2025/ocr_text/DOJ-OGR-00001000.txt
   ```

4. **Begin Email Processing**:
   - Parse email candidates
   - Extract email metadata
   - Canonicalize email addresses
   - Build relationship graphs

---

## Troubleshooting

### Process Not Running

```bash
# Check if process died
ps aux | grep ocr_house_oversight.py | grep -v grep

# Check last log entry
tail -20 /Users/masa/Projects/Epstein/logs/ocr_house_oversight.log

# Restart if needed
/Users/masa/Projects/Epstein/scripts/extraction/start_ocr_background.sh
```

### Slow Processing

```bash
# Check CPU usage
top -pid $(cat /Users/masa/Projects/Epstein/logs/ocr_process.pid)

# Reduce workers if CPU maxed
kill $(cat /Users/masa/Projects/Epstein/logs/ocr_process.pid)
python scripts/extraction/ocr_house_oversight.py --workers 5 --resume &
```

### Out of Disk Space

```bash
# Check disk usage
df -h /Users/masa/Projects/Epstein

# Estimated final size: ~500-800 MB for all text files
```

---

## System Requirements

### Verified Working On
- **OS**: macOS (Darwin 24.6.0)
- **Python**: 3.13.7
- **Tesseract**: Installed via Homebrew
- **Memory**: ~70-100 MB process size
- **Disk Space**: ~1 GB needed for output

### Dependencies
```
pytesseract==0.3.13
pdf2image==1.17.0
pillow==12.0.0
tqdm==4.67.1
```

Installed in virtual environment at: `/Users/masa/Projects/Epstein/.venv`

---

## Contact & Support

For issues or questions about this OCR processing system:
1. Check logs: `/Users/masa/Projects/Epstein/logs/ocr_house_oversight.log`
2. Review progress: `python scripts/extraction/check_ocr_status.py`
3. Check this README for troubleshooting steps

---

**Last Updated**: 2025-11-16
**Document Version**: 1.0
