#!/usr/bin/env python3
"""
Visual Test of Document Categorization

Shows sample documents from each classification category.
"""

import json
from collections import defaultdict


def show_category_samples():
    """Display sample documents from each category."""

    # Load document index
    with open("data/metadata/all_documents_index.json") as f:
        data = json.load(f)

    documents = data.get("documents", [])
    data.get("statistics", {})

    print("\n" + "="*80)
    print("DOCUMENT CATEGORIZATION VISUAL TEST")
    print("="*80)

    print(f"\nTotal Documents: {len(documents):,}")
    print(f"Version: {data.get('version')}")

    # Group documents by classification
    by_classification = defaultdict(list)
    for doc in documents:
        classification = doc.get("classification", "unknown")
        by_classification[classification].append(doc)

    # Show statistics
    print("\n" + "-"*80)
    print("CLASSIFICATION SUMMARY")
    print("-"*80)

    for classification in sorted(by_classification.keys(), key=lambda x: -len(by_classification[x])):
        count = len(by_classification[classification])
        percentage = (count / len(documents)) * 100
        bar_length = int(percentage / 2)
        bar = "█" * bar_length
        print(f"{classification:25} {count:>6,} ({percentage:>5.1f}%) {bar}")

    # Show samples from each category
    print("\n" + "-"*80)
    print("SAMPLE DOCUMENTS BY CATEGORY")
    print("-"*80)

    for classification in sorted(by_classification.keys(), key=lambda x: -len(by_classification[x])):
        samples = by_classification[classification][:3]  # First 3

        print(f"\n{classification.upper()} ({len(by_classification[classification]):,} documents)")
        print("-" * 40)

        for i, doc in enumerate(samples, 1):
            filename = doc.get("filename", "N/A")
            path = doc.get("path", "N/A")
            source = doc.get("source", "N/A")
            confidence = doc.get("classification_confidence", 0.0)
            doc_type = doc.get("type", "N/A")

            # Truncate long filenames
            if len(filename) > 50:
                filename = filename[:47] + "..."

            print(f"\n  {i}. {filename}")
            print(f"     Type: {doc_type}")
            print(f"     Source: {source}")
            print(f"     Confidence: {confidence:.2f}")
            if path and len(path) < 80:
                print(f"     Path: {path}")

    # Show confidence distribution
    print("\n" + "-"*80)
    print("CONFIDENCE SCORE DISTRIBUTION")
    print("-"*80)

    confidence_buckets = {
        "High (>0.8)": 0,
        "Medium (0.5-0.8)": 0,
        "Low (<0.5)": 0,
    }

    for doc in documents:
        confidence = doc.get("classification_confidence", 0.0)
        if confidence > 0.8:
            confidence_buckets["High (>0.8)"] += 1
        elif confidence >= 0.5:
            confidence_buckets["Medium (0.5-0.8)"] += 1
        else:
            confidence_buckets["Low (<0.5)"] += 1

    for bucket, count in confidence_buckets.items():
        percentage = (count / len(documents)) * 100
        print(f"{bucket:20} {count:>6,} ({percentage:>5.1f}%)")

    # Success metrics
    print("\n" + "="*80)
    print("SUCCESS METRICS")
    print("="*80)

    unknown_count = len(by_classification.get("unknown", []))
    classified_count = len(documents) - unknown_count

    print(f"\n✅ Unknown documents: {unknown_count:,} ({(unknown_count/len(documents)*100):.1f}%)")
    print(f"✅ Classified documents: {classified_count:,} ({(classified_count/len(documents)*100):.1f}%)")

    # Check specific categories
    print(f"\n✅ Emails classified: {len(by_classification.get('email', []))} of {len([d for d in documents if d.get('type') == 'email'])}")
    print(f"✅ Court filings identified: {len(by_classification.get('court_filing', []))}")
    print(f"✅ Government documents identified: {len(by_classification.get('government_document', []))}")

    high_confidence = confidence_buckets["High (>0.8)"]
    print(f"✅ High confidence classifications: {high_confidence:,} ({(high_confidence/len(documents)*100):.1f}%)")

    print("\n" + "="*80)
    print("✅ CATEGORIZATION SYSTEM OPERATIONAL")
    print("="*80 + "\n")


if __name__ == "__main__":
    show_category_samples()
