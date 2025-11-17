#!/usr/bin/env python3
"""
Entity-based document search
Search documents by entity mentions, document type, or keywords
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path("/Users/masa/Projects/Epstein")
DATA_DIR = PROJECT_ROOT / "data"
METADATA_DIR = DATA_DIR / "metadata"

class DocumentSearch:
    """Search engine for Epstein archive"""

    def __init__(self):
        """Load indexes"""
        print("Loading indexes...")

        # Load semantic index (entity -> documents)
        semantic_index_path = METADATA_DIR / "semantic_index.json"
        with open(semantic_index_path) as f:
            self.semantic_data = json.load(f)
            self.entity_to_docs = self.semantic_data.get("entity_to_documents", {})

        # Load classifications
        classifications_path = METADATA_DIR / "document_classifications.json"
        with open(classifications_path) as f:
            self.classifications = json.load(f).get("results", {})

        # Load entity network
        network_path = METADATA_DIR / "entity_network.json"
        with open(network_path) as f:
            self.network_data = json.load(f)
            self.entity_nodes = {n["id"]: n for n in self.network_data["nodes"]}

        print(f"  Loaded {len(self.entity_to_docs)} entities")
        print(f"  Loaded {len(self.classifications)} classified documents")

    def search_by_entity(self, entity_name: str) -> List[Dict]:
        """
        Find all documents mentioning an entity

        Args:
            entity_name: Name of entity to search for (case-insensitive)

        Returns:
            List of documents with metadata
        """
        entity_lower = entity_name.lower()

        # Find matching entity names
        matching_entities = [
            entity for entity in self.entity_to_docs.keys()
            if entity_lower in entity.lower()
        ]

        if not matching_entities:
            return []

        # Collect all documents
        results = []
        seen_docs = set()

        for entity in matching_entities:
            docs = self.entity_to_docs.get(entity, [])

            for doc_info in docs:
                doc_path = doc_info["document"]

                if doc_path in seen_docs:
                    continue

                seen_docs.add(doc_path)

                # Get classification
                classification = self.classifications.get(doc_path, {})

                results.append({
                    "document": doc_path,
                    "entity": entity,
                    "document_type": classification.get("type", "unknown"),
                    "confidence": classification.get("confidence", 0.0),
                    "entity_count": classification.get("entity_count", 0)
                })

        return results

    def search_by_type(self, doc_type: str) -> List[Dict]:
        """Find all documents of a specific type"""
        results = []

        for doc_path, classification in self.classifications.items():
            if classification["type"] == doc_type:
                results.append({
                    "document": doc_path,
                    "document_type": doc_type,
                    "confidence": classification["confidence"],
                    "entity_count": classification["entity_count"],
                    "entities": classification.get("entities_mentioned", [])[:10]
                })

        return results

    def find_connections(self, entity_name: str) -> Dict:
        """
        Find all connections for an entity

        Returns:
            Dictionary with entity info and connections
        """
        entity_lower = entity_name.lower()

        # Find matching entity in network
        matching_nodes = [
            node for node in self.entity_nodes.values()
            if entity_lower in node["name"].lower()
        ]

        if not matching_nodes:
            return {"error": "Entity not found in network"}

        node = matching_nodes[0]

        # Find edges
        edges = [
            edge for edge in self.network_data["edges"]
            if edge["source"] == node["id"] or edge["target"] == node["id"]
        ]

        # Sort by weight
        edges_sorted = sorted(edges, key=lambda e: e["weight"], reverse=True)

        return {
            "entity": node["name"],
            "in_black_book": node["in_black_book"],
            "is_billionaire": node["is_billionaire"],
            "flight_count": node["flight_count"],
            "connection_count": node["connection_count"],
            "top_connections": [
                {
                    "connected_to": edge["target"] if edge["source"] == node["id"] else edge["source"],
                    "flights_together": edge["weight"]
                }
                for edge in edges_sorted[:20]
            ]
        }

    def search_by_multiple_entities(self, entity_names: List[str]) -> List[Dict]:
        """
        Find documents mentioning multiple entities together

        Args:
            entity_names: List of entity names

        Returns:
            Documents mentioning ALL specified entities
        """
        # Get documents for each entity
        entity_docs = []
        for entity_name in entity_names:
            docs = self.search_by_entity(entity_name)
            doc_paths = {d["document"] for d in docs}
            entity_docs.append(doc_paths)

        # Find intersection
        if not entity_docs:
            return []

        common_docs = entity_docs[0]
        for doc_set in entity_docs[1:]:
            common_docs = common_docs.intersection(doc_set)

        # Build results
        results = []
        for doc_path in common_docs:
            classification = self.classifications.get(doc_path, {})
            results.append({
                "document": doc_path,
                "document_type": classification.get("type", "unknown"),
                "confidence": classification.get("confidence", 0.0),
                "entity_count": classification.get("entity_count", 0),
                "entities_mentioned": classification.get("entities_mentioned", [])[:20]
            })

        return results

def format_results(results: List[Dict], result_type: str = "entity"):
    """Format search results for display"""
    if not results:
        return "No results found."

    output = [
        "=" * 70,
        f"SEARCH RESULTS ({len(results)} documents)",
        "=" * 70,
        ""
    ]

    for i, result in enumerate(results, 1):
        doc_name = Path(result["document"]).name
        doc_type = result.get("document_type", "unknown")
        entity_count = result.get("entity_count", 0)

        if result_type == "entity":
            entity = result.get("entity", "")
            output.append(f"{i}. {doc_name}")
            output.append(f"   Entity: {entity}")
            output.append(f"   Type: {doc_type} | Entities: {entity_count}")
        elif result_type == "type":
            entities = result.get("entities", [])
            entities_str = ", ".join(entities[:5])
            output.append(f"{i}. {doc_name}")
            output.append(f"   Type: {doc_type}")
            output.append(f"   Top entities: {entities_str}")
        elif result_type == "multiple":
            entities = result.get("entities_mentioned", [])
            entities_str = ", ".join(entities[:8])
            output.append(f"{i}. {doc_name}")
            output.append(f"   Type: {doc_type} | Entities: {entity_count}")
            output.append(f"   Mentions: {entities_str}")

        output.append("")

    return "\n".join(output)

def main():
    """CLI interface for document search"""
    parser = argparse.ArgumentParser(description="Search Epstein document archive")
    parser.add_argument("--entity", "-e", help="Search by entity name")
    parser.add_argument("--type", "-t", help="Search by document type")
    parser.add_argument("--connections", "-c", help="Show entity connections")
    parser.add_argument("--multiple", "-m", nargs="+", help="Search for documents with multiple entities")

    args = parser.parse_args()

    search = DocumentSearch()

    if args.entity:
        print(f"\nSearching for entity: {args.entity}")
        results = search.search_by_entity(args.entity)
        print(format_results(results, "entity"))

    elif args.type:
        print(f"\nSearching for document type: {args.type}")
        results = search.search_by_type(args.type)
        print(format_results(results, "type"))

    elif args.connections:
        print(f"\nFinding connections for: {args.connections}")
        result = search.find_connections(args.connections)

        if "error" in result:
            print(result["error"])
        else:
            print(f"\nEntity: {result['entity']}")
            print(f"  Black Book: {result['in_black_book']}")
            print(f"  Billionaire: {result['is_billionaire']}")
            print(f"  Flight Count: {result['flight_count']}")
            print(f"  Total Connections: {result['connection_count']}")
            print("\nTop Connections:")
            for conn in result["top_connections"]:
                print(f"  - {conn['connected_to']:40s}: {conn['flights_together']} flights together")

    elif args.multiple:
        print(f"\nSearching for documents with: {', '.join(args.multiple)}")
        results = search.search_by_multiple_entities(args.multiple)
        print(format_results(results, "multiple"))

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
