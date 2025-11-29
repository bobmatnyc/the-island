#!/usr/bin/env python3
"""
Find entity aliases for network migration missing entities
"""

import json
from difflib import SequenceMatcher


def load_entity_mappings():
    """Load entity ID mappings"""
    with open("/Users/masa/Projects/epstein/data/migration/entity_id_mappings.json") as f:
        data = json.load(f)
    return data["id_to_entity"]


def similarity_ratio(a, b):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_matches(missing_name, entities):
    """Find potential matches for a missing entity"""
    matches = []

    # Extract keywords from missing name
    keywords = set(missing_name.lower().split())

    for entity_id, entity_data in entities.items():
        entity_name = entity_data.get("name", "")
        name_variations = entity_data.get("name_variations", [])

        # Check all name variations
        for variation in [entity_name, *name_variations]:
            # Calculate similarity
            score = similarity_ratio(missing_name, variation)

            # Check keyword overlap
            var_keywords = set(variation.lower().split())
            keyword_overlap = len(keywords & var_keywords) / max(len(keywords), 1)

            # Combined score
            combined_score = (score * 0.6) + (keyword_overlap * 0.4)

            if combined_score > 0.5:
                matches.append(
                    {
                        "entity_id": entity_id,
                        "entity_name": entity_name,
                        "matched_variation": variation,
                        "similarity_score": score,
                        "keyword_overlap": keyword_overlap,
                        "combined_score": combined_score,
                        "sources": entity_data.get("sources", []),
                        "flight_count": entity_data.get("metadata", {}).get("flight_count", 0),
                    }
                )

    # Sort by combined score
    matches.sort(key=lambda x: x["combined_score"], reverse=True)
    return matches


def main():
    missing_entities = [
        "Alyssa Holders",
        "Alyssa Kristy",
        "Baby",
        "Barry Massion",
        "Bill Clinton",
        "Christopher Wagner",
        "David Roth",
        "Doug Schoettle",
        "Frank Gamble",
        "Gary Blackwell",
        "Gary Roxburgh",
        "Illegible",
        "Jeffrey Shantz",
        "Jonathan Mano",
        "Kathy Alexander",
        "Kristy Rodgers",
        "Marcinkova, Nadia",
        "Mary Kerney",
        "Michael Durberry",
        "Nathan Myhrbold",
        "Prince Andrew",
        "Ralph Pascale",
        "Reposition",
        "Robert Breslen",
        "Ryan Coomer",
        "Sarah Ferguson",
        "Sean Koo",
        "Secret Service Secret Service",
        "Steven Lister",
        "Test Flight",
        "William Hammond",
        "William Murphy",
    ]

    # Invalid entities (non-persons or metadata)
    invalid_entities = [
        "Illegible",
        "Reposition",
        "Test Flight",
        "Baby",
        "Secret Service Secret Service",
    ]

    entities = load_entity_mappings()

    print("=" * 80)
    print("ENTITY ALIAS ANALYSIS")
    print("=" * 80)

    aliases = {}
    needs_review = []

    for missing_name in missing_entities:
        print(f"\n{'='*80}")
        print(f"Searching for: {missing_name}")
        print("=" * 80)

        # Skip invalid entities
        if missing_name in invalid_entities:
            print("  ⚠️  INVALID ENTITY (non-person or metadata) - SKIP")
            continue

        matches = find_matches(missing_name, entities)

        if matches:
            top_match = matches[0]
            print(f"\n  ✓ TOP MATCH (score: {top_match['combined_score']:.2f}):")
            print(f"    Entity ID: {top_match['entity_id']}")
            print(f"    Name: {top_match['entity_name']}")
            print(f"    Matched via: {top_match['matched_variation']}")
            print(f"    Sources: {top_match['sources']}")
            print(f"    Flights: {top_match['flight_count']}")

            # Auto-accept high confidence matches (>0.8)
            if top_match["combined_score"] > 0.8:
                aliases[missing_name] = top_match["entity_id"]
                print("    ✅ AUTO-ACCEPT (high confidence)")
            else:
                print("    ⚠️  NEEDS REVIEW (moderate confidence)")
                needs_review.append(
                    {
                        "missing_name": missing_name,
                        "suggested_id": top_match["entity_id"],
                        "suggested_name": top_match["entity_name"],
                        "confidence": top_match["combined_score"],
                    }
                )

            # Show additional candidates
            if len(matches) > 1:
                print("\n  Other candidates:")
                for match in matches[1:4]:  # Top 3 additional matches
                    print(
                        f"    - {match['entity_name']} ({match['entity_id']}) - score: {match['combined_score']:.2f}"
                    )
        else:
            print("  ❌ NO MATCHES FOUND")
            needs_review.append(
                {
                    "missing_name": missing_name,
                    "suggested_id": None,
                    "suggested_name": None,
                    "confidence": 0.0,
                }
            )

    # Print summary
    print("\n\n")
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nTotal missing entities: {len(missing_entities)}")
    print(f"Invalid entities (skipped): {len(invalid_entities)}")
    print(f"Auto-accepted aliases: {len(aliases)}")
    print(f"Needs manual review: {len(needs_review)}")

    print("\n\nAUTO-ACCEPTED ALIASES:")
    print("-" * 80)
    for name, entity_id in sorted(aliases.items()):
        print(f"  {name} → {entity_id}")

    print("\n\nNEEDS MANUAL REVIEW:")
    print("-" * 80)
    for item in needs_review:
        if item["suggested_id"]:
            print(f"  {item['missing_name']}")
            print(
                f"    Suggested: {item['suggested_name']} ({item['suggested_id']}) - confidence: {item['confidence']:.2f}"
            )
        else:
            print(f"  {item['missing_name']}")
            print("    No match found - may need manual search")

    # Save results to JSON
    output = {
        "aliases": aliases,
        "invalid_entities": invalid_entities,
        "needs_review": needs_review,
        "generated_at": "2025-11-20T19:15:00",
        "statistics": {
            "total_missing": len(missing_entities),
            "invalid_count": len(invalid_entities),
            "auto_accepted": len(aliases),
            "needs_review": len(needs_review),
        },
    }

    output_path = "/Users/masa/Projects/epstein/data/migration/entity_network_aliases_analysis.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n\n✅ Analysis saved to: {output_path}")


if __name__ == "__main__":
    main()
