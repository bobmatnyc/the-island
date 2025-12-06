#!/usr/bin/env python3
"""
Semantic Classification Derivation for Entities

Derives entity classifications using:
1. Biography keyword matching (for persons)
2. Document context analysis (document types entities appear in)
3. Relationship keyword patterns from classification_rules.json

Output: entity_classifications_derived.json with confidence scores and evidence.

Part of Issue #21: Fix Data Relationships (M3: Relationships milestone)
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, Counter
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EntityClassificationDeriver:
    """Derive semantic classifications for entities from multiple sources."""

    def __init__(self, data_dir: Path):
        """Initialize with paths to data files.

        Args:
            data_dir: Path to project data directory
        """
        self.data_dir = data_dir
        self.schemas_dir = data_dir / "schemas"
        self.transformed_dir = data_dir / "transformed"

        # Load reference data
        self.taxonomy = self._load_json(self.schemas_dir / "entity_classifications.json")
        self.rules = self._load_json(self.schemas_dir / "classification_rules.json")
        self.doc_classifications = self._load_json(
            self.transformed_dir / "document_classifications.json"
        )

        # Load entity data
        self.persons = self._load_json(self.transformed_dir / "entities_persons.json")
        self.locations = self._load_json(self.transformed_dir / "entities_locations.json")
        self.organizations = self._load_json(self.transformed_dir / "entities_organizations.json")
        self.entity_to_docs = self._load_json(self.transformed_dir / "entity_to_documents.json")

        # Build lookup structures
        self._build_classification_lookup()
        self._build_document_type_index()

    def _load_json(self, path: Path) -> Dict:
        """Load JSON file with error handling."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"File not found: {path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {path}: {e}")
            raise

    def _build_classification_lookup(self) -> None:
        """Build fast lookup structures from taxonomy and rules."""
        self.classification_types = {}
        self.classification_applies_to = defaultdict(list)

        # Index taxonomy
        for category, cat_data in self.taxonomy["categories"].items():
            for cls in cat_data["classifications"]:
                cls_type = cls["type"]
                self.classification_types[cls_type] = {
                    "category": category,
                    "label": cls["label"],
                    "priority": cls["priority"],
                    "applies_to": cls["applies_to"],
                    "description": cls["description"]
                }

                # Index by entity type
                for entity_type in cls["applies_to"]:
                    self.classification_applies_to[entity_type].append(cls_type)

        # Index rules keywords (case-insensitive)
        self.classification_keywords = {}
        self.classification_context_keywords = {}
        self.classification_exclusions = {}
        self.classification_thresholds = {}

        for cls_type, rule in self.rules["classification_rules"].items():
            # Primary keywords
            self.classification_keywords[cls_type] = [
                kw.lower() for kw in rule.get("keywords", [])
            ]

            # Context keywords
            self.classification_context_keywords[cls_type] = [
                kw.lower() for kw in rule.get("context_keywords", [])
            ]

            # Exclusion keywords
            self.classification_exclusions[cls_type] = [
                kw.lower() for kw in rule.get("exclusions", [])
            ]

            # Confidence thresholds
            self.classification_thresholds[cls_type] = rule.get(
                "confidence_threshold",
                {"high": 0.8, "medium": 0.6, "low": 0.4}
            )

    def _build_document_type_index(self) -> None:
        """Build index of document types from document_classifications.json."""
        self.doc_type_map = {}

        for doc in self.doc_classifications.get("documents", []):
            doc_id = doc.get("id")
            doc_type = doc.get("new_classification")
            if doc_id and doc_type:
                self.doc_type_map[doc_id] = doc_type

        logger.info(f"Indexed {len(self.doc_type_map)} document type classifications")

    def _keyword_match_score(
        self,
        text: str,
        cls_type: str,
        include_context: bool = True
    ) -> Tuple[float, List[str]]:
        """Score text against classification keywords.

        Args:
            text: Text to analyze (biography, document content, etc.)
            cls_type: Classification type to check
            include_context: Whether to include context keywords

        Returns:
            Tuple of (score 0.0-1.0, matched_keywords)
        """
        if not text:
            return 0.0, []

        text_lower = text.lower()

        # Check exclusions first
        exclusions = self.classification_exclusions.get(cls_type, [])
        for exclusion in exclusions:
            if exclusion in text_lower:
                return 0.0, []  # Excluded

        # Primary keywords
        primary_keywords = self.classification_keywords.get(cls_type, [])
        primary_matches = [kw for kw in primary_keywords if kw in text_lower]

        # Context keywords (if enabled)
        context_matches = []
        if include_context:
            context_keywords = self.classification_context_keywords.get(cls_type, [])
            context_matches = [kw for kw in context_keywords if kw in text_lower]

        # Calculate score
        total_keywords = len(primary_keywords)
        if total_keywords == 0:
            return 0.0, []

        # Weight: primary keywords = 1.0, context keywords = 0.5
        primary_score = len(primary_matches) / total_keywords
        context_score = len(context_matches) / max(len(context_keywords), 1) * 0.5 if include_context else 0

        combined_score = min(primary_score + context_score, 1.0)
        matched_keywords = primary_matches + context_matches

        return combined_score, matched_keywords

    def _classify_from_biography(
        self,
        entity_id: str,
        biography: str,
        entity_type: str
    ) -> List[Dict]:
        """Derive classifications from entity biography.

        Args:
            entity_id: UUID of entity
            biography: Biography text
            entity_type: person/location/organization

        Returns:
            List of classification dictionaries
        """
        if not biography or biography.strip() == "":
            return []

        classifications = []

        # Get applicable classification types for this entity type
        applicable_types = self.classification_applies_to.get(entity_type, [])

        for cls_type in applicable_types:
            # Skip if not in rules
            if cls_type not in self.classification_keywords:
                continue

            score, matched_keywords = self._keyword_match_score(
                biography, cls_type, include_context=True
            )

            if score == 0:
                continue

            # Determine confidence level
            thresholds = self.classification_thresholds[cls_type]
            if score >= thresholds["high"]:
                confidence = score
                confidence_label = "high"
            elif score >= thresholds["medium"]:
                confidence = score
                confidence_label = "medium"
            elif score >= thresholds["low"]:
                confidence = score
                confidence_label = "low"
            else:
                continue  # Below minimum threshold

            # Extract evidence snippet
            evidence = self._extract_evidence_snippet(biography, matched_keywords)

            cls_info = self.classification_types[cls_type]
            classifications.append({
                "classification_id": cls_type,
                "category": cls_info["category"],
                "label": cls_info["label"],
                "confidence": round(confidence, 3),
                "confidence_label": confidence_label,
                "source": "biography",
                "evidence": evidence,
                "keywords_matched": matched_keywords[:5]  # Limit to 5 keywords
            })

        return classifications

    def _classify_from_documents(
        self,
        entity_id: str,
        entity_name: str,
        entity_type: str
    ) -> List[Dict]:
        """Derive classifications from document context.

        Args:
            entity_id: UUID of entity
            entity_name: Canonical or normalized name for lookup
            entity_type: person/location/organization

        Returns:
            List of classification dictionaries
        """
        # Get documents this entity appears in
        # Try multiple name formats: original (space-separated), canonical, normalized
        entity_to_docs_map = self.entity_to_docs.get("entity_to_documents", {})

        # Convert normalized_name (underscore) to space-separated for lookup
        lookup_names = [
            entity_name,  # Original
            entity_name.replace('_', ' '),  # underscore to space
            entity_name.lower(),  # lowercase
            entity_name.replace('_', ' ').lower()  # both
        ]

        doc_ids = []
        for name in lookup_names:
            if name in entity_to_docs_map:
                doc_ids = entity_to_docs_map[name]
                break

        if not doc_ids:
            return []

        # Count document types
        doc_type_counts = Counter()
        for doc_id in doc_ids:
            doc_type = self.doc_type_map.get(doc_id)
            if doc_type:
                doc_type_counts[doc_type] += 1

        if not doc_type_counts:
            return []

        classifications = []

        # Document type → classification mapping
        doc_type_to_classification = {
            "court_record": ["witnesses", "legal_professionals", "plaintiffs", "defendants"],
            "court_filing": ["witnesses", "legal_professionals", "plaintiffs", "defendants"],
            "fbi_report": ["investigators", "witnesses", "co_conspirators"],
            "flight_log": ["frequent_travelers", "social_contacts"],
            "contact_directory": ["social_contacts"],
            "email": ["associates", "social_contacts"],
            "deposition": ["witnesses", "plaintiffs", "defendants"],
        }

        # Get applicable classification types for this entity type
        applicable_types = self.classification_applies_to.get(entity_type, [])

        # Aggregate scores by classification type
        cls_scores = defaultdict(lambda: {"count": 0, "doc_types": []})

        for doc_type, count in doc_type_counts.items():
            potential_classes = doc_type_to_classification.get(doc_type, [])

            for cls_type in potential_classes:
                if cls_type in applicable_types:
                    cls_scores[cls_type]["count"] += count
                    cls_scores[cls_type]["doc_types"].append(doc_type)

        # Calculate confidence from document frequency
        total_docs = len(doc_ids)

        for cls_type, data in cls_scores.items():
            count = data["count"]
            doc_types = data["doc_types"]

            # Base confidence from proportion of documents
            base_confidence = min(count / total_docs, 0.8)  # Cap at 0.8 for document-based

            # Boost if multiple document types support same classification
            if len(set(doc_types)) > 1:
                base_confidence = min(base_confidence + 0.1, 0.9)

            # Apply minimum threshold
            thresholds = self.classification_thresholds.get(
                cls_type,
                {"high": 0.8, "medium": 0.6, "low": 0.4}
            )

            if base_confidence >= thresholds["low"]:
                if base_confidence >= thresholds["high"]:
                    confidence_label = "high"
                elif base_confidence >= thresholds["medium"]:
                    confidence_label = "medium"
                else:
                    confidence_label = "low"

                cls_info = self.classification_types[cls_type]
                classifications.append({
                    "classification_id": cls_type,
                    "category": cls_info["category"],
                    "label": cls_info["label"],
                    "confidence": round(base_confidence, 3),
                    "confidence_label": confidence_label,
                    "source": "document_context",
                    "evidence": f"Appears in {count} documents of types: {', '.join(set(doc_types))}",
                    "document_count": count,
                    "document_types": list(set(doc_types))
                })

        return classifications

    def _extract_evidence_snippet(
        self,
        text: str,
        keywords: List[str],
        max_length: int = 200
    ) -> str:
        """Extract relevant text snippet containing keywords.

        Args:
            text: Full text
            keywords: Keywords to search for
            max_length: Maximum snippet length

        Returns:
            Relevant text snippet
        """
        if not text or not keywords:
            return ""

        text_lower = text.lower()

        # Find first keyword occurrence
        best_pos = -1
        for keyword in keywords:
            pos = text_lower.find(keyword.lower())
            if pos != -1 and (best_pos == -1 or pos < best_pos):
                best_pos = pos

        if best_pos == -1:
            return text[:max_length] + "..."

        # Extract context around keyword
        start = max(0, best_pos - 50)
        end = min(len(text), best_pos + max_length - 50)

        snippet = text[start:end].strip()

        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        return snippet

    def _merge_classifications(
        self,
        bio_classifications: List[Dict],
        doc_classifications: List[Dict]
    ) -> List[Dict]:
        """Merge and deduplicate classifications from different sources.

        Args:
            bio_classifications: Classifications from biography
            doc_classifications: Classifications from documents

        Returns:
            Merged and sorted classifications
        """
        # Index by classification_id
        merged = {}

        for cls in bio_classifications:
            cls_id = cls["classification_id"]
            merged[cls_id] = cls

        for cls in doc_classifications:
            cls_id = cls["classification_id"]

            if cls_id in merged:
                # Merge: take higher confidence, combine evidence
                existing = merged[cls_id]

                if cls["confidence"] > existing["confidence"]:
                    # Use higher confidence but note multiple sources
                    cls["source"] = "biography+document_context"
                    cls["evidence"] = f"Biography: {existing['evidence'][:100]}... | Documents: {cls['evidence']}"
                    merged[cls_id] = cls
                else:
                    existing["source"] = "biography+document_context"
                    existing["evidence"] = f"Biography: {existing['evidence'][:100]}... | Documents: {cls['evidence']}"
            else:
                merged[cls_id] = cls

        # Sort by confidence (descending), then priority (ascending)
        sorted_classifications = sorted(
            merged.values(),
            key=lambda x: (-x["confidence"], self.classification_types[x["classification_id"]]["priority"])
        )

        return sorted_classifications

    def derive_entity_classifications(self, entity_data: Dict, entity_type: str) -> Dict:
        """Derive classifications for a single entity.

        Args:
            entity_data: Entity dictionary from entities_*.json
            entity_type: person/location/organization

        Returns:
            Entity with derived classifications
        """
        entity_id = entity_data["entity_id"]
        canonical_name = entity_data.get("canonical_name", "")
        normalized_name = entity_data.get("normalized_name", "")
        biography = entity_data.get("biography", "")

        # Derive from biography
        bio_classifications = []
        if biography and biography.strip():
            bio_classifications = self._classify_from_biography(
                entity_id, biography, entity_type
            )

        # Derive from document context
        # Try multiple name variations to match entity_to_documents.json keys
        doc_classifications = []
        name_variations = set()

        if canonical_name:
            name_variations.add(canonical_name)
            name_variations.add(canonical_name.lower())

        if normalized_name:
            name_variations.add(normalized_name)
            name_variations.add(normalized_name.replace('_', ' '))
            name_variations.add(normalized_name.replace('_', ' ').lower())

        # Also try aliases if available
        for alias in entity_data.get("aliases", []):
            if alias:
                name_variations.add(alias)
                name_variations.add(alias.lower())

        for name in name_variations:
            if name:
                doc_cls = self._classify_from_documents(entity_id, name, entity_type)
                doc_classifications.extend(doc_cls)

        # Deduplicate document classifications
        doc_cls_by_id = {}
        for cls in doc_classifications:
            cls_id = cls["classification_id"]
            if cls_id not in doc_cls_by_id or cls["confidence"] > doc_cls_by_id[cls_id]["confidence"]:
                doc_cls_by_id[cls_id] = cls
        doc_classifications = list(doc_cls_by_id.values())

        # Merge classifications
        merged_classifications = self._merge_classifications(
            bio_classifications, doc_classifications
        )

        # If no classifications found, add "peripheral" if entity appears in documents
        if not merged_classifications:
            doc_ids = self.entity_to_docs.get("entity_to_documents", {}).get(normalized_name, [])
            if doc_ids:
                cls_info = self.classification_types.get("peripheral")
                if cls_info and entity_type in cls_info["applies_to"]:
                    merged_classifications.append({
                        "classification_id": "peripheral",
                        "category": cls_info["category"],
                        "label": cls_info["label"],
                        "confidence": 0.3,
                        "confidence_label": "low",
                        "source": "default",
                        "evidence": f"Mentioned in {len(doc_ids)} documents with no specific role identified"
                    })

        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "canonical_name": canonical_name,
            "classifications": merged_classifications
        }

    def derive_all_classifications(self) -> Dict:
        """Derive classifications for all entities.

        Returns:
            Full output dictionary
        """
        logger.info("Starting entity classification derivation...")

        all_entities = {}
        stats = {
            "total_entities": 0,
            "classified_entities": 0,
            "by_type": {
                "person": {"total": 0, "classified": 0},
                "location": {"total": 0, "classified": 0},
                "organization": {"total": 0, "classified": 0}
            },
            "by_source": {
                "biography": 0,
                "document_context": 0,
                "biography+document_context": 0,
                "default": 0
            },
            "by_confidence": {
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }

        # Process persons (with biographies)
        logger.info("Processing persons...")
        for entity_id, entity_data in self.persons.get("entities", {}).items():
            result = self.derive_entity_classifications(entity_data, "person")
            all_entities[entity_id] = result

            stats["total_entities"] += 1
            stats["by_type"]["person"]["total"] += 1

            if result["classifications"]:
                stats["classified_entities"] += 1
                stats["by_type"]["person"]["classified"] += 1

                # Track sources and confidence
                for cls in result["classifications"]:
                    source = cls["source"]
                    stats["by_source"][source] = stats["by_source"].get(source, 0) + 1

                    confidence_label = cls["confidence_label"]
                    stats["by_confidence"][confidence_label] += 1

        # Process locations (no biographies, document context only)
        logger.info("Processing locations...")
        for entity_id, entity_data in self.locations.get("entities", {}).items():
            result = self.derive_entity_classifications(entity_data, "location")
            all_entities[entity_id] = result

            stats["total_entities"] += 1
            stats["by_type"]["location"]["total"] += 1

            if result["classifications"]:
                stats["classified_entities"] += 1
                stats["by_type"]["location"]["classified"] += 1

                for cls in result["classifications"]:
                    source = cls["source"]
                    stats["by_source"][source] = stats["by_source"].get(source, 0) + 1

                    confidence_label = cls["confidence_label"]
                    stats["by_confidence"][confidence_label] += 1

        # Process organizations (no biographies, document context only)
        logger.info("Processing organizations...")
        for entity_id, entity_data in self.organizations.get("entities", {}).items():
            result = self.derive_entity_classifications(entity_data, "organization")
            all_entities[entity_id] = result

            stats["total_entities"] += 1
            stats["by_type"]["organization"]["total"] += 1

            if result["classifications"]:
                stats["classified_entities"] += 1
                stats["by_type"]["organization"]["classified"] += 1

                for cls in result["classifications"]:
                    source = cls["source"]
                    stats["by_source"][source] = stats["by_source"].get(source, 0) + 1

                    confidence_label = cls["confidence_label"]
                    stats["by_confidence"][confidence_label] += 1

        # Calculate coverage percentage
        coverage = (stats["classified_entities"] / stats["total_entities"] * 100) if stats["total_entities"] > 0 else 0

        logger.info(f"Classification complete: {stats['classified_entities']}/{stats['total_entities']} entities classified ({coverage:.1f}%)")

        return {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_entities": stats["total_entities"],
                "classified_entities": stats["classified_entities"],
                "classification_coverage": f"{coverage:.2f}%",
                "method": "semantic_derivation",
                "version": "1.0.0"
            },
            "statistics": stats,
            "entities": all_entities
        }


