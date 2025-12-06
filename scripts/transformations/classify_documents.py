#!/usr/bin/env python3
"""
Semantic Document Type Classification

Classifies Epstein documents into specific types using rule-based analysis of:
- File paths and filenames
- Document summaries (from master index)
- Source folder names

Classification types:
- email: Email correspondence
- court_record: Court filings, depositions, legal documents
- flight_log: Flight logs, passenger manifests
- fbi_report: FBI investigation reports
- deposition: Sworn testimony, depositions
- correspondence: Letters, memos, fax documents
- financial: Banking, transactions, invoices
- administrative: Administrative documents, scheduling
- contact_directory: Address books, contact lists
- government_document: Generic government documents (fallback)
- media_article: News articles, press coverage
- other: Unclassified documents

Usage:
    python scripts/transformations/classify_documents.py
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter, defaultdict
from datetime import datetime


# Classification rules with keyword patterns
CLASSIFICATION_RULES = {
    "email": {
        "keywords": [
            "email", "e-mail", "mail", "from:", "to:", "subject:", "cc:", "sent:",
            "received:", "message", "correspondence", "inbox", "outbox"
        ],
        "path_patterns": ["email", "mail", "correspondence"],
        "source_patterns": ["email"],
    },
    "court_record": {
        "keywords": [
            "court", "case no", "case number", "plaintiff", "defendant", "motion",
            "order", "judgment", "docket", "filing", "appeal", "circuit", "district",
            "honorable", "magistrate", "clerk of court", "hearing", "trial",
            "exhibits", "affidavit", "declaration", "stipulation", "complaint",
            "answer", "discovery", "subpoena"
        ],
        "path_patterns": ["court", "filing", "uscourts", "giuffre", "maxwell"],
        "source_patterns": ["courtlistener", "giuffre_maxwell"],
    },
    "flight_log": {
        "keywords": [
            "flight", "aircraft", "passenger", "manifest", "tail number", "lolita",
            "aviation", "pilot", "crew", "departure", "arrival", "flight plan",
            "n-number", "registration", "airstrip", "runway"
        ],
        "path_patterns": ["flight", "manifest", "aviation", "aircraft"],
        "source_patterns": [],
    },
    "fbi_report": {
        "keywords": [
            "fbi", "federal bureau", "302 report", "investigation", "special agent",
            "bureau", "field office", "confidential", "memorandum for record",
            "interview", "witness", "informant", "surveillance", "intelligence"
        ],
        "path_patterns": ["fbi", "bureau"],
        "source_patterns": ["fbi_vault"],
    },
    "deposition": {
        "keywords": [
            "deposition", "testimony", "sworn statement", "under oath", "q.", "a.",
            "examination", "cross-examination", "witness", "transcript", "stenographer",
            "court reporter", "appeared before", "being duly sworn"
        ],
        "path_patterns": ["deposition", "testimony", "transcript"],
        "source_patterns": [],
    },
    "financial": {
        "keywords": [
            "bank", "account", "transaction", "wire transfer", "invoice", "payment",
            "receipt", "statement", "balance", "credit", "debit", "check", "cheque",
            "financial", "ledger", "accounting", "funds", "money", "currency",
            "deposit", "withdrawal"
        ],
        "path_patterns": ["bank", "financial", "transaction", "invoice"],
        "source_patterns": [],
    },
    "contact_directory": {
        "keywords": [
            "contact", "address book", "phone", "directory", "telephone", "mobile",
            "cell", "fax", "birthday", "rolodex", "contacts list"
        ],
        "path_patterns": ["contact", "directory", "address", "birthday"],
        "source_patterns": [],
    },
    "correspondence": {
        "keywords": [
            "letter", "memo", "memorandum", "fax", "facsimile", "note", "communication",
            "dear", "sincerely", "regards", "re:", "reference", "attn:", "attention"
        ],
        "path_patterns": ["letter", "memo", "fax", "correspondence"],
        "source_patterns": [],
    },
    "administrative": {
        "keywords": [
            "schedule", "calendar", "appointment", "meeting", "agenda", "minutes",
            "itinerary", "booking", "reservation", "arrangement", "coordination",
            "planning", "logistics", "organization"
        ],
        "path_patterns": ["schedule", "calendar", "admin"],
        "source_patterns": [],
    },
    "media_article": {
        "keywords": [
            "article", "news", "press", "journalist", "reporter", "published",
            "newspaper", "magazine", "story", "headline", "byline", "editorial"
        ],
        "path_patterns": ["media", "article", "news", "press"],
        "source_patterns": ["404media"],
    },
}


def calculate_confidence(match_count: int, total_keywords: int, source_boost: float = 0.0) -> float:
    """Calculate classification confidence score.

    Args:
        match_count: Number of keyword matches
        total_keywords: Total keywords checked
        source_boost: Confidence boost from source/path matching (0.0-0.3)

    Returns:
        Confidence score between 0.0 and 1.0
    """
    if total_keywords == 0:
        base_confidence = 0.5
    else:
        # Base confidence from keyword matching
        base_confidence = min(match_count / total_keywords * 2, 0.7)

    # Add source/path boost
    total_confidence = min(base_confidence + source_boost, 1.0)

    # Require minimum 0.3 confidence
    return max(total_confidence, 0.3) if match_count > 0 or source_boost > 0 else 0.0


def classify_by_path(path: str, source: str) -> Tuple[str, float]:
    """Classify document by file path and source patterns.

    Args:
        path: Document file path
        source: Document source identifier

    Returns:
        Tuple of (classification, confidence)
    """
    path_lower = path.lower()
    source_lower = source.lower()

    matches = []

    for doc_type, rules in CLASSIFICATION_RULES.items():
        # Check source patterns (highest confidence)
        for pattern in rules["source_patterns"]:
            if pattern.lower() in source_lower:
                matches.append((doc_type, 0.9, "source_match"))

        # Check path patterns
        for pattern in rules["path_patterns"]:
            if pattern.lower() in path_lower:
                matches.append((doc_type, 0.7, "path_match"))

    if matches:
        # Sort by confidence and return highest
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[0][0], matches[0][1]

    return None, 0.0


def classify_by_content(summary: str, filename: str) -> Tuple[str, float, List[str]]:
    """Classify document by content analysis of summary and filename.

    Args:
        summary: Document summary text
        filename: Document filename

    Returns:
        Tuple of (classification, confidence, matched_keywords)
    """
    if not summary:
        return None, 0.0, []

    text = (summary + " " + filename).lower()

    best_match = None
    best_score = 0.0
    best_keywords = []

    for doc_type, rules in CLASSIFICATION_RULES.items():
        keywords = rules["keywords"]
        matches = []

        for keyword in keywords:
            # Use word boundary matching for accuracy
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text):
                matches.append(keyword)

        if matches:
            # Enhanced confidence for summary classification
            # More keywords = higher confidence, with bonus for multiple matches
            match_ratio = len(matches) / max(len(keywords), 1)
            base_confidence = min(match_ratio * 3.0, 0.9)  # Up to 0.9 confidence

            # Boost confidence if multiple strong keywords matched
            if len(matches) >= 3:
                base_confidence = min(base_confidence + 0.1, 0.95)

            if base_confidence > best_score:
                best_score = base_confidence
                best_match = doc_type
                best_keywords = matches

    return best_match, best_score, best_keywords


def classify_document(doc: Dict, master_index: Dict) -> Tuple[str, float, Dict]:
    """Classify a single document using all available signals.

    Args:
        doc: Document record from all_documents_index
        master_index: Master document index (hash -> metadata)

    Returns:
        Tuple of (classification, confidence, metadata)
    """
    # Get document metadata from master index
    doc_hash = doc["id"]
    master_doc = master_index.get(doc_hash, {})
    summary = master_doc.get("summary", "")

    # Strategy: Try multiple classification methods, use highest confidence
    classifications = []

    # Method 1: Path and source classification (fast, high confidence)
    path_class, path_conf = classify_by_path(doc["path"], doc["source"])
    if path_class:
        classifications.append({
            "type": path_class,
            "confidence": path_conf,
            "method": "path_source",
            "keywords": []
        })

    # Method 2: Content classification (PRIORITIZED - most accurate)
    content_class, content_conf, keywords = classify_by_content(
        summary, doc.get("filename", "")
    )
    if content_class:
        classifications.append({
            "type": content_class,
            "confidence": content_conf,
            "method": "content_analysis",
            "keywords": keywords
        })

    # Method 3: Use existing classification as fallback (only if no better option)
    # Lower the confidence of existing classifications to prioritize new analysis
    if doc.get("classification"):
        existing_class = doc["classification"]
        existing_conf = doc.get("classification_confidence", 0.5)
        # Only use existing if it's not generic "government_document" OR no better option
        if existing_class != "government_document" or not classifications:
            # Reduce confidence to prefer content analysis
            adjusted_conf = existing_conf * 0.8 if existing_class == "government_document" else existing_conf
            classifications.append({
                "type": existing_class,
                "confidence": adjusted_conf,
                "method": "existing",
                "keywords": []
            })

    # Select best classification
    if classifications:
        best = max(classifications, key=lambda x: x["confidence"])
        return best["type"], best["confidence"], {
            "method": best["method"],
            "keywords": best["keywords"],
            "all_candidates": classifications
        }

    # Fallback to government_document
    return "government_document", 0.3, {
        "method": "fallback",
        "keywords": [],
        "all_candidates": []
    }


def load_master_index(master_path: Path) -> Dict:
    """Load master document index and create hash lookup."""
    with open(master_path, 'r') as f:
        data = json.load(f)

    # Create hash -> document mapping
    master_index = {}
    for doc in data.get("documents", []):
        doc_hash = doc.get("hash")
        if doc_hash:
            master_index[doc_hash] = doc

    return master_index


def classify_all_documents(
    all_docs_path: Path,
    master_path: Path,
    output_path: Path
) -> Dict:
    """Classify all documents and generate report.

    Args:
        all_docs_path: Path to all_documents_index.json
        master_path: Path to master_document_index.json
        output_path: Path to save classification results

    Returns:
        Classification statistics and results
    """
    print("Loading document indexes...")

    # Load documents
    with open(all_docs_path, 'r') as f:
        all_docs = json.load(f)

    documents = all_docs["documents"]
    print(f"Loaded {len(documents)} documents")

    # Load master index
    master_index = load_master_index(master_path)
    print(f"Loaded master index with {len(master_index)} documents")

    # Track statistics
    stats = {
        "total_documents": len(documents),
        "classified": 0,
        "by_type": Counter(),
        "by_confidence": defaultdict(int),
        "by_method": Counter(),
        "confidence_distribution": {
            "high": 0,  # >= 0.8
            "medium": 0,  # 0.5-0.8
            "low": 0,  # < 0.5
        },
        "examples_by_type": defaultdict(list),
    }

    # Original statistics (before reclassification)
    original_stats = Counter(doc.get("classification", "unknown") for doc in documents)

    # Classify all documents
    print("\nClassifying documents...")
    results = []

    for i, doc in enumerate(documents):
        if (i + 1) % 1000 == 0:
            print(f"Progress: {i + 1}/{len(documents)} documents...")

        doc_type, confidence, metadata = classify_document(doc, master_index)

        result = {
            "id": doc["id"],
            "filename": doc.get("filename", ""),
            "path": doc["path"],
            "source": doc["source"],
            "original_classification": doc.get("classification"),
            "new_classification": doc_type,
            "confidence": round(confidence, 2),
            "classification_method": metadata["method"],
            "keywords_matched": metadata["keywords"][:5],  # Top 5 keywords
        }

        results.append(result)

        # Update statistics
        stats["classified"] += 1
        stats["by_type"][doc_type] += 1
        stats["by_method"][metadata["method"]] += 1

        # Confidence distribution
        if confidence >= 0.8:
            stats["confidence_distribution"]["high"] += 1
        elif confidence >= 0.5:
            stats["confidence_distribution"]["medium"] += 1
        else:
            stats["confidence_distribution"]["low"] += 1

        # Store examples (max 5 per type)
        if len(stats["examples_by_type"][doc_type]) < 5:
            stats["examples_by_type"][doc_type].append({
                "filename": doc.get("filename", ""),
                "path": doc["path"],
                "confidence": round(confidence, 2),
                "keywords": metadata["keywords"][:3],
            })

    # Save results
    print(f"\nSaving results to {output_path}...")
    output_data = {
        "generated": datetime.utcnow().isoformat(),
        "version": "1.0",
        "source_file": str(all_docs_path),
        "total_documents": stats["total_documents"],
        "statistics": {
            "original_distribution": dict(original_stats),
            "new_distribution": dict(stats["by_type"]),
            "classification_methods": dict(stats["by_method"]),
            "confidence_distribution": stats["confidence_distribution"],
        },
        "documents": results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"✓ Saved {len(results)} classified documents")

    # Return stats for report generation
    stats["original_stats"] = original_stats
    stats["examples"] = dict(stats["examples_by_type"])

    return stats


def generate_report(stats: Dict, output_path: Path) -> None:
    """Generate markdown report of classification results."""

    report = f"""# Document Classification Report

