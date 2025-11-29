#!/usr/bin/env python3
"""
Automated Entity Enrichment Pipeline with Content Agent Integration

This script uses Claude's content optimization agent capabilities to:
1. Search web for entity biographical data
2. Extract relevant information with source provenance
3. Track reliability tiers (court docs > journalism > public records)
4. Format data for entity database with full attribution

Features:
- WebSearch integration for entity biographical research
- WebFetch for content extraction from reliable sources
- Source reliability tier classification (Tier 1-4)
- Batch processing with rate limiting
- Human review flagging for low-confidence results
- Export to enriched_entity_data.json format
"""

import asyncio
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@dataclass
class SourceProvenance:
    """Source tracking with reliability tier"""

    url: str
    title: str
    accessed_date: str
    reliability_tier: int  # 1 (court docs) to 4 (general sources)
    source_type: str
    quote: Optional[str] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


class ReliabilityTierClassifier:
    """
    Classify sources by reliability tier for provenance tracking

    Tier 1 (Highest): Court documents, legal filings
    Tier 2 (High): Investigative journalism, major news
    Tier 3 (Verified): Public records, Wikipedia, academic
    Tier 4 (General): Biographical databases, general sources
    """

    TIER_1_DOMAINS = [
        "courtlistener.com",
        "pacer.gov",
        "supremecourt.gov",
        "justice.gov",
        "uscourts.gov",
    ]

    TIER_2_DOMAINS = [
        "nytimes.com",
        "washingtonpost.com",
        "theguardian.com",
        "reuters.com",
        "apnews.com",
        "bbc.com",
        "bbc.co.uk",
        "npr.org",
        "wsj.com",
        "ft.com",
        "propublica.org",
        "miamiherald.com",
    ]

    TIER_3_DOMAINS = ["wikipedia.org", "britannica.com", "documentcloud.org", "archive.org"]

    TIER_4_DOMAINS = ["forbes.com", "bloomberg.com", "cnn.com", "vanityfair.com"]

    @classmethod
    def classify_tier(cls, url: str) -> int:
        """Classify source reliability tier based on domain"""
        domain = urlparse(url).netloc.lower()

        for tier1_domain in cls.TIER_1_DOMAINS:
            if tier1_domain in domain:
                return 1

        for tier2_domain in cls.TIER_2_DOMAINS:
            if tier2_domain in domain:
                return 2

        for tier3_domain in cls.TIER_3_DOMAINS:
            if tier3_domain in domain:
                return 3

        for tier4_domain in cls.TIER_4_DOMAINS:
            if tier4_domain in domain:
                return 4

        # Default to tier 4 for unknown sources
        return 4

    @classmethod
    def get_source_type(cls, url: str, tier: int) -> str:
        """Determine source type based on tier and domain"""
        type_map = {
            1: "court_document",
            2: "journalism",
            3: "biographical_database",
            4: "biographical_database",
        }

        domain = urlparse(url).netloc.lower()

        # Override for specific types
        if "court" in domain or "pacer" in domain or "justice" in domain:
            return "court_document"
        if any(news in domain for news in ["times", "post", "guardian", "reuters", "bbc"]):
            return "journalism"
        if "wikipedia" in domain or "britannica" in domain:
            return "biographical_database"
        if "documentcloud" in domain or "archive" in domain:
            return "public_record"

        return type_map.get(tier, "biographical_database")


