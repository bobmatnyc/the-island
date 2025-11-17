#!/usr/bin/env python3
"""Extract detected emails from OCR results into organized directory.

This script processes email candidates identified during OCR processing
and extracts them into a structured directory with:
- Organized subdirectories by date (YYYY-MM format)
- Metadata JSON with parsed email headers
- Full OCR text and body-only text files

Author: Claude Code (Python Engineer)
Created: 2025-11-16
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)



@dataclass
class EmailMetadata:
    """Track download statistics."""

    def __init__(self):
        self.successful = 0
        self.failed = 0
        self.total_bytes = 0
        self.failed_pages = []
        self.file_sizes = {}

    def add_success(self, filename: str, size: int):
        self.successful += 1
        self.total_bytes += size
        self.file_sizes[filename] = size

    def add_failure(self, filename: str, error: str):
        self.failed += 1
        self.failed_pages.append((filename, error))

    def get_summary(self) -> str:
        summary = f"""
Download Statistics:
-------------------
Total Successful: {self.successful}
Total Failed: {self.failed}
Total Bytes: {self.total_bytes:,} ({self.total_bytes / 1024 / 1024:.2f} MB)

"""
        if self.failed_pages:
            summary += "Failed Downloads:\n"
            for filename, error in self.failed_pages:
                summary += f"  - {filename}: {error}\n"

        return summary


def download_file(url: str, output_path: Path, stats: DownloadStats) -> bool:
    """
    Download a file from URL to output path.

    Args:
        url: Source URL
        output_path: Destination file path
        stats: DownloadStats object to track progress

    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)

        file_size = len(response.content)
        stats.add_success(output_path.name, file_size)

        return True

    except requests.exceptions.RequestException as e:
        stats.add_failure(output_path.name, str(e))
        print(f"  ✗ Failed: {e}")
        return False


def download_structured_json(stats: DownloadStats) -> bool:
    """Download the structured JSON file."""
    print("\n[1/4] Downloading structured JSON...")
    output_path = DATA_DIR / "epstein-emails-structured.json"

    success = download_file(STRUCTURED_JSON_URL, output_path, stats)
    if success:
        print(f"  ✓ Saved to: {output_path}")

    return success


def download_pdf(stats: DownloadStats) -> bool:
    """Download the complete PDF file."""
    print("\n[2/4] Downloading complete PDF...")
    output_path = DATA_DIR / "epstein-emails-complete.pdf"

    success = download_file(PDF_URL, output_path, stats)
    if success:
        print(f"  ✓ Saved to: {output_path}")

    return success


def download_individual_pages(stats: DownloadStats) -> Tuple[int, int]:
    """
    Download individual page text files.

    Returns:
        Tuple of (successful_count, failed_count)
    """
    print(f"\n[3/4] Downloading individual pages (1-{TOTAL_PAGES})...")
    print("This may take a few minutes with rate limiting...")

    successful = 0
    failed = 0

    for page_num in range(1, TOTAL_PAGES + 1):
        url = PAGE_URL_PATTERN.format(page=page_num)
        output_path = PAGES_DIR / f"page-{page_num:03d}.txt"

        # Progress indicator every 10 pages
        if page_num % 10 == 0:
            print(f"  Progress: {page_num}/{TOTAL_PAGES} pages...")

        if download_file(url, output_path, stats):
            successful += 1
        else:
            failed += 1

        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)

    print(f"  ✓ Downloaded {successful}/{TOTAL_PAGES} pages")
    if failed > 0:
        print(f"  ✗ Failed: {failed} pages")

    return successful, failed


def download_and_process_notes(stats: DownloadStats) -> bool:
    """
    Download notes from API and create human-readable summary.

    Returns:
        True if successful, False otherwise
    """
    print("\n[4/4] Downloading and processing notes...")

    # Download raw notes JSON
    notes_json_path = NOTES_DIR / "epstein-emails-notes.json"

    try:
        response = requests.get(NOTES_API_URL, timeout=30)
        response.raise_for_status()

        notes_data = response.json()

        # Save raw JSON
        notes_json_path.write_text(json.dumps(notes_data, indent=2))
        stats.add_success(notes_json_path.name, len(json.dumps(notes_data)))
        print(f"  ✓ Saved raw notes JSON to: {notes_json_path}")

        # Create human-readable summary
        summary_path = NOTES_DIR / "notes-summary.md"
        create_notes_summary(notes_data, summary_path, stats)

        return True

    except requests.exceptions.RequestException as e:
        stats.add_failure("notes.json", str(e))
        print(f"  ✗ Failed to download notes: {e}")
        return False
    except Exception as e:
        stats.add_failure("notes.json", str(e))
        print(f"  ✗ Error processing notes: {e}")
        return False