**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

## Summary

Total documents classified: **{stats['total_documents']:,}**

## Classification Distribution

### Before Reclassification

| Type | Count | Percentage |
|------|-------|------------|
"""

    # Original distribution
    original_total = sum(stats['original_stats'].values())
    for doc_type, count in stats['original_stats'].most_common():
        pct = (count / original_total * 100) if original_total > 0 else 0
        report += f"| {doc_type} | {count:,} | {pct:.1f}% |\n"

    report += """
### After Semantic Classification

| Type | Count | Percentage | Change |
|------|-------|------------|--------|
"""

    # New distribution with comparison
    for doc_type, count in stats['by_type'].most_common():
        pct = (count / stats['total_documents'] * 100) if stats['total_documents'] > 0 else 0
        original_count = stats['original_stats'].get(doc_type, 0)
        change = count - original_count
        change_str = f"+{change:,}" if change > 0 else f"{change:,}"
        report += f"| {doc_type} | {count:,} | {pct:.1f}% | {change_str} |\n"

    report += f"""
## Classification Quality

### Confidence Distribution

- **High confidence (≥0.8):** {stats['confidence_distribution']['high']:,} documents ({stats['confidence_distribution']['high']/stats['total_documents']*100:.1f}%)
- **Medium confidence (0.5-0.8):** {stats['confidence_distribution']['medium']:,} documents ({stats['confidence_distribution']['medium']/stats['total_documents']*100:.1f}%)
- **Low confidence (<0.5):** {stats['confidence_distribution']['low']:,} documents ({stats['confidence_distribution']['low']/stats['total_documents']*100:.1f}%)

