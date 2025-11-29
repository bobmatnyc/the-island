#!/usr/bin/env python3
"""
Classify extracted emails by document type using existing classifier.

Reads email metadata and full text, applies classification patterns,
and updates the master document_classifications.json file.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

# Import existing classifier
from classification.document_classifier import DocumentClassifier


# Paths
EMAILS_DIR = PROJECT_ROOT / "data" / "emails" / "house_oversight_nov2025"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
CLASSIFICATIONS_FILE = METADATA_DIR / "document_classifications.json"


def load_email_data(metadata_file: Path) -> dict[str, Any]:
    """Load email metadata and full text."""
    with open(metadata_file) as f:
        metadata = json.load(f)

    # Load full text
    full_text_file = metadata_file.with_name(
        metadata_file.name.replace("_metadata.json", "_full.txt")
    )

    if full_text_file.exists():
        with open(full_text_file) as f:
            full_text = f.read()
    else:
        full_text = metadata.get("body", "")

    return {"metadata": metadata, "full_text": full_text, "path": str(metadata_file)}


def classify_email(email_data: dict[str, Any], classifier: DocumentClassifier) -> dict[str, Any]:
    """Classify a single email using the document classifier."""
    # Combine metadata and full text for classification
    text_to_classify = f"""
    From: {email_data['metadata'].get('from_address', '')}
    To: {email_data['metadata'].get('to_address', '')}
    Subject: {email_data['metadata'].get('subject', '')}
    Date: {email_data['metadata'].get('date', '')}

    {email_data['full_text']}
    """

    # Use the document classifier
    result = classifier.classify(text_to_classify)

    # Convert ClassificationResult to dict
    classification = {
        "type": result.document_type.value,
        "confidence": result.confidence,
        "secondary_types": [(dt.value, conf) for dt, conf in result.secondary_types],
        "keywords": result.keywords_found,
        "document_id": email_data["metadata"].get("document_id", "unknown"),
        "email_index": email_data["metadata"].get("email_index", -1),
        "source": "house_oversight_nov2025_emails",
        "file_path": email_data["path"],
    }

    # Enhance classification based on email content
    classification = enhance_email_classification(
        classification, email_data["metadata"], email_data["full_text"]
    )

    return classification


def enhance_email_classification(
    classification: dict[str, Any], metadata: dict[str, Any], full_text: str
) -> dict[str, Any]:
    """Enhance classification with email-specific patterns."""
    text_lower = full_text.lower()

    # Legal document indicators
    legal_indicators = [
        "appearance of counsel",
        "united states district court",
        "case no.",
        "plaintiff",
        "defendant",
        "court order",
        "motion",
        "subpoena",
        "deposition",
        "discovery",
    ]

    # BOP/Administrative indicators
    admin_indicators = [
        "bureau of prisons",
        "bop.gov",
        "administrative",
        "notification",
        "public affairs",
    ]

    # Court notification indicators
    court_indicators = [
        "ecf",
        "electronic case filing",
        "notice of electronic filing",
        "uscourts.gov",
        "pacer",
    ]

    legal_score = sum(1 for indicator in legal_indicators if indicator in text_lower)
    admin_score = sum(1 for indicator in admin_indicators if indicator in text_lower)
    court_score = sum(1 for indicator in court_indicators if indicator in text_lower)

    # Override or boost classification based on email patterns
    if court_score >= 2:
        classification["secondary_types"].append("court_notification")
        classification["keywords"].append("COURT_NOTIFICATION")

    if legal_score >= 3 and classification["type"] != "court_filing":
        classification["type"] = "court_filing"
        classification["confidence"] = max(classification["confidence"], 0.8)

    if admin_score >= 2:
        classification["secondary_types"].append("administrative")
        classification["keywords"].append("BOP_ADMINISTRATIVE")

    # Email-specific metadata
    classification["email_metadata"] = {
        "from": metadata.get("from_address"),
        "to": metadata.get("to_address"),
        "subject": metadata.get("subject"),
        "date": metadata.get("date"),
        "confidence": metadata.get("confidence", 0.0),
    }

    return classification


def classify_all_emails() -> dict[str, Any]:
    """Classify all extracted emails."""
    print("\n" + "=" * 80)
    print("CLASSIFYING EXTRACTED EMAILS")
    print("=" * 80 + "\n")

    # Initialize classifier
    classifier = DocumentClassifier()

    # Find all metadata files
    metadata_files = sorted(EMAILS_DIR.rglob("*_metadata.json"))
    total = len(metadata_files)

    print(f"Found {total} emails to classify\n")

    classifications = {}
    stats = {
        "total": total,
        "by_type": {},
        "high_confidence": 0,
        "medium_confidence": 0,
        "low_confidence": 0,
    }

    for i, metadata_file in enumerate(metadata_files, 1):
        # Load email data
        email_data = load_email_data(metadata_file)
        email_data["metadata"].get("document_id", f"email_{i}")

        # Classify
        classification = classify_email(email_data, classifier)

        # Store classification
        classifications[str(metadata_file)] = classification

        # Update stats
        doc_type = classification["type"]
        stats["by_type"][doc_type] = stats["by_type"].get(doc_type, 0) + 1

        confidence = classification["confidence"]
        if confidence >= 0.8:
            stats["high_confidence"] += 1
        elif confidence >= 0.6:
            stats["medium_confidence"] += 1
        else:
            stats["low_confidence"] += 1

        # Progress
        if i % 50 == 0 or i == total:
            print(
                f"Progress: {i}/{total} ({i/total*100:.1f}%) - Latest: {doc_type} ({confidence:.2f})"
            )

    return {
        "generated": datetime.now().isoformat(),
        "source": "house_oversight_nov2025_emails",
        "total_documents": total,
        "classifications": classifications,
        "statistics": stats,
    }


def merge_with_existing_classifications(new_classifications: dict[str, Any]) -> dict[str, Any]:
    """Merge email classifications with existing document classifications."""
    # Load existing classifications
    if CLASSIFICATIONS_FILE.exists():
        with open(CLASSIFICATIONS_FILE) as f:
            existing = json.load(f)
    else:
        existing = {"generated": datetime.now().isoformat(), "total_documents": 0, "results": {}}

    # Merge
    existing["results"].update(new_classifications["classifications"])
    existing["total_documents"] = len(existing["results"])
    existing["generated"] = datetime.now().isoformat()

    # Add email statistics
    if "sources" not in existing:
        existing["sources"] = {}

    existing["sources"]["emails"] = new_classifications["statistics"]

    return existing


def save_classifications(classifications: dict[str, Any]) -> None:
    """Save classifications to file."""
    with open(CLASSIFICATIONS_FILE, "w") as f:
        json.dump(classifications, f, indent=2)

    print(f"\n✅ Classifications saved to: {CLASSIFICATIONS_FILE}")

    # Also save email-specific classifications
    email_classifications_file = METADATA_DIR / "email_classifications.json"

    email_only = {
        "generated": classifications.get("generated"),
        "source": "house_oversight_nov2025_emails",
        "total": classifications.get("sources", {}).get("emails", {}).get("total", 0),
        "statistics": classifications.get("sources", {}).get("emails", {}),
        "classifications": {k: v for k, v in classifications["results"].items() if "emails" in k},
    }

    with open(email_classifications_file, "w") as f:
        json.dump(email_only, f, indent=2)

    print(f"✅ Email classifications saved to: {email_classifications_file}")


def print_summary(stats: dict[str, Any]) -> None:
    """Print classification summary."""
    print("\n" + "=" * 80)
    print("EMAIL CLASSIFICATION SUMMARY")
    print("=" * 80 + "\n")

    print(f"Total Emails Classified: {stats['total']}")
    print("\nConfidence Distribution:")
    print(
        f"  High (≥0.8): {stats['high_confidence']} ({stats['high_confidence']/stats['total']*100:.1f}%)"
    )
    print(
        f"  Medium (≥0.6): {stats['medium_confidence']} ({stats['medium_confidence']/stats['total']*100:.1f}%)"
    )
    print(
        f"  Low (<0.6): {stats['low_confidence']} ({stats['low_confidence']/stats['total']*100:.1f}%)"
    )

    print("\nDocuments by Type:")
    for doc_type, count in sorted(stats["by_type"].items(), key=lambda x: x[1], reverse=True):
        print(f"  {doc_type}: {count} ({count/stats['total']*100:.1f}%)")


def main():
    """Main execution."""
    try:
        # Classify all emails
        email_classifications = classify_all_emails()

        # Merge with existing classifications
        merged = merge_with_existing_classifications(email_classifications)

        # Save
        save_classifications(merged)

        # Print summary
        print_summary(email_classifications["statistics"])

        print("\n✅ Email classification complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
