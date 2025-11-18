#!/usr/bin/env python3
"""
Entity-Document Linking System
Epstein Document Archive - RAG System

Scans all embedded documents for entity mentions and builds a comprehensive
entity → document index for fast entity-based retrieval.

Output: data/metadata/entity_document_index.json

Usage:
    python3 scripts/rag/link_entities_to_docs.py
    python3 scripts/rag/link_entities_to_docs.py --min-mentions 5
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict
from tqdm import tqdm
import argparse

# Project paths
PROJECT_ROOT = Path("/Users/masa/Projects/Epstein")
OCR_TEXT_DIR = PROJECT_ROOT / "data/sources/house_oversight_nov2025/ocr_text"
ENTITY_INDEX_PATH = PROJECT_ROOT / "data/md/entities/ENTITIES_INDEX.json"
OUTPUT_PATH = PROJECT_ROOT / "data/metadata/entity_document_index.json"
ENTITY_NETWORK_PATH = PROJECT_ROOT / "data/metadata/entity_network.json"


class EntityDocumentLinker:
    def __init__(self, min_mentions: int = 1):
        """Initialize the entity-document linker."""
        self.min_mentions = min_mentions
        self.entity_index = self._load_entity_index()
        self.entity_network = self._load_entity_network()

        # Build entity name variations for better matching
        self.entity_variations = self._build_entity_variations()

    def _load_entity_index(self) -> Dict:
        """Load the master entity index."""
        with open(ENTITY_INDEX_PATH, 'r') as f:
            data = json.load(f)
            print(f"✅ Loaded entity index: {len(data.get('entities', []))} entities")
            return data

    def _load_entity_network(self) -> Dict:
        """Load entity network for additional context."""
        if ENTITY_NETWORK_PATH.exists():
            with open(ENTITY_NETWORK_PATH, 'r') as f:
                data = json.load(f)
                print(f"✅ Loaded entity network: {data.get('metadata', {}).get('total_nodes', 0)} nodes")
                return data
        return {"nodes": [], "edges": []}

    def _build_entity_variations(self) -> Dict[str, Set[str]]:
        """Build entity name variations for matching."""
        variations = defaultdict(set)

        for entity in self.entity_index.get('entities', []):
            name = entity.get('name', '')
            if not name:
                continue

            canonical = name
            variations[canonical].add(name)

            # Add variations
            # "LastName, FirstName" → "FirstName LastName" and "LastName"
            if ',' in name:
                parts = name.split(',')
                last_name = parts[0].strip()
                if len(parts) > 1:
                    first_name = parts[1].strip()
                    variations[canonical].add(f"{first_name} {last_name}")
                    variations[canonical].add(last_name)
                else:
                    variations[canonical].add(last_name)

            # Add lowercase version
            variations[canonical].add(name.lower())

        return variations

    def _find_entity_mentions(self, text: str) -> Dict[str, int]:
        """Find all entity mentions in text with counts."""
        mentions = defaultdict(int)
        text_lower = text.lower()

        # Search for each entity and its variations
        for canonical_name, name_variations in self.entity_variations.items():
            total_count = 0

            for variation in name_variations:
                # Count occurrences (case-insensitive)
                # Use word boundaries to avoid partial matches
                if len(variation) < 4:  # Skip very short names
                    continue

                pattern = r'\b' + re.escape(variation) + r'\b'
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                total_count += len(matches)

            if total_count > 0:
                mentions[canonical_name] = total_count

        return mentions

    def _get_document_files(self) -> List[Path]:
        """Get all .txt files from OCR directory."""
        txt_files = sorted(OCR_TEXT_DIR.glob("*.txt"))
        print(f"📄 Found {len(txt_files)} text files")
        return txt_files

    def link_entities_to_documents(self):
        """Build entity → document index."""
        print("\n" + "="*70)
        print("ENTITY-DOCUMENT LINKING SYSTEM")
        print("="*70)

        # Entity → documents mapping
        entity_to_docs = defaultdict(lambda: {
            "documents": [],
            "mention_count": 0,
            "document_count": 0
        })

        # Document → entities mapping (for verification)
        doc_to_entities = {}

        # Get all documents
        all_files = self._get_document_files()

        print(f"\n🔍 Scanning {len(all_files)} documents for entity mentions...")

        # Process each document
        with tqdm(total=len(all_files), desc="Processing documents") as pbar:
            for file_path in all_files:
                try:
                    # Read document
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()

                    # Skip empty documents
                    if len(text.strip()) < 50:
                        pbar.update(1)
                        continue

                    doc_id = file_path.stem

                    # Find entity mentions
                    mentions = self._find_entity_mentions(text)

                    # Filter by minimum mentions
                    mentions = {
                        entity: count
                        for entity, count in mentions.items()
                        if count >= self.min_mentions
                    }

                    if mentions:
                        # Update entity → docs index
                        for entity, count in mentions.items():
                            entity_to_docs[entity]["documents"].append({
                                "doc_id": doc_id,
                                "filename": file_path.name,
                                "mentions": count
                            })
                            entity_to_docs[entity]["mention_count"] += count
                            entity_to_docs[entity]["document_count"] += 1

                        # Update doc → entities mapping
                        doc_to_entities[doc_id] = list(mentions.keys())

                    pbar.update(1)

                except Exception as e:
                    print(f"\n⚠️  Error processing {file_path.name}: {e}")
                    pbar.update(1)

        # Sort documents by mention count for each entity
        for entity in entity_to_docs:
            entity_to_docs[entity]["documents"].sort(
                key=lambda x: x["mentions"],
                reverse=True
            )

        # Convert to regular dict for JSON serialization
        entity_to_docs = dict(entity_to_docs)

        # Generate statistics
        total_entities_mentioned = len(entity_to_docs)
        total_documents_with_entities = len(doc_to_entities)
        total_mentions = sum(
            entity_data["mention_count"]
            for entity_data in entity_to_docs.values()
        )

        # Top entities by document count
        top_entities = sorted(
            entity_to_docs.items(),
            key=lambda x: x[1]["document_count"],
            reverse=True
        )[:20]

        # Save results
        output_data = {
            "generated": "2025-11-17",
            "metadata": {
                "total_entities_mentioned": total_entities_mentioned,
                "total_documents_with_entities": total_documents_with_entities,
                "total_entity_mentions": total_mentions,
                "min_mentions_threshold": self.min_mentions
            },
            "entity_to_documents": entity_to_docs,
            "statistics": {
                "top_entities_by_document_count": [
                    {
                        "entity": entity,
                        "document_count": data["document_count"],
                        "total_mentions": data["mention_count"]
                    }
                    for entity, data in top_entities
                ]
            }
        }

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(output_data, f, indent=2)

        # Print summary
        print("\n" + "="*70)
        print("✅ ENTITY-DOCUMENT LINKING COMPLETE")
        print("="*70)
        print(f"Entities mentioned: {total_entities_mentioned}")
        print(f"Documents with entities: {total_documents_with_entities}")
        print(f"Total entity mentions: {total_mentions}")
        print(f"\nTop 10 entities by document count:")
        for i, (entity, data) in enumerate(top_entities[:10], 1):
            print(f"  {i:2d}. {entity:30s} - {data['document_count']:4d} docs, {data['mention_count']:6d} mentions")
        print(f"\n📁 Output saved to: {OUTPUT_PATH}")
        print("="*70)


def main():
    parser = argparse.ArgumentParser(description="Link entities to documents")
    parser.add_argument(
        '--min-mentions',
        type=int,
        default=1,
        help='Minimum mentions required to link entity to document'
    )

    args = parser.parse_args()

    linker = EntityDocumentLinker(min_mentions=args.min_mentions)
    linker.link_entities_to_documents()


if __name__ == "__main__":
    main()
