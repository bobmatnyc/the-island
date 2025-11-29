"""
Document Service - Business logic for document operations

Design Decision: Centralized Document Management
Rationale: All document search, filtering, and classification logic
in one service for consistency and maintainability.

Handles:
- Document search (full-text, entity mentions, classification)
- Document filtering by type, source, entity
- Document classification metadata
- Content retrieval
"""

import json
from pathlib import Path
from typing import Optional


class DocumentService:
    """Service for document data operations"""

    def __init__(self, data_path: Path):
        """Initialize document service

        Args:
            data_path: Path to data directory
        """
        self.data_path = data_path
        self.metadata_dir = data_path / "metadata"
        self.md_dir = data_path / "md"

        # Data caches
        self.documents: list[dict] = []
        self.classifications: dict = {}
        self.semantic_index: dict = {}
        self._document_index: dict[str, dict] = {}  # ID → document mapping for O(1) lookups

        # Load data
        self.load_data()

    def load_data(self):
        """Load document index and classifications"""
        # Load unified document index
        doc_index_path = self.metadata_dir / "all_documents_index.json"
        if doc_index_path.exists():
            with open(doc_index_path) as f:
                doc_data = json.load(f)
                self.documents = doc_data.get("documents", [])

        # Load classifications
        class_path = self.metadata_dir / "document_classifications.json"
        if class_path.exists():
            with open(class_path) as f:
                data = json.load(f)
                self.classifications = data.get("results", {})

        # Load semantic index
        semantic_path = self.metadata_dir / "semantic_index.json"
        if semantic_path.exists():
            with open(semantic_path) as f:
                data = json.load(f)
                self.semantic_index = data.get("entity_to_documents", {})

        # Build ID index for O(1) lookups
        self._build_document_index()

    def _build_document_index(self):
        """Build document ID index for O(1) lookups

        Validates:
        - Warns about duplicate IDs (keeps last occurrence)
        - Skips documents with missing/null IDs (logs warning)
        """
        self._document_index = {}
        duplicate_ids = []
        skipped_count = 0

        for doc in self.documents:
            doc_id = doc.get("id")

            # Skip documents without valid IDs
            if not doc_id:
                skipped_count += 1
                continue

            # Track duplicates (should not happen, but validate anyway)
            if doc_id in self._document_index:
                duplicate_ids.append(doc_id)

            self._document_index[doc_id] = doc

        # Log warnings for data quality issues
        if skipped_count > 0:
            print(f"WARNING: Skipped {skipped_count} documents with missing/null IDs during index build")

        if duplicate_ids:
            print(f"WARNING: Found {len(duplicate_ids)} duplicate document IDs: {duplicate_ids[:10]}...")

        # Log success
        print(f"Built document ID index: {len(self._document_index)} documents indexed")

    def search_documents(
        self,
        q: Optional[str] = None,
        entity: Optional[str] = None,
        doc_type: Optional[str] = None,
        source: Optional[str] = None,
        classification: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """Search documents with multiple filters

        Args:
            q: Full-text search query (searches filename and path)
            entity: Filter by entity mention
            doc_type: Filter by document type (email, pdf)
            source: Filter by source collection
            classification: Filter by classification (email, court_filing, etc.)
            limit: Results per page
            offset: Pagination offset

        Returns:
            {
                "documents": List of matching documents,
                "total": Total matching count,
                "facets": Available filter options
            }
        """
        filtered_docs = self.documents.copy()

        # ALWAYS filter out JSON metadata files and unavailable content
        filtered_docs = [
            doc
            for doc in filtered_docs
            if not (
                # Exclude JSON files from data/metadata/ directory
                (
                    doc.get("path", "").startswith("data/metadata/")
                    and doc.get("filename", "").endswith(".json")
                )
                or
                # Exclude documents with unavailable content
                doc.get("content") == "Content not available for this document."
            )
        ]

        # Full-text search in filename and path
        if q:
            q_lower = q.lower()
            filtered_docs = [
                doc
                for doc in filtered_docs
                if q_lower in doc.get("filename", "").lower()
                or q_lower in doc.get("path", "").lower()
            ]

        # Filter by entity mention
        if entity:
            entity_lower = entity.lower()
            filtered_docs = [
                doc
                for doc in filtered_docs
                if any(entity_lower in e.lower() for e in doc.get("entities_mentioned", []))
            ]

        # Filter by document type (email, pdf)
        if doc_type:
            filtered_docs = [
                doc for doc in filtered_docs if doc.get("type", "").lower() == doc_type.lower()
            ]

        # Filter by classification
        if classification:
            filtered_docs = [
                doc
                for doc in filtered_docs
                if doc.get("classification", "").lower() == classification.lower()
            ]

        # Filter by source
        if source:
            filtered_docs = [
                doc for doc in filtered_docs if source.lower() in doc.get("source", "").lower()
            ]

        # Get facets for filtering
        all_types = {doc.get("type", "unknown") for doc in self.documents}
        all_classifications = {doc.get("classification", "unknown") for doc in self.documents}
        all_sources = {doc.get("source", "unknown") for doc in self.documents}

        # Paginate
        total = len(filtered_docs)
        docs_page = filtered_docs[offset : offset + limit]

        return {
            "documents": docs_page,
            "total": total,
            "offset": offset,
            "limit": limit,
            "facets": {
                "types": sorted(all_types),
                "classifications": sorted(all_classifications),
                "sources": sorted(all_sources),
            },
        }

    def get_document_by_id(self, doc_id: str) -> Optional[dict]:
        """Get single document by ID

        Args:
            doc_id: Document ID

        Returns:
            Document with full content, or None if not found

        Performance:
            O(1) hash lookup via document index (previously O(n) linear search)
        """
        # O(1) index lookup (replaces O(n) linear search)
        document = self._document_index.get(doc_id)

        if not document:
            return None

        # Try to load content from markdown file
        content = None
        doc_path = document.get("path", "")
        if doc_path:
            md_path = Path(doc_path)
            if md_path.exists() and md_path.suffix == ".md":
                try:
                    with open(md_path) as f:
                        content = f.read()
                except Exception:
                    pass

        document["content"] = content
        return document

    def get_documents_by_entity(self, entity_name: str) -> dict:
        """Get all documents mentioning an entity

        Args:
            entity_name: Entity name

        Returns:
            {
                "entity": Entity name,
                "documents": List of documents,
                "total": Count
            }
        """
        # Get document paths from semantic index
        doc_paths = self.semantic_index.get(entity_name, [])

        # Find matching documents
        matching_docs = [
            doc
            for doc in self.documents
            if doc.get("path") in doc_paths or entity_name in doc.get("entities_mentioned", [])
        ]

        return {"entity": entity_name, "documents": matching_docs, "total": len(matching_docs)}

    def get_statistics(self) -> dict:
        """Get document statistics

        Returns:
            {
                "total_documents": Total count,
                "by_type": Count per type,
                "by_classification": Count per classification,
                "by_source": Count per source
            }
        """
        # Count by type
        by_type = {}
        for doc in self.documents:
            doc_type = doc.get("type", "unknown")
            by_type[doc_type] = by_type.get(doc_type, 0) + 1

        # Count by classification
        by_classification = {}
        for doc in self.documents:
            classification = doc.get("classification", "unknown")
            by_classification[classification] = by_classification.get(classification, 0) + 1

        # Count by source
        by_source = {}
        for doc in self.documents:
            source = doc.get("source", "unknown")
            by_source[source] = by_source.get(source, 0) + 1

        return {
            "total_documents": len(self.documents),
            "by_type": by_type,
            "by_classification": by_classification,
            "by_source": by_source,
        }
