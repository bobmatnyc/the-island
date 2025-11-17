#!/usr/bin/env python3
"""
Classify all documents in the Epstein archive and create semantic index
Links documents to entities mentioned in them
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Set


# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from document_classifier import DocumentClassifier


PROJECT_ROOT = Path("/Users/masa/Projects/Epstein")
DATA_DIR = PROJECT_ROOT / "data"
MD_DIR = DATA_DIR / "md"
METADATA_DIR = DATA_DIR / "metadata"

class SemanticIndexBuilder:
    """Build semantic index linking documents to entities"""

    def __init__(self, entities_index_path: Path):
        """Load entity index"""
        with open(entities_index_path) as f:
            self.entities_data = json.load(f)

        # Extract entity names for matching
        self.entity_names = set()
        if "entities" in self.entities_data:
            for entity in self.entities_data["entities"]:
                name = entity.get("name", "").strip()
                if name:
                    self.entity_names.add(name.lower())

                    # Add variations
                    parts = name.split()
                    if len(parts) >= 2:
                        # Add last name
                        self.entity_names.add(parts[-1].lower())
                        # Add first name + last name
                        self.entity_names.add(f"{parts[0]} {parts[-1]}".lower())

        print(f"Loaded {len(self.entity_names)} entity name variations")

    def find_entities_in_text(self, text: str) -> Set[str]:
        """Find entity names mentioned in text"""
        text_lower = text.lower()
        found_entities = set()

        for entity_name in self.entity_names:
            # Use word boundaries for better matching
            pattern = r"\b" + re.escape(entity_name) + r"\b"
            if re.search(pattern, text_lower):
                found_entities.add(entity_name)

        return found_entities

    def index_document(self, filepath: Path) -> Dict:
        """Create semantic index entry for a document"""
        try:
            text = filepath.read_text(encoding="utf-8", errors="ignore")

            # Find entities mentioned
            entities_mentioned = self.find_entities_in_text(text)

            return {
                "filepath": str(filepath),
                "entities_mentioned": list(entities_mentioned),
                "entity_count": len(entities_mentioned),
                "word_count": len(text.split()),
                "has_entities": len(entities_mentioned) > 0
            }
        except Exception as e:
            return {
                "filepath": str(filepath),
                "error": str(e),
                "entities_mentioned": [],
                "entity_count": 0
            }

def classify_all_documents():
    """Classify all markdown documents"""

    classifier = DocumentClassifier()
    semantic_indexer = SemanticIndexBuilder(MD_DIR / "entities" / "ENTITIES_INDEX.json")

    # Find all markdown files
    md_files = []
    for source_dir in MD_DIR.iterdir():
        if source_dir.is_dir():
            md_files.extend(source_dir.glob("*.md"))

    print(f"\nFound {len(md_files)} markdown files to classify")

    # Classify all documents
    results = {}
    semantic_index = {}
    entity_to_docs = defaultdict(list)

    for i, filepath in enumerate(md_files, 1):
        if i % 10 == 0:
            print(f"  Processed {i}/{len(md_files)} documents...")

        # Classify
        classification = classifier.classify_file(filepath)

        # Build semantic index
        semantic_entry = semantic_indexer.index_document(filepath)

        # Link entities to documents
        for entity in semantic_entry["entities_mentioned"]:
            entity_to_docs[entity].append({
                "document": str(filepath),
                "document_type": classification.document_type.value
            })

        results[str(filepath)] = {
            "type": classification.document_type.value,
            "confidence": classification.confidence,
            "secondary_types": [
                {"type": st.value, "confidence": conf}
                for st, conf in classification.secondary_types
            ],
            "keywords": classification.keywords_found[:10],
            "entities_mentioned": semantic_entry["entities_mentioned"],
            "entity_count": semantic_entry["entity_count"]
        }

    # Save classification results
    classification_path = METADATA_DIR / "document_classifications.json"
    with open(classification_path, "w") as f:
        json.dump({
            "generated": "2025-11-16T23:35:00",
            "total_documents": len(results),
            "results": results
        }, f, indent=2)

    print(f"\n✓ Saved classifications: {classification_path}")

    # Save semantic index (entity -> documents)
    semantic_index_path = METADATA_DIR / "semantic_index.json"
    with open(semantic_index_path, "w") as f:
        json.dump({
            "generated": "2025-11-16T23:35:00",
            "total_entities": len(entity_to_docs),
            "entity_to_documents": dict(entity_to_docs)
        }, f, indent=2)

    print(f"✓ Saved semantic index: {semantic_index_path}")

    # Generate statistics
    generate_statistics(results, entity_to_docs)

def generate_statistics(results: Dict, entity_to_docs: Dict):
    """Generate classification and semantic statistics"""

    # Count by type
    type_counts = defaultdict(int)
    high_conf = 0
    low_conf = 0
    docs_with_entities = 0
    total_entity_mentions = 0

    for filepath, data in results.items():
        doc_type = data["type"]
        confidence = data["confidence"]
        entity_count = data["entity_count"]

        type_counts[doc_type] += 1

        if confidence > 0.8:
            high_conf += 1
        elif confidence < 0.5:
            low_conf += 1

        if entity_count > 0:
            docs_with_entities += 1
            total_entity_mentions += entity_count

    # Top entities by document mentions
    top_entities = sorted(
        entity_to_docs.items(),
        key=lambda x: len(x[1]),
        reverse=True
    )[:20]

    # Generate report
    report = [
        "=" * 70,
        "EPSTEIN ARCHIVE CLASSIFICATION & SEMANTIC INDEX",
        "=" * 70,
        "",
        f"Total documents: {len(results)}",
        f"Documents with entities: {docs_with_entities} ({docs_with_entities/len(results)*100:.1f}%)",
        f"Total entity mentions: {total_entity_mentions}",
        f"Average entities per document: {total_entity_mentions/len(results):.1f}",
        "",
        "CLASSIFICATION BREAKDOWN:",
        "-" * 70
    ]

    for doc_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(results)) * 100
        report.append(f"  {doc_type:20s}: {count:5d} ({percentage:5.1f}%)")

    report.extend([
        "",
        "CONFIDENCE DISTRIBUTION:",
        "-" * 70,
        f"  High confidence (>0.8):  {high_conf:5d} ({high_conf/len(results)*100:5.1f}%)",
        f"  Low confidence (<0.5):   {low_conf:5d} ({low_conf/len(results)*100:5.1f}%)",
        "",
        "TOP 20 MOST MENTIONED ENTITIES:",
        "-" * 70
    ])

    for entity_name, docs in top_entities:
        doc_types = defaultdict(int)
        for doc in docs:
            doc_types[doc["document_type"]] += 1

        types_str = ", ".join([f"{dt}: {c}" for dt, c in sorted(doc_types.items())])
        report.append(f"  {entity_name:30s}: {len(docs):4d} mentions ({types_str})")

    report_text = "\n".join(report)

    # Save report
    report_path = METADATA_DIR / "classification_report.txt"
    report_path.write_text(report_text)

    print(f"✓ Saved report: {report_path}")
    print("\n" + report_text)

def main():
    """Run classification and semantic indexing"""
    print("=" * 70)
    print("DOCUMENT CLASSIFICATION & SEMANTIC INDEXING")
    print("=" * 70)

    classify_all_documents()

    print("\n" + "=" * 70)
    print("INDEXING COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
