#!/usr/bin/env python3
"""
Entity Relationship Enrichment System

Enhances entity network with web-researched familial and business relationships.
Every relationship includes strict source attribution (flight logs, documents, or web search).

Usage:
    python3 scripts/analysis/enrich_entity_relationships.py --top 50
    python3 scripts/analysis/enrich_entity_relationships.py --entity "Jeffrey Epstein"
    python3 scripts/analysis/enrich_entity_relationships.py --refresh-all
"""

import argparse
import json
import logging
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


# Import web relationship finder
sys.path.insert(0, str(Path(__file__).parent))
from web_relationship_finder import WebRelationshipFinder


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path("/Users/masa/Projects/Epstein")
ENTITIES_INDEX_PATH = PROJECT_ROOT / "data/md/entities/ENTITIES_INDEX.json"
ENTITY_NETWORK_PATH = PROJECT_ROOT / "data/metadata/entity_network.json"
SEMANTIC_INDEX_PATH = PROJECT_ROOT / "data/metadata/semantic_index.json"
OUTPUT_PATH = PROJECT_ROOT / "data/metadata/entity_relationships_enhanced.json"
REPORT_PATH = PROJECT_ROOT / "data/metadata/relationship_enrichment_report.txt"


@dataclass
class RelationshipSource:
    """Source attribution for a relationship."""
    type: str  # flight_log, document, web_search, semantic
    count: Optional[int] = None
    date_range: Optional[str] = None
    doc_ids: Optional[List[str]] = None
    url: Optional[str] = None
    description: Optional[str] = None
    confidence: float = 1.0


@dataclass
class EntityRelationship:
    """Relationship between two entities with full source attribution."""
    entity_a: str
    entity_b: str
    relationship_type: str  # associate, family, spouse, parent_of, child_of, sibling_of, employee, business_partner
    sources: List[RelationshipSource]
    confidence: float
    bidirectional: bool = True  # Most relationships are symmetric
    notes: Optional[str] = None