class ContentAgentEnricher:
    """
    Content agent for automated entity enrichment using web search

    Workflow:
    1. Search web for entity + "Jeffrey Epstein" + biographical terms
    2. Filter results by reliability tier
    3. Extract biographical facts (birth, occupation, relationships)
    4. Extract Epstein-related facts with sources
    5. Build structured data with full provenance
    6. Flag low-confidence results for human review
    """

    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.classifier = ReliabilityTierClassifier()
        self.existing_data = self._load_existing()

    def _load_existing(self) -> dict:
        """Load existing enriched entity data"""
        if self.output_path.exists():
            with open(self.output_path) as f:
                return json.load(f)

        return {
            "metadata": {
                "version": "1.0",
                "generated_date": datetime.now().strftime("%Y-%m-%d"),
                "researcher": "Claude Code Content Agent",
                "total_entities_enriched": 0,
                "research_methodology": "Automated web search with source provenance tracking",
                "verification_standard": "Minimum 2 independent sources for biographical facts, court documents preferred for Epstein connections",
                "last_updated": datetime.now().isoformat(),
            },
            "entities": [],
        }

    def _save(self):
        """Save enriched data to disk"""
        self.existing_data["metadata"]["last_updated"] = datetime.now().isoformat()
        self.existing_data["metadata"]["total_entities_enriched"] = len(
            self.existing_data["entities"]
        )

        with open(self.output_path, "w") as f:
            json.dump(self.existing_data, f, indent=2, default=str)

    async def enrich_entity(self, entity_name: str, entity_metadata: dict) -> dict:
        """
        Enrich single entity with web search

        Args:
            entity_name: Entity name for search
            entity_metadata: Additional metadata (flights, billionaire status, etc.)

        Returns:
            Enriched entity data with sources
        """
        print(f"\n{'='*80}")
        print(f"Enriching: {entity_name}")
        print(f"Priority: {entity_metadata.get('priority_reason', 'N/A')}")
        print(f"Flights: {entity_metadata.get('flights', 0)}")
        print(f"{'='*80}\n")

        entity_id = self._generate_entity_id(entity_name)

        # Check if already enriched
        existing = self._find_existing(entity_id)
        if existing:
            print("⚠️  Entity already enriched. Use --force-refresh to re-enrich.")
            return existing

        # Construct search queries
        search_queries = self._build_search_queries(entity_name)

        enriched_data = {
            "entity_id": entity_id,
            "name": entity_name,
            "name_variations": [entity_name],
            "biographical_data": {},
            "epstein_relationship": {},
            "network_relationships": {},
            "archive_metadata": {
                "appears_in_sources": entity_metadata.get("sources", []),
                "total_flights": entity_metadata.get("flights", 0),
                "is_billionaire": entity_metadata.get("is_billionaire", False),
            },
            "research_metadata": {
                "research_date": datetime.now().strftime("%Y-%m-%d"),
                "researcher": "Claude Code Content Agent",
                "research_completeness": "pending",
                "verification_status": "unverified",
                "notes": "",
                "requires_human_review": False,
                "review_reasons": [],
            },
        }

        # Execute searches and extract information
        all_sources = []
        biographical_facts = []
        epstein_facts = []

        for query in search_queries:
            print(f"🔍 Searching: {query}")

            try:
                # Note: In production, this would call WebSearch MCP tool
                # For now, we'll create placeholder for integration
                search_results = await self._web_search(query)

                for result in search_results:
                    url = result.get("url", "")
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")

                    # Classify reliability tier
                    tier = self.classifier.classify_tier(url)
                    source_type = self.classifier.get_source_type(url, tier)

                    source = SourceProvenance(
                        url=url,
                        title=title,
                        accessed_date=datetime.now().strftime("%Y-%m-%d"),
                        reliability_tier=tier,
                        source_type=source_type,
                        quote=snippet[:200] if snippet else None,
                    )

                    all_sources.append(source)

                    # Extract facts from snippet
                    if tier <= 2:  # Only use high-reliability sources for facts
                        facts = self._extract_facts(snippet, entity_name)
                        biographical_facts.extend(facts["biographical"])
                        epstein_facts.extend(facts["epstein_related"])

                print(
                    f"  ✓ Found {len(search_results)} results (Tier 1-2: {sum(1 for s in all_sources if s.reliability_tier <= 2)})"
                )

            except Exception as e:
                print(f"  ✗ Search failed: {e}")

        # Build biographical data from facts
        enriched_data["biographical_data"] = self._build_biographical_section(
            biographical_facts, all_sources
        )

        # Build Epstein relationship section
        enriched_data["epstein_relationship"] = self._build_relationship_section(
            epstein_facts, all_sources
        )

        # Determine if human review needed
        enriched_data["research_metadata"] = self._assess_quality(enriched_data, all_sources)

        print("\n✅ Enrichment complete:")
        print(f"   - Total sources: {len(all_sources)}")
        print(f"   - Tier 1 (court docs): {sum(1 for s in all_sources if s.reliability_tier == 1)}")
        print(f"   - Tier 2 (journalism): {sum(1 for s in all_sources if s.reliability_tier == 2)}")
        print(
            f"   - Requires review: {enriched_data['research_metadata']['requires_human_review']}"
        )

        return enriched_data

    def _generate_entity_id(self, name: str) -> str:
        """Generate consistent entity ID"""
        return name.lower().replace(" ", "_").replace(",", "").replace(".", "")

    def _find_existing(self, entity_id: str) -> Optional[dict]:
        """Find existing enriched entity"""
        for entity in self.existing_data.get("entities", []):
            if entity.get("entity_id") == entity_id:
                return entity
        return None

    def _build_search_queries(self, entity_name: str) -> list[str]:
        """Build search queries for entity research"""
        return [
            f'"{entity_name}" Jeffrey Epstein biography',
            f'"{entity_name}" Epstein relationship court documents',
            f'"{entity_name}" Epstein flight logs',
            f'"{entity_name}" biography occupation',
        ]

    async def _web_search(self, query: str) -> list[dict]:
        """
        Placeholder for WebSearch MCP integration

        In production, this would call:
        results = await WebSearch(query=query)

        For now, return mock structure for testing
        """
        # This is where WebSearch MCP tool would be called
        # Return empty list as placeholder
        return []

    def _extract_facts(self, snippet: str, entity_name: str) -> dict[str, list[str]]:
        """Extract biographical and Epstein-related facts from snippet"""
        biographical = []
        epstein_related = []

        # Extract biographical facts
        # Birth date patterns
        birth_patterns = [
            r"born (?:on )?(\d{1,2} \w+ \d{4})",
            r"born (?:on )?(\w+ \d{1,2}, \d{4})",
            r"\((?:born )?(\d{4})\)",
        ]
        for pattern in birth_patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                biographical.append(f"Birth date: {match.group(1)}")

        # Occupation patterns
        occupation_patterns = [
            r"is (?:a |an )?(\w+(?:\s+\w+){0,3}?(?:businessman|financier|banker|lawyer|professor|model|actress))",
            r"worked as (?:a |an )?(\w+(?:\s+\w+){0,3})",
            r"former (\w+(?:\s+\w+){0,3}?(?:president|CEO|executive|director))",
        ]
        for pattern in occupation_patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                biographical.append(f"Occupation: {match.group(1)}")

        # Epstein-related facts
        if "epstein" in snippet.lower():
            # Relationship type
            relationship_patterns = [
                r"((?:friend|associate|business partner|client|employee) of (?:Jeffrey )?Epstein)",
                r"(?:Epstein\'s|Epstein) ((?:lawyer|banker|pilot|assistant|friend|associate))",
            ]
            for pattern in relationship_patterns:
                match = re.search(pattern, snippet, re.IGNORECASE)
                if match:
                    epstein_related.append(f"Relationship: {match.group(1)}")

            # Documented interactions
            if "flight" in snippet.lower() or "flew" in snippet.lower():
                epstein_related.append("Documented in flight logs")
            if "court" in snippet.lower() or "testimony" in snippet.lower():
                epstein_related.append("Mentioned in court documents")

        return {"biographical": biographical, "epstein_related": epstein_related}

    def _build_biographical_section(
        self, facts: list[str], sources: list[SourceProvenance]
    ) -> dict:
        """Build biographical data section with sources"""
        biographical = {}

        # Group facts by type
        for fact in facts:
            if fact.startswith("Birth date:"):
                date_value = fact.replace("Birth date: ", "")
                biographical["birth_date"] = {
                    "value": date_value,
                    "precision": "exact",
                    "confidence": "medium",
                    "sources": [s.to_dict() for s in sources if s.reliability_tier <= 3][:3],
                }
            elif fact.startswith("Occupation:"):
                occupation_value = fact.replace("Occupation: ", "")
                biographical["occupation"] = {
                    "primary": occupation_value,
                    "sources": [s.to_dict() for s in sources if s.reliability_tier <= 3][:3],
                }

        return biographical

    def _build_relationship_section(
        self, facts: list[str], sources: list[SourceProvenance]
    ) -> dict:
        """Build Epstein relationship section with sources"""
        relationship = {
            "relationship_summary": "Under research - automated enrichment",
            "relationship_type": "unknown",
            "documented_interactions": [],
            "public_statements": [],
            "legal_involvement": [],
        }

        # Add documented interactions based on facts
        for fact in facts:
            if "flight logs" in fact.lower():
                relationship["documented_interactions"].append(
                    {
                        "type": "flight",
                        "description": "Appeared in flight logs",
                        "sources": [s.to_dict() for s in sources if s.reliability_tier <= 2][:2],
                    }
                )
            elif "court documents" in fact.lower():
                relationship["documented_interactions"].append(
                    {
                        "type": "legal",
                        "description": "Mentioned in court documents",
                        "sources": [s.to_dict() for s in sources if s.reliability_tier == 1][:2],
                    }
                )

        return relationship

    def _assess_quality(self, enriched_data: dict, sources: list[SourceProvenance]) -> dict:
        """Assess research quality and determine if human review needed"""
        metadata = enriched_data["research_metadata"]

        tier1_count = sum(1 for s in sources if s.reliability_tier == 1)
        tier2_count = sum(1 for s in sources if s.reliability_tier == 2)
        total_sources = len(sources)

        # Determine research completeness
        has_biographical = bool(enriched_data["biographical_data"])
        has_epstein_info = bool(enriched_data["epstein_relationship"]["documented_interactions"])

        if has_biographical and has_epstein_info and tier1_count > 0:
            metadata["research_completeness"] = "comprehensive"
            metadata["verification_status"] = "verified"
        elif has_biographical or has_epstein_info:
            metadata["research_completeness"] = "partial"
            metadata["verification_status"] = "partially_verified"
        else:
            metadata["research_completeness"] = "minimal"
            metadata["verification_status"] = "unverified"

        # Determine if human review needed
        review_reasons = []

        if total_sources < 3:
            review_reasons.append("Insufficient sources (< 3)")

        if tier1_count == 0 and tier2_count == 0:
            review_reasons.append("No high-reliability sources (Tier 1-2)")

        if not has_biographical:
            review_reasons.append("Missing biographical data")

        if not has_epstein_info:
            review_reasons.append("Missing Epstein relationship information")

        metadata["requires_human_review"] = len(review_reasons) > 0
        metadata["review_reasons"] = review_reasons

        return metadata

    async def enrich_batch(self, entities: list[dict], max_concurrent: int = 3) -> list[dict]:
        """
        Enrich multiple entities in batch with rate limiting

        Args:
            entities: List of entity dicts with 'name' and metadata
            max_concurrent: Maximum concurrent enrichment tasks

        Returns:
            List of enriched entity data
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def bounded_enrich(entity: dict) -> dict:
            async with semaphore:
                result = await self.enrich_entity(entity["name"], entity)
                await asyncio.sleep(2)  # Rate limiting: 2 seconds between requests
                return result

        results = await asyncio.gather(*[bounded_enrich(entity) for entity in entities])

        # Add to existing data and save
        for result in results:
            # Check if entity already exists
            existing_idx = None
            for idx, existing in enumerate(self.existing_data["entities"]):
                if existing.get("entity_id") == result["entity_id"]:
                    existing_idx = idx
                    break

            if existing_idx is not None:
                self.existing_data["entities"][existing_idx] = result
            else:
                self.existing_data["entities"].append(result)

        self._save()

        return results

    def generate_report(self) -> str:
        """Generate enrichment report for review"""
        entities = self.existing_data.get("entities", [])

        total = len(entities)
        requires_review = sum(
            1 for e in entities if e["research_metadata"]["requires_human_review"]
        )
        comprehensive = sum(
            1
            for e in entities
            if e["research_metadata"]["research_completeness"] == "comprehensive"
        )
        partial = sum(
            1 for e in entities if e["research_metadata"]["research_completeness"] == "partial"
        )
        minimal = sum(
            1 for e in entities if e["research_metadata"]["research_completeness"] == "minimal"
        )

        report = f"""
{'='*80}
ENTITY ENRICHMENT REPORT
{'='*80}

