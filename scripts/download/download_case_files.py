#!/usr/bin/env python3
"""
Download Case Files - Epstein Document Archive
Downloads publicly available court documents from various sources.

Usage:
    python3 scripts/download/download_case_files.py [options]

Options:
    --case CASE_ID          Download specific case (e.g., giuffre_v_maxwell_2015)
    --all                   Download all available cases
    --source SOURCE         Download from specific source (courtlistener, documentcloud, archive_org)
    --dry-run               Show what would be downloaded without downloading
    --output-dir DIR        Custom output directory (default: data/sources/cases/)

Examples:
    # Download Giuffre v Maxwell documents
    python3 scripts/download/download_case_files.py --case giuffre_v_maxwell_2015

    # Download all CourtListener cases
    python3 scripts/download/download_case_files.py --source courtlistener

    # Dry run to see what would be downloaded
    python3 scripts/download/download_case_files.py --all --dry-run
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests


# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CASES_INDEX = PROJECT_ROOT / "data/metadata/cases_index.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "data/sources/cases"
DOWNLOAD_LOG = PROJECT_ROOT / "data/metadata/case_downloads.json"


class CaseDownloader:
    """Download court case documents from public sources."""

    def __init__(self, output_dir: Path = DEFAULT_OUTPUT, dry_run: bool = False):
        self.output_dir = Path(output_dir)
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "EpsteinArchive/1.0 (Document Research Project)"}
        )

        # Load cases index
        with open(CASES_INDEX) as f:
            self.cases_data = json.load(f)

        # Load or initialize download log
        self.download_log = self._load_download_log()

    def _load_download_log(self) -> dict:
        """Load existing download log or create new one."""
        if DOWNLOAD_LOG.exists():
            with open(DOWNLOAD_LOG) as f:
                return json.load(f)
        return {"last_updated": None, "downloads": {}}

    def _save_download_log(self):
        """Save download log."""
        self.download_log["last_updated"] = datetime.now().isoformat()
        DOWNLOAD_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(DOWNLOAD_LOG, "w") as f:
            json.dump(self.download_log, f, indent=2)

    def _get_case_by_id(self, case_id: str) -> Optional[dict]:
        """Find case by ID in cases index."""
        # Search all case categories
        for category in [
            "criminal_cases",
            "civil_individual_cases",
            "bank_settlement_cases",
            "estate_claims",
        ]:
            if category in self.cases_data:
                for case in self.cases_data[category]:
                    if case.get("case_id") == case_id:
                        return case
        return None

    def download_courtlistener_case(self, case: dict) -> bool:
        """
        Download documents from CourtListener.

        Note: This is a placeholder implementation. CourtListener requires
        API access or web scraping. Actual implementation should use:
        - CourtListener API if available
        - RECAP browser extension exports
        - Manual download instructions
        """
        case_id = case["case_id"]
        docket = case.get("docket")
        docs_url = case.get("documents_url")

        print(f"  Case: {case['case_name']}")
        print(f"  Docket: {docket}")
        print(f"  URL: {docs_url}")

        if self.dry_run:
            print("  [DRY RUN] Would download from CourtListener")
            return True

        # Create case directory
        case_dir = self.output_dir / case_id
        case_dir.mkdir(parents=True, exist_ok=True)

        # Save case metadata
        metadata_file = case_dir / "case_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(case, f, indent=2)

        print(f"  ✓ Saved metadata to {metadata_file}")
        print(f"  ℹ Manual download required from: {docs_url}")
        print(f"  ℹ Documents should be saved to: {case_dir}/")
        print("  ℹ See download_instructions in cases_index.json")

        # Log the download attempt
        self.download_log["downloads"][case_id] = {
            "case_name": case["case_name"],
            "docket": docket,
            "url": docs_url,
            "status": "metadata_saved",
            "manual_download_required": True,
            "output_dir": str(case_dir),
            "timestamp": datetime.now().isoformat(),
        }

        return True

    def download_archive_org_case(self, case_id: str = "house_oversight_nov2025") -> bool:
        """
        Download House Oversight documents from Archive.org.

        Note: Archive.org provides bulk download tools. This provides instructions.
        """
        print("\n📦 Archive.org Download Instructions:")
        print("  Case: House Oversight Committee Release (67,144 PDFs)")
        print("  URL: https://archive.org/details/epstein-pdf")
        print()
        print("  Option 1: Download using Archive.org's 'Download Options'")
        print("    - Visit the URL above")
        print("    - Click 'Download Options' on right side")
        print("    - Select 'Torrent' or 'Show All' for individual files")
        print()
        print("  Option 2: Use internetarchive CLI tool")
        print("    pip install internetarchive")
        print("    ia download epstein-pdf")
        print()

        if not self.dry_run:
            case_dir = self.output_dir / case_id
            case_dir.mkdir(parents=True, exist_ok=True)

            # Save download instructions
            instructions_file = case_dir / "DOWNLOAD_INSTRUCTIONS.txt"
            with open(instructions_file, "w") as f:
                f.write("House Oversight Committee Epstein Documents\\n")
                f.write("=" * 50 + "\\n\\n")
                f.write("Total Files: 67,144 PDFs\\n")
                f.write("Source: https://archive.org/details/epstein-pdf\\n\\n")
                f.write("Download Methods:\\n\\n")
                f.write("1. Archive.org Web Interface:\\n")
                f.write("   - Visit: https://archive.org/details/epstein-pdf\\n")
                f.write("   - Click 'Download Options'\\n")
                f.write("   - Choose Torrent or individual files\\n\\n")
                f.write("2. Command Line (internetarchive tool):\\n")
                f.write("   pip install internetarchive\\n")
                f.write("   ia download epstein-pdf\\n\\n")
                f.write("3. Torrent:\\n")
                f.write("   Download .torrent file from Archive.org\\n")
                f.write("   Use BitTorrent client\\n\\n")
                f.write(f"Save all files to: {case_dir}/\\n")

            print(f"  ✓ Instructions saved to {instructions_file}")

        return True

    def download_case(self, case_id: str) -> bool:
        """Download a specific case's documents."""
        case = self._get_case_by_id(case_id)

        if not case:
            print(f"❌ Case not found: {case_id}")
            return False

        print(f"\\n📄 Downloading: {case['case_name']}")

        # Check if download is recommended
        if not case.get("download_recommended", False):
            print("  ⚠ Download not recommended for this case")
            print(f"  Reason: {case.get('status', 'See case details')}")
            return False

        # Route to appropriate downloader based on documents_url
        docs_url = case.get("documents_url", "")

        if "courtlistener.com" in docs_url:
            return self.download_courtlistener_case(case)
        if "archive.org" in docs_url:
            return self.download_archive_org_case(case_id)
        print("  ℹ Manual download required")
        print(f"  URL: {docs_url}")
        return False

    def download_all_cases(self, source: Optional[str] = None):
        """Download all recommended cases."""
        downloaded = 0
        skipped = 0

        # Collect all cases
        all_cases = []
        for category in ["criminal_cases", "civil_individual_cases"]:
            if category in self.cases_data:
                all_cases.extend(self.cases_data[category])

        print(f"\\n🔍 Found {len(all_cases)} cases")

        for case in all_cases:
            case_id = case["case_id"]

            # Filter by source if specified
            if source:
                docs_url = case.get("documents_url", "")
                if source not in docs_url:
                    continue

            # Only download recommended cases
            if not case.get("download_recommended", False):
                skipped += 1
                continue

            if self.download_case(case_id):
                downloaded += 1
                time.sleep(1)  # Be respectful to servers
            else:
                skipped += 1

        print("\\n✅ Summary:")
        print(f"  Downloaded: {downloaded}")
        print(f"  Skipped: {skipped}")

        # Save download log
        if not self.dry_run:
            self._save_download_log()
            print(f"  Log saved: {DOWNLOAD_LOG}")

    def list_cases(self):
        """List all available cases."""
        print("\\n📋 Available Cases:\\n")

        categories = {
            "criminal_cases": "Criminal Cases",
            "civil_individual_cases": "Civil Cases",
            "bank_settlement_cases": "Bank Settlements",
            "estate_claims": "Estate Claims",
        }

        for cat_key, cat_name in categories.items():
            if cat_key not in self.cases_data:
                continue

            cases = self.cases_data[cat_key]
            if not cases:
                continue

            print(f"\\n{cat_name} ({len(cases)}):")
            print("=" * 60)

            for case in cases:
                case_id = case["case_id"]
                case_name = case["case_name"]
                recommended = "✓" if case.get("download_recommended") else "○"

                print(f"  {recommended} {case_id}")
                print(f"     {case_name}")
                if case.get("docket"):
                    print(f"     Docket: {case['docket']}")
                print()


def main():
    parser = argparse.ArgumentParser(
        description="Download Epstein case documents from public sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("--case", help="Download specific case by ID")
    parser.add_argument("--all", action="store_true", help="Download all recommended cases")
    parser.add_argument("--source", help="Filter by source (courtlistener, archive_org)")
    parser.add_argument("--list", action="store_true", help="List all available cases")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be downloaded")
    parser.add_argument("--output-dir", help="Custom output directory", default=DEFAULT_OUTPUT)

    args = parser.parse_args()

    # Create downloader
    downloader = CaseDownloader(output_dir=Path(args.output_dir), dry_run=args.dry_run)

    # Execute command
    if args.list:
        downloader.list_cases()
    elif args.case:
        downloader.download_case(args.case)
    elif args.all:
        downloader.download_all_cases(source=args.source)
    else:
        parser.print_help()
        print("\\n💡 Tip: Start with --list to see available cases")
        sys.exit(1)


if __name__ == "__main__":
    main()
