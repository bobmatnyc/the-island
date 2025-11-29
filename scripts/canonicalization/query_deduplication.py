#!/usr/bin/env python3
"""
Query Deduplication Database

Interactive queries and monitoring for deduplication system.

Usage:
    python scripts/query_deduplication.py [command]

Commands:
    stats               Show database statistics
    duplicates          List all duplicate groups
    sources <doc_id>    Show all sources for a document
    recent              Show recently processed documents
    quality             Show documents by quality metrics
    search <term>       Search documents by title/subject
    export <format>     Export database to CSV/JSON
"""

import argparse
import json
import sys
from pathlib import Path


# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from core.database import CanonicalDatabase


def show_statistics(db: CanonicalDatabase):
    """Display comprehensive database statistics."""
    stats = db.get_statistics()

    print("=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)

    print("\nOverview:")
    print(f"  Total documents: {stats['total_documents']}")
    print(f"  Total sources: {stats['total_sources']}")
    print(f"  Duplicate groups: {stats['duplicate_groups']}")
    print(f"  Avg sources per doc: {stats['avg_sources_per_doc']:.2f}")

    if stats["documents_by_type"]:
        print("\nDocuments by type:")
        for doc_type, count in stats["documents_by_type"].items():
            print(f"  {doc_type}: {count}")

    if stats["documents_by_quality"]:
        print("\nDocuments by quality:")
        for quality, count in stats["documents_by_quality"].items():
            print(f"  {quality}: {count}")

    # Recent activity
    recent_logs = db.get_recent_logs(limit=10)
    if recent_logs:
        print("\nRecent activity (last 10):")
        for log in recent_logs:
            timestamp = log["timestamp"]
            operation = log["operation"]
            status = log["status"]
            message = log["message"]
            print(f"  [{timestamp}] {operation} - {status}: {message}")


def list_duplicates(db: CanonicalDatabase):
    """List all duplicate groups."""
    with db.get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                dg.canonical_id,
                cd.title,
                cd.date,
                dg.duplicate_type,
                dg.similarity_score,
                dg.detection_method
            FROM duplicate_groups dg
            JOIN canonical_documents cd ON dg.canonical_id = cd.canonical_id
            ORDER BY dg.similarity_score DESC
        """
        )

        rows = cursor.fetchall()

    print("=" * 60)
    print("DUPLICATE GROUPS")
    print("=" * 60)

    if not rows:
        print("\nNo duplicates found")
        return

    print(f"\nFound {len(rows)} duplicate entries:\n")

    for row in rows:
        canonical_id = row["canonical_id"]
        title = row["title"] or "Untitled"
        date = row["date"] or "No date"
        dup_type = row["duplicate_type"]
        similarity = row["similarity_score"] or 0
        method = row["detection_method"]

        print(f"ID: {canonical_id}")
        print(f"  Title: {title}")
        print(f"  Date: {date}")
        print(f"  Type: {dup_type} | Similarity: {similarity:.2f} | Method: {method}")
        print()


def show_sources(db: CanonicalDatabase, canonical_id: str):
    """Show all sources for a document."""
    doc = db.get_canonical_document(canonical_id)

    if not doc:
        print(f"Document not found: {canonical_id}")
        return

    sources = db.get_sources(canonical_id)

    print("=" * 60)
    print("DOCUMENT SOURCES")
    print("=" * 60)

    print(f"\nDocument: {doc['title'] or 'Untitled'}")
    print(f"ID: {canonical_id}")
    print(f"Type: {doc['document_type']}")
    print(f"Date: {doc['date'] or 'No date'}")

    print(f"\nSources ({len(sources)}):")

    for source in sources:
        print(f"\n  Source: {source['source_name']}")
        print(f"  Collection: {source['collection']}")
        print(f"  File: {source['file_path']}")
        print(f"  Quality: {source.get('quality_score', 'N/A')}")
        print(f"  Downloaded: {source.get('download_date', 'Unknown')}")


def show_recent(db: CanonicalDatabase, limit: int = 20):
    """Show recently processed documents."""
    with db.get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                canonical_id,
                document_type,
                title,
                date,
                from_person,
                created_at
            FROM canonical_documents
            ORDER BY created_at DESC
            LIMIT ?
        """,
            (limit,),
        )

        rows = cursor.fetchall()

    print("=" * 60)
    print(f"RECENT DOCUMENTS (last {limit})")
    print("=" * 60)

    if not rows:
        print("\nNo documents found")
        return

    for row in rows:
        canonical_id = row["canonical_id"]
        doc_type = row["document_type"]
        title = row["title"] or "Untitled"
        date = row["date"] or "No date"
        from_person = row["from_person"] or "Unknown"
        created = row["created_at"]

        print(f"\n{canonical_id}")
        print(f"  Type: {doc_type}")
        print(f"  Title: {title}")
        print(f"  Date: {date}")
        print(f"  From: {from_person}")
        print(f"  Added: {created}")


