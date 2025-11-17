#!/usr/bin/env python3
"""
Classification Report Generator

Generates comprehensive reports on document classification results.

Reports:
1. Classification summary by type
2. Confidence distribution
3. Entity frequency analysis
4. Timeline visualization
5. Quality metrics
6. Documents needing review
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import argparse


class ReportGenerator:
    """Generate classification reports from database."""

    def __init__(self, db_path: str):
        """
        Initialize report generator.

        Args:
            db_path: Path to classification database
        """
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def generate_classification_summary(self) -> Dict:
        """
        Generate summary of classifications by type.

        Returns:
            Dictionary with classification statistics
        """
        cursor = self.conn.cursor()

        # Total documents
        cursor.execute('SELECT COUNT(*) as total FROM documents')
        total = cursor.fetchone()['total']

        # By type
        cursor.execute('''
            SELECT
                document_type,
                COUNT(*) as count,
                AVG(classification_confidence) as avg_confidence,
                MIN(classification_confidence) as min_confidence,
                MAX(classification_confidence) as max_confidence
            FROM documents
            GROUP BY document_type
            ORDER BY count DESC
        ''')

        by_type = []
        for row in cursor.fetchall():
            by_type.append({
                'document_type': row['document_type'],
                'count': row['count'],
                'percentage': round(row['count'] / total * 100, 2) if total > 0 else 0,
                'avg_confidence': round(row['avg_confidence'], 3),
                'min_confidence': round(row['min_confidence'], 3),
                'max_confidence': round(row['max_confidence'], 3)
            })

        # Confidence distribution
        cursor.execute('''
            SELECT
                CASE
                    WHEN classification_confidence >= 0.9 THEN 'high'
                    WHEN classification_confidence >= 0.7 THEN 'medium'
                    WHEN classification_confidence >= 0.5 THEN 'low'
                    ELSE 'very_low'
                END as confidence_level,
                COUNT(*) as count
            FROM documents
            GROUP BY confidence_level
        ''')

        confidence_dist = {}
        for row in cursor.fetchall():
            confidence_dist[row['confidence_level']] = row['count']

        return {
            'total_documents': total,
            'by_type': by_type,
            'confidence_distribution': confidence_dist,
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        }

    def generate_entity_report(self) -> Dict:
        """
        Generate entity frequency analysis.

        Returns:
            Dictionary with entity statistics
        """
        cursor = self.conn.cursor()

        # People
        cursor.execute('''
            SELECT
                entity_name,
                entity_type,
                SUM(mentions) as total_mentions,
                COUNT(DISTINCT canonical_id) as document_count
            FROM document_entities
            WHERE entity_type = 'person'
            GROUP BY entity_name
            ORDER BY document_count DESC
            LIMIT 100
        ''')

        people = []
        for row in cursor.fetchall():
            people.append({
                'name': row['entity_name'],
                'mentions': row['total_mentions'],
                'documents': row['document_count']
            })

        # Organizations
        cursor.execute('''
            SELECT
                entity_name,
                SUM(mentions) as total_mentions,
                COUNT(DISTINCT canonical_id) as document_count
            FROM document_entities
            WHERE entity_type = 'organization'
            GROUP BY entity_name
            ORDER BY document_count DESC
            LIMIT 50
        ''')

        organizations = []
        for row in cursor.fetchall():
            organizations.append({
                'name': row['entity_name'],
                'mentions': row['total_mentions'],
                'documents': row['document_count']
            })

        # Cases
        cursor.execute('''
            SELECT
                entity_name as case_number,
                COUNT(DISTINCT canonical_id) as document_count
            FROM document_entities
            WHERE entity_type = 'case'
            GROUP BY entity_name
            ORDER BY document_count DESC
        ''')

        cases = []
        for row in cursor.fetchall():
            cases.append({
                'case_number': row['case_number'],
                'documents': row['document_count']
            })

        return {
            'top_people': people[:20],
            'top_organizations': organizations[:20],
            'cases': cases,
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        }

    def generate_timeline_report(self) -> Dict:
        """
        Generate timeline of documents by type.

        Returns:
            Dictionary with timeline data
        """
        cursor = self.conn.cursor()

        cursor.execute('''
            SELECT
                date,
                document_type,
                COUNT(*) as count
            FROM documents
            WHERE date IS NOT NULL
            GROUP BY date, document_type
            ORDER BY date
        ''')

        timeline = []
        for row in cursor.fetchall():
            timeline.append({
                'date': row['date'],
                'document_type': row['document_type'],
                'count': row['count']
            })

        # Year summary
        cursor.execute('''
            SELECT
                substr(date, 1, 4) as year,
                COUNT(*) as count
            FROM documents
            WHERE date IS NOT NULL
            GROUP BY year
            ORDER BY year
        ''')

        by_year = []
        for row in cursor.fetchall():
            by_year.append({
                'year': row['year'],
                'count': row['count']
            })

        return {
            'timeline': timeline,
            'by_year': by_year,
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        }

    def generate_quality_report(self) -> Dict:
        """
        Generate quality metrics report.

        Returns:
            Dictionary with quality statistics
        """
        cursor = self.conn.cursor()

        # OCR quality distribution
        cursor.execute('''
            SELECT
                ocr_quality,
                COUNT(*) as count
            FROM documents
            GROUP BY ocr_quality
        ''')

        ocr_quality = {}
        for row in cursor.fetchall():
            ocr_quality[row['ocr_quality']] = row['count']

        # Completeness
        cursor.execute('''
            SELECT
                completeness,
                COUNT(*) as count
            FROM documents
            GROUP BY completeness
        ''')

        completeness = {}
        for row in cursor.fetchall():
            completeness[row['completeness']] = row['count']

        # Average OCR confidence by type
        cursor.execute('''
            SELECT
                document_type,
                AVG(ocr_confidence) as avg_ocr_confidence
            FROM documents
            WHERE ocr_confidence IS NOT NULL
            GROUP BY document_type
            ORDER BY avg_ocr_confidence DESC
        ''')

        by_type = []
        for row in cursor.fetchall():
            by_type.append({
                'document_type': row['document_type'],
                'avg_ocr_confidence': round(row['avg_ocr_confidence'], 3)
            })

        return {
            'ocr_quality_distribution': ocr_quality,
            'completeness_distribution': completeness,
            'ocr_confidence_by_type': by_type,
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        }

    def generate_review_list(self) -> List[Dict]:
        """
        Generate list of documents needing manual review.

        Returns:
            List of documents with low confidence or quality issues
        """
        cursor = self.conn.cursor()

        cursor.execute('''
            SELECT
                canonical_id,
                document_type,
                title,
                date,
                classification_confidence,
                ocr_quality,
                completeness
            FROM documents
            WHERE
                classification_confidence < 0.7
                OR ocr_quality = 'low'
                OR completeness IN ('partial', 'fragment')
            ORDER BY classification_confidence ASC
            LIMIT 1000
        ''')

        review_list = []
        for row in cursor.fetchall():
            review_list.append({
                'canonical_id': row['canonical_id'],
                'document_type': row['document_type'],
                'title': row['title'],
                'date': row['date'],
                'classification_confidence': round(row['classification_confidence'], 3),
                'ocr_quality': row['ocr_quality'],
                'completeness': row['completeness'],
                'issues': self._identify_issues(row)
            })

        return review_list

    def _identify_issues(self, row: sqlite3.Row) -> List[str]:
        """Identify specific issues with a document."""
        issues = []

        if row['classification_confidence'] < 0.5:
            issues.append('very_low_confidence')
        elif row['classification_confidence'] < 0.7:
            issues.append('low_confidence')

        if row['ocr_quality'] == 'low':
            issues.append('poor_ocr_quality')

        if row['completeness'] in ('partial', 'fragment'):
            issues.append('incomplete_document')

        return issues

    def generate_all_reports(self, output_dir: Path):
        """
        Generate all reports and save to output directory.

        Args:
            output_dir: Directory to save reports
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        print("Generating classification summary...")
        summary = self.generate_classification_summary()
        with open(output_dir / 'classification_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

        # Create human-readable text version
        with open(output_dir / 'classification_summary.txt', 'w') as f:
            f.write("DOCUMENT CLASSIFICATION SUMMARY\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Total Documents: {summary['total_documents']:,}\n\n")

            f.write("Confidence Distribution:\n")
            for level, count in summary['confidence_distribution'].items():
                pct = count / summary['total_documents'] * 100 if summary['total_documents'] > 0 else 0
                f.write(f"  {level:12s}: {count:6,d} ({pct:5.1f}%)\n")

            f.write("\n\nDocuments by Type:\n")
            f.write("-" * 70 + "\n")
            f.write(f"{'Type':<40} {'Count':>10} {'%':>6} {'Avg Conf':>10}\n")
            f.write("-" * 70 + "\n")

            for item in summary['by_type']:
                f.write(f"{item['document_type']:<40} {item['count']:>10,d} "
                       f"{item['percentage']:>5.1f}% {item['avg_confidence']:>10.3f}\n")

        print("Generating entity report...")
        entities = self.generate_entity_report()
        with open(output_dir / 'entity_report.json', 'w') as f:
            json.dump(entities, f, indent=2)

        with open(output_dir / 'entity_report.txt', 'w') as f:
            f.write("ENTITY FREQUENCY ANALYSIS\n")
            f.write("=" * 70 + "\n\n")

            f.write("Top People:\n")
            f.write("-" * 70 + "\n")
            f.write(f"{'Name':<40} {'Documents':>12} {'Mentions':>12}\n")
            f.write("-" * 70 + "\n")
            for person in entities['top_people']:
                f.write(f"{person['name']:<40} {person['documents']:>12,d} "
                       f"{person['mentions']:>12,d}\n")

            f.write("\n\nTop Organizations:\n")
            f.write("-" * 70 + "\n")
            f.write(f"{'Name':<40} {'Documents':>12} {'Mentions':>12}\n")
            f.write("-" * 70 + "\n")
            for org in entities['top_organizations']:
                f.write(f"{org['name']:<40} {org['documents']:>12,d} "
                       f"{org['mentions']:>12,d}\n")

        print("Generating timeline report...")
        timeline = self.generate_timeline_report()
        with open(output_dir / 'timeline_report.json', 'w') as f:
            json.dump(timeline, f, indent=2)

        with open(output_dir / 'timeline_summary.txt', 'w') as f:
            f.write("DOCUMENT TIMELINE SUMMARY\n")
            f.write("=" * 70 + "\n\n")

            f.write("Documents by Year:\n")
            f.write("-" * 70 + "\n")
            for item in timeline['by_year']:
                f.write(f"{item['year']}: {item['count']:,d} documents\n")

        print("Generating quality report...")
        quality = self.generate_quality_report()
        with open(output_dir / 'quality_report.json', 'w') as f:
            json.dump(quality, f, indent=2)

        with open(output_dir / 'quality_report.txt', 'w') as f:
            f.write("DOCUMENT QUALITY METRICS\n")
            f.write("=" * 70 + "\n\n")

            f.write("OCR Quality Distribution:\n")
            for level, count in quality['ocr_quality_distribution'].items():
                f.write(f"  {level:12s}: {count:6,d}\n")

            f.write("\nCompleteness Distribution:\n")
            for level, count in quality['completeness_distribution'].items():
                f.write(f"  {level:12s}: {count:6,d}\n")

        print("Generating review list...")
        review = self.generate_review_list()
        with open(output_dir / 'needs_review.json', 'w') as f:
            json.dump(review, f, indent=2)

        with open(output_dir / 'needs_review.txt', 'w') as f:
            f.write("DOCUMENTS NEEDING MANUAL REVIEW\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Total: {len(review):,d} documents\n\n")

            for doc in review[:100]:  # Top 100
                f.write(f"\nID: {doc['canonical_id']}\n")
                f.write(f"Type: {doc['document_type']}\n")
                f.write(f"Title: {doc['title'][:60]}\n")
                f.write(f"Confidence: {doc['classification_confidence']:.3f}\n")
                f.write(f"Issues: {', '.join(doc['issues'])}\n")
                f.write("-" * 70 + "\n")

        print(f"\nAll reports saved to {output_dir}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


def main():
    parser = argparse.ArgumentParser(description='Generate classification reports')
    parser.add_argument('--database', required=True, help='SQLite database path')
    parser.add_argument('--output', required=True, help='Output directory for reports')

    args = parser.parse_args()

    output_dir = Path(args.output)
    generator = ReportGenerator(args.database)

    try:
        generator.generate_all_reports(output_dir)
    finally:
        generator.close()


if __name__ == '__main__':
    main()
