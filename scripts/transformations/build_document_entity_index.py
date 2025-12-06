#!/usr/bin/env python3
"""
Build bidirectional Document-Entity index.

Creates:
- document_to_entities.json: Document ID → [Entity IDs/names]
- entity_to_documents.json: Entity normalized_name → [Document IDs]

Source files:
- data/metadata/document_entities_full.json (entity→docs mapping)
- data/metadata/document_entity_index.json (doc→entities mapping)
- data/transformed/entity_uuid_mappings.json (entity UUIDs)
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Set


class DocumentEntityIndexBuilder:
    """Build bidirectional document-entity indices."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.metadata_dir = project_root / "data" / "metadata"
        self.transformed_dir = project_root / "data" / "transformed"

        # Source files
        self.doc_entities_full_path = self.metadata_dir / "document_entities_full.json"
        self.doc_entity_index_path = self.metadata_dir / "document_entity_index.json"
        self.entity_uuid_path = self.transformed_dir / "entity_uuid_mappings.json"

        # Output files
        self.doc_to_entities_path = self.transformed_dir / "document_to_entities.json"
        self.entity_to_docs_path = self.transformed_dir / "entity_to_documents.json"

        # Data structures
        self.entity_uuid_map: Dict[str, str] = {}  # normalized_name → UUID
        self.doc_to_entities: Dict[str, List[str]] = {}  # doc_id → [entity_names]
        self.entity_to_docs: Dict[str, Set[str]] = defaultdict(set)  # entity_name → {doc_ids}

    def load_entity_uuids(self) -> None:
        """Load entity UUID mappings."""
        print(f"Loading entity UUID mappings from {self.entity_uuid_path}")

        with open(self.entity_uuid_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Build normalized_name → UUID mapping
        for uuid, entity_data in data['mappings'].items():
            normalized_name = entity_data['normalized_name']
            self.entity_uuid_map[normalized_name] = uuid

        print(f"✓ Loaded {len(self.entity_uuid_map)} entity UUID mappings")

    def build_forward_index(self) -> None:
        """Build Document → Entities forward index."""
        print(f"\nBuilding forward index from {self.doc_entity_index_path}")

        with open(self.doc_entity_index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.doc_to_entities = data['document_entities']

        print(f"✓ Forward index: {len(self.doc_to_entities)} documents")

    def build_reverse_index(self) -> None:
        """Build Entity → Documents reverse index."""
        print(f"\nBuilding reverse index from {self.doc_entities_full_path}")

        with open(self.doc_entities_full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract entity → document mappings
        for entity_name, entity_data in data['entities'].items():
            normalized_name = entity_data['normalized_name']
            document_sources = entity_data['document_sources']

            # Add documents to this entity's set
            self.entity_to_docs[normalized_name].update(document_sources)

        print(f"✓ Reverse index: {len(self.entity_to_docs)} entities")

    def calculate_metrics(self) -> Dict:
        """Calculate coverage and distribution metrics."""
        print("\nCalculating metrics...")

        # Document metrics
        docs_with_entities = len(self.doc_to_entities)
        entities_per_doc = [len(entities) for entities in self.doc_to_entities.values()]

        # Entity metrics
        entities_with_docs = len(self.entity_to_docs)
        docs_per_entity = [len(docs) for docs in self.entity_to_docs.values()]

        # Coverage
        entities_in_forward = set()
        for doc_entities in self.doc_to_entities.values():
            entities_in_forward.update(doc_entities)

        entities_in_reverse = set(self.entity_to_docs.keys())

        # Entity UUID coverage
        entities_with_uuids = sum(
            1 for entity in entities_in_reverse
            if entity in self.entity_uuid_map
        )

        metrics = {
            "forward_index": {
                "total_documents": docs_with_entities,
                "total_entities_referenced": len(entities_in_forward),
                "avg_entities_per_doc": sum(entities_per_doc) / len(entities_per_doc) if entities_per_doc else 0,
                "min_entities_per_doc": min(entities_per_doc) if entities_per_doc else 0,
                "max_entities_per_doc": max(entities_per_doc) if entities_per_doc else 0
            },
            "reverse_index": {
                "total_entities": entities_with_docs,
                "total_documents_referenced": sum(len(docs) for docs in self.entity_to_docs.values()),
                "avg_docs_per_entity": sum(docs_per_entity) / len(docs_per_entity) if docs_per_entity else 0,
                "min_docs_per_entity": min(docs_per_entity) if docs_per_entity else 0,
                "max_docs_per_entity": max(docs_per_entity) if docs_per_entity else 0
            },
            "coverage": {
                "entities_in_forward_only": len(entities_in_forward - entities_in_reverse),
                "entities_in_reverse_only": len(entities_in_reverse - entities_in_forward),
                "entities_in_both": len(entities_in_forward & entities_in_reverse),
                "entities_with_uuids": entities_with_uuids,
                "uuid_coverage_pct": (entities_with_uuids / len(entities_in_reverse) * 100) if entities_in_reverse else 0
            }
        }

        return metrics

    def save_indices(self, metrics: Dict) -> None:
        """Save both indices to disk."""
        print("\nSaving indices...")

        # Save forward index: Document → Entities
        forward_output = {
            "metadata": {
                "generated_at": datetime.now().astimezone().isoformat(),
                "total_documents": len(self.doc_to_entities),
                "total_entities_referenced": metrics['forward_index']['total_entities_referenced'],
                "source_file": str(self.doc_entity_index_path.name)
            },
            "document_to_entities": self.doc_to_entities
        }

        with open(self.doc_to_entities_path, 'w', encoding='utf-8') as f:
            json.dump(forward_output, f, indent=2, ensure_ascii=False)

        print(f"✓ Saved forward index to {self.doc_to_entities_path}")

        # Save reverse index: Entity → Documents (convert sets to sorted lists)
        entity_to_docs_serializable = {
            entity: sorted(list(docs))
            for entity, docs in self.entity_to_docs.items()
        }

        reverse_output = {
            "metadata": {
                "generated_at": datetime.now().astimezone().isoformat(),
                "total_entities": len(self.entity_to_docs),
                "total_documents_referenced": metrics['reverse_index']['total_documents_referenced'],
                "source_file": str(self.doc_entities_full_path.name)
            },
            "entity_to_documents": entity_to_docs_serializable
        }

        with open(self.entity_to_docs_path, 'w', encoding='utf-8') as f:
            json.dump(reverse_output, f, indent=2, ensure_ascii=False)

        print(f"✓ Saved reverse index to {self.entity_to_docs_path}")

    def print_summary(self, metrics: Dict) -> None:
        """Print summary of indices built."""
        print("\n" + "="*70)
        print("DOCUMENT-ENTITY BIDIRECTIONAL INDEX SUMMARY")
        print("="*70)

        print("\n📄 FORWARD INDEX (Document → Entities)")
        print(f"  Total documents:             {metrics['forward_index']['total_documents']:,}")
        print(f"  Total entities referenced:   {metrics['forward_index']['total_entities_referenced']:,}")
        print(f"  Avg entities per document:   {metrics['forward_index']['avg_entities_per_doc']:.2f}")
        print(f"  Min entities per document:   {metrics['forward_index']['min_entities_per_doc']}")
        print(f"  Max entities per document:   {metrics['forward_index']['max_entities_per_doc']}")

        print("\n👤 REVERSE INDEX (Entity → Documents)")
        print(f"  Total entities:              {metrics['reverse_index']['total_entities']:,}")
        print(f"  Total documents referenced:  {metrics['reverse_index']['total_documents_referenced']:,}")
        print(f"  Avg documents per entity:    {metrics['reverse_index']['avg_docs_per_entity']:.2f}")
        print(f"  Min documents per entity:    {metrics['reverse_index']['min_docs_per_entity']}")
        print(f"  Max documents per entity:    {metrics['reverse_index']['max_docs_per_entity']}")

        print("\n🔍 COVERAGE ANALYSIS")
        print(f"  Entities in both indices:    {metrics['coverage']['entities_in_both']:,}")
        print(f"  Entities only in forward:    {metrics['coverage']['entities_in_forward_only']:,}")
        print(f"  Entities only in reverse:    {metrics['coverage']['entities_in_reverse_only']:,}")
        print(f"  Entities with UUIDs:         {metrics['coverage']['entities_with_uuids']:,} ({metrics['coverage']['uuid_coverage_pct']:.1f}%)")

        print("\n📁 OUTPUT FILES")
        print(f"  Forward index:  {self.doc_to_entities_path}")
        print(f"  Reverse index:  {self.entity_to_docs_path}")

        print("="*70)

    def build(self) -> None:
        """Execute full index building pipeline."""
        print("Starting Document-Entity Bidirectional Index Build")
        print("="*70)

        # Load entity UUIDs
        self.load_entity_uuids()

        # Build indices
        self.build_forward_index()
        self.build_reverse_index()

        # Calculate metrics
        metrics = self.calculate_metrics()

        # Save indices
        self.save_indices(metrics)

        # Print summary
        self.print_summary(metrics)


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent.parent

    builder = DocumentEntityIndexBuilder(project_root)
    builder.build()


if __name__ == "__main__":
    main()