def main():
    """Main entry point."""
    # Setup paths
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    output_path = data_dir / "transformed" / "entity_classifications_derived.json"

    logger.info(f"Project root: {project_root}")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Output path: {output_path}")

    # Initialize deriver
    deriver = EntityClassificationDeriver(data_dir)

    # Derive classifications
    result = deriver.derive_all_classifications()

    # Write output
    logger.info(f"Writing results to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "="*60)
    print("ENTITY CLASSIFICATION DERIVATION COMPLETE")
    print("="*60)
    print(f"Total entities processed: {result['metadata']['total_entities']}")
    print(f"Entities classified: {result['metadata']['classified_entities']}")
    print(f"Coverage: {result['metadata']['classification_coverage']}")
    print("\nBy entity type:")
    for entity_type, stats in result['statistics']['by_type'].items():
        coverage = (stats['classified'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  {entity_type}: {stats['classified']}/{stats['total']} ({coverage:.1f}%)")
    print("\nBy source:")
    for source, count in result['statistics']['by_source'].items():
        print(f"  {source}: {count}")
    print("\nBy confidence:")
    for level, count in result['statistics']['by_confidence'].items():
        print(f"  {level}: {count}")
    print(f"\nOutput written to: {output_path}")
    print("="*60)


if __name__ == "__main__":
    main()