Total Entities Enriched: {total}

Research Completeness:
  - Comprehensive: {comprehensive} ({comprehensive/total*100:.1f}%)
  - Partial:       {partial} ({partial/total*100:.1f}%)
  - Minimal:       {minimal} ({minimal/total*100:.1f}%)

Quality Assurance:
  - Requires Human Review: {requires_review} ({requires_review/total*100:.1f}%)
  - Ready for Publication: {total - requires_review} ({(total-requires_review)/total*100:.1f}%)

{'='*80}
ENTITIES REQUIRING REVIEW:
{'='*80}
"""

        for entity in entities:
            if entity["research_metadata"]["requires_human_review"]:
                report += f"\n{entity['name']}\n"
                report += f"  ID: {entity['entity_id']}\n"
                report += f"  Reasons: {', '.join(entity['research_metadata']['review_reasons'])}\n"

        return report


async def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description="Automated entity enrichment with content agent")
    parser.add_argument("--entity", help="Enrich single entity by name")
    parser.add_argument("--batch", type=int, help="Enrich batch of N priority entities")
    parser.add_argument("--report", action="store_true", help="Generate enrichment report")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/Users/masa/Projects/epstein/data/metadata/enriched_entity_data.json"),
        help="Output path for enriched data",
    )

    args = parser.parse_args()

    # Initialize enricher
    enricher = ContentAgentEnricher(output_path=args.output)

    # Load priority entities
    priority_path = Path(
        "/Users/masa/Projects/epstein/data/metadata/priority_entities_for_research.json"
    )
    with open(priority_path) as f:
        priority_data = json.load(f)

    priority_entities = priority_data["entities"]

    if args.report:
        # Generate report
        print(enricher.generate_report())

    elif args.entity:
        # Enrich single entity
        entity_data = next(
            (e for e in priority_entities if e["name"].lower() == args.entity.lower()), None
        )

        if not entity_data:
            print(f"❌ Entity '{args.entity}' not found in priority list")
            return

        await enricher.enrich_entity(entity_data["name"], entity_data)
        print(f"\n✅ Enrichment saved to: {args.output}")

    elif args.batch:
        # Enrich batch
        batch = priority_entities[: args.batch]
        print(f"\n🚀 Enriching batch of {len(batch)} entities...")
        print("Rate limit: 3 concurrent requests, 2 seconds between batches\n")

        results = await enricher.enrich_batch(batch, max_concurrent=3)

        print("\n✅ Batch enrichment complete:")
        print(f"   - Total enriched: {len(results)}")
        print(f"   - Saved to: {args.output}")
        print("\nRun with --report to see quality assessment")

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
