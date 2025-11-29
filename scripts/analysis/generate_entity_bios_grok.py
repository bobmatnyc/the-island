#!/usr/bin/env python3
"""
Entity Biography Generator using Grok-4.1-fast

Generates descriptive biographies for entities based on available source material.
Uses OpenRouter API to access x-ai/grok-4.1-fast:free model.

Design: docs/ENTITY_BIOGRAPHY_ENHANCEMENT_SYSTEM.md
Author: Entity Biography Enhancement System
Created: 2025-11-21
"""

import json
import os
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import requests
from pydantic import BaseModel, Field


class BiographyGenerationRequest(BaseModel):
    """Request structure for biography generation"""
    entity_id: str
    entity_name: str
    flight_count: int = 0
    connection_count: int = 0
    top_connections: List[str] = Field(default_factory=list)
    in_black_book: bool = False
    sources: List[str] = Field(default_factory=list)
    additional_context: Optional[str] = None


class BiographyGenerationResult(BaseModel):
    """Result structure for generated biography"""
    entity_id: str
    entity_name: str
    biography: str
    metadata: Dict
    success: bool
    error: Optional[str] = None


class GrokBiographyGenerator:
    """Biography generator using Grok-4.1-fast API via OpenRouter"""

    def __init__(self, api_key: str, dry_run: bool = False):
        """Initialize generator with OpenRouter API key"""
        self.api_key = api_key
        self.dry_run = dry_run
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "x-ai/grok-4.1-fast:free"

        # Statistics
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "total_tokens_used": 0,
            "total_api_calls": 0,
            "start_time": datetime.now().isoformat()
        }

    def build_context(self, entity_data: Dict) -> str:
        """Build rich context from entity data"""
        context_parts = []

        # Flight log context
        if entity_data.get("flight_count", 0) > 0:
            top_connections = entity_data.get('top_connections', [])
            if isinstance(top_connections, list) and len(top_connections) > 0:
                # Handle both dict and string formats
                if isinstance(top_connections[0], dict):
                    connection_names = [c.get('name', '') for c in top_connections[:10]]
                else:
                    connection_names = top_connections[:10]
            else:
                connection_names = []

            context_parts.append(
                f"Flight Logs:\n"
                f"- Total flights: {entity_data['flight_count']}\n"
                f"- Top co-passengers: {', '.join(connection_names) if connection_names else 'Unknown'}"
            )

        # Black book context
        if entity_data.get("in_black_book"):
            context_parts.append("Black Book: Listed in Epstein's contact book")

        # Network statistics
        context_parts.append(
            f"Network Statistics:\n"
            f"- Direct connections: {entity_data.get('connection_count', 0)}\n"
            f"- Document mentions: {entity_data.get('total_documents', 0)}\n"
            f"- Data sources: {', '.join(entity_data.get('sources', []))}"
        )

        return "\n\n".join(context_parts)

    def generate_biography(self, request: BiographyGenerationRequest) -> BiographyGenerationResult:
        """Generate biography for single entity"""

        if self.dry_run:
            # Update stats even in dry run
            self.stats["successful"] += 1
            self.stats["total_processed"] += 1

            return BiographyGenerationResult(
                entity_id=request.entity_id,
                entity_name=request.entity_name,
                biography=f"[DRY RUN] Biography would be generated for {request.entity_name}",
                metadata={
                    "dry_run": True,
                    "word_count": 10,
                    "quality_score": 0.0,
                    "generated_by": "grok-4.1-fast",
                    "generation_date": datetime.now(timezone.utc).isoformat()
                },
                success=True
            )

        # Build prompt
        context = self.build_context(request.model_dump())

        system_prompt = """You are an expert investigative journalist writing factual biographical summaries for a public interest archive about Jeffrey Epstein's network.

Your task is to generate concise, fact-based biographies focusing on:
- Verifiable information from source material
- Professional and factual tone
- Clear relationship to Jeffrey Epstein
- Timeline of involvement (when available)
- Avoiding speculation or unsubstantiated claims

Be precise, neutral, and encyclopedic in your writing."""

        user_prompt = f"""Entity: {request.entity_name}

{context}

Generate a biographical paragraph (150-300 words) for this entity based ONLY on the provided context. Focus on:
1. Their apparent role or relationship to Jeffrey Epstein
2. Timeframe of involvement (if determinable from flight dates)
3. Network position (connections, frequency of contact)
4. Observable patterns from the data
5. Public information if this is a known figure

Important constraints:
- Use ONLY information from the context provided
- Maintain a factual, investigative journalism tone
- Clearly distinguish documented facts from patterns/observations
- Avoid speculation beyond what the data shows
- If limited information is available, acknowledge this
- Be privacy-respecting, especially for potential victims

Output ONLY the biography paragraph, no additional commentary or preamble."""

        try:
            # Call OpenRouter API
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/epstein-archive",
                    "X-Title": "Epstein Archive Entity Bio Generator"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ],
                    "temperature": 0.3,  # Lower temperature for factual content
                    "max_tokens": 500
                },
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # Extract biography
            biography = result["choices"][0]["message"]["content"].strip()

            # Track usage
            usage = result.get("usage", {})
            self.stats["total_tokens_used"] += usage.get("total_tokens", 0)
            self.stats["total_api_calls"] += 1
            self.stats["successful"] += 1

            # Validate biography
            validation = self.validate_biography(biography, request.entity_name)

            return BiographyGenerationResult(
                entity_id=request.entity_id,
                entity_name=request.entity_name,
                biography=biography,
                metadata={
                    "generated_by": "grok-4.1-fast",
                    "generation_date": datetime.now(timezone.utc).isoformat(),
                    "source_material": request.sources,
                    "word_count": len(biography.split()),
                    "tokens_used": usage.get("total_tokens", 0),
                    "validation": validation,
                    "quality_score": validation.get("quality_score", 0.0),
                    "needs_web_enrichment": True
                },
                success=True
            )

        except requests.exceptions.RequestException as e:
            self.stats["failed"] += 1
            error_msg = f"API request failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = f"API error: {error_data.get('error', {}).get('message', str(e))}"
                except:
                    error_msg = f"API error (HTTP {e.response.status_code}): {str(e)}"

            return BiographyGenerationResult(
                entity_id=request.entity_id,
                entity_name=request.entity_name,
                biography="",
                metadata={},
                success=False,
                error=error_msg
            )

        except Exception as e:
            self.stats["failed"] += 1
            return BiographyGenerationResult(
                entity_id=request.entity_id,
                entity_name=request.entity_name,
                biography="",
                metadata={},
                success=False,
                error=f"Unexpected error: {str(e)}"
            )

        finally:
            # Increment total_processed counter for both success and failure cases
            if not self.dry_run:
                self.stats["total_processed"] += 1
                # Rate limiting: 1 second between requests to be conservative
                time.sleep(1.0)

    def validate_biography(self, bio: str, entity_name: str) -> Dict:
        """Validate generated biography quality"""

        issues = []
        warnings = []

        # Length check
        word_count = len(bio.split())
        if word_count < 50:
            issues.append(f"Too short: {word_count} words (min 50)")
        elif word_count > 500:
            warnings.append(f"Long biography: {word_count} words")

        # Entity name check (case-insensitive)
        if entity_name.lower() not in bio.lower():
            # Check if any part of the name appears
            name_parts = entity_name.lower().split()
            if not any(part in bio.lower() for part in name_parts if len(part) > 2):
                warnings.append(f"Entity name '{entity_name}' may not be mentioned")

        # Epstein mention check
        if "epstein" not in bio.lower():
            warnings.append("No explicit mention of Epstein relationship")

        # Speculation detection
        speculation_keywords = ["allegedly", "supposedly", "rumored", "believed to be", "may have"]
        speculation_count = sum(1 for kw in speculation_keywords if kw in bio.lower())
        if speculation_count > 3:
            warnings.append(f"High speculation count: {speculation_count} instances")

        # Vague language detection
        vague_terms = ["appears to", "seems to", "possibly", "might have", "could be"]
        vague_count = sum(1 for term in vague_terms if term in bio.lower())
        if vague_count > 3:
            warnings.append(f"Excessive vague language: {vague_count} instances")

        # Fact density check (dates, numbers, specific details)
        has_dates = bool(re.search(r'\b(19|20)\d{2}\b', bio))
        has_numbers = bool(re.search(r'\b\d+\b', bio))

        if not (has_dates or has_numbers):
            warnings.append("Low fact density: no dates or statistics")

        # Calculate quality score
        quality_score = 1.0 - (len(issues) * 0.2 + len(warnings) * 0.05)
        quality_score = max(0.0, min(1.0, quality_score))

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "quality_score": quality_score,
            "word_count": word_count,
            "has_dates": has_dates,
            "has_numbers": has_numbers,
            "speculation_count": speculation_count,
            "vague_language_count": vague_count
        }

    def batch_generate(
        self,
        entities: List[Dict],
        output_file: Path,
        checkpoint_every: int = 10
    ) -> Dict:
        """Generate biographies for batch of entities with checkpointing"""

        results = []
        checkpoint_file = output_file.parent / f"{output_file.stem}_checkpoint.json"

        print(f"\n{'='*70}")
        print(f"BATCH BIOGRAPHY GENERATION")
        print(f"{'='*70}")
        print(f"Total entities: {len(entities)}")
        print(f"Output file: {output_file}")
        print(f"Checkpoint interval: every {checkpoint_every} entities")
        print(f"Model: {self.model}")
        print(f"Dry run: {self.dry_run}")
        print(f"{'='*70}\n")

        for i, entity in enumerate(entities, 1):
            print(f"\n[{i}/{len(entities)}] Processing: {entity['name']}")

            request = BiographyGenerationRequest(
                entity_id=entity["id"],
                entity_name=entity["name"],
                flight_count=entity.get("flight_count", 0),
                connection_count=entity.get("connection_count", 0),
                top_connections=entity.get("top_connections", []),
                in_black_book=entity.get("in_black_book", False),
                sources=entity.get("sources", [])
            )

            result = self.generate_biography(request)
            results.append(result)

            if result.success:
                quality = result.metadata.get('quality_score', 0.0)
                word_count = result.metadata.get('word_count', 0)
                print(f"  ✓ Generated ({word_count} words, quality: {quality:.2f})")

                # Show validation warnings if any
                validation = result.metadata.get('validation', {})
                if validation.get('warnings'):
                    for warning in validation['warnings'][:2]:  # Show first 2 warnings
                        print(f"    ⚠ {warning}")
            else:
                print(f"  ✗ Failed: {result.error}")

            # Checkpoint progress
            if i % checkpoint_every == 0:
                self._save_checkpoint(results, checkpoint_file)
                print(f"  💾 Checkpoint saved ({i} entities processed)")

        # Final save
        print(f"\n{'='*70}")
        print(f"Saving final results...")
        self._save_results(results, output_file)

        # Remove checkpoint file after successful completion
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            print(f"Checkpoint file removed")

        return self.stats

    def _save_checkpoint(self, results: List[BiographyGenerationResult], checkpoint_file: Path):
        """Save intermediate checkpoint"""
        self._save_results(results, checkpoint_file)

    def _save_results(self, results: List[BiographyGenerationResult], output_file: Path):
        """Save results to file in entity_biographies.json format"""

        successful_results = [r for r in results if r.success]

        output_data = {
            "metadata": {
                "generated": datetime.now(timezone.utc).isoformat(),
                "generator": "grok-4.1-fast",
                "total_entities": len(successful_results),
                "successful": sum(1 for r in results if r.success),
                "failed": sum(1 for r in results if not r.success),
                "statistics": self.stats,
                "average_quality_score": sum(
                    r.metadata.get('quality_score', 0)
                    for r in successful_results
                ) / len(successful_results) if successful_results else 0.0,
                "average_word_count": sum(
                    r.metadata.get('word_count', 0)
                    for r in successful_results
                ) / len(successful_results) if successful_results else 0.0
            },
            "entities": {
                r.entity_id: {
                    "id": r.entity_id,
                    "display_name": r.entity_name,
                    "biography": r.biography,
                    "generated_by": r.metadata.get("generated_by"),
                    "generation_date": r.metadata.get("generation_date"),
                    "source_material": r.metadata.get("source_material", []),
                    "word_count": r.metadata.get("word_count"),
                    "quality_score": r.metadata.get("quality_score"),
                    "validation": r.metadata.get("validation")
                }
                for r in successful_results
            }
        }

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)


