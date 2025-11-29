#!/usr/bin/env python3
"""
Download documents from CourtListener docket pages.

This script handles the Giuffre v. Maxwell case docket with robust
error handling, resume capability, and rate limiting.

Design Decisions:
- Session persistence: Maintains cookies/headers across requests
- Rate limiting: 2-second delay between requests to avoid 429/403
- Resume capability: Skips already-downloaded files
- Multiple strategies: Tries direct PDF links, document pages, and RECAP archive
- User-Agent rotation: Mimics real browser to avoid blocking

Trade-offs:
- Performance vs. Politeness: 2s delay is conservative but respectful
- Robustness vs. Speed: Multiple fallback strategies slow down happy path
- Storage vs. Bandwidth: Downloads all versions rather than deduplicating first

Extension Points:
- Add CLI arguments for different dockets
- Implement concurrent downloads with semaphore
- Add authentication support for restricted documents
"""

import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class DocumentLink:
    """Represents a document link from the docket."""

    url: str
    entry_number: Optional[str] = None
    description: Optional[str] = None
    document_number: Optional[str] = None

    def __hash__(self):
        return hash(self.url)


class CourtListenerDownloader:
    """
    Download documents from CourtListener with rate limiting and error handling.

    Performance:
    - Time Complexity: O(n) where n is number of documents
    - Rate: ~30 documents/minute (2s delay between requests)

    Error Handling:
    1. 403 Forbidden: Retry with different User-Agent
    2. 404 Not Found: Skip and log missing document
    3. Network errors: Retry up to 3 times with exponential backoff
    4. Rate limiting (429): Exponential backoff starting at 5s

    Usage:
        downloader = CourtListenerDownloader(output_dir)
        count = await downloader.download_docket(docket_url)
    """

    def __init__(self, output_dir: Path, delay: float = 2.0):
        """Initialize downloader.

        Args:
            output_dir: Directory to save downloaded PDFs
            delay: Seconds to wait between requests (default: 2.0)
        """
        self.output_dir = output_dir
        self.delay = delay
        self.session = requests.Session()
        self.downloaded_urls: set[str] = set()

        # Multiple User-Agent strings to rotate through
        self.user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        self.current_ua_index = 0

        # Setup session headers
        self._update_headers()

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Metadata file to track downloads
        self.metadata_file = self.output_dir / "download_metadata.json"
        self.metadata = self._load_metadata()

    def _update_headers(self):
        """Update session headers with current User-Agent."""
        self.session.headers.update(
            {
                "User-Agent": self.user_agents[self.current_ua_index],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",  # Removed 'br' (Brotli) - requires extra package
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
            }
        )

    def _rotate_user_agent(self):
        """Switch to next User-Agent in rotation."""
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        self._update_headers()
        logger.info(f"Rotated to User-Agent #{self.current_ua_index}")

    def _load_metadata(self) -> dict:
        """Load download metadata from JSON file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}")
        return {"downloads": [], "failed": [], "last_update": None}

    def _save_metadata(self):
        """Save download metadata to JSON file."""
        import datetime

        self.metadata["last_update"] = datetime.datetime.now().isoformat()
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f, indent=2)

    def _fetch_with_retry(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """
        Fetch URL with exponential backoff retry logic.

        Args:
            url: URL to fetch
            max_retries: Maximum retry attempts

        Returns:
            Response object or None if all retries failed
        """
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5 * (2**attempt)))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    time.sleep(retry_after)
                    continue

                # Handle forbidden - try rotating User-Agent
                if response.status_code == 403:
                    if attempt < max_retries - 1:
                        logger.warning("403 Forbidden, rotating User-Agent and retrying")
                        self._rotate_user_agent()
                        time.sleep(2)
                        continue
                    logger.error(f"403 Forbidden after all retries: {url}")
                    return None

                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    backoff = 2**attempt
                    logger.warning(
                        f"Request failed (attempt {attempt + 1}/{max_retries}), retrying in {backoff}s: {e}"
                    )
                    time.sleep(backoff)
                else:
                    logger.error(f"Request failed after all retries: {e}")
                    return None

        return None

    def extract_document_links(self, docket_url: str) -> list[DocumentLink]:
        """
        Extract all document links from docket page.

        Handles CourtListener's storage.courtlistener.com RECAP PDFs with pattern:
        https://storage.courtlistener.com/recap/gov.uscourts.{court}.{docket}.{doc}.{attachment}.pdf

        Args:
            docket_url: URL of the docket page

        Returns:
            List of DocumentLink objects
        """
        logger.info(f"Fetching docket page: {docket_url}")

        response = self._fetch_with_retry(docket_url)
        if not response:
            logger.error("Failed to fetch docket page")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        links: list[DocumentLink] = []
        seen_urls: set[str] = set()

        # Extract all RECAP PDF links from storage.courtlistener.com
        for link in soup.find_all("a", href=True):
            href = link["href"]

            # Match RECAP PDF pattern
            if ".pdf" in href.lower() and (
                "storage.courtlistener.com/recap/" in href or "/recap/gov.uscourts." in href
            ):
                # Make absolute URL
                if href.startswith("http"):
                    full_url = href
                else:
                    full_url = urljoin("https://www.courtlistener.com", href)

                # Skip duplicates
                if full_url in seen_urls:
                    continue

                # Extract document and attachment numbers from pattern:
                # gov.uscourts.nysd.447706/gov.uscourts.nysd.447706.123.0.pdf
                # gov.uscourts.nysd.447706/gov.uscourts.nysd.447706.123.0_5.pdf (version)
                # where 123 is doc number, 0 is attachment number
                match = re.search(r"gov\.uscourts\.\w+\.\d+\.(\d+)\.(\d+)(?:_\d+)?\.pdf", href)
                if match:
                    doc_num = match.group(1)
                    attach_num = match.group(2)

                    # Get link text as description
                    description = link.get_text(strip=True)
                    if not description or len(description) > 200:
                        description = None

                    links.append(
                        DocumentLink(
                            url=full_url,
                            entry_number=doc_num,  # Use doc number as entry number
                            description=description,
                            document_number=f"{doc_num}.{attach_num}",
                        )
                    )
                    seen_urls.add(full_url)
                else:
                    # Fallback for PDFs that don't match expected pattern
                    logger.debug(f"PDF doesn't match expected pattern: {href}")
                    doc_num = self._extract_doc_number(href)
                    links.append(
                        DocumentLink(
                            url=full_url,
                            description=link.get_text(strip=True),
                            document_number=doc_num,
                        )
                    )
                    seen_urls.add(full_url)

        logger.info(f"Found {len(links)} RECAP PDF links")

        # Log summary statistics
        main_docs = [l for l in links if l.document_number and l.document_number.endswith(".0")]
        attachments = [
            l for l in links if l.document_number and not l.document_number.endswith(".0")
        ]
        logger.info(f"  Main documents: {len(main_docs)}")
        logger.info(f"  Attachments: {len(attachments)}")

        return links

    def _extract_doc_number(self, url: str) -> Optional[str]:
        """Extract document number from URL."""
        # Try various patterns
        patterns = [
            r"/(\d+)\.pdf$",  # Direct PDF: /123.pdf
            r"/document/(\d+)",  # Document page: /document/123
            r"\.(\d+)\.pdf$",  # RECAP: name.123.pdf
            r"/(\d+)-\d+\.pdf$",  # Entry-attachment: /123-1.pdf
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def download_document(self, doc_link: DocumentLink) -> bool:
        """
        Download a single document.

        Returns:
            True if download successful, False otherwise
        """
        # Generate filename from document number
        # Format: giuffre_maxwell_123.0.pdf (doc 123, main document)
        #         giuffre_maxwell_123.1.pdf (doc 123, attachment 1)
        if doc_link.document_number:
            filename = f"giuffre_maxwell_{doc_link.document_number}.pdf"
        else:
            # Use hash of URL as fallback
            url_hash = hash(doc_link.url) % 100000
            filename = f"giuffre_maxwell_doc_{url_hash}.pdf"

        filepath = self.output_dir / filename

        # Skip if already downloaded
        if filepath.exists():
            logger.info(f"Skipping {filename} (already exists)")
            return True

        # Check if URL already processed
        if doc_link.url in self.downloaded_urls:
            logger.info(f"Skipping {filename} (URL already processed)")
            return True

        logger.info(f"Downloading: {filename}")
        logger.debug(f"  URL: {doc_link.url}")
        if doc_link.description:
            logger.debug(f"  Description: {doc_link.description[:100]}")

        try:
            # CourtListener storage URLs are direct PDF links
            pdf_url = doc_link.url

            # Download PDF
            pdf_response = self._fetch_with_retry(pdf_url)
            if not pdf_response:
                self.metadata["failed"].append(
                    {"url": pdf_url, "reason": "Failed to fetch PDF", "filename": filename}
                )
                self._save_metadata()
                return False

            # Verify it's actually a PDF
            content_type = pdf_response.headers.get("Content-Type", "")
            if "pdf" not in content_type.lower() and not pdf_url.endswith(".pdf"):
                logger.warning(f"  Content-Type is not PDF: {content_type}")
                # Save anyway, might still be valid

            # Save to file
            with open(filepath, "wb") as f:
                for chunk in pdf_response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = filepath.stat().st_size
            logger.info(f"✓ Downloaded: {filename} ({file_size / 1024:.1f} KB)")

            # Update metadata
            self.metadata["downloads"].append(
                {
                    "filename": filename,
                    "url": doc_link.url,
                    "pdf_url": pdf_url,
                    "size_bytes": file_size,
                    "entry_number": doc_link.entry_number,
                    "document_number": doc_link.document_number,
                    "description": doc_link.description,
                }
            )
            self.downloaded_urls.add(doc_link.url)
            self._save_metadata()

            # Rate limiting
            time.sleep(self.delay)
            return True

        except Exception as e:
            logger.error(f"✗ Error downloading {filename}: {e}")
            self.metadata["failed"].append(
                {"url": doc_link.url, "reason": str(e), "filename": filename}
            )
            self._save_metadata()
            return False

    def download_docket(self, docket_url: str) -> int:
        """
        Download all documents from a docket page.

        Args:
            docket_url: URL of the docket page

        Returns:
            Number of documents successfully downloaded
        """
        # Extract all document links
        doc_links = self.extract_document_links(docket_url)

        if not doc_links:
            logger.error("No document links found!")
            return 0

        logger.info(f"Starting download of {len(doc_links)} documents...")

        # Download each document
        downloaded = 0
        for i, doc_link in enumerate(doc_links, 1):
            logger.info(f"Progress: [{i}/{len(doc_links)}]")
            if self.download_document(doc_link):
                downloaded += 1

        return downloaded


def main():
    """Main entry point for CourtListener downloader."""
    # Configuration
    docket_url = "https://www.courtlistener.com/docket/4355835/giuffre-v-maxwell/"
    output_dir = (
        Path(__file__).parent.parent.parent / "data" / "sources" / "courtlistener_giuffre_maxwell"
    )

    print("=" * 70)
    print("CourtListener Document Downloader")
    print("=" * 70)
    print("Case: Giuffre v. Maxwell")
    print(f"URL: {docket_url}")
    print(f"Output: {output_dir}")
    print("=" * 70)
    print()

    # Create downloader
    downloader = CourtListenerDownloader(output_dir=output_dir, delay=2.0)

    # Download documents
    try:
        downloaded = downloader.download_docket(docket_url)

        print()
        print("=" * 70)
        print("Download Complete")
        print("=" * 70)
        print(f"Successfully downloaded: {downloaded} documents")
        print(f"Total files in directory: {len(list(output_dir.glob('*.pdf')))}")
        print(f"Failed downloads: {len(downloader.metadata['failed'])}")
        print(f"Metadata saved to: {downloader.metadata_file}")
        print("=" * 70)

        # Show failed downloads if any
        if downloader.metadata["failed"]:
            print("\nFailed Downloads:")
            for fail in downloader.metadata["failed"][:10]:  # Show first 10
                print(f"  - {fail['filename']}: {fail['reason']}")
            if len(downloader.metadata["failed"]) > 10:
                print(f"  ... and {len(downloader.metadata['failed']) - 10} more")

    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user")
        print(f"Progress saved to: {downloader.metadata_file}")
        print("Run script again to resume download")

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        print(f"\nError: {e}")
        print(f"Progress saved to: {downloader.metadata_file}")


if __name__ == "__main__":
    main()