### Classification Methods

| Method | Count | Percentage |
|--------|-------|------------|
"""

    for method, count in stats['by_method'].most_common():
        pct = (count / stats['total_documents'] * 100) if stats['total_documents'] > 0 else 0
        report += f"| {method} | {count:,} | {pct:.1f}% |\n"

    report += """
## Examples by Type

"""

    for doc_type in sorted(stats['by_type'].keys()):
        examples = stats['examples'].get(doc_type, [])
        if examples:
            report += f"### {doc_type.replace('_', ' ').title()}\n\n"
            for example in examples[:3]:  # Show top 3
                report += f"- **{example['filename']}**\n"
                report += f"  - Path: `{example['path']}`\n"
                report += f"  - Confidence: {example['confidence']}\n"
                if example['keywords']:
                    report += f"  - Keywords: {', '.join(example['keywords'])}\n"
                report += "\n"

    report += """
## Key Findings

"""

    # Calculate key metrics
    government_doc_count = stats['by_type'].get('government_document', 0)
    government_pct = (government_doc_count / stats['total_documents'] * 100) if stats['total_documents'] > 0 else 0
    original_gov_count = stats['original_stats'].get('government_document', 0)
    original_gov_pct = (original_gov_count / original_total * 100) if original_total > 0 else 0

    report += f"1. **Generic classification reduction:** Government documents reduced from {original_gov_pct:.1f}% to {government_pct:.1f}%\n"
    report += f"2. **Specific types identified:** {len(stats['by_type'])} distinct document types\n"
    report += f"3. **High confidence classifications:** {stats['confidence_distribution']['high']/stats['total_documents']*100:.1f}% of documents\n"

    # Top types
    top_types = stats['by_type'].most_common(5)
    report += f"4. **Most common types:**\n"
    for doc_type, count in top_types:
        pct = (count / stats['total_documents'] * 100)
        report += f"   - {doc_type}: {count:,} ({pct:.1f}%)\n"

    report += """
