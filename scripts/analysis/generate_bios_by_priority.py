#!/usr/bin/env python3
"""
Priority-Based Biography Generation Strategy

Intelligently processes 1,637 entities in order of importance based on:
- Document mentions (most important)
- Multiple data sources
- Network connections
- Flight log presence
- Black Book listings

Author: Entity Biography Enhancement System
Created: 2025-11-24
Design: docs/1M-184-BIO-ENRICHMENT-PLAN.md
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Define priority tiers
TIER_DEFINITIONS = {
    1: {
        "name": "High Priority (Immediate)",
        "description": "Document mentions ≥ 2 OR multiple sources",
        "criteria": lambda e: e["total_documents"] >= 2 or len(e["sources"]) > 2,
        "expected_count": "~81 entities",
        "estimated_time": "~8 minutes",
        "rationale": "Primary subjects with substantial evidence"
    },
    2: {
        "name": "Medium-High Priority (Short Term)",
        "description": "Flight logs OR network connections OR 1 document mention",
        "criteria": lambda e: (
            e["flight_count"] > 0 or
            e["connection_count"] > 0 or
            e["total_documents"] == 1
        ),
        "expected_count": "~263 entities",
        "estimated_time": "~26 minutes",
        "rationale": "Direct evidence of involvement or proximity"
    },
    3: {
        "name": "Medium Priority (Medium Term)",
        "description": "Black Book + 1 other source",
        "criteria": lambda e: (
            e["in_black_book"] and
            len(e["sources"]) == 2
        ),
        "expected_count": "~293 entities",
        "estimated_time": "~30 minutes",
        "rationale": "Contact book entries with corroborating evidence"
    },
    4: {
        "name": "Low Priority (Long Term)",
        "description": "Black Book only (single source)",
        "criteria": lambda e: (
            e["in_black_book"] and
            len(e["sources"]) == 1 and
            e["total_documents"] == 0 and
            e["flight_count"] == 0 and
            e["connection_count"] == 0
        ),
        "expected_count": "~1,000 entities",
        "estimated_time": "~100 minutes (batch across sessions)",
        "rationale": "Address book contacts with minimal evidence"
    }
}


def load_entity_statistics() -> Dict:
    """Load entity statistics from JSON file"""
    stats_file = Path("data/metadata/entity_statistics.json")

    if not stats_file.exists():
        print(f"ERROR: Entity statistics file not found: {stats_file}")
        sys.exit(1)

    with open(stats_file) as f:
        data = json.load(f)

    return data.get("statistics", {})


def get_existing_biographies() -> set:
    """Get set of entity IDs that already have biographies"""
    db_path = Path("data/metadata/entities.db")

    if not db_path.exists():
        print(f"WARNING: Database not found: {db_path}")
        return set()

    db = sqlite3.connect(db_path)
    cursor = db.cursor()

    # Get entities with biographies
    cursor.execute("SELECT entity_id FROM entity_biographies")
    existing_bios = {row[0] for row in cursor.fetchall()}

    db.close()

    return existing_bios


def classify_entity_tier(entity_data: Dict) -> int:
    """Classify entity into priority tier (1=highest, 4=lowest)"""

    # Check tiers in order (highest to lowest priority)
    for tier_num in [1, 2, 3, 4]:
        tier = TIER_DEFINITIONS[tier_num]
        if tier["criteria"](entity_data):
            return tier_num

    # Default to tier 4 if no criteria match
    return 4


def calculate_priority_score(entity_data: Dict, tier: int) -> float:
    """Calculate fine-grained priority score within tier"""

    # Base score from tier (higher tier = higher base score)
    base_score = (5 - tier) * 1000

    # Add weights for various factors
    doc_weight = entity_data.get("total_documents", 0) * 100
    source_weight = len(entity_data.get("sources", [])) * 50
    connection_weight = entity_data.get("connection_count", 0) * 10
    flight_weight = entity_data.get("flight_count", 0) * 5

    # Billionaire bonus (notable figures get priority)
    billionaire_bonus = 200 if entity_data.get("is_billionaire", False) else 0

    # Multiple sources bonus
    multi_source_bonus = 100 if len(entity_data.get("sources", [])) > 1 else 0

    total_score = (
        base_score +
        doc_weight +
        source_weight +
        connection_weight +
        flight_weight +
        billionaire_bonus +
        multi_source_bonus
    )

    return total_score


def get_entities_by_tier(
    tier: int,
    stats: Dict,
    existing_bios: set,
    limit: int = None
) -> List[Tuple[str, Dict]]:
    """Get entities for specific priority tier"""

    entities = []

    for entity_id, entity_data in stats.items():
        # Skip if already has biography
        if entity_id in existing_bios:
            continue

        # Check if entity matches tier criteria
        entity_tier = classify_entity_tier(entity_data)

        if entity_tier == tier:
            priority_score = calculate_priority_score(entity_data, tier)
            entities.append((entity_id, entity_data, priority_score))

    # Sort by priority score (highest first)
    entities.sort(key=lambda x: x[2], reverse=True)

    # Apply limit if specified
    if limit:
        entities = entities[:limit]

    # Return entity_id and data (without score)
    return [(eid, edata) for eid, edata, _ in entities]


def generate_tier_summary(tier: int, entities: List[Tuple[str, Dict]]) -> str:
    """Generate human-readable summary of tier"""

    tier_def = TIER_DEFINITIONS[tier]

    summary = []
    summary.append(f"\n{'='*70}")
    summary.append(f"TIER {tier}: {tier_def['name']}")
    summary.append(f"{'='*70}")
    summary.append(f"Description: {tier_def['description']}")
    summary.append(f"Rationale: {tier_def['rationale']}")
    summary.append(f"Expected count: {tier_def['expected_count']}")
    summary.append(f"Estimated time: {tier_def['estimated_time']}")
    summary.append(f"\nActual entities found: {len(entities)}")

    if entities:
        summary.append(f"\nTop 5 entities by priority:")
        for i, (entity_id, entity_data) in enumerate(entities[:5], 1):
            name = entity_data.get("name", entity_id)
            docs = entity_data.get("total_documents", 0)
            sources = len(entity_data.get("sources", []))
            flights = entity_data.get("flight_count", 0)
            connections = entity_data.get("connection_count", 0)

            summary.append(f"  {i}. {name}")
            summary.append(f"     Documents: {docs}, Sources: {sources}, "
                         f"Flights: {flights}, Connections: {connections}")

    return "\n".join(summary)


def save_tier_file(
    tier: int,
    entities: List[Tuple[str, Dict]],
    output_dir: Path
) -> Path:
    """Save tier entities to JSON file for generation script"""

    output_file = output_dir / f"entities_tier{tier}.json"

    # Convert to format expected by generation script
    output_data = {
        "metadata": {
            "generated": datetime.now().isoformat(),
            "tier": tier,
            "tier_name": TIER_DEFINITIONS[tier]["name"],
            "tier_description": TIER_DEFINITIONS[tier]["description"],
            "total_entities": len(entities)
        },
        "entities": {
            entity_id: entity_data
            for entity_id, entity_data in entities
        }
    }

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    return output_file


def print_overall_summary(tier_counts: Dict[int, int], existing_count: int, total_entities: int):
    """Print overall summary of all tiers"""

    print(f"\n{'='*70}")
    print(f"OVERALL SUMMARY")
    print(f"{'='*70}")
    print(f"Total entities: {total_entities}")
    print(f"Existing biographies: {existing_count}")
    print(f"Remaining entities: {total_entities - existing_count}")
    print(f"\nBreakdown by tier:")

    total_remaining = 0
    for tier_num in sorted(tier_counts.keys()):
        count = tier_counts[tier_num]
        tier_name = TIER_DEFINITIONS[tier_num]["name"]
        total_remaining += count
        print(f"  Tier {tier_num} ({tier_name}): {count} entities")

    print(f"\nTotal to generate: {total_remaining}")

    # Calculate estimated time
    tier_times = {
        1: 0.1,  # ~6 seconds per bio
        2: 0.1,  # ~6 seconds per bio
        3: 0.1,  # ~6 seconds per bio
        4: 0.1   # ~6 seconds per bio
    }

    total_minutes = sum(
        tier_counts[tier] * tier_times[tier]
        for tier in tier_counts
    )

    print(f"\nEstimated total time: ~{total_minutes:.0f} minutes ({total_minutes/60:.1f} hours)")
    print(f"  (Based on ~6 seconds per biography with rate limiting)")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate biographies in priority tiers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Priority Tier Definitions:
  Tier 1: High Priority (IMMEDIATE)
    - Document mentions ≥ 2 OR multiple sources
    - Primary subjects with substantial evidence
    - Expected: ~81 entities, ~8 minutes

  Tier 2: Medium-High Priority (SHORT TERM)
    - Flight logs OR network connections OR 1 document mention
    - Direct evidence of involvement or proximity
    - Expected: ~263 entities, ~26 minutes

  Tier 3: Medium Priority (MEDIUM TERM)
    - Black Book + 1 other source
    - Contact book entries with corroborating evidence
    - Expected: ~293 entities, ~30 minutes

  Tier 4: Low Priority (LONG TERM)
    - Black Book only (single source)
    - Address book contacts with minimal evidence
    - Expected: ~1,000 entities, ~100 minutes (batch across sessions)

Examples:
  # Dry run: see what entities are in each tier
  python3 scripts/analysis/generate_bios_by_priority.py --tier 1 --dry-run

  # Generate Tier 1 file (high priority entities)
  python3 scripts/analysis/generate_bios_by_priority.py --tier 1

  # Generate Tier 1 file with limit
  python3 scripts/analysis/generate_bios_by_priority.py --tier 1 --limit 100

  # Generate all tiers
  python3 scripts/analysis/generate_bios_by_priority.py --all-tiers

  # Then use with generation script:
  python3 scripts/analysis/generate_entity_bios_grok.py \\
    --source data/metadata/entities_tier1.json --limit 100
        """
    )

    parser.add_argument(
        "--tier",
        type=int,
        choices=[1, 2, 3, 4],
        help="Specific tier to generate (1=highest, 4=lowest)"
    )
    parser.add_argument(
        "--all-tiers",
        action="store_true",
        help="Generate files for all tiers"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of entities per tier"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show tier summary without saving files"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/metadata"),
        help="Output directory for tier files (default: data/metadata)"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.tier and not args.all_tiers:
        parser.error("Must specify either --tier or --all-tiers")

    # Load data
    print("Loading entity statistics...")
    stats = load_entity_statistics()
    print(f"Loaded {len(stats)} entities")

    print("Loading existing biographies...")
    existing_bios = get_existing_biographies()
    print(f"Found {len(existing_bios)} existing biographies")

    # Process tiers
    tiers_to_process = [args.tier] if args.tier else [1, 2, 3, 4]
    tier_counts = {}

    for tier_num in tiers_to_process:
        # Get entities for tier
        entities = get_entities_by_tier(
            tier=tier_num,
            stats=stats,
            existing_bios=existing_bios,
            limit=args.limit
        )

        tier_counts[tier_num] = len(entities)

        # Print summary
        summary = generate_tier_summary(tier_num, entities)
        print(summary)

        # Save file if not dry run
        if not args.dry_run and entities:
            output_file = save_tier_file(tier_num, entities, args.output_dir)
            print(f"\n✓ Saved to: {output_file}")
            print(f"  Use with: python3 scripts/analysis/generate_entity_bios_grok.py \\")
            print(f"    --source {output_file} --limit {len(entities)}")

    # Print overall summary if processing multiple tiers
    if args.all_tiers:
        print_overall_summary(tier_counts, len(existing_bios), len(stats))

    return 0


if __name__ == "__main__":
    sys.exit(main())