def load_entities(
    stats_file: Path,
    existing_bios_file: Path,
    min_connections: int = 0,
    min_flights: int = 0,
    tier: Optional[str] = None
) -> List[Dict]:
    """Load and filter entities based on criteria"""

    # Load entity statistics
    with open(stats_file) as f:
        stats_data = json.load(f)

    # Load existing biographies to skip
    existing_bios = set()
    if existing_bios_file.exists():
        with open(existing_bios_file) as f:
            bios_data = json.load(f)
            existing_bios = set(bios_data.get("entities", {}).keys())

    # Define tier criteria
    tier_criteria = {
        "1": {"min_connections": 15, "description": "Tier 1: High-value entities (15+ connections)"},
        "2": {"min_connections": 10, "description": "Tier 2: Medium-value entities (10+ connections)"},
        "3": {"min_connections": 5, "description": "Tier 3: Lower-value entities (5+ connections)"},
        "all": {"min_connections": 0, "description": "All entities"}
    }

    # Override min_connections if tier is specified
    if tier and tier in tier_criteria:
        min_connections = tier_criteria[tier]["min_connections"]
        print(f"\nUsing {tier_criteria[tier]['description']}")

    entities = []
    for entity_id, entity_data in stats_data["statistics"].items():
        # Skip if already has bio
        if entity_id in existing_bios:
            continue

        # Filter by connection count
        connection_count = entity_data.get("connection_count", 0)
        flight_count = entity_data.get("flight_count", 0)

        if connection_count < min_connections:
            continue

        if flight_count < min_flights:
            continue

        # Calculate priority score (connections weighted more heavily)
        priority_score = (connection_count * 2) + flight_count

        entities.append({
            **entity_data,
            "priority_score": priority_score
        })

    # Sort by priority score (highest first)
    entities.sort(key=lambda x: x["priority_score"], reverse=True)

    return entities


