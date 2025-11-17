#!/usr/bin/env python3
"""
Generate comprehensive summary report of all document classifications
and the unified document index.
"""

import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict


# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
UNIFIED_INDEX = METADATA_DIR / "all_documents_index.json"
EMAIL_CLASSIFICATIONS = METADATA_DIR / "email_classifications.json"
REPORT_FILE = METADATA_DIR / "classification_summary_report.txt"

def load_json(filepath: Path) -> Dict:
    """Load JSON file."""
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)

def generate_report() -> str:
    """Generate comprehensive summary report."""
    # Load data
    unified_index = load_json(UNIFIED_INDEX)
    email_classifications = load_json(EMAIL_CLASSIFICATIONS)

    # Build report
    lines = []
    lines.append("="*80)
    lines.append("EPSTEIN DOCUMENT ARCHIVE - CLASSIFICATION SUMMARY REPORT")
    lines.append("="*80)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # Overall Statistics
    lines.append("OVERALL STATISTICS")
    lines.append("-"*80)
    lines.append(f"Total Documents Indexed: {unified_index['total_documents']:,}")
    lines.append(f"  - PDF Documents: {unified_index['statistics']['by_type'].get('pdf', 0):,}")
    lines.append(f"  - Email Documents: {unified_index['statistics']['by_type'].get('email', 0):,}")
    lines.append("")

    # Document Sources
    lines.append("DOCUMENT SOURCES")
    lines.append("-"*80)
    for source, count in sorted(
        unified_index["statistics"]["by_source"].items(),
        key=lambda x: x[1],
        reverse=True
    ):
        pct = (count / unified_index["total_documents"] * 100) if unified_index["total_documents"] > 0 else 0
        lines.append(f"  {source:40s}: {count:7,d} ({pct:5.1f}%)")
    lines.append("")

    # Email Classification Details
    lines.append("EMAIL CLASSIFICATION DETAILS")
    lines.append("-"*80)
    email_stats = email_classifications.get("statistics", {})
    lines.append(f"Total Emails Classified: {email_stats.get('total', 0)}")
    lines.append("")

    lines.append("Email Classification Confidence Distribution:")
    total_emails = email_stats.get("total", 1)
    lines.append(f"  High Confidence (≥0.8): {email_stats.get('high_confidence', 0):3d} ({email_stats.get('high_confidence', 0)/total_emails*100:5.1f}%)")
    lines.append(f"  Medium Confidence (≥0.6): {email_stats.get('medium_confidence', 0):3d} ({email_stats.get('medium_confidence', 0)/total_emails*100:5.1f}%)")
    lines.append(f"  Low Confidence (<0.6): {email_stats.get('low_confidence', 0):3d} ({email_stats.get('low_confidence', 0)/total_emails*100:5.1f}%)")
    lines.append("")

    lines.append("Email Document Types:")
    for doc_type, count in sorted(
        email_stats.get("by_type", {}).items(),
        key=lambda x: x[1],
        reverse=True
    ):
        pct = (count / total_emails * 100) if total_emails > 0 else 0
        lines.append(f"  {doc_type:20s}: {count:3d} ({pct:5.1f}%)")
    lines.append("")

    # Overall Classification Breakdown
    lines.append("OVERALL CLASSIFICATION BREAKDOWN")
    lines.append("-"*80)
    classified_count = sum(
        count for class_type, count in unified_index["statistics"]["by_classification"].items()
        if class_type
    )
    lines.append(f"Total Classified Documents: {classified_count:,} of {unified_index['total_documents']:,}")
    lines.append(f"Classification Coverage: {(classified_count/unified_index['total_documents']*100):.1f}%")
    lines.append("")

    lines.append("Classification Types:")
    for class_type, count in sorted(
        unified_index["statistics"]["by_classification"].items(),
        key=lambda x: x[1],
        reverse=True
    ):
        pct = (count / classified_count * 100) if classified_count > 0 else 0
        lines.append(f"  {class_type:20s}: {count:7,d} ({pct:5.1f}%)")
    lines.append("")

    # Email Date Distribution
    if unified_index["statistics"].get("by_date"):
        lines.append("EMAIL DATE DISTRIBUTION (Top 20)")
        lines.append("-"*80)
        for date, count in sorted(
            unified_index["statistics"]["by_date"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]:
            lines.append(f"  {date}: {count:3d} emails")
        lines.append("")

    # Email Content Analysis
    lines.append("EMAIL CONTENT INSIGHTS")
    lines.append("-"*80)

    # Analyze secondary classifications
    secondary_types = Counter()
    court_notifications = 0
    bop_emails = 0

    for email_data in email_classifications.get("classifications", {}).values():
        # Count secondary types
        for sec_type in email_data.get("secondary_types", []):
            if isinstance(sec_type, str):
                secondary_types[sec_type] += 1
            elif isinstance(sec_type, (list, tuple)) and len(sec_type) > 0:
                secondary_types[sec_type[0]] += 1

        # Count specific patterns
        keywords = email_data.get("keywords", [])
        if "COURT_NOTIFICATION" in keywords:
            court_notifications += 1
        if "BOP_ADMINISTRATIVE" in keywords:
            bop_emails += 1

    lines.append(f"Court-related notifications: {court_notifications}")
    lines.append(f"Bureau of Prisons emails: {bop_emails}")

    if secondary_types:
        lines.append("")
        lines.append("Secondary Classification Patterns:")
        for sec_type, count in secondary_types.most_common(10):
            lines.append(f"  {sec_type:20s}: {count:3d}")

    lines.append("")

    # Key Findings
    lines.append("KEY FINDINGS")
    lines.append("-"*80)
    lines.append(f"1. Email to PDF Ratio: 1:{int(unified_index['statistics']['by_type'].get('pdf', 0) / max(1, unified_index['statistics']['by_type'].get('email', 1)))}")
    lines.append(f"2. Email Classification Accuracy: {(email_stats.get('high_confidence', 0) + email_stats.get('medium_confidence', 0))/total_emails*100:.1f}% (medium+ confidence)")
    lines.append(f"3. Court Filings in Emails: {email_stats.get('by_type', {}).get('court_filing', 0)} ({email_stats.get('by_type', {}).get('court_filing', 0)/total_emails*100:.1f}%)")
    lines.append(f"4. Primary Email Type: {max(email_stats.get('by_type', {}).items(), key=lambda x: x[1])[0]} ({max(email_stats.get('by_type', {}).values())/total_emails*100:.1f}%)")

    # Calculate date range
    if unified_index["statistics"].get("by_date"):
        dates = sorted(unified_index["statistics"]["by_date"].keys())
        if dates:
            lines.append(f"5. Email Date Range: {dates[0]} to {dates[-1]}")
            lines.append(f"6. Most Active Period: {max(unified_index['statistics']['by_date'].items(), key=lambda x: x[1])[0]} ({max(unified_index['statistics']['by_date'].values())} emails)")

    lines.append("")

    # Next Steps
    lines.append("RECOMMENDED NEXT STEPS")
    lines.append("-"*80)
    lines.append("1. Review low-confidence email classifications (44 emails)")
    lines.append("2. Classify remaining 38,177 PDF documents")
    lines.append("3. Extract entity mentions from emails")
    lines.append("4. Build email network graph (sender/recipient relationships)")
    lines.append("5. Create timeline visualization from dated documents")
    lines.append("6. Implement full-text search across all documents")
    lines.append("")

    lines.append("="*80)
    lines.append(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("="*80)

    return "\n".join(lines)

def main():
    """Main execution."""
    try:
        print("\nGenerating classification summary report...")

        # Generate report
        report_text = generate_report()

        # Save to file
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(report_text)

        print(f"✅ Report saved to: {REPORT_FILE}")

        # Print to console
        print("\n" + report_text)

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
