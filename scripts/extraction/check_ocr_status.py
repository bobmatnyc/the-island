#!/usr/bin/env python3
"""
OCR Processing Status Monitor
Quick status check for ongoing OCR processing
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

PROGRESS_FILE = Path("/Users/masa/Projects/Epstein/data/sources/house_oversight_nov2025/ocr_progress.json")
LOG_FILE = Path("/Users/masa/Projects/Epstein/logs/ocr_house_oversight.log")
EMAIL_INDEX_FILE = Path("/Users/masa/Projects/Epstein/data/sources/house_oversight_nov2025/email_candidates.jsonl")
TOTAL_FILES = 33572


def format_timedelta(td):
    """Format timedelta to human readable string"""
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")

    return " ".join(parts)


def main():
    print("\n" + "=" * 70)
    print("HOUSE OVERSIGHT OCR PROCESSING STATUS")
    print("=" * 70)

    # Check if processing has started
    if not PROGRESS_FILE.exists():
        print("\nStatus: NOT STARTED")
        print("Run: python scripts/extraction/ocr_house_oversight.py")
        return

    # Load progress
    with open(PROGRESS_FILE, 'r') as f:
        progress = json.load(f)

    stats = progress.get('stats', {})
    completed_count = len(progress.get('completed', []))
    failed_count = len(progress.get('failed', []))
    email_count = stats.get('emails_found', 0)

    # Calculate progress
    progress_pct = (completed_count / TOTAL_FILES) * 100 if TOTAL_FILES > 0 else 0

    print(f"\nProgress: {completed_count:,} / {TOTAL_FILES:,} files ({progress_pct:.2f}%)")
    print(f"Failed: {failed_count:,} files")
    print(f"Email candidates found: {email_count:,}")

    # Show progress bar
    bar_width = 50
    filled = int(bar_width * progress_pct / 100)
    bar = '█' * filled + '░' * (bar_width - filled)
    print(f"\n[{bar}] {progress_pct:.1f}%")

    # Time estimates
    start_time_str = stats.get('start_time')
    last_update_str = stats.get('last_update')

    if start_time_str and completed_count > 0:
        start_time = datetime.fromisoformat(start_time_str)
        elapsed = datetime.now() - start_time

        print(f"\nElapsed time: {format_timedelta(elapsed)}")

        # Estimate remaining time
        rate = completed_count / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
        remaining_files = TOTAL_FILES - completed_count

        if rate > 0:
            eta_seconds = remaining_files / rate
            eta = timedelta(seconds=int(eta_seconds))
            print(f"Estimated time remaining: {format_timedelta(eta)}")

            completion_time = datetime.now() + eta
            print(f"Estimated completion: {completion_time.strftime('%Y-%m-%d %H:%M:%S')}")

            # Processing rate
            files_per_hour = rate * 3600
            print(f"\nProcessing rate: {files_per_hour:.1f} files/hour")

    if last_update_str:
        last_update = datetime.fromisoformat(last_update_str)
        time_since_update = datetime.now() - last_update
        print(f"\nLast update: {format_timedelta(time_since_update)} ago")

        if time_since_update.total_seconds() > 300:  # 5 minutes
            print("⚠️  WARNING: No updates in over 5 minutes. Process may be stalled.")

    # Recent failures
    if failed_count > 0:
        print(f"\n⚠️  {failed_count} files failed to process")
        recent_failures = progress.get('failed', [])[-5:]
        print("\nRecent failures:")
        for failure in recent_failures:
            print(f"  - {failure.get('file', 'unknown')}: {failure.get('error', 'unknown error')}")

    # Email candidates summary
    if email_count > 0:
        email_pct = (email_count / max(completed_count, 1)) * 100
        print(f"\n📧 Email Detection:")
        print(f"  {email_count} email candidates ({email_pct:.1f}% of processed files)")

        if EMAIL_INDEX_FILE.exists():
            print(f"  Email index: {EMAIL_INDEX_FILE}")

    # Log file info
    if LOG_FILE.exists():
        log_size = LOG_FILE.stat().st_size / 1024 / 1024  # MB
        print(f"\nLog file: {LOG_FILE}")
        print(f"Log size: {log_size:.2f} MB")
        print(f"\nTo view recent log entries:")
        print(f"  tail -f {LOG_FILE}")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