def backup_existing_file(file_path: Path):
    """Create timestamped backup of existing file"""
    if not file_path.exists():
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.parent / f"{file_path.stem}.backup_{timestamp}{file_path.suffix}"
    shutil.copy(file_path, backup_path)
    print(f"Backup created: {backup_path}")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate entity biographies using Grok-4.1-fast API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run with top 10 entities
  python3 generate_entity_bios_grok.py --dry-run --limit 10

  # Tier 1 entities (high-value, 15+ connections)
  python3 generate_entity_bios_grok.py --tier 1 --limit 75

  # Tier 2 entities (medium-value, 10+ connections)
  python3 generate_entity_bios_grok.py --tier 2 --limit 150

  # Custom criteria
  python3 generate_entity_bios_grok.py --min-connections 20 --min-flights 30 --limit 50

  # All entities without biographies
  python3 generate_entity_bios_grok.py --tier all --limit 1000
        """
    )

    parser.add_argument(
        "--api-key",
        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Maximum number of entities to process (default: 200)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run without making API calls"
    )
    parser.add_argument(
        "--min-connections",
        type=int,
        default=10,
        help="Minimum connection count (default: 10)"
    )
    parser.add_argument(
        "--min-flights",
        type=int,
        default=0,
        help="Minimum flight count (default: 0)"
    )
    parser.add_argument(
        "--tier",
        choices=["1", "2", "3", "all"],
        help="Entity tier: 1 (15+ connections), 2 (10+), 3 (5+), all (0+)"
    )
    parser.add_argument(
        "--output",
        default="data/metadata/entity_biographies_grok.json",
        help="Output file path (default: data/metadata/entity_biographies_grok.json)"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup before overwriting output file"
    )

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key and not args.dry_run:
        print("ERROR: API key required")
        print("Either:")
        print("  1. Set OPENROUTER_API_KEY environment variable")
        print("  2. Use --api-key argument")
        print("  3. Use --dry-run for testing")
        return 1

    # Define paths
    project_root = Path(__file__).parent.parent.parent
    stats_file = project_root / "data/metadata/entity_statistics.json"
    bios_file = project_root / "data/metadata/entity_biographies.json"

    # Handle both absolute and relative output paths
    output_path = Path(args.output)
    if output_path.is_absolute():
        output_file = output_path
    else:
        output_file = project_root / args.output

    # Verify input files exist
    if not stats_file.exists():
        print(f"ERROR: Entity statistics file not found: {stats_file}")
        return 1

    # Backup existing output if requested
    if args.backup and output_file.exists():
        backup_existing_file(output_file)

    # Load and filter entities
    print(f"\n{'='*70}")
    print(f"LOADING ENTITIES")
    print(f"{'='*70}")

    entities = load_entities(
        stats_file=stats_file,
        existing_bios_file=bios_file,
        min_connections=args.min_connections,
        min_flights=args.min_flights,
        tier=args.tier
    )

    # Apply limit
    if args.limit:
        entities = entities[:args.limit]

    if not entities:
        print("\nNo entities match the criteria.")
        print("Either all entities already have biographies or filters are too restrictive.")
        return 0

    print(f"\nTotal entities matching criteria: {len(entities)}")
    print(f"Output: {output_file}")

    if not args.dry_run:
        print(f"API: {api_key[:20]}..." if len(api_key) > 20 else "API: [key present]")
    else:
        print(f"Mode: DRY RUN (no API calls)")

    # Show top 5 entities
    print(f"\nTop 5 entities by priority:")
    for i, entity in enumerate(entities[:5], 1):
        print(f"  {i}. {entity['name']}")
        print(f"     Connections: {entity.get('connection_count', 0)}, "
              f"Flights: {entity.get('flight_count', 0)}, "
              f"Priority: {entity.get('priority_score', 0)}")

    # Generate biographies
    generator = GrokBiographyGenerator(api_key=api_key or "", dry_run=args.dry_run)
    stats = generator.batch_generate(
        entities=entities,
        output_file=output_file,
        checkpoint_every=10
    )

    # Print summary
    print(f"\n{'='*70}")
    print(f"GENERATION COMPLETE")
    print(f"{'='*70}")
    print(f"Total processed: {stats['total_processed']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Success rate: {(stats['successful'] / stats['total_processed'] * 100) if stats['total_processed'] > 0 else 0:.1f}%")

    if not args.dry_run:
        print(f"Total API calls: {stats['total_api_calls']}")
        print(f"Total tokens used: {stats['total_tokens_used']:,}")

        # Estimate cost (post-December 3, 2025 pricing)
        input_cost = (stats['total_tokens_used'] * 0.70) / 1_000_000 * 0.20  # Assume 70% input
        output_cost = (stats['total_tokens_used'] * 0.30) / 1_000_000 * 0.50  # Assume 30% output
        total_cost = input_cost + output_cost
        print(f"Estimated cost (post-Dec 3): ${total_cost:.4f}")
        print(f"  (Currently FREE until December 3, 2025)")

    print(f"\nOutput file: {output_file}")
    print(f"Start time: {stats['start_time']}")
    print(f"End time: {datetime.now().isoformat()}")

    return 0


if __name__ == "__main__":
    exit(main())