def show_quality(db: CanonicalDatabase):
    """Show documents grouped by quality metrics."""
    with db.get_connection() as conn:
        cursor = conn.cursor()

        # High quality documents
        cursor.execute(
            """
            SELECT canonical_id, title, ocr_quality
            FROM canonical_documents
            WHERE ocr_quality >= 0.9
            ORDER BY ocr_quality DESC
        """
        )
        high_quality = cursor.fetchall()

        # Medium quality
        cursor.execute(
            """
            SELECT canonical_id, title, ocr_quality
            FROM canonical_documents
            WHERE ocr_quality >= 0.7 AND ocr_quality < 0.9
            ORDER BY ocr_quality DESC
        """
        )
        medium_quality = cursor.fetchall()

        # Low quality
        cursor.execute(
            """
            SELECT canonical_id, title, ocr_quality
            FROM canonical_documents
            WHERE ocr_quality < 0.7
            ORDER BY ocr_quality DESC
        """
        )
        low_quality = cursor.fetchall()

    print("=" * 60)
    print("DOCUMENTS BY QUALITY")
    print("=" * 60)

    print(f"\nHigh Quality (≥0.9): {len(high_quality)}")
    for doc in high_quality[:10]:
        print(f"  {doc['canonical_id']}: {doc['title']} ({doc['ocr_quality']:.2f})")

    print(f"\nMedium Quality (0.7-0.9): {len(medium_quality)}")
    for doc in medium_quality[:10]:
        print(f"  {doc['canonical_id']}: {doc['title']} ({doc['ocr_quality']:.2f})")

    print(f"\nLow Quality (<0.7): {len(low_quality)}")
    for doc in low_quality[:10]:
        print(f"  {doc['canonical_id']}: {doc['title']} ({doc['ocr_quality']:.2f})")


def search_documents(db: CanonicalDatabase, term: str):
    """Search documents by title or subject."""
    with db.get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                canonical_id,
                document_type,
                title,
                subject,
                date,
                from_person
            FROM canonical_documents
            WHERE title LIKE ? OR subject LIKE ?
            ORDER BY date DESC
        """,
            (f"%{term}%", f"%{term}%"),
        )

        rows = cursor.fetchall()

    print("=" * 60)
    print(f"SEARCH RESULTS: '{term}'")
    print("=" * 60)

    if not rows:
        print("\nNo documents found")
        return

    print(f"\nFound {len(rows)} documents:\n")

    for row in rows:
        canonical_id = row["canonical_id"]
        doc_type = row["document_type"]
        title = row["title"] or row["subject"] or "Untitled"
        date = row["date"] or "No date"
        from_person = row["from_person"] or "Unknown"

        print(f"{canonical_id}")
        print(f"  Type: {doc_type}")
        print(f"  Title: {title}")
        print(f"  Date: {date}")
        print(f"  From: {from_person}")
        print()


def export_database(db: CanonicalDatabase, format: str, output_file: Path):
    """Export database to CSV or JSON."""
    with db.get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM canonical_documents")
        rows = cursor.fetchall()

    if format == "json":
        # Convert to JSON
        documents = [dict(row) for row in rows]
        output_file.write_text(json.dumps(documents, indent=2))
        print(f"Exported {len(documents)} documents to {output_file}")

    elif format == "csv":
        # Convert to CSV
        import csv

        with output_file.open("w", newline="") as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                for row in rows:
                    writer.writerow(dict(row))
        print(f"Exported {len(rows)} documents to {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Query deduplication database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "command",
        choices=["stats", "duplicates", "sources", "recent", "quality", "search", "export"],
        help="Command to run",
    )

    parser.add_argument("args", nargs="*", help="Command arguments")

    args = parser.parse_args()

    # Initialize database
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "metadata" / "deduplication.db"

    if not db_path.exists():
        print(f"Error: Database not found: {db_path}")
        print("Run initialize_deduplication.py first")
        sys.exit(1)

    db = CanonicalDatabase(db_path)

    # Execute command
    if args.command == "stats":
        show_statistics(db)

    elif args.command == "duplicates":
        list_duplicates(db)

    elif args.command == "sources":
        if not args.args:
            print("Error: Provide canonical_id")
            sys.exit(1)
        show_sources(db, args.args[0])

    elif args.command == "recent":
        limit = int(args.args[0]) if args.args else 20
        show_recent(db, limit)

    elif args.command == "quality":
        show_quality(db)

    elif args.command == "search":
        if not args.args:
            print("Error: Provide search term")
            sys.exit(1)
        search_documents(db, " ".join(args.args))

    elif args.command == "export":
        if len(args.args) < 2:
            print("Error: Provide format (json|csv) and output file")
            sys.exit(1)
        format = args.args[0]
        output_file = Path(args.args[1])
        export_database(db, format, output_file)


if __name__ == "__main__":
    main()