## Next Steps

1. **Review low-confidence classifications** (confidence < 0.5) for potential improvements
2. **Add LLM-based classification** for remaining generic "government_document" entries
3. **Validate classification accuracy** through manual sampling
4. **Update search and filtering** to use new semantic classifications
"""

    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(report)

    print(f"\n✓ Report saved to {output_path}")


def main():
    """Main execution function."""
    project_root = Path(__file__).parent.parent.parent

    # File paths
    all_docs_path = project_root / "data/metadata/all_documents_index.json"
    master_path = project_root / "data/metadata/master_document_index.json"
    output_path = project_root / "data/transformed/document_classifications.json"
    report_path = project_root / "docs/implementation-summaries/document-classification-report.md"

    print("=" * 80)
    print("Semantic Document Type Classification")
    print("=" * 80)

    # Classify documents
    stats = classify_all_documents(all_docs_path, master_path, output_path)

    # Generate report
    generate_report(stats, report_path)

    print("\n" + "=" * 80)
    print("Classification Complete!")
    print("=" * 80)
    print(f"\nResults saved to: {output_path}")
    print(f"Report saved to: {report_path}")
    print("\nClassification Summary:")
    print(f"  Total documents: {stats['total_documents']:,}")
    print(f"  Types identified: {len(stats['by_type'])}")
    print(f"  High confidence: {stats['confidence_distribution']['high']:,} ({stats['confidence_distribution']['high']/stats['total_documents']*100:.1f}%)")
    print("\nTop 5 document types:")
    for doc_type, count in stats['by_type'].most_common(5):
        pct = (count / stats['total_documents'] * 100)
        print(f"  - {doc_type}: {count:,} ({pct:.1f}%)")


if __name__ == "__main__":
    main()