class EntityRelationshipEnricher:
    """Enriches entity relationships with web-researched data."""

    def __init__(self, use_live_search: bool = False):
        """Initialize the enricher with existing data."""
        self.entities_index = self._load_json(ENTITIES_INDEX_PATH)
        self.entity_network = self._load_json(ENTITY_NETWORK_PATH)
        self.semantic_index = self._load_json(SEMANTIC_INDEX_PATH)

        # Extract entity list and metadata
        self.entities = self.entities_index.get("entities", [])
        self.entity_map = {e["normalized_name"]: e for e in self.entities}

        # Network data
        self.network_nodes = {n["id"]: n for n in self.entity_network.get("nodes", [])}
        self.network_edges = self.entity_network.get("edges", [])

        # Relationship storage
        self.relationships: List[EntityRelationship] = []
        self.relationship_cache: Set[Tuple[str, str, str]] = set()  # (entity_a, entity_b, type)

        # Web search integration
        self.web_finder = WebRelationshipFinder(use_live_search=use_live_search)

        logger.info(f"Loaded {len(self.entities)} entities, {len(self.network_edges)} flight co-occurrences")

    def _load_json(self, path: Path) -> Dict:
        """Load JSON file."""
        if not path.exists():
            logger.warning(f"File not found: {path}")
            return {}
        with open(path) as f:
            return json.load(f)

    def _save_json(self, data: Dict, path: Path):
        """Save JSON file with pretty printing."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved to {path}")

    def _normalize_name(self, name: str) -> str:
        """Normalize entity name for matching."""
        # Remove extra whitespace
        normalized = re.sub(r"\s+", " ", name).strip()
        # Handle common name patterns
        normalized = normalized.replace("  ", " ")
        return normalized

    def _add_relationship(self, rel: EntityRelationship):
        """Add relationship if not duplicate."""
        # Create bidirectional key for symmetric relationships
        if rel.bidirectional:
            key = tuple(sorted([rel.entity_a, rel.entity_b]) + [rel.relationship_type])
        else:
            key = (rel.entity_a, rel.entity_b, rel.relationship_type)

        if key not in self.relationship_cache:
            self.relationships.append(rel)
            self.relationship_cache.add(key)
            return True
        return False

    def extract_flight_cooccurrences(self):
        """Extract relationships from flight logs."""
        logger.info("Extracting flight co-occurrence relationships...")

        # Group edges by entity pair
        cooccurrence_map = defaultdict(list)
        for edge in self.network_edges:
            source = edge.get("source")
            target = edge.get("target")
            weight = edge.get("weight", 1)

            if source and target:
                # Create sorted key for bidirectional matching
                key = tuple(sorted([source, target]))
                cooccurrence_map[key].append(weight)

        # Create relationships
        for (entity_a, entity_b), weights in cooccurrence_map.items():
            total_flights = sum(weights)

            source = RelationshipSource(
                type="flight_log",
                count=total_flights,
                date_range="1997-2005",  # Known range from flight logs
                confidence=0.95
            )

            rel = EntityRelationship(
                entity_a=entity_a,
                entity_b=entity_b,
                relationship_type="associate",
                sources=[source],
                confidence=0.95,
                bidirectional=True,
                notes=f"Co-occurred on {total_flights} flights in Epstein's flight logs"
            )

            self._add_relationship(rel)

        logger.info(f"Extracted {len(cooccurrence_map)} flight co-occurrence relationships")

    def get_top_entities_by_mentions(self, limit: int = 50) -> List[Dict]:
        """Get top entities by document mentions and flight count."""
        # Score entities by: flights * 10 + black_book_presence
        entity_scores = []

        for entity in self.entities:
            name = entity["normalized_name"]
            flights = entity.get("flights", 0)
            in_black_book = 1 if "black_book" in entity.get("sources", []) else 0
            is_billionaire = 1 if entity.get("is_billionaire", False) else 0

            # Score: prioritize flight activity and billionaire status
            score = (flights * 10) + (in_black_book * 5) + (is_billionaire * 20)

            entity_scores.append({
                "name": name,
                "score": score,
                "flights": flights,
                "in_black_book": in_black_book > 0,
                "is_billionaire": is_billionaire > 0,
                "entity": entity
            })

        # Sort by score descending
        entity_scores.sort(key=lambda x: x["score"], reverse=True)

        return entity_scores[:limit]

    def search_web_relationships(self, entity_name: str, relationship_types: List[str] = None) -> List[Dict]:
        """
        Search web for entity relationships using WebRelationshipFinder.

        Args:
            entity_name: Name to search for
            relationship_types: Types to search (spouse, child_of, etc.)

        Returns:
            List of relationship dictionaries with web sources
        """
        return self.web_finder.find_relationships(entity_name)

    def enrich_entity(self, entity_name: str):
        """Enrich a single entity with web-researched relationships."""
        logger.info(f"Enriching entity: {entity_name}")

        # Search for web relationships
        web_relations = self.search_web_relationships(entity_name)

        for rel_data in web_relations:
            related_entity = rel_data["related_entity"]
            rel_type = rel_data["relationship_type"]

            # Create source
            source = RelationshipSource(
                type="web_search",
                url=rel_data.get("source_url"),
                description=rel_data.get("description"),
                confidence=rel_data.get("confidence", 0.8)
            )

            # Determine if bidirectional
            bidirectional = rel_type in ["spouse", "sibling_of", "associate", "business_partner"]

            # Create relationship
            rel = EntityRelationship(
                entity_a=entity_name,
                entity_b=related_entity,
                relationship_type=rel_type,
                sources=[source],
                confidence=rel_data.get("confidence", 0.8),
                bidirectional=bidirectional,
                notes=rel_data.get("description")
            )

            self._add_relationship(rel)

    def merge_relationship_sources(self):
        """Merge relationships with multiple sources."""
        # Group relationships by (entity_a, entity_b, type)
        grouped = defaultdict(list)

        for rel in self.relationships:
            if rel.bidirectional:
                key = tuple(sorted([rel.entity_a, rel.entity_b]) + [rel.relationship_type])
            else:
                key = (rel.entity_a, rel.entity_b, rel.relationship_type)
            grouped[key].append(rel)

        # Merge sources for duplicate relationships
        merged_relationships = []
        for key, rels in grouped.items():
            if len(rels) == 1:
                merged_relationships.append(rels[0])
            else:
                # Merge sources
                base_rel = rels[0]
                all_sources = []
                for rel in rels:
                    all_sources.extend(rel.sources)

                # Calculate combined confidence (max of all sources)
                max_confidence = max(rel.confidence for rel in rels)

                merged_rel = EntityRelationship(
                    entity_a=base_rel.entity_a,
                    entity_b=base_rel.entity_b,
                    relationship_type=base_rel.relationship_type,
                    sources=all_sources,
                    confidence=max_confidence,
                    bidirectional=base_rel.bidirectional,
                    notes=base_rel.notes
                )
                merged_relationships.append(merged_rel)

        self.relationships = merged_relationships
        logger.info(f"Merged to {len(merged_relationships)} unique relationships")

    def generate_output(self):
        """Generate enhanced relationship JSON."""
        # Convert relationships to dict format
        relationships_data = []
        for rel in self.relationships:
            rel_dict = {
                "entity_a": rel.entity_a,
                "entity_b": rel.entity_b,
                "relationship_type": rel.relationship_type,
                "sources": [
                    {k: v for k, v in asdict(s).items() if v is not None}
                    for s in rel.sources
                ],
                "confidence": rel.confidence,
                "bidirectional": rel.bidirectional
            }
            if rel.notes:
                rel_dict["notes"] = rel.notes

            relationships_data.append(rel_dict)

        # Calculate statistics
        source_breakdown = Counter()
        relationship_type_breakdown = Counter()

        for rel in self.relationships:
            relationship_type_breakdown[rel.relationship_type] += 1
            for source in rel.sources:
                source_breakdown[source.type] += 1

        # Build output
        output = {
            "generated": datetime.now().isoformat(),
            "metadata": {
                "total_relationships": len(self.relationships),
                "relationship_types": dict(relationship_type_breakdown),
                "sources_breakdown": dict(source_breakdown),
                "entities_enriched": len(set(
                    [rel.entity_a for rel in self.relationships] +
                    [rel.entity_b for rel in self.relationships]
                ))
            },
            "relationships": relationships_data
        }

        self._save_json(output, OUTPUT_PATH)
        return output

    def generate_report(self, output_data: Dict):
        """Generate human-readable summary report."""
        metadata = output_data["metadata"]

        report_lines = [
            "=" * 80,
            "ENTITY RELATIONSHIP ENRICHMENT REPORT",
            "=" * 80,
            f"Generated: {output_data['generated']}",
            "",
            "SUMMARY",
            "-" * 80,
            f"Total Relationships: {metadata['total_relationships']:,}",
            f"Entities with Relationships: {metadata['entities_enriched']:,}",
            "",
            "RELATIONSHIP TYPES",
            "-" * 80,
        ]

        for rel_type, count in sorted(
            metadata["relationship_types"].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            report_lines.append(f"  {rel_type:20s}: {count:4,} relationships")

        report_lines.extend([
            "",
            "SOURCE BREAKDOWN",
            "-" * 80,
        ])

        for source_type, count in sorted(
            metadata["sources_breakdown"].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            report_lines.append(f"  {source_type:20s}: {count:4,} sources")

        # Sample relationships by type
        report_lines.extend([
            "",
            "SAMPLE RELATIONSHIPS",
            "-" * 80,
        ])

        # Group relationships by type for sampling
        rels_by_type = defaultdict(list)
        for rel in self.relationships:
            rels_by_type[rel.relationship_type].append(rel)

        for rel_type, rels in sorted(rels_by_type.items()):
            report_lines.append(f"\n{rel_type.upper()} ({len(rels)} total):")
            for rel in rels[:5]:  # Show top 5 per type
                sources_str = ", ".join([s.type for s in rel.sources])
                report_lines.append(
                    f"  • {rel.entity_a} ↔ {rel.entity_b} "
                    f"(sources: {sources_str}, confidence: {rel.confidence:.2f})"
                )

        report_lines.extend([
            "",
            "=" * 80,
            "END OF REPORT",
            "=" * 80,
        ])

        report_text = "\n".join(report_lines)

        # Save report
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(REPORT_PATH, "w") as f:
            f.write(report_text)

        logger.info(f"Report saved to {REPORT_PATH}")
        print(report_text)

    def run_enrichment(self, top_n: int = 50, entity_filter: Optional[str] = None):
        """Run full enrichment process."""
        logger.info("Starting entity relationship enrichment...")

        # Step 1: Extract flight co-occurrences
        self.extract_flight_cooccurrences()

        # Step 2: Get top entities or specific entity
        if entity_filter:
            entities_to_enrich = [
                {"name": entity_filter, "entity": self.entity_map.get(entity_filter)}
            ]
            if not entities_to_enrich[0]["entity"]:
                logger.error(f"Entity not found: {entity_filter}")
                return None
        else:
            top_entities = self.get_top_entities_by_mentions(top_n)
            entities_to_enrich = top_entities
            logger.info(f"Top {top_n} entities by activity:")
            for i, e in enumerate(top_entities[:10], 1):
                logger.info(
                    f"  {i:2d}. {e['name']:30s} "
                    f"(flights: {e['flights']:3d}, billionaire: {e['is_billionaire']})"
                )

        # Step 3: Enrich each entity with web research
        for i, entity_data in enumerate(entities_to_enrich, 1):
            entity_name = entity_data["name"]
            logger.info(f"[{i}/{len(entities_to_enrich)}] Enriching: {entity_name}")
            self.enrich_entity(entity_name)

            # Rate limiting for web searches (if we were actually calling web APIs)
            # time.sleep(0.5)

        # Step 4: Merge duplicate relationships
        self.merge_relationship_sources()

        # Step 5: Generate output
        output_data = self.generate_output()

        # Step 6: Generate report
        self.generate_report(output_data)

        logger.info("Enrichment complete!")
        return output_data


def main():
    parser = argparse.ArgumentParser(
        description="Enrich entity relationships with web-researched data"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=50,
        help="Number of top entities to enrich (default: 50)"
    )
    parser.add_argument(
        "--entity",
        type=str,
        help="Enrich specific entity by name"
    )
    parser.add_argument(
        "--refresh-all",
        action="store_true",
        help="Refresh all existing relationships"
    )

    args = parser.parse_args()

    enricher = EntityRelationshipEnricher()

    if args.refresh_all:
        enricher.run_enrichment(top_n=len(enricher.entities))
    elif args.entity:
        enricher.run_enrichment(entity_filter=args.entity)
    else:
        enricher.run_enrichment(top_n=args.top)


if __name__ == "__main__":
    main()
