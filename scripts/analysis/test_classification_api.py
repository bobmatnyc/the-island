#!/usr/bin/env python3
"""
Test script for Entity Classification System

Demonstrates how to query and use entity classifications from the database.

Usage:
    python3 test_classification_api.py [entity_id]

Examples:
    # Query specific entity
    python3 test_classification_api.py ghislaine_maxwell

    # Show top 10 by significance
    python3 test_classification_api.py

    # Show all classifications
    python3 test_classification_api.py --all
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional


class ClassificationAPI:
    """Simple API for querying entity classifications"""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def get_classification(self, entity_id: str) -> Optional[Dict]:
        """Get classification for specific entity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                e.id,
                e.display_name,
                c.primary_role,
                c.connection_strength,
                c.professional_category,
                c.temporal_activity,
                c.significance_score,
                c.justification,
                c.classified_by,
                c.classified_at,
                c.metadata
            FROM entity_classifications c
            JOIN entities e ON c.entity_id = e.id
            WHERE c.entity_id = ?
        """, (entity_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "entity_id": row[0],
            "entity_name": row[1],
            "primary_role": row[2],
            "connection_strength": row[3],
            "professional_category": row[4],
            "temporal_activity": json.loads(row[5]) if row[5] else [],
            "significance_score": row[6],
            "justification": row[7],
            "classified_by": row[8],
            "classified_at": row[9],
            "metadata": json.loads(row[10]) if row[10] else {}
        }

    def get_top_by_significance(self, limit: int = 10) -> List[Dict]:
        """Get top entities by significance score"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                e.id,
                e.display_name,
                c.primary_role,
                c.connection_strength,
                c.significance_score
            FROM entity_classifications c
            JOIN entities e ON c.entity_id = e.id
            ORDER BY c.significance_score DESC
            LIMIT ?
        """, (limit,))

        results = []
        for row in cursor.fetchall():
            results.append({
                "entity_id": row[0],
                "entity_name": row[1],
                "primary_role": row[2],
                "connection_strength": row[3],
                "significance_score": row[4]
            })

        conn.close()
        return results

    def get_by_role(self, role: str, limit: int = 20) -> List[Dict]:
        """Get entities by primary role"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                e.id,
                e.display_name,
                c.connection_strength,
                c.professional_category,
                c.significance_score
            FROM entity_classifications c
            JOIN entities e ON c.entity_id = e.id
            WHERE c.primary_role = ?
            ORDER BY c.significance_score DESC
            LIMIT ?
        """, (role, limit))

        results = []
        for row in cursor.fetchall():
            results.append({
                "entity_id": row[0],
                "entity_name": row[1],
                "connection_strength": row[2],
                "professional_category": row[3],
                "significance_score": row[4]
            })

        conn.close()
        return results

    def get_by_connection_strength(self, strength: str, limit: int = 20) -> List[Dict]:
        """Get entities by connection strength"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                e.id,
                e.display_name,
                c.primary_role,
                c.professional_category,
                c.significance_score
            FROM entity_classifications c
            JOIN entities e ON c.entity_id = e.id
            WHERE c.connection_strength = ?
            ORDER BY c.significance_score DESC
            LIMIT ?
        """, (strength, limit))

        results = []
        for row in cursor.fetchall():
            results.append({
                "entity_id": row[0],
                "entity_name": row[1],
                "primary_role": row[2],
                "professional_category": row[3],
                "significance_score": row[4]
            })

        conn.close()
        return results

    def get_statistics(self) -> Dict:
        """Get classification statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total count
        cursor.execute("SELECT COUNT(*) FROM entity_classifications")
        total_count = cursor.fetchone()[0]

        # Average significance
        cursor.execute("SELECT AVG(significance_score) FROM entity_classifications")
        avg_significance = cursor.fetchone()[0] or 0

        # Connection strength distribution
        cursor.execute("""
            SELECT connection_strength, COUNT(*) as count
            FROM entity_classifications
            GROUP BY connection_strength
            ORDER BY count DESC
        """)
        strength_dist = {row[0]: row[1] for row in cursor.fetchall()}

        # Role distribution
        cursor.execute("""
            SELECT primary_role, COUNT(*) as count
            FROM entity_classifications
            GROUP BY primary_role
            ORDER BY count DESC
            LIMIT 10
        """)
        role_dist = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return {
            "total_classified": total_count,
            "average_significance": round(avg_significance, 2),
            "connection_strength_distribution": strength_dist,
            "top_roles": role_dist
        }


