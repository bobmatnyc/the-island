# Download Management Commands

**Quick Summary**: Historical documentation archived for reference purposes.

**Category**: Archive
**Status**: Historical
**Last Updated**: 2025-11-24

**Key Points**:
- Check Current Status
- View Logs
- Check Downloaded Files

---

Quick reference for monitoring and managing Epstein document downloads.

## Check Current Status

```bash
# Quick status check
bash /Users/masa/Projects/Epstein/scripts/check_download_status.sh

# View quick summary
cat /Users/masa/Projects/Epstein/logs/downloads/QUICK_SUMMARY.txt

# View detailed manifest
cat /Users/masa/Projects/Epstein/DOWNLOAD_MANIFEST.md
```

## View Logs

```bash
# View all logs
ls -lh /Users/masa/Projects/Epstein/logs/downloads/*.log

# Tail specific logs
tail -50 /Users/masa/Projects/Epstein/logs/downloads/fbi_vault.log
tail -50 /Users/masa/Projects/Epstein/logs/downloads/internet_archive.log
tail -50 /Users/masa/Projects/Epstein/logs/downloads/documentcloud_extra.log
tail -50 /Users/masa/Projects/Epstein/logs/downloads/house_oversight_sept2024.log

# View master coordinator log
tail -50 /Users/masa/Projects/Epstein/logs/downloads/master.log
```

## Check Downloaded Files

```bash
# List all downloaded files
find /Users/masa/Projects/Epstein/data/sources -name "*.pdf" -type f | wc -l

# List by source
for dir in /Users/masa/Projects/Epstein/data/sources/*/; do
    count=$(find "$dir" -name "*.pdf" 2>/dev/null | wc -l | tr -d ' ')
    size=$(du -sh "$dir" 2>/dev/null | awk '{print $1}')
    echo "$(basename "$dir"): $count PDFs ($size)"
done

# Check new House Oversight Sept 2024 files
ls -lh /Users/masa/Projects/Epstein/data/sources/house_oversight_sept2024/

# Verify PDFs are valid
file /Users/masa/Projects/Epstein/data/sources/house_oversight_sept2024/*.pdf
```

## Storage Usage

```bash
# Total storage by source
du -sh /Users/masa/Projects/Epstein/data/sources/*

# Detailed storage breakdown
du -h /Users/masa/Projects/Epstein/data/sources/ | sort -h

# Total project size
du -sh /Users/masa/Projects/Epstein/
```

## Re-run Downloads

```bash
# Re-run all downloads
bash /Users/masa/Projects/Epstein/scripts/parallel_downloads_master.sh

# Run individual downloads
bash /Users/masa/Projects/Epstein/scripts/download_fbi_vault.sh
bash /Users/masa/Projects/Epstein/scripts/download_internet_archive.sh
bash /Users/masa/Projects/Epstein/scripts/download_documentcloud.sh
bash /Users/masa/Projects/Epstein/scripts/download_house_oversight_sept2024.sh
```

## Process Management

```bash
# Check if downloads are running
cat /Users/masa/Projects/Epstein/logs/downloads/download_pids.txt

# Check specific processes
ps -p $(cat /Users/masa/Projects/Epstein/logs/downloads/download_pids.txt | cut -d: -f2 | tr '\n' ',')

# Kill all download processes (if needed)
while IFS=: read -r name pid; do
    kill $pid 2>/dev/null && echo "Killed $name (PID: $pid)"
done < /Users/masa/Projects/Epstein/logs/downloads/download_pids.txt
```

## Manual Download Guides

### FBI Vault (CRITICAL - 22 parts)

```bash
# Visit in browser:
open https://vault.fbi.gov/jeffrey-epstein

# Or use this command to see all URLs:
for i in {01..22}; do
    echo "Part $i: https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%20$i%20of%2022/view"
done

# After manual download, verify:
ls -lh /Users/masa/Projects/Epstein/data/sources/fbi_vault/
```

### Internet Archive Collections

```bash
# Open each collection in browser:
open https://archive.org/details/jeffrey-epstein-documents-collection_202502
open https://archive.org/details/epstein-flight-logs
open https://archive.org/details/epstein-black-book
open https://archive.org/details/ghislaine-maxwell-documents
```

### DocumentCloud

```bash
# Search manually:
open https://www.documentcloud.org/

# Or try authenticated API (requires account):
# 1. Create account at documentcloud.org
# 2. Get API key
# 3. Use API with authentication headers
```

### Google Drive (House Oversight Sept 2024)

```bash
# Open folder:
open https://drive.google.com/drive/folders/1ZSVpXEhI7gKI0zatJdYe6QhKJ5pjUo4b

# Check what was already downloaded:
ls -lh /Users/masa/Projects/Epstein/data/sources/house_oversight_sept2024/
```

## Cleanup

```bash
# Remove failed/empty downloads
find /Users/masa/Projects/Epstein/data/sources -type f -size 0 -delete

# Clear old logs (be careful!)
# rm /Users/masa/Projects/Epstein/logs/downloads/*.log

# Remove metadata files (keep PDFs only)
find /Users/masa/Projects/Epstein/data/sources/internet_archive -type f ! -name "*.pdf" -delete
find /Users/masa/Projects/Epstein/data/sources/documentcloud_extra -type f ! -name "*.pdf" -delete
```

## Integration with OCR

```bash
# Add new files to OCR queue
# (Assuming OCR system is set up)

# Check if new files need OCR
find /Users/masa/Projects/Epstein/data/sources/house_oversight_sept2024 -name "*.pdf" -type f

# Verify no conflicts with running OCR processes
ps aux | grep -i ocr

# Start OCR on new files (example command - adjust for your OCR system)
# for file in /Users/masa/Projects/Epstein/data/sources/house_oversight_sept2024/*.pdf; do
#     ocrmypdf "$file" "${file%.pdf}_ocr.pdf"
# done
```

## Monitoring During Downloads

```bash
# Watch download progress live
watch -n 5 'bash /Users/masa/Projects/Epstein/scripts/check_download_status.sh'

# Monitor network activity
nettop -p $(pgrep -f download_ | tr '\n' ',')

# Check download speeds
while true; do
    du -sh /Users/masa/Projects/Epstein/data/sources/house_oversight_sept2024/
    sleep 5
done
```

---

**Quick Start:**
```bash
# Check what was downloaded:
bash /Users/masa/Projects/Epstein/scripts/check_download_status.sh

# View the manifest:
cat /Users/masa/Projects/Epstein/DOWNLOAD_MANIFEST.md

# Next: Manually download FBI Vault (most important!)
open https://vault.fbi.gov/jeffrey-epstein
```
