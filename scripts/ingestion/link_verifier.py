"""
Link Verification Module
Verifies URL availability and retrieves archive.org snapshots.

Design Decision: Resilient URL Verification
Rationale: News articles frequently disappear due to paywall changes, site
migrations, or content removal. This module provides automated verification
with fallback to archive.org snapshots.

Trade-offs:
- Performance: Sequential verification with rate limiting (1 req/sec)
- Reliability: 3 retries with exponential backoff for transient failures
- Completeness: waybackpy integration for archive retrieval

Time Complexity: O(n) for batch verification with rate limiting
Space Complexity: O(n) for results storage
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.util.retry import Retry


try:
    from waybackpy import WaybackMachineCDXServerAPI

    WAYBACK_AVAILABLE = True
except ImportError:
    WAYBACK_AVAILABLE = False
    logging.warning("waybackpy not installed. Archive.org fallback disabled.")


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class LinkStatus:
    """Result of link verification.

    Attributes:
        url: Original URL checked
        status: "live", "dead", "archived", or "error"
        status_code: HTTP status code (or None for errors)
        archive_url: Archive.org URL if found (None otherwise)
        error_message: Error details if status is "error"
    """

    url: str
    status: str  # "live", "dead", "archived", "error"
    status_code: Optional[int] = None
    archive_url: Optional[str] = None
    error_message: Optional[str] = None


class LinkVerifier:
    """
    Verify URL availability and retrieve archive.org snapshots.

    Features:
    - HTTP status verification with timeout (10s)
    - Retry logic: 3 attempts with exponential backoff (1s, 2s, 4s)
    - User-Agent spoofing to avoid bot blocking
    - Archive.org fallback via waybackpy
    - Batch processing with rate limiting (1 req/sec)

    Performance:
    - Single verification: ~1-2 seconds average
    - Batch (100 URLs): ~2-3 minutes with rate limiting

    Error Handling:
    - Timeouts: Logged and marked as "error" status
    - Network errors: Retried 3 times before failing
    - Archive API errors: Logged but don't block main verification

    Example:
        verifier = LinkVerifier()
        result = verifier.verify_url("https://example.com/article")
        if result.status == "dead" and result.archive_url:
            print(f"Use archive: {result.archive_url}")
    """

    def __init__(self, timeout: int = 10, max_retries: int = 3, rate_limit: float = 1.0):
        """
        Initialize link verifier.

        Args:
            timeout: Request timeout in seconds (default: 10)
            max_retries: Maximum retry attempts (default: 3)
            rate_limit: Seconds between requests (default: 1.0)
        """
        self.timeout = timeout
        self.rate_limit = rate_limit

        # Configure session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,  # 1s, 2s, 4s, 8s...
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # User-Agent to avoid bot blocking
        self.session.headers.update(
            {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )

    def verify_url(self, url: str) -> LinkStatus:
        """
        Check if URL is accessible (HTTP 200 range).

        Performs HEAD request first (faster), falls back to GET if HEAD fails.
        Considers 200-299 as "live", 4xx/5xx as "dead".

        Args:
            url: URL to verify

        Returns:
            LinkStatus with verification results

        Error Conditions:
        - Timeout: Returns status="error" after 10s
        - DNS failure: Returns status="error"
        - SSL errors: Returns status="error"
        - 4xx/5xx: Returns status="dead" with status_code

        Example:
            >>> verifier = LinkVerifier()
            >>> result = verifier.verify_url("https://example.com")
            >>> result.status
            'live'
            >>> result.status_code
            200
        """
        try:
            # Try HEAD first (faster, no body download)
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)

            # Some servers don't support HEAD, try GET
            if response.status_code == 405:  # Method Not Allowed
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    allow_redirects=True,
                    stream=True,  # Don't download full body
                )

            # Check status
            if 200 <= response.status_code < 300:
                return LinkStatus(url=url, status="live", status_code=response.status_code)
            return LinkStatus(url=url, status="dead", status_code=response.status_code)

        except requests.Timeout:
            logger.warning(f"Timeout verifying URL: {url}")
            return LinkStatus(
                url=url, status="error", error_message="Request timeout after 10 seconds"
            )

        except requests.ConnectionError as e:
            logger.warning(f"Connection error for URL {url}: {str(e)[:100]}")
            return LinkStatus(
                url=url, status="error", error_message=f"Connection error: {str(e)[:100]}"
            )

        except Exception as e:
            logger.error(f"Unexpected error verifying {url}: {e!s}")
            return LinkStatus(
                url=url, status="error", error_message=f"Unexpected error: {str(e)[:100]}"
            )

    def get_archive_url(self, url: str) -> Optional[str]:
        """
        Get latest archive.org snapshot URL for a given URL.

        Uses waybackpy to query Wayback Machine CDX API for most recent
        snapshot. Returns None if no archive found or API unavailable.

        Args:
            url: Original URL to find in archive

        Returns:
            Archive.org URL (e.g., "https://web.archive.org/web/20231101.../article")
            or None if not found

        Error Conditions:
        - No archive found: Returns None (not an error)
        - API errors: Logs warning and returns None
        - waybackpy not installed: Returns None

        Rate Limiting:
        - Wayback CDX API allows ~15 requests/second
        - No additional rate limiting needed for this method

        Example:
            >>> verifier = LinkVerifier()
            >>> archive_url = verifier.get_archive_url("https://example.com/article")
            >>> if archive_url:
            ...     print(f"Found: {archive_url}")
        """
        if not WAYBACK_AVAILABLE:
            logger.debug("waybackpy not available, skipping archive lookup")
            return None

        try:
            # Query Wayback Machine for snapshots
            cdx_api = WaybackMachineCDXServerAPI(url, user_agent="EpsteinArchiveScraper/1.0")

            # Get newest snapshot
            newest = cdx_api.newest()

            if newest:
                archive_url = newest.archive_url
                logger.info(f"Found archive for {url}: {archive_url}")
                return archive_url
            logger.debug(f"No archive found for {url}")
            return None

        except Exception as e:
            logger.warning(f"Archive lookup failed for {url}: {str(e)[:100]}")
            return None

    def verify_with_archive_fallback(self, url: str) -> LinkStatus:
        """
        Verify URL and automatically check archive.org if dead.

        Convenience method that:
        1. Verifies URL is live
        2. If dead/error, checks archive.org
        3. Returns combined result

        Args:
            url: URL to verify

        Returns:
            LinkStatus with archive_url populated if found

        Example:
            >>> verifier = LinkVerifier()
            >>> result = verifier.verify_with_archive_fallback("https://dead-site.com")
            >>> if result.archive_url:
            ...     print("Use archived version")
        """
        result = self.verify_url(url)

        # If dead or error, try archive
        if result.status in ["dead", "error"]:
            logger.info(f"URL {result.status}, checking archive.org...")
            archive_url = self.get_archive_url(url)

            if archive_url:
                result.archive_url = archive_url
                result.status = "archived"

        return result

    def batch_verify(
        self, urls: list[str], check_archive: bool = True, log_file: Optional[str] = None
    ) -> list[LinkStatus]:
        """
        Verify multiple URLs with progress bar and rate limiting.

        Processes URLs sequentially with configurable rate limit to avoid
        overwhelming servers or triggering rate limits. Shows progress bar
        using tqdm.

        Args:
            urls: List of URLs to verify
            check_archive: Whether to check archive.org for dead links (default: True)
            log_file: Optional path to write error log (default: None)

        Returns:
            List of LinkStatus results (same order as input)

        Performance:
        - Rate limited to 1 request/second by default
        - 100 URLs takes ~2-3 minutes
        - Archive lookups add ~1-2 seconds per dead link

        Error Handling:
        - Individual failures logged but don't stop batch
        - All errors written to log_file if provided
        - Progress bar shows failures in real-time

        Example:
            >>> verifier = LinkVerifier()
            >>> urls = ["https://example.com", "https://dead.com"]
            >>> results = verifier.batch_verify(
            ...     urls,
            ...     log_file="/tmp/errors.log"
            ... )
            >>> live_count = sum(1 for r in results if r.status == "live")
        """
        results = []
        errors = []

        logger.info(f"Starting batch verification of {len(urls)} URLs...")

        for url in tqdm(urls, desc="Verifying URLs", unit="url"):
            # Apply rate limiting
            time.sleep(self.rate_limit)

            # Verify URL
            if check_archive:
                result = self.verify_with_archive_fallback(url)
            else:
                result = self.verify_url(url)

            results.append(result)

            # Track errors for logging
            if result.status == "error":
                errors.append(result)

        # Log summary
        live_count = sum(1 for r in results if r.status == "live")
        dead_count = sum(1 for r in results if r.status == "dead")
        archived_count = sum(1 for r in results if r.status == "archived")
        error_count = sum(1 for r in results if r.status == "error")

        logger.info(
            f"Batch verification complete: "
            f"{live_count} live, {dead_count} dead, "
            f"{archived_count} archived, {error_count} errors"
        )

        # Write errors to log file
        if log_file and errors:
            with open(log_file, "w") as f:
                f.write(f"Link Verification Errors ({len(errors)} total)\n")
                f.write("=" * 80 + "\n\n")

                for error in errors:
                    f.write(f"URL: {error.url}\n")
                    f.write(f"Error: {error.error_message}\n")
                    f.write("-" * 80 + "\n")

            logger.info(f"Errors written to {log_file}")

        return results


# Convenience functions for simple use cases


def verify_single_url(url: str) -> LinkStatus:
    """
    Verify a single URL (convenience wrapper).

    Args:
        url: URL to verify

    Returns:
        LinkStatus with verification results

    Example:
        >>> from link_verifier import verify_single_url
        >>> result = verify_single_url("https://example.com")
        >>> print(result.status)
    """
    verifier = LinkVerifier()
    return verifier.verify_with_archive_fallback(url)


def verify_urls_from_list(urls: list[str], output_file: Optional[str] = None) -> dict:
    """
    Verify list of URLs and return summary statistics.

    Args:
        urls: List of URLs to verify
        output_file: Optional file to write error log

    Returns:
        Dictionary with summary statistics and results

    Example:
        >>> urls = ["https://example.com", "https://dead.com"]
        >>> summary = verify_urls_from_list(urls, "errors.log")
        >>> print(f"Live: {summary['live_count']}")
    """
    verifier = LinkVerifier()
    results = verifier.batch_verify(urls, log_file=output_file)

    return {
        "total": len(results),
        "live_count": sum(1 for r in results if r.status == "live"),
        "dead_count": sum(1 for r in results if r.status == "dead"),
        "archived_count": sum(1 for r in results if r.status == "archived"),
        "error_count": sum(1 for r in results if r.status == "error"),
        "results": results,
    }


if __name__ == "__main__":
    # Test verification
    verifier = LinkVerifier()

    # Test live URL
    print("Testing live URL...")
    result = verifier.verify_with_archive_fallback("https://www.example.com")
    print(f"Result: {result.status} (code: {result.status_code})")

    # Test batch verification
    print("\nTesting batch verification...")
    test_urls = [
        "https://www.example.com",
        "https://www.nytimes.com",
        "https://this-site-definitely-does-not-exist-12345.com",
    ]

    results = verifier.batch_verify(test_urls, check_archive=True)

    print("\nResults:")
    for result in results:
        print(f"  {result.url[:50]}: {result.status}")