def print_classification(classification: Dict):
    """Pretty print a classification"""
    print(f"\n{'='*70}")
    print(f"Entity: {classification['entity_name']}")
    print(f"{'='*70}")
    print(f"Primary Role: {classification['primary_role']}")
    print(f"Connection Strength: {classification['connection_strength']}")
    print(f"Professional Category: {classification['professional_category']}")
    print(f"Temporal Activity: {', '.join(classification['temporal_activity'])}")
    print(f"Significance Score: {classification['significance_score']}/10")
    print(f"\nJustification:")
    print(f"  {classification['justification']}")

    # Metadata
    meta = classification['metadata']
    if meta:
        print(f"\nMetrics:")
        print(f"  Flights: {meta.get('flight_count', 0)}")
        print(f"  Documents: {meta.get('document_count', 0)}")
        print(f"  Connections: {meta.get('connection_count', 0)}")

    print(f"\nClassified: {classification['classified_at']}")
    print(f"Classifier: {classification['classified_by']}")
    print(f"{'='*70}\n")


def print_summary_list(entities: List[Dict], title: str):
    """Pretty print a list of entities"""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}\n")

    for i, entity in enumerate(entities, 1):
        print(f"{i:2d}. {entity['entity_name']}")
        print(f"    Role: {entity.get('primary_role', 'N/A')}")
        print(f"    Strength: {entity.get('connection_strength', 'N/A')}")
        print(f"    Significance: {entity['significance_score']}/10")
        print()


def print_statistics(stats: Dict):
    """Pretty print statistics"""
    print(f"\n{'='*70}")
    print(f"CLASSIFICATION STATISTICS")
    print(f"{'='*70}\n")

    print(f"Total Classified: {stats['total_classified']}")
    print(f"Average Significance: {stats['average_significance']}/10")

    print(f"\nConnection Strength Distribution:")
    for strength, count in stats['connection_strength_distribution'].items():
        pct = (count / stats['total_classified']) * 100
        print(f"  {strength}: {count} ({pct:.1f}%)")

    print(f"\nTop Roles:")
    for role, count in list(stats['top_roles'].items())[:5]:
        pct = (count / stats['total_classified']) * 100
        print(f"  {role}: {count} ({pct:.1f}%)")

    print(f"\n{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Test Entity Classification API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show top 10 by significance
  python3 test_classification_api.py

  # Query specific entity
  python3 test_classification_api.py ghislaine_maxwell

  # Show statistics
  python3 test_classification_api.py --stats

  # Filter by role
  python3 test_classification_api.py --role "Close Associate"

  # Filter by connection strength
  python3 test_classification_api.py --strength "Core Circle"
        """
    )

    parser.add_argument(
        "entity_id",
        nargs="?",
        help="Entity ID to query (optional)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show classification statistics"
    )
    parser.add_argument(
        "--role",
        help="Filter by primary role"
    )
    parser.add_argument(
        "--strength",
        help="Filter by connection strength"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of results to show (default: 10)"
    )

    args = parser.parse_args()

    # Database path
    project_root = Path(__file__).parent.parent.parent
    db_path = project_root / "data/metadata/entities.db"

    if not db_path.exists():
        print(f"ERROR: Database not found: {db_path}")
        return 1

    # Initialize API
    api = ClassificationAPI(db_path)

    # Handle different modes
    if args.stats:
        stats = api.get_statistics()
        print_statistics(stats)
        return 0

    if args.entity_id:
        classification = api.get_classification(args.entity_id)
        if not classification:
            print(f"ERROR: No classification found for entity: {args.entity_id}")
            return 1
        print_classification(classification)
        return 0

    if args.role:
        entities = api.get_by_role(args.role, args.limit)
        if not entities:
            print(f"No entities found with role: {args.role}")
            return 0
        print_summary_list(entities, f"Entities with Role: {args.role}")
        return 0

    if args.strength:
        entities = api.get_by_connection_strength(args.strength, args.limit)
        if not entities:
            print(f"No entities found with connection strength: {args.strength}")
            return 0
        print_summary_list(entities, f"Entities with Strength: {args.strength}")
        return 0

    # Default: Show top by significance
    entities = api.get_top_by_significance(args.limit)
    if not entities:
        print("No classifications found in database.")
        print("\nRun classification script first:")
        print("  python3 classify_entity_relationships.py --tier 1 --import-db")
        return 0

    print_summary_list(entities, f"Top {args.limit} Entities by Significance")
    return 0


if __name__ == "__main__":
    exit(main())
