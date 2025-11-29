#!/usr/bin/env python3
"""
Entity Similarity Validation Report

Validates that semantically similar entities have overlapping relationship categories.
Uses ChromaDB vector similarity to find similar entities and compares their categories.

Analysis:
1. Sample entities and find their top similar matches
2. Compare category overlap between similar entities
3. Identify entities with low category overlap (potential miscategorization)
4. Generate summary statistics and recommendations

Output: Markdown report to docs/qa-reports/entity_similarity_validation_report.md
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict, Counter
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "server"))

try:
    from services.entity_similarity import EntitySimilarityService
except ImportError:
    print("Error: Could not import EntitySimilarityService")
    print("Make sure server/services/entity_similarity.py exists")
    sys.exit(1)

# Paths
ENTITY_BIOGRAPHIES_PATH = PROJECT_ROOT / "data" / "metadata" / "entity_biographies.json"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "qa-reports" / "entity_similarity_validation_report.md"


class SimilarityValidator:
    """Validates entity categorization using semantic similarity."""

    def __init__(self):
        """Initialize validator with similarity service and entity data."""
        print("Loading entity biographies...")
        with open(ENTITY_BIOGRAPHIES_PATH, "r") as f:
            data = json.load(f)
            self.entities = data["entities"]
        print(f"✓ Loaded {len(self.entities)} entities\n")

        print("Initializing similarity service...")
        self.similarity_service = EntitySimilarityService()
        print("✓ Similarity service ready\n")

    def get_entity_categories(self, entity: Dict) -> Set[str]:
        """Extract category types from entity."""
        categories = entity.get("relationship_categories", [])
        return {cat["type"] for cat in categories if isinstance(cat, dict)}

    def analyze_similarity_validation(self, sample_size: int = 100) -> Dict:
        """Analyze category overlap among similar entities.

        Args:
            sample_size: Number of entities to analyze

        Returns:
            Dict with validation statistics
        """
        print(f"Analyzing similarity for {sample_size} entities...")

        # Sample entities with categories
        entities_with_cats = [
            (k, v) for k, v in self.entities.items()
            if v.get("relationship_categories")
        ][:sample_size]

        results = {
            "total_analyzed": 0,
            "avg_category_overlap": 0.0,
            "high_overlap": 0,  # >50% category overlap
            "medium_overlap": 0,  # 25-50% overlap
            "low_overlap": 0,  # <25% overlap
            "outliers": [],
            "category_co_occurrence": defaultdict(Counter),
        }

        total_overlap = 0
        comparisons = 0

        for entity_id, entity in entities_with_cats:
            try:
                # Get entity categories
                entity_cats = self.get_entity_categories(entity)
                if not entity_cats:
                    continue

                # Find similar entities
                similar_entities = self.similarity_service.find_similar_entities(
                    entity_name=entity_id,
                    limit=10,
                    min_similarity=0.4
                )

                if not similar_entities:
                    continue

                # Compare categories with similar entities
                overlap_scores = []
                for similar in similar_entities:
                    similar_entity = self.entities.get(similar["entity_id"])
                    if not similar_entity:
                        continue

                    similar_cats = self.get_entity_categories(similar_entity)
                    if not similar_cats:
                        continue

                    # Calculate Jaccard similarity
                    intersection = entity_cats & similar_cats
                    union = entity_cats | similar_cats
                    overlap = len(intersection) / len(union) if union else 0
                    overlap_scores.append(overlap)

                    # Track co-occurrence
                    for cat in entity_cats:
                        for similar_cat in similar_cats:
                            results["category_co_occurrence"][cat][similar_cat] += 1

                if not overlap_scores:
                    continue

                # Calculate average overlap for this entity
                avg_overlap = sum(overlap_scores) / len(overlap_scores)
                total_overlap += avg_overlap
                comparisons += 1

                results["total_analyzed"] += 1

                # Categorize by overlap level
                if avg_overlap > 0.5:
                    results["high_overlap"] += 1
                elif avg_overlap > 0.25:
                    results["medium_overlap"] += 1
                else:
                    results["low_overlap"] += 1

                    # Flag as outlier
                    results["outliers"].append({
                        "entity_id": entity_id,
                        "display_name": entity.get("display_name", entity_id),
                        "categories": list(entity_cats),
                        "avg_overlap": avg_overlap,
                        "similar_count": len(similar_entities)
                    })

            except Exception as e:
                print(f"  ⚠ Error analyzing {entity_id}: {e}")
                continue

        # Calculate overall statistics
        if comparisons > 0:
            results["avg_category_overlap"] = total_overlap / comparisons

        return results

    def generate_report(self, results: Dict) -> str:
        """Generate markdown report from validation results.

        Args:
            results: Validation analysis results

        Returns:
            Markdown formatted report string
        """
        report = [
            "# Entity Similarity Validation Report",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Entities Analyzed**: {results['total_analyzed']}",
            f"**Average Category Overlap**: {results['avg_category_overlap']:.2%}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            "This report validates that semantically similar entities (based on biography text) have overlapping relationship categories. Category overlap indicates consistent categorization.",
            "",
            f"- **High Overlap** (>50%): {results['high_overlap']} entities",
            f"- **Medium Overlap** (25-50%): {results['medium_overlap']} entities",
            f"- **Low Overlap** (<25%): {results['low_overlap']} entities",
            "",
            "### Interpretation",
            "",
        ]

        if results['avg_category_overlap'] > 0.40:
            report.append(f"✅ **Good**: Average overlap of {results['avg_category_overlap']:.2%} indicates consistent categorization. Similar entities tend to share relationship categories.")
        elif results['avg_category_overlap'] > 0.25:
            report.append(f"⚠️ **Moderate**: Average overlap of {results['avg_category_overlap']:.2%} suggests some consistency, but there's room for improvement.")
        else:
            report.append(f"❌ **Low**: Average overlap of {results['avg_category_overlap']:.2%} indicates potential categorization issues. Similar entities have different categories.")

        report.extend([
            "",
            "---",
            "",
            "## Distribution Analysis",
            "",
            "| Overlap Level | Count | Percentage |",
            "|--------------|-------|------------|",
            f"| High (>50%) | {results['high_overlap']} | {results['high_overlap']/results['total_analyzed']*100 if results['total_analyzed'] > 0 else 0:.1f}% |",
            f"| Medium (25-50%) | {results['medium_overlap']} | {results['medium_overlap']/results['total_analyzed']*100 if results['total_analyzed'] > 0 else 0:.1f}% |",
            f"| Low (<25%) | {results['low_overlap']} | {results['low_overlap']/results['total_analyzed']*100 if results['total_analyzed'] > 0 else 0:.1f}% |",
            "",
            "---",
            "",
            "## Low Overlap Entities (Potential Review Candidates)",
            "",
            "These entities have low category overlap with their similar entities. This could indicate:",
            "- The entity is unique and doesn't fit standard categories well",
            "- Categories may need adjustment",
            "- Similar entities are found but categories differ",
            "",
        ])

        # List outliers
        for outlier in sorted(results["outliers"], key=lambda x: x["avg_overlap"])[:20]:
            report.extend([
                f"### {outlier['display_name']}",
                "",
                f"- **Average Overlap**: {outlier['avg_overlap']:.2%}",
                f"- **Current Categories**: {', '.join(outlier['categories'])}",
                f"- **Similar Entities Found**: {outlier['similar_count']}",
                "",
                "**Action**: Review if categories accurately reflect entity's role",
                ""
            ])

        # Category co-occurrence analysis
        report.extend([
            "---",
            "",
            "## Category Co-Occurrence",
            "",
            "This shows which categories frequently appear together among similar entities.",
            ""
        ])

        # Get top category pairs
        co_occurrence_pairs = []
        for cat, counter in results["category_co_occurrence"].items():
            for other_cat, count in counter.most_common(3):
                if cat != other_cat:
                    co_occurrence_pairs.append((cat, other_cat, count))

        # Sort by count and take top 10
        top_pairs = sorted(co_occurrence_pairs, key=lambda x: -x[2])[:10]

        if top_pairs:
            report.extend([
                "| Category 1 | Category 2 | Co-occurrence Count |",
                "|-----------|-----------|---------------------|"
            ])
            for cat1, cat2, count in top_pairs:
                report.append(f"| {cat1} | {cat2} | {count} |")
        else:
            report.append("No significant co-occurrence patterns found.")

        report.extend([
            "",
            "---",
            "",
            "## Recommendations",
            "",
        ])

        if results['low_overlap'] > results['total_analyzed'] * 0.3:
            report.append("1. **Review Low Overlap Entities**: Focus on entities with <25% overlap listed above")
            report.append("2. **Category Refinement**: Consider adding or adjusting categories for outlier entities")
        else:
            report.append("1. **Maintain Current Categorization**: Overall overlap is good, minimal changes needed")

        report.append("2. **Leverage Co-Occurrence**: Use frequent category pairs to identify entity relationships")
        report.append("3. **Continuous Validation**: Re-run this analysis as new entities are added")

        return "\n".join(report)


def main():
    """Main entry point."""
    print("=" * 60)
    print("Entity Similarity Validation Report Generator")
    print("=" * 60)
    print()

    # Initialize validator
    validator = SimilarityValidator()

    # Run analysis
    results = validator.analyze_similarity_validation(sample_size=100)

    print(f"\n✓ Analysis complete:")
    print(f"  - Total analyzed: {results['total_analyzed']}")
    print(f"  - Average overlap: {results['avg_category_overlap']:.2%}")
    print(f"  - High overlap: {results['high_overlap']}")
    print(f"  - Medium overlap: {results['medium_overlap']}")
    print(f"  - Low overlap: {results['low_overlap']}")

    # Generate report
    print("\nGenerating report...")
    report = validator.generate_report(results)

    # Save report
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        f.write(report)

    print(f"\n✓ Report saved to: {OUTPUT_PATH}")
    print(f"  - Outliers identified: {len(results['outliers'])}")
    print(f"  - Category pairs analyzed: {len(results['category_co_occurrence'])}")


if __name__ == "__main__":
    main()
