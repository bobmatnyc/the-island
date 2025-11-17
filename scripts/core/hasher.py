"""
Document Hashing Utilities

Provides multiple hashing strategies:
1. File hash - SHA-256 of exact binary content
2. Content hash - SHA-256 of normalized text content
3. Fuzzy hash - ssdeep for near-duplicate detection
4. Visual hash - For image-based documents
"""

import hashlib
import re
from pathlib import Path
from typing import Dict, Optional, Tuple


class DocumentHasher:
    """
    Multi-strategy document hashing for deduplication.

    Design Decision: Multiple Hash Types
    Rationale: Different hash types serve different deduplication needs:
    - File hash: Catches exact binary duplicates (same PDF file)
    - Content hash: Catches same text in different formats
    - Fuzzy hash: Catches OCR variations and minor differences

    Trade-offs:
    - Performance: Multiple hashes take more time vs. better deduplication
    - Storage: More hashes require more database space
    - Accuracy: Multiple strategies reduce false negatives
    """

    def __init__(self):
        self.fuzzy_available = self._check_ssdeep()

    def _check_ssdeep(self) -> bool:
        """Check if ssdeep library is available for fuzzy hashing."""
        try:
            import ssdeep
            return True
        except ImportError:
            return False

    def hash_file(self, file_path: Path) -> str:
        """
        Generate SHA-256 hash of file binary content.

        Args:
            file_path: Path to file

        Returns:
            SHA-256 hash as hex string

        Performance: O(n) where n is file size. Chunked reading for memory efficiency.
        """
        sha256 = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read in 8KB chunks for memory efficiency
            while chunk := f.read(8192):
                sha256.update(chunk)

        return f"sha256:{sha256.hexdigest()}"

    def hash_content(self, text: str, normalize: bool = True) -> str:
        """
        Generate SHA-256 hash of text content.

        Args:
            text: Text content to hash
            normalize: Whether to normalize text first (removes OCR artifacts)

        Returns:
            SHA-256 hash as hex string

        Design Decision: Text Normalization
        Rationale: OCR variations produce different text for same document.
        Normalization handles whitespace, line breaks, encoding differences.
        """
        if normalize:
            text = self.normalize_text(text)

        sha256 = hashlib.sha256()
        sha256.update(text.encode("utf-8"))

        return f"sha256:{sha256.hexdigest()}"

    def hash_fuzzy(self, text: str) -> Optional[str]:
        """
        Generate fuzzy hash (ssdeep) for near-duplicate detection.

        Args:
            text: Text content to hash

        Returns:
            ssdeep hash string, or None if ssdeep not available

        Performance: O(n) but slower than SHA-256. Only use when needed.
        """
        if not self.fuzzy_available:
            return None

        import ssdeep
        return f"ssdeep:{ssdeep.hash(text)}"

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text to handle OCR variations.

        Normalization steps:
        1. Convert to lowercase
        2. Normalize whitespace (collapse multiple spaces)
        3. Normalize line breaks
        4. Remove common OCR artifacts
        5. Remove control characters

        Args:
            text: Raw text

        Returns:
            Normalized text

        Design Decision: Aggressive Normalization
        Rationale: OCR engines produce different output for same document.
        We need to ignore formatting differences while preserving content.

        Trade-off: May miss legitimate differences vs. better duplicate detection
        """
        # Convert to lowercase
        text = text.lower()

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # Normalize line breaks
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Remove common OCR artifacts
        # Replace common OCR misreads
        text = text.replace("‐", "-")  # Unicode hyphen to ASCII
        text = text.replace("–", "-")  # En dash to hyphen
        text = text.replace("—", "-")  # Em dash to hyphen
        text = text.replace('"', '"').replace('"', '"')  # Smart quotes
        text = text.replace(""", "'").replace(""", "'")  # Smart apostrophes

        # Remove control characters except newlines
        text = "".join(char for char in text if char == "\n" or not char.isspace() or char == " ")

        # Trim
        text = text.strip()

        return text

    def hash_document(self, file_path: Path, text: Optional[str] = None) -> Dict[str, str]:
        """
        Generate all hash types for a document.

        Args:
            file_path: Path to document file
            text: Extracted text content (if available)

        Returns:
            Dictionary with all hash types:
            {
                'file_hash': 'sha256:...',
                'content_hash': 'sha256:...',
                'fuzzy_hash': 'ssdeep:...' or None
            }

        Usage:
            hasher = DocumentHasher()
            text = extract_text(pdf_file)
            hashes = hasher.hash_document(pdf_file, text)
        """
        result = {
            "file_hash": self.hash_file(file_path)
        }

        if text:
            result["content_hash"] = self.hash_content(text, normalize=True)
            result["fuzzy_hash"] = self.hash_fuzzy(text)

        return result

    @staticmethod
    def compare_fuzzy(hash1: str, hash2: str) -> float:
        """
        Compare two fuzzy hashes and return similarity score.

        Args:
            hash1: First fuzzy hash (ssdeep format)
            hash2: Second fuzzy hash (ssdeep format)

        Returns:
            Similarity score (0.0-1.0)

        Raises:
            ImportError: If ssdeep not available
        """
        import ssdeep

        # Strip 'ssdeep:' prefix if present
        h1 = hash1.replace("ssdeep:", "")
        h2 = hash2.replace("ssdeep:", "")

        # ssdeep.compare returns 0-100
        similarity = ssdeep.compare(h1, h2)

        return similarity / 100.0


class PageHasher:
    """
    Hash individual pages for partial overlap detection.

    Design Decision: Page-Level Hashing
    Rationale: Some documents share only partial pages (e.g., same email
    but different attachments). Page-level hashing detects these cases.

    Use Case: Doc A has pages 1-10, Doc B has pages 5-15.
    We can detect pages 5-10 are duplicates while keeping both docs.
    """

    def __init__(self):
        self.hasher = DocumentHasher()

    def hash_pages(self, pages: list) -> Dict[int, str]:
        """
        Hash each page individually.

        Args:
            pages: List of page text content

        Returns:
            Dictionary mapping page number to content hash
            {
                1: 'sha256:...',
                2: 'sha256:...',
                ...
            }

        Performance: O(n * m) where n = num pages, m = avg page length
        """
        page_hashes = {}

        for i, page_text in enumerate(pages, start=1):
            if page_text:
                page_hashes[i] = self.hasher.hash_content(page_text)

        return page_hashes

    def find_common_pages(
        self,
        pages_a: Dict[int, str],
        pages_b: Dict[int, str]
    ) -> Tuple[set, float, float]:
        """
        Find common pages between two documents.

        Args:
            pages_a: Page hashes for document A
            pages_b: Page hashes for document B

        Returns:
            Tuple of:
            - Set of common page hashes
            - Overlap percentage for doc A (0.0-1.0)
            - Overlap percentage for doc B (0.0-1.0)

        Example:
            Doc A has 10 pages, Doc B has 20 pages, 5 pages in common.
            Returns: (common_hashes, 0.5, 0.25)
        """
        hashes_a = set(pages_a.values())
        hashes_b = set(pages_b.values())

        common = hashes_a & hashes_b

        overlap_a = len(common) / len(hashes_a) if hashes_a else 0.0
        overlap_b = len(common) / len(hashes_b) if hashes_b else 0.0

        return common, overlap_a, overlap_b


def generate_canonical_id(content_hash: str) -> str:
    """
    Generate canonical document ID from content hash.

    Format: epstein_doc_[first_12_chars_of_hash]

    Args:
        content_hash: SHA-256 content hash (format: "sha256:...")

    Returns:
        Canonical ID string

    Example:
        "sha256:abc123def456..." -> "epstein_doc_abc123def456"

    Design Decision: Hash-Based IDs
    Rationale: Content-based IDs are deterministic and collision-resistant.
    Same content always produces same ID, making deduplication easier.

    Alternative Considered: Sequential IDs (rejected due to non-determinism)
    """
    # Extract hex portion
    hash_hex = content_hash.split(":")[1] if ":" in content_hash else content_hash

    # Use first 12 characters for readability
    short_hash = hash_hex[:12]

    return f"epstein_doc_{short_hash}"


if __name__ == "__main__":
    # Example usage
    hasher = DocumentHasher()

    # Example text
    text1 = "This is a sample document with some content."
    text2 = "This  is  a  sample   document with some content."  # Extra whitespace

    # Generate hashes
    hash1 = hasher.hash_content(text1)
    hash2 = hasher.hash_content(text2)

    print(f"Text 1 hash: {hash1}")
    print(f"Text 2 hash: {hash2}")
    print(f"Are they the same? {hash1 == hash2}")  # Should be True after normalization

    # Generate canonical ID
    canonical_id = generate_canonical_id(hash1)
    print(f"Canonical ID: {canonical_id}")
