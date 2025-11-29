#!/usr/bin/env python3
"""Comprehensive Epstein document downloader for all known sources.

Downloads from 10+ public sources, deduplicates via content hashing,
and builds master index with complete provenance tracking.

Sources:
- FBI Vault (22 parts)
- DocumentCloud collections (3 releases)
- DOJ Official Release
- Internet Archive
- CourtListener (requires API/manual)
- Google Pinpoint (requires manual)
"""

import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/Users/masa/Projects/epstein/logs/download_all_sources.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class DownloadMetadata:
    """Metadata for downloaded document."""

    source: str
    url: str
    filename: str
    size: int
    hash: str
    downloaded_at: str
    part: Optional[int] = None
    duplicate: bool = False


class EpsteinDocumentDownloader:
    """Comprehensive document downloader with deduplication."""

    def __init__(self, base_dir: Path):
        """Initialize downloader.

        Args:
            base_dir: Project root directory
        """
        self.base_dir = base_dir
        self.sources_dir = base_dir / "data" / "sources"
        self.canonical_dir = base_dir / "data" / "canonical"
        self.metadata_dir = base_dir / "data" / "metadata"
        self.logs_dir = base_dir / "logs"

        # Track downloads and deduplication
        self.downloaded_hashes: set[str] = set()
        self.download_log: list[DownloadMetadata] = []
        self.duplicate_count = 0
        self.success_count = 0
        self.error_count = 0

        # Create directories
        for dir_path in [self.sources_dir, self.canonical_dir, self.metadata_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Load existing hashes if available
        self._load_existing_hashes()

    def _load_existing_hashes(self) -> None:
        """Load existing document hashes to avoid re-downloading."""
        index_path = self.metadata_dir / "master_document_index.json"
        if index_path.exists():
            try:
                with open(index_path) as f:
                    index = json.load(f)
                    for doc in index.get("documents", []):
                        self.downloaded_hashes.add(doc["hash"])
                logger.info(f"Loaded {len(self.downloaded_hashes)} existing document hashes")
            except Exception as e:
                logger.warning(f"Could not load existing index: {e}")

    def calculate_hash(self, filepath: Path) -> str:
        """Calculate SHA256 hash of file for deduplication.

        Args:
            filepath: Path to file

        Returns:
            Hex digest of SHA256 hash
        """
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def is_duplicate(self, filepath: Path) -> bool:
        """Check if file is a duplicate based on content hash.

        Args:
            filepath: Path to file to check

        Returns:
            True if duplicate exists, False otherwise
        """
        file_hash = self.calculate_hash(filepath)
        if file_hash in self.downloaded_hashes:
            return True
        self.downloaded_hashes.add(file_hash)
        return False

    def download_file(
        self,
        url: str,
        output_path: Path,
        source_name: str,
        metadata: Optional[dict] = None,
        max_retries: int = 3,
    ) -> bool:
        """Download a single file with retry logic and deduplication.

        Args:
            url: URL to download from
            output_path: Local path to save file
            source_name: Name of source (for tracking)
            metadata: Optional additional metadata
            max_retries: Maximum retry attempts

        Returns:
            True if successfully downloaded (not duplicate), False otherwise
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        for attempt in range(max_retries):
            try:
                logger.info(f"Downloading: {url} (attempt {attempt + 1}/{max_retries})")
                response = requests.get(url, headers=headers, stream=True, timeout=60)
                response.raise_for_status()

                # Write file
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                # Check for duplicates
                if self.is_duplicate(output_path):
                    logger.info(f"  ✗ Duplicate detected: {output_path.name}")
                    output_path.unlink()
                    self.duplicate_count += 1

                    # Log duplicate
                    self.download_log.append(
                        DownloadMetadata(
                            source=source_name,
                            url=url,
                            filename=output_path.name,
                            size=0,
                            hash=self.calculate_hash(output_path) if output_path.exists() else "",
                            downloaded_at=datetime.utcnow().isoformat(),
                            duplicate=True,
                            **(metadata or {}),
                        )
                    )
                    return False

                # Log successful download
                file_hash = self.calculate_hash(output_path)
                file_size = output_path.stat().st_size

                self.download_log.append(
                    DownloadMetadata(
                        source=source_name,
                        url=url,
                        filename=output_path.name,
                        size=file_size,
                        hash=file_hash,
                        downloaded_at=datetime.utcnow().isoformat(),
                        duplicate=False,
                        **(metadata or {}),
                    )
                )

                self.success_count += 1
                logger.info(f"  ✓ Downloaded: {output_path.name} ({file_size / 1024:.1f} KB)")
                return True

            except requests.exceptions.RequestException as e:
                logger.warning(f"  ✗ Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    logger.error(f"  ✗ Failed after {max_retries} attempts: {url}")
                    self.error_count += 1
                    return False

            except Exception as e:
                logger.error(f"  ✗ Unexpected error: {e}")
                self.error_count += 1
                return False

        return False

    def download_fbi_vault(self) -> None:
        """Download all 22 parts from FBI Vault.

        FBI releases documents in parts. Each part is a separate PDF.
        URL pattern: https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%20XX/at_download/file
        """
        logger.info("\n" + "=" * 70)
        logger.info("FBI VAULT - Jeffrey Epstein Files (Parts 1-22)")
        logger.info("=" * 70)

        output_dir = self.sources_dir / "fbi_vault"
        output_dir.mkdir(exist_ok=True)

        base_url = "https://vault.fbi.gov/jeffrey-epstein/Jeffrey%20Epstein%20Part%20{:02d}/at_download/file"

        downloaded = 0
        for part in range(1, 23):
            url = base_url.format(part)
            filename = f"jeffrey_epstein_part_{part:02d}.pdf"
            filepath = output_dir / filename

            if filepath.exists():
                logger.info(f"Part {part:02d}: Already exists, checking for duplicates")
                # Still check hash in case it's a duplicate from another source
                if not self.is_duplicate(filepath):
                    self.downloaded_hashes.add(self.calculate_hash(filepath))
                continue

            if self.download_file(url, filepath, "FBI Vault", {"part": part}):
                downloaded += 1

            time.sleep(2)  # Be polite to FBI servers

        logger.info(f"\nFBI Vault: {downloaded} new parts downloaded")

    def download_documentcloud(self) -> None:
        """Download DocumentCloud collections.

        DocumentCloud hosts multiple releases:
        - DOJ Feb 2025 release
        - Unsealing Jan 2024 (943 pages)
        - Original Epstein docs collection
        """
        logger.info("\n" + "=" * 70)
        logger.info("DOCUMENTCLOUD - Epstein Files")
        logger.info("=" * 70)

        output_dir = self.sources_dir / "documentcloud"
        output_dir.mkdir(exist_ok=True)

        # Direct PDF URLs from DocumentCloud
        urls = [
            (
                "https://assets.documentcloud.org/documents/25547032/doj-jeffrey-epstein-files-released-2025-02-27.pdf",
                "doj_feb2025_release.pdf",
            ),
            (
                "https://s3.documentcloud.org/documents/24253240/1324-epstein-documents-943-pages.pdf",
                "unsealing_jan2024_943pages.pdf",
            ),
            (
                "https://assets.documentcloud.org/documents/6250471/Epstein-Docs.pdf",
                "epstein_docs_6250471.pdf",
            ),
        ]

        downloaded = 0
        for url, filename in urls:
            filepath = output_dir / filename
            if filepath.exists():
                logger.info(f"{filename}: Already exists, skipping")
                continue

            if self.download_file(url, filepath, "DocumentCloud"):
                downloaded += 1
            time.sleep(2)

        logger.info(f"\nDocumentCloud: {downloaded} new documents downloaded")

    def download_doj_official(self) -> None:
        """Download DOJ official release.

        Department of Justice declassified document release.
        """
        logger.info("\n" + "=" * 70)
        logger.info("DEPARTMENT OF JUSTICE - Official Release")
        logger.info("=" * 70)

        output_dir = self.sources_dir / "doj_official"
        output_dir.mkdir(exist_ok=True)

        url = "https://www.justice.gov/opa/media/1407001/dl?inline="
        filepath = output_dir / "doj_epstein_declassified.pdf"

        if filepath.exists():
            logger.info("DOJ file already exists, skipping")
            return

        if self.download_file(url, filepath, "DOJ Official"):
            logger.info("DOJ official release downloaded")

    def download_internet_archive(self) -> None:
        """Download from Internet Archive.

        Large consolidated archive from January 2024.
        Note: This is a large file (potentially hundreds of MB).
        """
        logger.info("\n" + "=" * 70)
        logger.info("INTERNET ARCHIVE - January 2024 Documents")
        logger.info("=" * 70)

        output_dir = self.sources_dir / "internet_archive"
        output_dir.mkdir(exist_ok=True)

        url = "https://archive.org/download/final-epstein-documents/final-epstein-documents.pdf"
        filepath = output_dir / "final_epstein_documents_jan2024.pdf"

        if filepath.exists():
            logger.info("Internet Archive file already exists, skipping")
            return

        logger.info("Downloading large archive file (this may take several minutes)...")
        if self.download_file(url, filepath, "Internet Archive", max_retries=5):
            logger.info("Internet Archive download complete")

    def deduplicate_existing(self) -> tuple[dict[str, list[Path]], dict[str, list[Path]]]:
        """Deduplicate all existing downloaded files.

        Scans all PDFs in sources directory, calculates hashes,
        and identifies duplicate documents across sources.

        Returns:
            Tuple of (all_files_by_hash, duplicate_sets)
        """
        logger.info("\n" + "=" * 70)
        logger.info("DEDUPLICATION - Scanning existing files")
        logger.info("=" * 70)

        all_pdfs = list(self.sources_dir.rglob("*.pdf"))
        logger.info(f"Found {len(all_pdfs)} PDFs across all sources")

        hash_to_files: dict[str, list[Path]] = {}

        for i, pdf in enumerate(all_pdfs, 1):
            if i % 100 == 0:
                logger.info(f"Processed {i}/{len(all_pdfs)} files...")

            file_hash = self.calculate_hash(pdf)
            if file_hash not in hash_to_files:
                hash_to_files[file_hash] = []
            hash_to_files[file_hash].append(pdf)

        # Find duplicates
        duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}

        logger.info(f"\nUnique documents: {len(hash_to_files)}")
        logger.info(f"Duplicate sets: {len(duplicates)}")
        logger.info(
            f"Total duplicate files: {sum(len(files) - 1 for files in duplicates.values())}"
        )

        if duplicates:
            logger.info("\nSample duplicate files (showing first 5 sets):")
            for i, (file_hash, files) in enumerate(list(duplicates.items())[:5], 1):
                logger.info(f"\n  Set {i} - Hash: {file_hash[:16]}...")
                for f in files:
                    logger.info(f"    - {f.relative_to(self.base_dir)}")

        return hash_to_files, duplicates

    def build_master_index(self) -> dict:
        """Build master index with provenance tracking.

        Creates comprehensive index of all documents with:
        - Unique document identification (hash)
        - All sources where document appears
        - Canonical file selection
        - Size and metadata

        Returns:
            Master index dictionary
        """
        logger.info("\n" + "=" * 70)
        logger.info("BUILDING MASTER INDEX")
        logger.info("=" * 70)

        hash_to_files, duplicates = self.deduplicate_existing()

        master_index = {
            "generated_at": datetime.utcnow().isoformat(),
            "total_files": sum(len(files) for files in hash_to_files.values()),
            "unique_documents": len(hash_to_files),
            "duplicate_sets": len(duplicates),
            "total_duplicates": sum(len(files) - 1 for files in duplicates.values()),
            "sources": {},
            "documents": [],
        }

        # Index by source
        for source_dir in self.sources_dir.iterdir():
            if source_dir.is_dir():
                pdf_count = len(list(source_dir.rglob("*.pdf")))
                master_index["sources"][source_dir.name] = {
                    "path": str(source_dir.relative_to(self.base_dir)),
                    "document_count": pdf_count,
                }

        # Index each unique document
        for file_hash, files in hash_to_files.items():
            # Choose canonical file (prefer certain sources, then alphabetically)
            # Priority: doj_official > fbi_vault > documentcloud > others
            def source_priority(f: Path) -> int:
                if "doj_official" in str(f):
                    return 0
                if "fbi_vault" in str(f):
                    return 1
                if "documentcloud" in str(f):
                    return 2
                return 3

            canonical = sorted(files, key=lambda f: (source_priority(f), str(f)))[0]

            doc_entry = {
                "hash": file_hash,
                "canonical_path": str(canonical.relative_to(self.base_dir)),
                "size": canonical.stat().st_size,
                "sources": [str(f.relative_to(self.base_dir)) for f in sorted(files, key=str)],
                "source_count": len(files),
                "duplicate_count": len(files) - 1,
            }

            master_index["documents"].append(doc_entry)

        # Sort documents by size (largest first)
        master_index["documents"].sort(key=lambda d: d["size"], reverse=True)

        # Save index
        index_path = self.metadata_dir / "master_document_index.json"
        with open(index_path, "w") as f:
            json.dump(master_index, f, indent=2)

        logger.info(f"\nMaster index saved: {index_path}")
        logger.info(f"Total files: {master_index['total_files']}")
        logger.info(f"Unique documents: {master_index['unique_documents']}")
        logger.info(f"Duplicates removed: {master_index['total_duplicates']}")
        logger.info(
            f"Deduplication rate: {(master_index['total_duplicates'] / master_index['total_files'] * 100):.1f}%"
        )

        return master_index

    def generate_report(self) -> None:
        """Generate comprehensive download and deduplication report."""
        logger.info("\n" + "=" * 70)
        logger.info("GENERATING FINAL REPORT")
        logger.info("=" * 70)

        master_index = self.build_master_index()

        report_path = self.base_dir / "DOWNLOAD_DEDUPLICATION_REPORT.md"

        with open(report_path, "w") as f:
            f.write("# Epstein Document Collection - Download & Deduplication Report\n\n")
            f.write(f"**Generated**: {datetime.utcnow().isoformat()}\n\n")

            f.write("## Summary Statistics\n\n")
            f.write(f"- **Total Files Downloaded**: {master_index['total_files']:,}\n")
            f.write(f"- **Unique Documents**: {master_index['unique_documents']:,}\n")
            f.write(f"- **Duplicate Files Removed**: {master_index['total_duplicates']:,}\n")
            f.write(
                f"- **Deduplication Rate**: {(master_index['total_duplicates'] / master_index['total_files'] * 100):.1f}%\n"
            )
            f.write(
                f"- **Total Storage (unique docs)**: {sum(d['size'] for d in master_index['documents']) / (1024**2):.1f} MB\n\n"
            )

            f.write("## Download Session Statistics\n\n")
            f.write(f"- **Successful Downloads**: {self.success_count}\n")
            f.write(f"- **Duplicates Detected**: {self.duplicate_count}\n")
            f.write(f"- **Errors**: {self.error_count}\n\n")

            f.write("## Sources\n\n")
            f.write("| Source | Document Count | Path |\n")
            f.write("|--------|---------------|------|\n")
            for source, info in sorted(master_index["sources"].items()):
                f.write(f"| {source} | {info['document_count']} | `{info['path']}` |\n")

            f.write("\n## Top 10 Largest Documents\n\n")
            f.write("| Size (MB) | Hash | Canonical Path | Sources |\n")
            f.write("|-----------|------|----------------|----------|\n")
            for doc in master_index["documents"][:10]:
                size_mb = doc["size"] / (1024**2)
                hash_short = doc["hash"][:16]
                source_count = doc["source_count"]
                f.write(
                    f"| {size_mb:.1f} | `{hash_short}...` | `{doc['canonical_path']}` | {source_count} |\n"
                )

            f.write("\n## Duplicate Analysis\n\n")
            if master_index["duplicate_sets"] > 0:
                f.write(
                    f"Found {master_index['duplicate_sets']} sets of duplicate documents across sources.\n\n"
                )
                f.write("### Sample Duplicate Sets (showing first 10)\n\n")

                # Get documents with duplicates
                dup_docs = [d for d in master_index["documents"] if d["duplicate_count"] > 0][:10]

                for i, doc in enumerate(dup_docs, 1):
                    f.write(f"#### Set {i} - Hash: `{doc['hash'][:16]}...`\n\n")
                    f.write(f"**Canonical**: `{doc['canonical_path']}`\n\n")
                    f.write("**All sources**:\n")
                    for source in doc["sources"]:
                        f.write(f"- `{source}`\n")
                    f.write("\n")
            else:
                f.write("No duplicates found across sources.\n\n")

            f.write("\n## Download Log\n\n")
            if self.download_log:
                f.write("| Timestamp | Source | Filename | Size (KB) | Status |\n")
                f.write("|-----------|--------|----------|-----------|--------|\n")
                for entry in self.download_log[:50]:  # Show first 50
                    status = "✗ Duplicate" if entry.duplicate else "✓ Success"
                    size_kb = entry.size / 1024 if entry.size > 0 else 0
                    f.write(
                        f"| {entry.downloaded_at[:19]} | {entry.source} | `{entry.filename}` | {size_kb:.1f} | {status} |\n"
                    )

                if len(self.download_log) > 50:
                    f.write(f"\n*Showing first 50 of {len(self.download_log)} total downloads*\n")
            else:
                f.write("No downloads in this session (all files already existed).\n")

            f.write("\n## Provenance Tracking\n\n")
            f.write("Each unique document tracks all sources where it appears:\n\n")
            f.write("```json\n")
            if master_index["documents"]:
                sample_doc = master_index["documents"][0]
                f.write(
                    json.dumps(
                        {
                            "hash": sample_doc["hash"],
                            "canonical_path": sample_doc["canonical_path"],
                            "sources": sample_doc["sources"],
                            "source_count": sample_doc["source_count"],
                        },
                        indent=2,
                    )
                )
            f.write("\n```\n\n")

            f.write("## Next Steps\n\n")
            f.write("1. **OCR Processing**: Run OCR on all unique documents\n")
            f.write(
                "2. **Classification**: Classify documents by type (email, court filing, etc.)\n"
            )
            f.write("3. **Entity Extraction**: Extract entities from all documents\n")
            f.write("4. **Timeline Building**: Create chronological timeline of events\n")
            f.write(
                "5. **Network Analysis**: Build entity relationship network across all docs\n\n"
            )

            f.write("## Manual Download Sources\n\n")
            f.write("The following sources require manual download or API access:\n\n")
            f.write(
                "- **Google Pinpoint Collection**: https://journaliststudio.google.com/pinpoint/search?collection=092314e384a58618\n"
            )
            f.write(
                "- **CourtListener - Giuffre v Maxwell**: https://www.courtlistener.com/docket/4355835/giuffre-v-maxwell/\n"
            )
            f.write(
                "- **CourtListener - Criminal Case**: https://www.courtlistener.com/docket/15887848/united-states-v-epstein/\n\n"
            )

            f.write("---\n\n")
            f.write("*Report generated by Epstein Document Archive downloader*\n")

        logger.info(f"Report saved: {report_path}")

        # Also save download log as JSON
        log_path = self.metadata_dir / "download_log.json"
        with open(log_path, "w") as f:
            json.dump([asdict(entry) for entry in self.download_log], f, indent=2)
        logger.info(f"Download log saved: {log_path}")


def main():
    """Main execution function."""
    base_dir = Path("/Users/masa/Projects/epstein")
    downloader = EpsteinDocumentDownloader(base_dir)

    logger.info("=" * 70)
    logger.info("EPSTEIN DOCUMENT COMPREHENSIVE DOWNLOADER")
    logger.info("=" * 70)
    logger.info("")

    # Download from all automated sources
    downloader.download_fbi_vault()
    downloader.download_documentcloud()
    downloader.download_doj_official()
    downloader.download_internet_archive()

    # Deduplicate and index
    downloader.generate_report()

    logger.info("\n" + "=" * 70)
    logger.info("DOWNLOAD COMPLETE")
    logger.info("=" * 70)
    logger.info("\nStatistics:")
    logger.info(f"  ✓ Successful downloads: {downloader.success_count}")
    logger.info(f"  ✗ Duplicates detected: {downloader.duplicate_count}")
    logger.info(f"  ✗ Errors: {downloader.error_count}")
    logger.info("\nSee DOWNLOAD_DEDUPLICATION_REPORT.md for full details")


if __name__ == "__main__":
    main()