def create_notes_summary(notes_data: Dict, output_path: Path, stats: DownloadStats):
    """
    Create a human-readable summary of notes.

    Args:
        notes_data: Notes data from API
        output_path: Path to save summary markdown
        stats: DownloadStats object
    """
    results = notes_data.get("results", [])

    summary_lines = [
        "# Epstein Emails - DocumentCloud Notes Summary",
        "",
        f"**Total Notes:** {len(results)}",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Source:** {NOTES_API_URL}",
        "",
        "---",
        ""
    ]

    if not results:
        summary_lines.append("*No notes found in this document.*")
    else:
        for idx, note in enumerate(results, 1):
            # Handle user field - can be int (user ID) or dict (user object)
            user_info = note.get("user", "Unknown")
            if isinstance(user_info, dict):
                author_str = f"{user_info.get('name', 'Unknown')} ({user_info.get('email', 'N/A')})"
            else:
                author_str = f"User ID: {user_info}"

            summary_lines.extend([
                f"## Note {idx}: {note.get('title', 'Untitled')}",
                "",
                f"- **Page:** {note.get('page_number', 'N/A')}",
                f"- **Author:** {author_str}",
                f"- **Organization:** {note.get('organization', 'N/A')}",
                f"- **Created:** {note.get('created_at', 'N/A')}",
                f"- **Updated:** {note.get('updated_at', 'N/A')}",
                f"- **Access:** {note.get('access', 'N/A')}",
                "",
            ])

            # Add content if available
            content = note.get("content", "").strip()
            if content:
                summary_lines.extend([
                    "**Content:**",
                    "",
                    content,
                    ""
                ])

            # Add location if available
            if note.get("x1") is not None:
                summary_lines.append(f"**Location:** x1={note.get('x1')}, y1={note.get('y1')}, x2={note.get('x2')}, y2={note.get('y2')}")
                summary_lines.append("")

            summary_lines.append("---")
            summary_lines.append("")

    summary_text = "\n".join(summary_lines)
    output_path.write_text(summary_text)
    stats.add_success(output_path.name, len(summary_text))

    print(f"  ✓ Created notes summary: {output_path}")
    print(f"  ✓ Found {len(results)} notes")


