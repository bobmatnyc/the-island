"""
Deduplication Engine

Implements multi-strategy duplicate detection:
1. Exact matching (file hash, content hash)
2. Fuzzy matching (ssdeep, text similarity)
3. Metadata matching (for emails)
4. Partial overlap detection
"""

from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional


@dataclass
class Document:
    """Document representation for deduplication."""

    id: str
    file_path: Path
    file_hash: str
    content_hash: str
    fuzzy_hash: Optional[str]
    text: str
    document_type: str

    # Metadata (for emails)
    from_person: Optional[str] = None
    to_persons: Optional[list[str]] = None
    date: Optional[str] = None
    subject: Optional[str] = None

    # Page hashes (for partial overlap)
    page_hashes: Optional[dict[int, str]] = None


@dataclass
class DuplicateGroup:
    """
    Group of duplicate documents.

    Attributes:
        type: exact|fuzzy|metadata|partial
        docs: List of document IDs in this group
        similarity: Similarity score (0.0-1.0)
        method: Detection method used
        metadata: Additional info about the match
    """

    type: str
    docs: list[str]
    similarity: float
    method: str
    metadata: Optional[dict] = None


class Deduplicator:
    """
    Multi-strategy deduplication engine.

    Design Decision: Four-Phase Deduplication
    Rationale: Different duplicate types require different detection methods.
    Exact matches are fast and certain. Fuzzy matching catches OCR variations.
    Metadata matching handles email duplicates. Partial overlap detection
    finds documents that share some pages.

    Trade-offs:
    - Performance: Multiple passes take more time vs. better detection
    - Accuracy: More strategies reduce false negatives but increase complexity
    - Threshold Tuning: Fuzzy matching threshold affects precision/recall

    Performance:
    - Phase 1 (Exact): O(n) with hash map
    - Phase 2 (Fuzzy): O(n²) comparisons (optimize with clustering)
    - Phase 3 (Metadata): O(n) with hash map
    - Phase 4 (Partial): O(n²) page comparisons
    """

    def __init__(
        self,
        fuzzy_threshold: float = 0.90,
        metadata_threshold: float = 0.95,
        partial_overlap_min: float = 0.10,
        partial_overlap_max: float = 0.90,
    ):
        """
        Initialize deduplicator with thresholds.

        Args:
            fuzzy_threshold: Minimum similarity for fuzzy matching (0.0-1.0)
            metadata_threshold: Minimum similarity for metadata matching
            partial_overlap_min: Min overlap % to detect (avoid exact duplicates)
            partial_overlap_max: Max overlap % to detect (avoid exact duplicates)
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.metadata_threshold = metadata_threshold
        self.partial_overlap_min = partial_overlap_min
        self.partial_overlap_max = partial_overlap_max

    def deduplicate(self, documents: list[Document]) -> list[DuplicateGroup]:
        """
        Run all deduplication phases.

        Args:
            documents: List of Document objects

        Returns:
            List of DuplicateGroup objects

        Usage:
            dedup = Deduplicator()
            groups = dedup.deduplicate(documents)

            for group in groups:
                print(f"Found {len(group.docs)} duplicates ({group.type})")
        """
        all_groups = []

        # Phase 1: Exact matching
        exact_groups = self.detect_exact_duplicates(documents)
        all_groups.extend(exact_groups)

        # Phase 2: Fuzzy matching (exclude documents already in exact groups)
        exact_doc_ids = {doc_id for group in exact_groups for doc_id in group.docs}
        fuzzy_candidates = [doc for doc in documents if doc.id not in exact_doc_ids]
        fuzzy_groups = self.detect_fuzzy_duplicates(fuzzy_candidates)
        all_groups.extend(fuzzy_groups)

        # Phase 3: Metadata matching (emails only)
        email_docs = [doc for doc in documents if doc.document_type == "email"]
        metadata_groups = self.detect_metadata_duplicates(email_docs)
        all_groups.extend(metadata_groups)

        # Phase 4: Partial overlaps
        partial_groups = self.detect_partial_overlaps(documents)
        all_groups.extend(partial_groups)

        return all_groups

    def detect_exact_duplicates(self, documents: list[Document]) -> list[DuplicateGroup]:
        """
        Phase 1: Detect exact duplicates using file and content hashes.

        Complexity: O(n) where n is number of documents
        Memory: O(n) for hash maps

        Returns:
            List of DuplicateGroup objects with type='exact'
        """
        file_hash_map = {}
        content_hash_map = {}

        # Build hash maps
        for doc in documents:
            # File hash
            if doc.file_hash:
                file_hash_map.setdefault(doc.file_hash, []).append(doc.id)

            # Content hash
            if doc.content_hash:
                content_hash_map.setdefault(doc.content_hash, []).append(doc.id)

        # Create duplicate groups
        groups = []

        # Content hash duplicates (prefer content over file)
        for content_hash, doc_ids in content_hash_map.items():
            if len(doc_ids) > 1:
                groups.append(
                    DuplicateGroup(
                        type="exact",
                        docs=doc_ids,
                        similarity=1.0,
                        method="content_hash",
                        metadata={"hash": content_hash},
                    )
                )

        # File hash duplicates (only if not already in content groups)
        content_group_docs = {doc_id for group in groups for doc_id in group.docs}
        for file_hash, doc_ids in file_hash_map.items():
            if len(doc_ids) > 1:
                # Only include docs not already in content groups
                unique_docs = [doc_id for doc_id in doc_ids if doc_id not in content_group_docs]
                if len(unique_docs) > 1:
                    groups.append(
                        DuplicateGroup(
                            type="exact",
                            docs=unique_docs,
                            similarity=1.0,
                            method="file_hash",
                            metadata={"hash": file_hash},
                        )
                    )

        return groups

    def detect_fuzzy_duplicates(self, documents: list[Document]) -> list[DuplicateGroup]:
        """
        Phase 2: Detect fuzzy duplicates using similarity matching.

        Uses both fuzzy hashing (ssdeep) and text similarity (difflib).
        Takes the maximum similarity score from both methods.

        Complexity: O(n²) - compares all pairs
        Optimization Opportunity: Use LSH (locality-sensitive hashing) for O(n)

        Returns:
            List of DuplicateGroup objects with type='fuzzy'
        """
        groups = []
        compared = set()

        for i, doc_a in enumerate(documents):
            for doc_b in documents[i + 1 :]:
                pair = tuple(sorted([doc_a.id, doc_b.id]))
                if pair in compared:
                    continue
                compared.add(pair)

                # Calculate similarity
                similarity = self._calculate_similarity(doc_a, doc_b)

                if similarity >= self.fuzzy_threshold:
                    groups.append(
                        DuplicateGroup(
                            type="fuzzy",
                            docs=[doc_a.id, doc_b.id],
                            similarity=similarity,
                            method="fuzzy_hash" if doc_a.fuzzy_hash else "text_diff",
                            metadata={"score": similarity},
                        )
                    )

        return groups

    def _calculate_similarity(self, doc_a: Document, doc_b: Document) -> float:
        """
        Calculate similarity between two documents.

        Uses multiple methods and returns maximum score:
        1. Fuzzy hash (ssdeep) if available
        2. Text similarity (difflib)

        Args:
            doc_a: First document
            doc_b: Second document

        Returns:
            Similarity score (0.0-1.0)
        """
        scores = []

        # Fuzzy hash comparison
        if doc_a.fuzzy_hash and doc_b.fuzzy_hash:
            try:
                import ssdeep

                # Strip 'ssdeep:' prefix
                hash_a = doc_a.fuzzy_hash.replace("ssdeep:", "")
                hash_b = doc_b.fuzzy_hash.replace("ssdeep:", "")
                fuzzy_score = ssdeep.compare(hash_a, hash_b) / 100.0
                scores.append(fuzzy_score)
            except ImportError:
                pass

        # Text similarity (use first 10KB for performance)
        if doc_a.text and doc_b.text:
            text_a = doc_a.text[:10000]
            text_b = doc_b.text[:10000]
            text_score = SequenceMatcher(None, text_a, text_b).ratio()
            scores.append(text_score)

        return max(scores) if scores else 0.0

    def detect_metadata_duplicates(self, documents: list[Document]) -> list[DuplicateGroup]:
        """
        Phase 3: Detect duplicates using email metadata.

        Creates signature from (from, to, date, subject) and finds matches.
        Useful for emails that may have different OCR but same metadata.

        Complexity: O(n) with hash map

        Returns:
            List of DuplicateGroup objects with type='metadata'
        """
        metadata_map = {}

        for doc in documents:
            if not doc.from_person:
                continue

            # Create metadata signature
            signature = self._create_metadata_signature(doc)

            metadata_map.setdefault(signature, []).append(doc.id)

        # Create groups
        groups = []
        for signature, doc_ids in metadata_map.items():
            if len(doc_ids) > 1:
                groups.append(
                    DuplicateGroup(
                        type="metadata",
                        docs=doc_ids,
                        similarity=self.metadata_threshold,
                        method="email_metadata",
                        metadata={"signature": str(signature)},
                    )
                )

        return groups

    @staticmethod
    def _create_metadata_signature(doc: Document) -> tuple:
        """
        Create hashable metadata signature for email.

        Normalizes subject line and email addresses for matching.
        """
        # Normalize subject (remove Re:, Fwd:, etc.)
        subject = doc.subject or ""
        subject = subject.lower()
        subject = subject.replace("re:", "").replace("fw:", "").replace("fwd:", "")
        subject = " ".join(subject.split())  # Normalize whitespace

        # Normalize email addresses
        from_email = (doc.from_person or "").lower().strip()
        to_emails = frozenset(email.lower().strip() for email in (doc.to_persons or []))

        return (from_email, to_emails, doc.date, subject)

    def detect_partial_overlaps(self, documents: list[Document]) -> list[DuplicateGroup]:
        """
        Phase 4: Detect documents with partial page overlaps.

        Finds documents that share some pages but not all.
        Example: Doc A has pages 1-10, Doc B has pages 5-15.

        Complexity: O(n² * p) where p is average page count
        Optimization Opportunity: Hash-based page matching for O(n * p)

        Returns:
            List of DuplicateGroup objects with type='partial'
        """
        groups = []

        # Filter documents with page hashes
        docs_with_pages = [doc for doc in documents if doc.page_hashes]

        for i, doc_a in enumerate(docs_with_pages):
            for doc_b in docs_with_pages[i + 1 :]:
                overlap_info = self._calculate_page_overlap(doc_a, doc_b)

                if overlap_info:
                    groups.append(
                        DuplicateGroup(
                            type="partial",
                            docs=[doc_a.id, doc_b.id],
                            similarity=overlap_info["overlap_percentage"],
                            method="page_hash",
                            metadata=overlap_info,
                        )
                    )

        return groups

    def _calculate_page_overlap(self, doc_a: Document, doc_b: Document) -> Optional[dict]:
        """
        Calculate page overlap between two documents.

        Args:
            doc_a: First document
            doc_b: Second document

        Returns:
            Dictionary with overlap info, or None if no overlap
        """
        if not doc_a.page_hashes or not doc_b.page_hashes:
            return None

        # Get page hash sets
        hashes_a = set(doc_a.page_hashes.values())
        hashes_b = set(doc_b.page_hashes.values())

        # Find common pages
        common = hashes_a & hashes_b

        if not common:
            return None

        # Calculate overlap percentages
        overlap_a = len(common) / len(hashes_a) if hashes_a else 0.0
        overlap_b = len(common) / len(hashes_b) if hashes_b else 0.0

        # Check if within partial overlap range
        if not (
            self.partial_overlap_min <= overlap_a <= self.partial_overlap_max
            or self.partial_overlap_min <= overlap_b <= self.partial_overlap_max
        ):
            return None

        # Find which pages overlap
        pages_a = [page for page, hash_val in doc_a.page_hashes.items() if hash_val in common]
        pages_b = [page for page, hash_val in doc_b.page_hashes.items() if hash_val in common]

        return {
            "common_pages": len(common),
            "overlap_pct_a": overlap_a,
            "overlap_pct_b": overlap_b,
            "overlap_percentage": max(overlap_a, overlap_b),
            "pages_a": self._format_page_range(pages_a),
            "pages_b": self._format_page_range(pages_b),
        }

    @staticmethod
    def _format_page_range(pages: list[int]) -> str:
        """
        Format list of page numbers as range string.

        Examples:
            [1, 2, 3, 5, 6] -> "1-3, 5-6"
            [1, 3, 5] -> "1, 3, 5"
        """
        if not pages:
            return ""

        pages = sorted(pages)
        ranges = []
        start = pages[0]
        end = pages[0]

        for page in pages[1:]:
            if page == end + 1:
                end = page
            else:
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                start = end = page

        # Add final range
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append(f"{start}-{end}")

        return ", ".join(ranges)


if __name__ == "__main__":
    # Example usage
    from core.hasher import DocumentHasher

    hasher = DocumentHasher()

    # Create test documents
    docs = [
        Document(
            id="doc1",
            file_path=Path("test1.pdf"),
            file_hash="sha256:abc123",
            content_hash=hasher.hash_content("This is document 1"),
            fuzzy_hash=None,
            text="This is document 1",
            document_type="email",
            from_person="sender@example.com",
            to_persons=["recipient@example.com"],
            date="2008-05-15",
            subject="Test Email",
        ),
        Document(
            id="doc2",
            file_path=Path("test2.pdf"),
            file_hash="sha256:def456",
            content_hash=hasher.hash_content("This is document 1"),  # Same content
            fuzzy_hash=None,
            text="This is document 1",
            document_type="email",
            from_person="sender@example.com",
            to_persons=["recipient@example.com"],
            date="2008-05-15",
            subject="Test Email",
        ),
    ]

    # Run deduplication
    dedup = Deduplicator()
    groups = dedup.deduplicate(docs)

    print(f"Found {len(groups)} duplicate groups:")
    for group in groups:
        print(f"  {group.type}: {group.docs} (similarity: {group.similarity:.2f})")
