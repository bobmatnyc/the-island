"""
SQLite Database Interface for Canonicalization System

Provides clean interface to deduplication_index.db with:
- Document CRUD operations
- Source tracking
- Duplicate group management
- Query utilities
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional


class CanonicalDatabase:
    """
    SQLite database interface for document canonicalization.

    Design Decision: SQLite vs PostgreSQL
    Rationale: SQLite chosen for simplicity and portability.
    - No server setup required
    - Entire database is single file
    - Sufficient performance for 100,000+ documents
    - Easy backup and version control

    Trade-offs:
    - Concurrency: SQLite has limited write concurrency
    - Scale: For millions of documents, consider PostgreSQL
    - Features: No full-text search (use external tool)

    Performance: Query times <1s for 100,000 docs with proper indexes
    """

    def __init__(self, db_path: Path):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()
        self._create_indexes()

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Usage:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(...)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _create_tables(self):
        """Create all database tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Canonical documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS canonical_documents (
                    canonical_id TEXT PRIMARY KEY,
                    content_hash TEXT NOT NULL UNIQUE,
                    file_hash TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    title TEXT,
                    date TEXT,
                    from_person TEXT,
                    to_persons TEXT,
                    subject TEXT,

                    ocr_quality REAL,
                    has_redactions BOOLEAN,
                    completeness TEXT,
                    page_count INTEGER,

                    primary_source TEXT,
                    selection_reason TEXT,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Document sources table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    canonical_id TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    source_url TEXT,
                    collection TEXT,
                    download_date TEXT,
                    pages TEXT,
                    file_path TEXT,

                    quality_score REAL,
                    file_size INTEGER,
                    format TEXT,

                    FOREIGN KEY (canonical_id) REFERENCES canonical_documents(canonical_id),
                    UNIQUE(canonical_id, source_name)
                )
            """)

            # Duplicate groups table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS duplicate_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    canonical_id TEXT NOT NULL,
                    duplicate_type TEXT,
                    similarity_score REAL,
                    detection_method TEXT,

                    FOREIGN KEY (canonical_id) REFERENCES canonical_documents(canonical_id)
                )
            """)

            # Partial overlaps table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS partial_overlaps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_a_canonical_id TEXT NOT NULL,
                    doc_b_canonical_id TEXT NOT NULL,
                    overlap_type TEXT,
                    overlap_percentage REAL,
                    pages_a TEXT,
                    pages_b TEXT,

                    FOREIGN KEY (doc_a_canonical_id) REFERENCES canonical_documents(canonical_id),
                    FOREIGN KEY (doc_b_canonical_id) REFERENCES canonical_documents(canonical_id)
                )
            """)

            # Processing log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processing_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    operation TEXT,
                    source TEXT,
                    status TEXT,
                    message TEXT,
                    details TEXT
                )
            """)

    def _create_indexes(self):
        """Create indexes for common queries."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Indexes for common lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_hash
                ON canonical_documents(content_hash)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_hash
                ON canonical_documents(file_hash)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_document_type
                ON canonical_documents(document_type)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_date
                ON canonical_documents(date)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_source_canonical
                ON document_sources(canonical_id)
            """)

    # ==================== Canonical Documents ====================

    def insert_canonical_document(self, doc: Dict) -> str:
        """
        Insert a new canonical document.

        Args:
            doc: Dictionary with document fields

        Returns:
            Canonical ID of inserted document

        Raises:
            sqlite3.IntegrityError: If content_hash already exists
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO canonical_documents (
                    canonical_id, content_hash, file_hash, document_type,
                    title, date, from_person, to_persons, subject,
                    ocr_quality, has_redactions, completeness, page_count,
                    primary_source, selection_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc["canonical_id"],
                doc["content_hash"],
                doc["file_hash"],
                doc["document_type"],
                doc.get("title"),
                doc.get("date"),
                doc.get("from_person"),
                json.dumps(doc.get("to_persons", [])),
                doc.get("subject"),
                doc.get("ocr_quality"),
                doc.get("has_redactions"),
                doc.get("completeness"),
                doc.get("page_count"),
                doc.get("primary_source"),
                doc.get("selection_reason")
            ))

        return doc["canonical_id"]

    def get_canonical_document(self, canonical_id: str) -> Optional[Dict]:
        """
        Retrieve canonical document by ID.

        Args:
            canonical_id: Document ID

        Returns:
            Dictionary with document data, or None if not found
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM canonical_documents WHERE canonical_id = ?
            """, (canonical_id,))

            row = cursor.fetchone()

            if row:
                doc = dict(row)
                # Parse JSON fields
                if doc.get("to_persons"):
                    doc["to_persons"] = json.loads(doc["to_persons"])
                return doc

        return None

    def find_by_content_hash(self, content_hash: str) -> Optional[Dict]:
        """
        Find document by content hash.

        Args:
            content_hash: SHA-256 content hash

        Returns:
            Document dict or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM canonical_documents WHERE content_hash = ?
            """, (content_hash,))

            row = cursor.fetchone()

            if row:
                doc = dict(row)
                if doc.get("to_persons"):
                    doc["to_persons"] = json.loads(doc["to_persons"])
                return doc

        return None

    # ==================== Document Sources ====================

    def insert_source(self, source: Dict) -> int:
        """
        Insert a document source.

        Args:
            source: Dictionary with source fields

        Returns:
            Source ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO document_sources (
                    canonical_id, source_name, source_url, collection,
                    download_date, pages, file_path,
                    quality_score, file_size, format
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source["canonical_id"],
                source["source_name"],
                source.get("source_url"),
                source.get("collection"),
                source.get("download_date"),
                source.get("pages"),
                source.get("file_path"),
                source.get("quality_score"),
                source.get("file_size"),
                source.get("format")
            ))

            return cursor.lastrowid

    def get_sources(self, canonical_id: str) -> List[Dict]:
        """
        Get all sources for a canonical document.

        Args:
            canonical_id: Document ID

        Returns:
            List of source dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM document_sources WHERE canonical_id = ?
                ORDER BY quality_score DESC
            """, (canonical_id,))

            return [dict(row) for row in cursor.fetchall()]

    # ==================== Duplicate Groups ====================

    def insert_duplicate_group(self, group: Dict) -> int:
        """
        Insert a duplicate group entry.

        Args:
            group: Dictionary with duplicate group fields

        Returns:
            Group ID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO duplicate_groups (
                    canonical_id, duplicate_type, similarity_score, detection_method
                ) VALUES (?, ?, ?, ?)
            """, (
                group["canonical_id"],
                group.get("duplicate_type"),
                group.get("similarity_score"),
                group.get("detection_method")
            ))

            return cursor.lastrowid

    def get_duplicates(self, canonical_id: str) -> List[Dict]:
        """
        Get all duplicates for a document.

        Args:
            canonical_id: Document ID

        Returns:
            List of duplicate group dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM duplicate_groups WHERE canonical_id = ?
            """, (canonical_id,))

            return [dict(row) for row in cursor.fetchall()]

    # ==================== Partial Overlaps ====================

    def insert_partial_overlap(self, overlap: Dict) -> int:
        """Insert a partial overlap entry."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO partial_overlaps (
                    doc_a_canonical_id, doc_b_canonical_id,
                    overlap_type, overlap_percentage, pages_a, pages_b
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                overlap["doc_a_canonical_id"],
                overlap["doc_b_canonical_id"],
                overlap.get("overlap_type"),
                overlap.get("overlap_percentage"),
                overlap.get("pages_a"),
                overlap.get("pages_b")
            ))

            return cursor.lastrowid

    # ==================== Processing Log ====================

    def log(self, operation: str, source: str, status: str,
            message: str, details: Optional[Dict] = None):
        """
        Add entry to processing log.

        Args:
            operation: Operation name (download|hash|deduplicate|canonicalize)
            source: Source name
            status: Status (success|error|warning)
            message: Log message
            details: Optional additional details (will be JSON serialized)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO processing_log (
                    operation, source, status, message, details
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                operation,
                source,
                status,
                message,
                json.dumps(details) if details else None
            ))

    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """Get recent processing log entries."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM processing_log
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

    # ==================== Statistics ====================

    def get_statistics(self) -> Dict:
        """
        Generate database statistics.

        Returns:
            Dictionary with statistics:
            {
                'total_documents': int,
                'total_sources': int,
                'duplicate_groups': int,
                'avg_sources_per_doc': float,
                'documents_by_type': dict,
                'documents_by_quality': dict
            }
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            stats = {}

            # Total documents
            cursor.execute("SELECT COUNT(*) FROM canonical_documents")
            stats["total_documents"] = cursor.fetchone()[0]

            # Total sources
            cursor.execute("SELECT COUNT(*) FROM document_sources")
            stats["total_sources"] = cursor.fetchone()[0]

            # Duplicate groups
            cursor.execute("SELECT COUNT(DISTINCT canonical_id) FROM duplicate_groups")
            stats["duplicate_groups"] = cursor.fetchone()[0]

            # Average sources per document
            if stats["total_documents"] > 0:
                stats["avg_sources_per_doc"] = stats["total_sources"] / stats["total_documents"]
            else:
                stats["avg_sources_per_doc"] = 0.0

            # Documents by type
            cursor.execute("""
                SELECT document_type, COUNT(*) as count
                FROM canonical_documents
                GROUP BY document_type
                ORDER BY count DESC
            """)
            stats["documents_by_type"] = {row[0]: row[1] for row in cursor.fetchall()}

            # Documents by quality
            cursor.execute("""
                SELECT
                    CASE
                        WHEN ocr_quality >= 0.9 THEN 'high'
                        WHEN ocr_quality >= 0.7 THEN 'medium'
                        ELSE 'low'
                    END as quality_level,
                    COUNT(*) as count
                FROM canonical_documents
                WHERE ocr_quality IS NOT NULL
                GROUP BY quality_level
            """)
            stats["documents_by_quality"] = {row[0]: row[1] for row in cursor.fetchall()}

            return stats


if __name__ == "__main__":
    # Example usage
    db = CanonicalDatabase(Path("data/metadata/deduplication_index.db"))

    # Insert test document
    doc = {
        "canonical_id": "epstein_doc_test123",
        "content_hash": "sha256:abc123",
        "file_hash": "sha256:def456",
        "document_type": "email",
        "title": "Test Email",
        "date": "2008-05-15",
        "from_person": "test@example.com",
        "to_persons": ["recipient@example.com"],
        "subject": "Test Subject",
        "ocr_quality": 0.95,
        "has_redactions": False,
        "completeness": "complete",
        "page_count": 1
    }

    try:
        db.insert_canonical_document(doc)
        print("Document inserted successfully")

        # Retrieve it
        retrieved = db.get_canonical_document("epstein_doc_test123")
        print(f"Retrieved: {retrieved}")

        # Get statistics
        stats = db.get_statistics()
        print(f"Statistics: {stats}")

    except sqlite3.IntegrityError:
        print("Document already exists")
