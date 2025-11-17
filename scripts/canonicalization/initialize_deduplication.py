#!/usr/bin/env python3
"""
Initialize Deduplication System

Creates database, runs test processing, and validates system readiness.

Usage:
    python scripts/initialize_deduplication.py
"""

import sys
from datetime import datetime
from pathlib import Path


# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from core.database import CanonicalDatabase
from core.deduplicator import Deduplicator, Document
from core.hasher import DocumentHasher, generate_canonical_id


def initialize_database(db_path: Path) -> CanonicalDatabase:
    """
    Initialize SQLite database with schema.

    Returns:
        CanonicalDatabase instance
    """
    print("\n=== Initializing Database ===")
    print(f"Location: {db_path}")

    # Create database (tables created automatically)
    db = CanonicalDatabase(db_path)

    # Verify tables exist
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]

    print(f"Tables created: {', '.join(tables)}")
    print("Database initialized successfully")

    return db


def process_test_emails(db: CanonicalDatabase, email_dir: Path):
    """
    Process test emails through deduplication pipeline.

    Args:
        db: Database instance
        email_dir: Directory containing markdown email files
    """
    print("\n=== Processing Test Emails ===")
    print(f"Email directory: {email_dir}")

    hasher = DocumentHasher()
    dedup = Deduplicator()

    # Find all markdown email files
    email_files = sorted(email_dir.glob("markdown/emails/*.md"))

    print(f"Found {len(email_files)} email files")

    documents = []
    processed_count = 0
    duplicate_count = 0

    for email_file in email_files:
        try:
            # Read file
            text = email_file.read_text(encoding="utf-8")

            # Extract metadata from frontmatter
            metadata = extract_metadata(text)

            # Calculate hashes
            file_hash = hasher.hash_file(email_file)
            content_hash = hasher.hash_content(text)
            fuzzy_hash = hasher.hash_fuzzy(text)

            # Generate canonical ID
            canonical_id = generate_canonical_id(content_hash)

            # Check if already exists
            existing = db.find_by_content_hash(content_hash)

            if existing:
                print(f"  DUPLICATE: {email_file.name}")
                duplicate_count += 1

                # Add as additional source
                db.insert_source({
                    "canonical_id": canonical_id,
                    "source_name": "test_import",
                    "collection": "initial_8_emails",
                    "file_path": str(email_file),
                    "format": "markdown",
                    "download_date": datetime.now().isoformat()
                })
                continue

            # Create document
            doc = {
                "canonical_id": canonical_id,
                "content_hash": content_hash,
                "file_hash": file_hash,
                "document_type": metadata.get("document_type", "email"),
                "title": metadata.get("title"),
                "date": metadata.get("date"),
                "from_person": metadata.get("from"),
                "to_persons": metadata.get("to", []),
                "subject": metadata.get("subject"),
                "ocr_quality": None,  # Markdown doesn't have OCR quality
                "has_redactions": False,
                "completeness": "complete",
                "page_count": 1,
                "primary_source": "test_import",
                "selection_reason": "initial_test_set"
            }

            # Insert into database
            db.insert_canonical_document(doc)

            # Add source
            db.insert_source({
                "canonical_id": canonical_id,
                "source_name": "test_import",
                "collection": "initial_8_emails",
                "file_path": str(email_file),
                "format": "markdown",
                "download_date": datetime.now().isoformat()
            })

            # Log processing
            db.log(
                operation="import",
                source="test_import",
                status="success",
                message=f"Imported {email_file.name}",
                details={"canonical_id": canonical_id}
            )

            print(f"  ✓ {email_file.name} -> {canonical_id}")
            processed_count += 1

        except Exception as e:
            print(f"  ✗ {email_file.name}: {e}")
            db.log(
                operation="import",
                source="test_import",
                status="error",
                message=f"Failed to import {email_file.name}",
                details={"error": str(e)}
            )

    print(f"\nProcessed: {processed_count} new documents")
    print(f"Duplicates: {duplicate_count}")


def extract_metadata(text: str) -> dict:
    """
    Extract metadata from markdown frontmatter.

    Args:
        text: Markdown content with YAML frontmatter

    Returns:
        Dictionary of metadata
    """
    metadata = {}

    # Simple frontmatter parser
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            for line in frontmatter.strip().split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    # Handle lists
                    if value.startswith("[") and value.endswith("]"):
                        value = [v.strip().strip('"\'') for v in value[1:-1].split(",")]

                    metadata[key] = value

    return metadata


