#!/usr/bin/env python3
"""
Entity Statistics Report
Generates comprehensive statistics for each entity including:
- Documents they appear in
- Connection statistics
- Temporal analysis
- Category breakdowns
"""

import json
from collections import Counter
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path("/Users/masa/Projects/Epstein")
DATA_DIR = PROJECT_ROOT / "data"
MD_DIR = DATA_DIR / "md/entities"
METADATA_DIR = DATA_DIR / "metadata"

class EntityStatisticsGenerator:
    """Generate comprehensive entity statistics"""

    def __init__(self):
        """Initialize generator"""
        self.entities = []
        self.semantic_index = {}
        self.network_data = {}
        self.classifications = {}
        self.entity_stats = {}

    def load_data(self):
        """Load all necessary data"""
        print("Loading data...")

        # Load entities (use merged if available)
        merged_index = MD_DIR / "ENTITIES_INDEX_MERGED.json"
        entities_index = merged_index if merged_index.exists() else MD_DIR / "ENTITIES_INDEX.json"

        with open(entities_index) as f:
            entity_data = json.load(f)
            self.entities = entity_data.get("entities", entity_data)

        # Load semantic index
        with open(METADATA_DIR / "semantic_index.json") as f:
            self.semantic_index = json.load(f).get("entity_to_documents", {})

        # Load network
        with open(METADATA_DIR / "entity_network.json") as f:
            self.network_data = json.load(f)

        # Load classifications
        with open(METADATA_DIR / "document_classifications.json") as f:
            self.classifications = json.load(f).get("results", {})

        print(f"  Loaded {len(self.entities)} entities")
        print(f"  Loaded {len(self.semantic_index)} entity mentions")
        print(f"  Loaded {len(self.network_data.get('nodes', []))} network nodes")

    def generate_entity_statistics(self) -> Dict:
        """Generate statistics for each entity"""
        print("\nGenerating entity statistics...")

        stats = {}

        for entity in self.entities:
            name = entity.get("name", "")
            if not name:
                continue

            # Get documents mentioning this entity
            docs = self.get_entity_documents(name, entity.get("name_variations", [name]))

            # Get network connections
            network_node = self.get_network_node(name)
            connections = self.get_entity_connections(name)

            # Document type breakdown
            doc_types = self.get_document_type_breakdown(docs)

            # Calculate statistics
            entity_stat = {
                "name": name,
                "name_variations": entity.get("name_variations", [name]),
                "in_black_book": entity.get("in_black_book", False),
                "is_billionaire": entity.get("is_billionaire", False),
                "categories": entity.get("categories", []),
                "sources": entity.get("sources", []),

                # Document statistics
                "total_documents": len(docs),
                "document_types": doc_types,
                "documents": [
                    {
                        "path": d["document"],
                        "type": d.get("document_type", "unknown")
                    }
                    for d in docs
                ],

                # Network statistics
                "flight_count": entity.get("trips", 0),
                "connection_count": network_node.get("connection_count", 0) if network_node else 0,
                "top_connections": [
                    {
                        "name": conn["connected_to"],
                        "flights_together": conn["flights_together"]
                    }
                    for conn in connections[:10]
                ],

                # Flags
                "has_connections": (network_node.get("connection_count", 0) if network_node else 0) > 0,
                "appears_in_multiple_sources": len(entity.get("sources", [])) > 1
            }

            stats[name] = entity_stat

        self.entity_stats = stats
        return stats

    def get_entity_documents(self, canonical_name: str, name_variations: List[str]) -> List[Dict]:
        """Get all documents mentioning an entity (any name variation)"""
        all_docs = []
        seen = set()

        for name in name_variations:
            name_lower = name.lower()

            # Search in semantic index
            for entity_key, docs in self.semantic_index.items():
                if name_lower in entity_key.lower() or entity_key.lower() in name_lower:
                    for doc in docs:
                        doc_path = doc["document"]
                        if doc_path not in seen:
                            seen.add(doc_path)
                            all_docs.append(doc)

        return all_docs

    def get_network_node(self, name: str) -> Dict:
        """Get network node for entity"""
        for node in self.network_data.get("nodes", []):
            if node["id"].lower() == name.lower():
                return node
        return {}

    def get_entity_connections(self, name: str) -> List[Dict]:
        """Get entity's top connections"""
        connections = []

        for edge in self.network_data.get("edges", []):
            if edge["source"].lower() == name.lower():
                connections.append({
                    "connected_to": edge["target"],
                    "flights_together": edge["weight"]
                })
            elif edge["target"].lower() == name.lower():
                connections.append({
                    "connected_to": edge["source"],
                    "flights_together": edge["weight"]
                })

        # Sort by flight count
        connections.sort(key=lambda x: x["flights_together"], reverse=True)
        return connections

    def get_document_type_breakdown(self, docs: List[Dict]) -> Dict:
        """Get breakdown of document types"""
        type_counts = Counter()

        for doc in docs:
            doc_type = doc.get("document_type", "unknown")
            type_counts[doc_type] += 1

        return dict(type_counts)

    def export_statistics(self, output_path: Path):
        """Export statistics to JSON"""
        output_data = {
            "generated": "2025-11-17T00:10:00",
            "total_entities": len(self.entity_stats),
            "statistics": self.entity_stats
        }

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        print(f"\n✓ Exported statistics: {output_path}")

    def generate_summary_report(self) -> str:
        """Generate human-readable summary"""
        # Top entities by document mentions
        top_by_docs = sorted(
            self.entity_stats.values(),
            key=lambda x: x["total_documents"],
            reverse=True
        )[:20]

        # Top entities by connections
        top_by_connections = sorted(
            self.entity_stats.values(),
            key=lambda x: x["connection_count"],
            reverse=True
        )[:20]

        # Billionaires with most documents
        billionaires = [e for e in self.entity_stats.values() if e["is_billionaire"]]
        top_billionaires = sorted(billionaires, key=lambda x: x["total_documents"], reverse=True)[:10]

        report = [
            "=" * 70,
            "ENTITY STATISTICS SUMMARY",
            "=" * 70,
            "",
            f"Total entities: {len(self.entity_stats)}",
            f"Entities in documents: {sum(1 for e in self.entity_stats.values() if e['total_documents'] > 0)}",
            f"Entities with connections: {sum(1 for e in self.entity_stats.values() if e['has_connections'])}",
            f"Billionaires: {len(billionaires)}",
            "",
            "TOP 20 ENTITIES BY DOCUMENT MENTIONS:",
            "-" * 70
        ]

        for i, entity in enumerate(top_by_docs, 1):
            flags = []
            if entity["is_billionaire"]:
                flags.append("💰")
            if entity["in_black_book"]:
                flags.append("📖")
            if entity["connection_count"] > 50:
                flags.append(f"🔗{entity['connection_count']}")

            flags_str = " ".join(flags)
            doc_types = ", ".join(f"{t}:{c}" for t, c in entity["document_types"].items())

            report.append(f"{i:2d}. {entity['name']:35s} {flags_str}")
            report.append(f"    Documents: {entity['total_documents']:3d} ({doc_types})")

        report.extend([
            "",
            "TOP 20 MOST CONNECTED ENTITIES:",
            "-" * 70
        ])

        for i, entity in enumerate(top_by_connections, 1):
            flags = []
            if entity["is_billionaire"]:
                flags.append("💰")
            if entity["flight_count"] > 100:
                flags.append(f"✈️{entity['flight_count']}")

            flags_str = " ".join(flags)

            # Top connection
            top_conn = entity["top_connections"][0] if entity["top_connections"] else None
            conn_str = f"(top: {top_conn['name']} - {top_conn['flights_together']} flights)" if top_conn else ""

            report.append(f"{i:2d}. {entity['name']:35s} {flags_str}")
            report.append(f"    Connections: {entity['connection_count']:3d} {conn_str}")

        report.extend([
            "",
            "TOP 10 BILLIONAIRES BY DOCUMENT MENTIONS:",
            "-" * 70
        ])

        for i, entity in enumerate(top_billionaires, 1):
            doc_types = ", ".join(f"{t}:{c}" for t, c in entity["document_types"].items())
            report.append(f"{i:2d}. {entity['name']:35s}: {entity['total_documents']:3d} docs ({doc_types})")

        return "\n".join(report)

def main():
    """Generate entity statistics"""
    print("=" * 70)
    print("ENTITY STATISTICS GENERATOR")
    print("=" * 70)

    generator = EntityStatisticsGenerator()
    generator.load_data()
    generator.generate_entity_statistics()

    # Export JSON
    stats_path = METADATA_DIR / "entity_statistics.json"
    generator.export_statistics(stats_path)

    # Generate summary report
    summary = generator.generate_summary_report()
    summary_path = METADATA_DIR / "entity_statistics_summary.txt"
    summary_path.write_text(summary)

    print(f"✓ Saved summary: {summary_path}")
    print("\n" + summary)

    print("\n" + "=" * 70)
    print("STATISTICS GENERATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