def create_manifest(stats: DownloadStats):
    """Create a manifest file documenting all downloads."""
    print("\nCreating manifest file...")

    manifest_path = DATA_DIR / "MANIFEST.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    manifest_lines = [
        "# Epstein Emails - Download Manifest",
        "",
        f"**Download Date:** {timestamp}",
        f"**Source:** DocumentCloud Document ID {DOC_ID}",
        "",
        "## Summary",
        "",
        f"- **Total Files Downloaded:** {stats.successful}",
        f"- **Failed Downloads:** {stats.failed}",
        f"- **Total Size:** {stats.total_bytes:,} bytes ({stats.total_bytes / 1024 / 1024:.2f} MB)",
        "",
        "## Data Sources",
        "",
        "### Primary Documents",
        "",
        "1. **Structured JSON** (73 pages)",
        f"   - URL: {STRUCTURED_JSON_URL}",
        "   - File: `epstein-emails-structured.json`",
        f"   - Size: {stats.file_sizes.get('epstein-emails-structured.json', 0):,} bytes",
        "",
        "2. **Complete PDF** (87 pages)",
        f"   - URL: {PDF_URL}",
        "   - File: `epstein-emails-complete.pdf`",
        f"   - Size: {stats.file_sizes.get('epstein-emails-complete.pdf', 0):,} bytes",
        "",
        "### Individual Pages",
        "",
        f"3. **Page Text Files** (pages 1-{TOTAL_PAGES})",
        f"   - URL Pattern: `{PAGE_URL_PATTERN}`",
        "   - Directory: `pages/`",
        f"   - Files: `page-001.txt` through `page-{TOTAL_PAGES:03d}.txt`",
        "",
        "### Annotations",
        "",
        "4. **Notes Data**",
        f"   - API URL: {NOTES_API_URL}",
        "   - Raw JSON: `notes/epstein-emails-notes.json`",
        "   - Summary: `notes/notes-summary.md`",
        "",
        "## File Descriptions",
        "",
        "### `epstein-emails-structured.json`",
        "Structured JSON export containing page-by-page text content with metadata. ",
        "Contains 73 pages of email content in machine-readable format.",
        "",
        "### `epstein-emails-complete.pdf`",
        "Complete PDF document containing all 87 pages of Epstein email records.",
        "Includes scanned documents and email printouts.",
        "",
        "### `pages/page-*.txt`",
        "Individual text files for each page (1-87). Each file contains the OCR-extracted",
        "text from the corresponding PDF page. Useful for page-by-page analysis.",
        "",
        "### `notes/epstein-emails-notes.json`",
        "Raw JSON data of annotations and notes added to the DocumentCloud document.",
        "Includes author information, timestamps, and note locations.",
        "",
        "### `notes/notes-summary.md`",
        "Human-readable summary of all notes with formatted metadata and content.",
        "",
    ]

    if stats.failed_pages:
        manifest_lines.extend([
            "## Download Issues",
            "",
            f"The following {len(stats.failed_pages)} file(s) failed to download:",
            ""
        ])
        for filename, error in stats.failed_pages:
            manifest_lines.append(f"- `{filename}`: {error}")
        manifest_lines.append("")

    manifest_lines.extend([
        "## Directory Structure",
        "",
        "```",
        "data/emails/",
        "├── epstein-emails-structured.json",
        "├── epstein-emails-complete.pdf",
        "├── MANIFEST.md",
        "├── pages/",
        "│   ├── page-001.txt",
        "│   ├── page-002.txt",
        "│   └── ... (87 total)",
        "└── notes/",
        "    ├── epstein-emails-notes.json",
        "    └── notes-summary.md",
        "```",
        "",
        "## Usage Notes",
        "",
        "- All page numbers are zero-padded to 3 digits (e.g., page-001.txt)",
        "- The structured JSON contains 73 pages, but the PDF has 87 pages",
        "- Individual page text files cover all 87 pages for completeness",
        "- Rate limiting of 0.1 seconds was applied between page downloads",
        "",
        "## Data Integrity",
        "",
        f"- Downloads completed: {timestamp}",
        f"- Total files verified: {stats.successful}",
        "- All file sizes recorded in this manifest",
        "",
        "---",
        "",
        "*Generated by extract_emails.py*",
        ""
    ])

    manifest_text = "\n".join(manifest_lines)
    manifest_path.write_text(manifest_text)

    print(f"  ✓ Manifest created: {manifest_path}")


def main():
    """Main execution function."""
    print("=" * 70)
    print("Epstein Emails - DocumentCloud Extraction Script")
    print("=" * 70)
    print(f"\nOutput Directory: {DATA_DIR}")
    print(f"Total Pages to Download: {TOTAL_PAGES}")
    print(f"Rate Limit: {RATE_LIMIT_DELAY}s between requests")

    stats = DownloadStats()
    start_time = time.time()

    # Execute downloads
    download_structured_json(stats)
    download_pdf(stats)
    download_individual_pages(stats)
    download_and_process_notes(stats)

    # Create manifest
    create_manifest(stats)

    # Final summary
    elapsed_time = time.time() - start_time

    print("\n" + "=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)
    print(stats.get_summary())
    print(f"Elapsed Time: {elapsed_time:.2f} seconds ({elapsed_time / 60:.2f} minutes)")
    print(f"\nAll data saved to: {DATA_DIR}")
    print("See MANIFEST.md for detailed information about downloaded files.")
    print("=" * 70)

    # Exit code based on failures
    if stats.failed > 0:
        print(f"\n⚠️  Warning: {stats.failed} download(s) failed. Check output above for details.")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