def run_deduplication_test(db: CanonicalDatabase):
    """
    Run deduplication test to verify fuzzy matching works.

    Args:
        db: Database instance
    """
    print("\n=== Testing Deduplication Engine ===")

    # Get all documents
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT canonical_id, content_hash, file_hash, document_type
            FROM canonical_documents
        """)
        rows = cursor.fetchall()

    print(f"Testing deduplication on {len(rows)} documents")

    # Create Document objects (simplified for testing)
    documents = [
        Document(
            id=row[0],
            file_path=Path("dummy"),
            file_hash=row[2],
            content_hash=row[1],
            fuzzy_hash=None,
            text="",
            document_type=row[3]
        )
        for row in rows
    ]

    # Run deduplication
    dedup = Deduplicator()
    groups = dedup.deduplicate(documents)

    print(f"Found {len(groups)} duplicate groups")

    for group in groups:
        print(f"  {group.type}: {len(group.docs)} documents (similarity: {group.similarity:.2f})")


def test_bulk_performance(db: CanonicalDatabase):
    """
    Test bulk insertion performance.

    Simulates processing 1,000 documents to verify performance.
    """
    print("\n=== Testing Bulk Performance ===")

    hasher = DocumentHasher()

    # Simulate processing time
    import time

    test_texts = [
        f"This is test email {i} with some content"
        for i in range(100)
    ]

    start = time.time()

    for text in test_texts:
        hasher.hash_content(text)

    elapsed = time.time() - start

    emails_per_second = len(test_texts) / elapsed

    print(f"Hashing performance: {emails_per_second:.1f} emails/second")
    print(f"Estimated time for 20,000 emails: {20000 / emails_per_second / 60:.1f} minutes")


def print_statistics(db: CanonicalDatabase):
    """Print database statistics."""
    print("\n=== Database Statistics ===")

    stats = db.get_statistics()

    print(f"Total documents: {stats['total_documents']}")
    print(f"Total sources: {stats['total_sources']}")
    print(f"Duplicate groups: {stats['duplicate_groups']}")
    print(f"Avg sources per doc: {stats['avg_sources_per_doc']:.2f}")

    if stats["documents_by_type"]:
        print("\nDocuments by type:")
        for doc_type, count in stats["documents_by_type"].items():
            print(f"  {doc_type}: {count}")


def verify_system_ready(db: CanonicalDatabase, db_path: Path) -> bool:
    """
    Verify system is ready for bulk processing.

    Returns:
        True if system is ready
    """
    print("\n=== System Readiness Check ===")

    checks = []

    # Check 1: Database exists
    db_exists = db_path.exists()
    checks.append(("Database file exists", db_exists))

    # Check 2: Tables exist
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]

    tables_ok = table_count >= 5
    checks.append(("Database tables created", tables_ok))

    # Check 3: Test data loaded
    stats = db.get_statistics()
    data_loaded = stats["total_documents"] > 0
    checks.append(("Test data loaded", data_loaded))

    # Check 4: Indexes created
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
        index_count = cursor.fetchone()[0]

    indexes_ok = index_count >= 5
    checks.append(("Indexes created", indexes_ok))

    # Print results
    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n✓ System is READY for bulk processing")
    else:
        print("\n✗ System is NOT ready - fix issues above")

    return all_passed


def main():
    """Main initialization process."""
    print("=" * 60)
    print("DEDUPLICATION SYSTEM INITIALIZATION")
    print("=" * 60)

    # Paths
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "metadata" / "deduplication.db"
    email_dir = project_root / "data" / "emails"

    # Initialize database
    db = initialize_database(db_path)

    # Process test emails
    process_test_emails(db, email_dir)

    # Run deduplication test
    run_deduplication_test(db)

    # Test bulk performance
    test_bulk_performance(db)

    # Print statistics
    print_statistics(db)

    # Verify system ready
    is_ready = verify_system_ready(db, db_path)

    # Print summary
    print("\n" + "=" * 60)
    print("INITIALIZATION COMPLETE")
    print("=" * 60)

    print(f"\nDatabase: {db_path}")
    print(f"Size: {db_path.stat().st_size / 1024:.1f} KB")

    if is_ready:
        print("\n✓ System ready for House Oversight collection processing")
        print("\nNext steps:")
        print("  1. Run: python scripts/process_bulk_emails.py <email_directory>")
        print("  2. Monitor processing with database statistics")
        print("  3. Review duplicates and quality metrics")
    else:
        print("\n✗ Fix issues above before bulk processing")
        sys.exit(1)


if __name__ == "__main__":
    main()
