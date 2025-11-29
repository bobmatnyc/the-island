#!/usr/bin/env python3
"""
Web Relationship Finder

Uses web search to discover familial and business relationships for entities.
This is designed to be integrated with the main enrichment script.
"""

import logging
import re


logger = logging.getLogger(__name__)


class WebRelationshipFinder:
    """Find entity relationships using web search."""

    # Relationship keywords to look for in search results
    RELATIONSHIP_KEYWORDS = {
        "spouse": ["wife", "husband", "spouse", "married to", "married"],
        "child_of": ["son of", "daughter of", "child of", "children of"],
        "parent_of": ["father of", "mother of", "parent of"],
        "sibling_of": ["brother of", "sister of", "sibling of"],
        "business_partner": ["partner", "co-founder", "business partner", "founded with"],
        "employee": ["works for", "employed by", "employee of", "worked for"],
        "associate": ["associate", "associated with", "linked to", "connected to"],
    }

    def __init__(self, use_live_search: bool = False):
        """
        Initialize the relationship finder.

        Args:
            use_live_search: If True, use live web search (requires API).
                           If False, use manual seed data only.
        """
        self.use_live_search = use_live_search
        self.search_cache = {}

        # Manual seed data for key entities (verified public knowledge)
        self.seed_relationships = self._load_seed_relationships()

    def _load_seed_relationships(self) -> dict[str, list[dict]]:
        """Load manually verified relationships for key entities."""
        return {
            # Core Epstein network
            "Jeffrey Epstein": [
                {
                    "related_entity": "Ghislaine Maxwell",
                    "relationship_type": "associate",
                    "description": "Long-time associate and alleged accomplice in trafficking",
                    "source_url": "https://en.wikipedia.org/wiki/Ghislaine_Maxwell",
                    "confidence": 0.99,
                },
            ],
            "Ghislaine Maxwell": [
                {
                    "related_entity": "Robert Maxwell",
                    "relationship_type": "child_of",
                    "description": "Daughter of British media tycoon Robert Maxwell (9th of 9 children)",
                    "source_url": "https://en.wikipedia.org/wiki/Ghislaine_Maxwell",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Elisabeth Meynard",
                    "relationship_type": "child_of",
                    "description": "Daughter of Elisabeth Meynard (French-born scholar, Huguenot descent)",
                    "source_url": "https://en.wikipedia.org/wiki/Ghislaine_Maxwell",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Christine Maxwell",
                    "relationship_type": "sibling_of",
                    "description": "Sister of Christine Maxwell",
                    "source_url": "https://en.wikipedia.org/wiki/Christine_Maxwell",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Isabel Maxwell",
                    "relationship_type": "sibling_of",
                    "description": "Twin sister Isabel Maxwell",
                    "source_url": "https://en.wikipedia.org/wiki/Ghislaine_Maxwell",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Ian Maxwell",
                    "relationship_type": "sibling_of",
                    "description": "Brother Ian Maxwell",
                    "source_url": "https://en.wikipedia.org/wiki/Ghislaine_Maxwell",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Kevin Maxwell",
                    "relationship_type": "sibling_of",
                    "description": "Brother Kevin Maxwell",
                    "source_url": "https://en.wikipedia.org/wiki/Ghislaine_Maxwell",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Jeffrey Epstein",
                    "relationship_type": "associate",
                    "description": "Long-time associate of Jeffrey Epstein",
                    "source_url": "https://en.wikipedia.org/wiki/Ghislaine_Maxwell",
                    "confidence": 0.99,
                },
            ],
            # Political figures
            "Bill Clinton": [
                {
                    "related_entity": "Hillary Clinton",
                    "relationship_type": "spouse",
                    "description": "42nd President of the United States, married to Hillary Clinton",
                    "source_url": "https://en.wikipedia.org/wiki/Bill_Clinton",
                    "confidence": 1.0,
                },
            ],
            "Donald Trump": [
                {
                    "related_entity": "Melania Trump",
                    "relationship_type": "spouse",
                    "description": "45th President of the United States, married to Melania Trump",
                    "source_url": "https://en.wikipedia.org/wiki/Donald_Trump",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Ivanka Trump",
                    "relationship_type": "parent_of",
                    "description": "Father of Ivanka Trump",
                    "source_url": "https://en.wikipedia.org/wiki/Donald_Trump",
                    "confidence": 1.0,
                },
            ],
            "Prince Andrew, Duke Of York": [  # Match entity index name
                {
                    "related_entity": "Queen Elizabeth II",
                    "relationship_type": "child_of",
                    "description": "Third child and second son of Queen Elizabeth II",
                    "source_url": "https://en.wikipedia.org/wiki/Prince_Andrew,_Duke_of_York",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Prince Philip",
                    "relationship_type": "child_of",
                    "description": "Son of Prince Philip, Duke of Edinburgh",
                    "source_url": "https://en.wikipedia.org/wiki/Prince_Andrew,_Duke_of_York",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "King Charles III",
                    "relationship_type": "sibling_of",
                    "description": "Younger brother of King Charles III",
                    "source_url": "https://en.wikipedia.org/wiki/Prince_Andrew,_Duke_of_York",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Sarah Ferguson",
                    "relationship_type": "spouse",
                    "description": "Married Sarah Ferguson 1986, divorced 1996",
                    "source_url": "https://en.wikipedia.org/wiki/Prince_Andrew,_Duke_of_York",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Princess Beatrice",
                    "relationship_type": "parent_of",
                    "description": "Father of Princess Beatrice (born August 8, 1988)",
                    "source_url": "https://en.wikipedia.org/wiki/Prince_Andrew,_Duke_of_York",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Princess Eugenie",
                    "relationship_type": "parent_of",
                    "description": "Father of Princess Eugenie (born March 23, 1990)",
                    "source_url": "https://en.wikipedia.org/wiki/Prince_Andrew,_Duke_of_York",
                    "confidence": 1.0,
                },
            ],
            "Prince Prince Andrew": [  # Alternative name from flight logs
                {
                    "related_entity": "Queen Elizabeth II",
                    "relationship_type": "child_of",
                    "description": "Third child and second son of Queen Elizabeth II",
                    "source_url": "https://en.wikipedia.org/wiki/Prince_Andrew,_Duke_of_York",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Prince Philip",
                    "relationship_type": "child_of",
                    "description": "Son of Prince Philip, Duke of Edinburgh",
                    "source_url": "https://en.wikipedia.org/wiki/Prince_Andrew,_Duke_of_York",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "King Charles III",
                    "relationship_type": "sibling_of",
                    "description": "Younger brother of King Charles III",
                    "source_url": "https://en.wikipedia.org/wiki/Prince_Andrew,_Duke_of_York",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Sarah Ferguson",
                    "relationship_type": "spouse",
                    "description": "Married Sarah Ferguson 1986, divorced 1996",
                    "source_url": "https://en.wikipedia.org/wiki/Prince_Andrew,_Duke_of_York",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Princess Beatrice",
                    "relationship_type": "parent_of",
                    "description": "Father of Princess Beatrice (born August 8, 1988)",
                    "source_url": "https://en.wikipedia.org/wiki/Prince_Andrew,_Duke_of_York",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Princess Eugenie",
                    "relationship_type": "parent_of",
                    "description": "Father of Princess Eugenie (born March 23, 1990)",
                    "source_url": "https://en.wikipedia.org/wiki/Prince_Andrew,_Duke_of_York",
                    "confidence": 1.0,
                },
            ],
            # Dubin family (known from flight logs)
            "Glenn Dubin": [
                {
                    "related_entity": "Eva Dubin",
                    "relationship_type": "spouse",
                    "description": "Hedge fund manager married to Eva Dubin",
                    "source_url": "https://en.wikipedia.org/wiki/Glenn_Dubin",
                    "confidence": 1.0,
                },
            ],
            "Eva Dubin": [
                {
                    "related_entity": "Glenn Dubin",
                    "relationship_type": "spouse",
                    "description": "Former Miss Sweden, married to Glenn Dubin",
                    "source_url": "https://en.wikipedia.org/wiki/Glenn_Dubin",
                    "confidence": 1.0,
                },
            ],
            # Other billionaires in network
            "Leon Black": [
                {
                    "related_entity": "Apollo Global Management",
                    "relationship_type": "business_partner",
                    "description": "Co-founder of Apollo Global Management",
                    "source_url": "https://en.wikipedia.org/wiki/Leon_Black",
                    "confidence": 1.0,
                },
            ],
            "Les Wexner": [  # Match entity index name
                {
                    "related_entity": "Abigail Wexner",
                    "relationship_type": "spouse",
                    "description": "Married Abigail S. Koppel on January 23, 1993",
                    "source_url": "https://en.wikipedia.org/wiki/Les_Wexner",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Sarah Wexner",
                    "relationship_type": "parent_of",
                    "description": "Father of Sarah Wexner",
                    "source_url": "https://en.wikipedia.org/wiki/Les_Wexner",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Harry Wexner",
                    "relationship_type": "parent_of",
                    "description": "Father of Harry Wexner",
                    "source_url": "https://en.wikipedia.org/wiki/Les_Wexner",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Hannah Wexner",
                    "relationship_type": "parent_of",
                    "description": "Father of Hannah Wexner",
                    "source_url": "https://en.wikipedia.org/wiki/Les_Wexner",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "David Wexner",
                    "relationship_type": "parent_of",
                    "description": "Father of David Wexner",
                    "source_url": "https://en.wikipedia.org/wiki/Les_Wexner",
                    "confidence": 1.0,
                },
            ],
            "Abigail Wexner": [
                {
                    "related_entity": "Leslie Wexner",
                    "relationship_type": "spouse",
                    "description": "Married Leslie Wexner on January 23, 1993 (attorney, CEO of Whitebarn Associates)",
                    "source_url": "https://en.wikipedia.org/wiki/Les_Wexner",
                    "confidence": 1.0,
                },
            ],
            # Maxwell family members
            "Christine Maxwell": [
                {
                    "related_entity": "Ghislaine Maxwell",
                    "relationship_type": "sibling_of",
                    "description": "Sister of Ghislaine Maxwell",
                    "source_url": "https://en.wikipedia.org/wiki/Christine_Maxwell",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Robert Maxwell",
                    "relationship_type": "child_of",
                    "description": "Daughter of Robert Maxwell",
                    "source_url": "https://en.wikipedia.org/wiki/Christine_Maxwell",
                    "confidence": 1.0,
                },
            ],
            "Isabel Maxwell": [
                {
                    "related_entity": "Ghislaine Maxwell",
                    "relationship_type": "sibling_of",
                    "description": "Twin sister of Ghislaine Maxwell",
                    "source_url": "https://en.wikipedia.org/wiki/Ghislaine_Maxwell",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Robert Maxwell",
                    "relationship_type": "child_of",
                    "description": "Daughter of Robert Maxwell",
                    "source_url": "https://en.wikipedia.org/wiki/Ghislaine_Maxwell",
                    "confidence": 1.0,
                },
            ],
            "Ian Maxwell": [
                {
                    "related_entity": "Ghislaine Maxwell",
                    "relationship_type": "sibling_of",
                    "description": "Brother of Ghislaine Maxwell",
                    "source_url": "https://en.wikipedia.org/wiki/Ghislaine_Maxwell",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Robert Maxwell",
                    "relationship_type": "child_of",
                    "description": "Son of Robert Maxwell",
                    "source_url": "https://en.wikipedia.org/wiki/Ghislaine_Maxwell",
                    "confidence": 1.0,
                },
            ],
            "Kevin Maxwell": [
                {
                    "related_entity": "Ghislaine Maxwell",
                    "relationship_type": "sibling_of",
                    "description": "Brother of Ghislaine Maxwell",
                    "source_url": "https://en.wikipedia.org/wiki/Ghislaine_Maxwell",
                    "confidence": 1.0,
                },
                {
                    "related_entity": "Robert Maxwell",
                    "relationship_type": "child_of",
                    "description": "Son of Robert Maxwell (charged with fraud 1992, acquitted 1996)",
                    "source_url": "https://en.wikipedia.org/wiki/Ghislaine_Maxwell",
                    "confidence": 1.0,
                },
            ],
            # Known victims/witnesses
            "Virginia Roberts": [
                {
                    "related_entity": "Virginia Giuffre",
                    "relationship_type": "associate",  # Same person, married name
                    "description": "Also known as Virginia Giuffre (married name)",
                    "source_url": "https://en.wikipedia.org/wiki/Virginia_Giuffre",
                    "confidence": 1.0,
                },
            ],
        }

    def normalize_entity_name(self, name: str) -> str:
        """
        Normalize entity names for matching.

        Handles variations like:
        - "Bill Bill Clinton" -> "Bill Clinton"
        - "Glenn       Glenn Dubin" -> "Glenn Dubin"
        """
        # Remove extra whitespace
        normalized = re.sub(r"\s+", " ", name).strip()

        # Handle duplicated first names (artifact from flight logs)
        parts = normalized.split()
        if len(parts) >= 2 and parts[0] == parts[1]:
            # "Bill Bill Clinton" -> "Bill Clinton"
            normalized = " ".join([parts[0], *parts[2:]])

        return normalized

    def find_relationships_web_search(self, entity_name: str) -> list[dict]:
        """
        Search web for entity relationships (LIVE SEARCH - PLACEHOLDER).

        This would integrate with WebSearch tool to find:
        1. Wikipedia infobox data (family, spouse, children)
        2. News articles mentioning relationships
        3. Corporate records (business partners, employees)

        Args:
            entity_name: Name to search for

        Returns:
            List of relationship dictionaries with web sources
        """
        if not self.use_live_search:
            logger.debug(f"Live search disabled for {entity_name}")
            return []

        # PLACEHOLDER: This is where WebSearch tool integration would go
        # Example query patterns:
        # - "{entity_name} wife husband spouse"
        # - "{entity_name} children family"
        # - "{entity_name} business partner"
        # - "{entity_name} wikipedia" (for structured data)

        logger.info(f"Live web search for {entity_name} (not implemented)")
        return []

    def find_relationships(self, entity_name: str) -> list[dict]:
        """
        Find all known relationships for an entity.

        Args:
            entity_name: Name to search for (will be normalized)

        Returns:
            List of relationship dictionaries
        """
        # Normalize name
        normalized_name = self.normalize_entity_name(entity_name)

        # Check cache
        if normalized_name in self.search_cache:
            logger.debug(f"Cache hit for {normalized_name}")
            return self.search_cache[normalized_name]

        relationships = []

        # 1. Check seed data (verified relationships)
        if normalized_name in self.seed_relationships:
            relationships.extend(self.seed_relationships[normalized_name])
            logger.debug(f"Found {len(relationships)} seed relationships for {normalized_name}")

        # Also check original (non-normalized) name
        if entity_name != normalized_name and entity_name in self.seed_relationships:
            relationships.extend(self.seed_relationships[entity_name])

        # 2. Optionally perform live web search
        if self.use_live_search:
            web_results = self.find_relationships_web_search(normalized_name)
            relationships.extend(web_results)

        # Cache results
        self.search_cache[normalized_name] = relationships

        return relationships

    def get_supported_entities(self) -> list[str]:
        """Get list of entities with known relationships."""
        return list(self.seed_relationships.keys())


# Standalone usage example
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    finder = WebRelationshipFinder(use_live_search=False)

    # Test entities
    test_entities = [
        "Jeffrey Epstein",
        "Ghislaine Maxwell",
        "Bill Clinton",
        "Glenn Dubin",
        "Eva         Eva Dubin",  # Test normalization
    ]

    print("=" * 80)
    print("WEB RELATIONSHIP FINDER - TEST MODE")
    print("=" * 80)
    print()

    for entity in test_entities:
        print(f"Entity: {entity}")
        print(f"Normalized: {finder.normalize_entity_name(entity)}")

        relationships = finder.find_relationships(entity)

        if relationships:
            print(f"Found {len(relationships)} relationships:")
            for rel in relationships:
                print(f"  • {rel['relationship_type']:15s} → {rel['related_entity']}")
                print(f"    {rel['description']}")
        else:
            print("  No relationships found")

        print()

    print("=" * 80)
    print(f"Total entities with known relationships: {len(finder.get_supported_entities())}")
    print("=" * 80)
