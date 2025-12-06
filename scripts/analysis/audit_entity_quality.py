#!/usr/bin/env python3
"""
Entity Data Quality Audit Script
Analyzes entity files for completeness, quality issues, and gaps.
"""

import json
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any
import re

class EntityQualityAuditor:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.results = {
            "biographies": {},
            "locations": {},
            "organizations": {},
            "summary": {}
        }

    def load_entities(self, filename: str) -> List[Dict[str, Any]]:
        """Load entity file"""
        filepath = self.data_dir / filename
        print(f"Loading {filepath}...")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle different JSON structures
        if isinstance(data, dict):
            if 'entities' in data:
                # Extract entities from dictionary
                entities = data['entities']
                if isinstance(entities, dict):
                    # Convert dict to list of entities
                    return list(entities.values())
                return entities
            # Assume the whole dict is entities
            return list(data.values())
        return data

    def analyze_entity_type(self, entities: List[Dict], entity_type: str) -> Dict:
        """Analyze a single entity type for quality metrics"""
        print(f"\nAnalyzing {entity_type}...")

        metrics = {
            "total_count": len(entities),
            "with_uuid": 0,
            "with_classification": 0,
            "with_biography": 0,
            "with_aliases": 0,
            "zero_connections": 0,
            "zero_documents": 0,
            "zero_news": 0,
            "missing_fields": defaultdict(int),
            "field_stats": {},
            "duplicates": [],
            "naming_issues": [],
            "classification_distribution": Counter()
        }

        # Track for duplicate detection
        name_map = defaultdict(list)

        for idx, entity in enumerate(entities):
            # Check UUID
            if entity.get("entity_id") and len(str(entity["entity_id"])) == 36:
                metrics["with_uuid"] += 1

            # Check classification
            classifications = entity.get("classifications", [])
            if classifications:
                metrics["with_classification"] += 1
                for cls in classifications:
                    metrics["classification_distribution"][cls] += 1

            # Check biography
            if entity.get("biography"):
                metrics["with_biography"] += 1

            # Check aliases
            if entity.get("aliases") and len(entity.get("aliases", [])) > 0:
                metrics["with_aliases"] += 1

            # Check connections
            if entity.get("connection_count", 0) == 0:
                metrics["zero_connections"] += 1

            # Check documents
            if entity.get("document_count", 0) == 0:
                metrics["zero_documents"] += 1

            # Check news
            if entity.get("news_count", 0) == 0:
                metrics["zero_news"] += 1

            # Check required fields
            required_fields = ["entity_id", "entity_type", "canonical_name"]
            for field in required_fields:
                if not entity.get(field):
                    metrics["missing_fields"][field] += 1

            # Track canonical names for duplicate detection
            canonical_name = entity.get("canonical_name", "").strip()
            if canonical_name:
                # Normalize for duplicate detection
                normalized = canonical_name.lower().strip()
                name_map[normalized].append({
                    "index": idx,
                    "original_name": canonical_name,
                    "entity_id": entity.get("entity_id")
                })

                # Check naming issues
                if canonical_name != canonical_name.strip():
                    metrics["naming_issues"].append(f"Index {idx}: Whitespace issue in '{canonical_name}'")

                # Check for all caps or all lowercase
                if canonical_name.isupper() and len(canonical_name) > 3:
                    metrics["naming_issues"].append(f"Index {idx}: ALL CAPS - '{canonical_name}'")
                elif canonical_name.islower() and len(canonical_name) > 3:
                    metrics["naming_issues"].append(f"Index {idx}: all lowercase - '{canonical_name}'")

        # Find duplicates
        for normalized_name, occurrences in name_map.items():
            if len(occurrences) > 1:
                metrics["duplicates"].append({
                    "normalized_name": normalized_name,
                    "count": len(occurrences),
                    "instances": occurrences
                })

        # Calculate percentages
        total = metrics["total_count"]
        if total > 0:
            metrics["field_stats"] = {
                "uuid_coverage": f"{(metrics['with_uuid'] / total * 100):.1f}%",
                "classification_coverage": f"{(metrics['with_classification'] / total * 100):.1f}%",
                "biography_coverage": f"{(metrics['with_biography'] / total * 100):.1f}%",
                "aliases_coverage": f"{(metrics['with_aliases'] / total * 100):.1f}%",
                "isolated_entities": f"{(metrics['zero_connections'] / total * 100):.1f}%",
                "no_document_refs": f"{(metrics['zero_documents'] / total * 100):.1f}%",
                "no_news_refs": f"{(metrics['zero_news'] / total * 100):.1f}%"
            }

        # Limit sample issues for readability
        metrics["naming_issues"] = metrics["naming_issues"][:10]
        metrics["duplicates"] = sorted(metrics["duplicates"], key=lambda x: x["count"], reverse=True)[:20]

        return metrics

    def check_cross_type_misclassifications(self) -> List[str]:
        """Check for entities that might be misclassified across types"""
        issues = []

        # Load all entities
        people = self.load_entities("entity_biographies.json")
        locations = self.load_entities("entity_locations.json")
        orgs = self.load_entities("entity_organizations.json")

        # Build name sets
        people_names = {e.get("canonical_name", "").lower().strip() for e in people}
        location_names = {e.get("canonical_name", "").lower().strip() for e in locations}
        org_names = {e.get("canonical_name", "").lower().strip() for e in orgs}

        # Find overlaps
        people_in_orgs = people_names & org_names
        people_in_locations = people_names & location_names
        orgs_in_locations = org_names & location_names

        if people_in_orgs:
            issues.append(f"Found {len(people_in_orgs)} names appearing in both PEOPLE and ORGANIZATIONS")
            for name in list(people_in_orgs)[:5]:
                issues.append(f"  - {name}")

        if people_in_locations:
            issues.append(f"Found {len(people_in_locations)} names appearing in both PEOPLE and LOCATIONS")
            for name in list(people_in_locations)[:5]:
                issues.append(f"  - {name}")

        if orgs_in_locations:
            issues.append(f"Found {len(orgs_in_locations)} names appearing in both ORGANIZATIONS and LOCATIONS")
            for name in list(orgs_in_locations)[:5]:
                issues.append(f"  - {name}")

        return issues

    def generate_report(self) -> str:
        """Generate markdown audit report"""
        report = [
            "# Entity Data Quality Audit Report",
            "",
            f"**Generated**: {self.results['summary'].get('timestamp', 'N/A')}",
            "",
            "## Executive Summary",
            "",
            f"Total entities audited: **{self.results['summary'].get('total_entities', 0):,}**",
            "",
            "### Key Findings",
            ""
        ]

        # Add key findings
        for entity_type in ["biographies", "locations", "organizations"]:
            metrics = self.results.get(entity_type, {})
            if metrics:
                report.append(f"**{entity_type.title()}**: {metrics['total_count']:,} entities")
                report.append(f"- UUID Coverage: {metrics['field_stats'].get('uuid_coverage', 'N/A')}")
                report.append(f"- Classification Coverage: {metrics['field_stats'].get('classification_coverage', 'N/A')}")
                report.append(f"- Biography Coverage: {metrics['field_stats'].get('biography_coverage', 'N/A')}")
                report.append(f"- Isolated Entities (0 connections): {metrics['field_stats'].get('isolated_entities', 'N/A')}")
                report.append(f"- Potential Duplicates: {len(metrics.get('duplicates', []))}")
                report.append("")

        # Detailed sections for each entity type
        for entity_type in ["biographies", "locations", "organizations"]:
            metrics = self.results.get(entity_type, {})
            if not metrics:
                continue

            report.append(f"## {entity_type.title()} Analysis")
            report.append("")
            report.append(f"**Total Count**: {metrics['total_count']:,}")
            report.append("")

            # Field Coverage
            report.append("### Field Coverage")
            report.append("")
            report.append("| Field | Coverage | Count |")
            report.append("|-------|----------|-------|")
            report.append(f"| UUID | {metrics['field_stats'].get('uuid_coverage', 'N/A')} | {metrics['with_uuid']:,} |")
            report.append(f"| Classification | {metrics['field_stats'].get('classification_coverage', 'N/A')} | {metrics['with_classification']:,} |")
            report.append(f"| Biography | {metrics['field_stats'].get('biography_coverage', 'N/A')} | {metrics['with_biography']:,} |")
            report.append(f"| Aliases | {metrics['field_stats'].get('aliases_coverage', 'N/A')} | {metrics['with_aliases']:,} |")
            report.append("")

            # Data Gaps
            report.append("### Data Gaps")
            report.append("")
            report.append(f"- **Zero Connections**: {metrics['zero_connections']:,} ({metrics['field_stats'].get('isolated_entities', 'N/A')})")
            report.append(f"- **No Document References**: {metrics['zero_documents']:,} ({metrics['field_stats'].get('no_document_refs', 'N/A')})")
            report.append(f"- **No News References**: {metrics['zero_news']:,} ({metrics['field_stats'].get('no_news_refs', 'N/A')})")
            report.append("")

            # Missing Required Fields
            if metrics.get('missing_fields'):
                report.append("### Missing Required Fields")
                report.append("")
                for field, count in metrics['missing_fields'].items():
                    report.append(f"- **{field}**: {count:,} entities missing")
                report.append("")

            # Classification Distribution
            if metrics.get('classification_distribution'):
                report.append("### Classification Distribution")
                report.append("")
                report.append("| Classification | Count |")
                report.append("|----------------|-------|")
                for cls, count in metrics['classification_distribution'].most_common(10):
                    report.append(f"| {cls} | {count:,} |")
                report.append("")

            # Duplicates
            if metrics.get('duplicates'):
                report.append(f"### Potential Duplicates ({len(metrics['duplicates'])} groups)")
                report.append("")
                report.append("Top duplicate groups (by occurrence count):")
                report.append("")
                for dup in metrics['duplicates'][:10]:
                    report.append(f"**{dup['normalized_name']}** - {dup['count']} instances")
                    for inst in dup['instances'][:3]:
                        report.append(f"  - Index {inst['index']}: '{inst['original_name']}' (ID: {inst.get('entity_id', 'N/A')})")
                    if dup['count'] > 3:
                        report.append(f"  - ... and {dup['count'] - 3} more")
                    report.append("")

            # Naming Issues
            if metrics.get('naming_issues'):
                report.append(f"### Naming Issues (showing first 10)")
                report.append("")
                for issue in metrics['naming_issues']:
                    report.append(f"- {issue}")
                report.append("")

        # Cross-type misclassifications
        if self.results['summary'].get('cross_type_issues'):
            report.append("## Cross-Type Misclassifications")
            report.append("")
            for issue in self.results['summary']['cross_type_issues']:
                report.append(f"- {issue}")
            report.append("")

        # Recommendations
        report.append("## Recommendations")
        report.append("")
        report.append("### Priority 1: Critical Data Quality Issues")
        report.append("")

        # Calculate missing UUIDs
        total_missing_uuid = sum(
            self.results[et]['total_count'] - self.results[et]['with_uuid']
            for et in ["biographies", "locations", "organizations"]
        )
        if total_missing_uuid > 0:
            report.append(f"1. **Generate UUIDs**: {total_missing_uuid:,} entities missing UUIDs")

        # Calculate missing classifications
        total_missing_classification = sum(
            self.results[et]['total_count'] - self.results[et]['with_classification']
            for et in ["biographies", "locations", "organizations"]
        )
        if total_missing_classification > 0:
            report.append(f"2. **Add Classifications**: {total_missing_classification:,} entities need classification")

        # Duplicates
        total_duplicates = sum(
            len(self.results[et].get('duplicates', []))
            for et in ["biographies", "locations", "organizations"]
        )
        if total_duplicates > 0:
            report.append(f"3. **Resolve Duplicates**: {total_duplicates} duplicate groups identified")

        report.append("")
        report.append("### Priority 2: Data Enrichment")
        report.append("")

        # Biographies
        total_missing_bio = sum(
            self.results[et]['total_count'] - self.results[et]['with_biography']
            for et in ["biographies", "locations", "organizations"]
        )
        if total_missing_bio > 0:
            report.append(f"1. **Add Biographies**: {total_missing_bio:,} entities missing biographical data")

        # Isolated entities
        total_isolated = sum(
            self.results[et]['zero_connections']
            for et in ["biographies", "locations", "organizations"]
        )
        if total_isolated > 0:
            report.append(f"2. **Connect Isolated Entities**: {total_isolated:,} entities with zero connections")

        report.append("")
        report.append("### Priority 3: Schema Compliance")
        report.append("")
        report.append("1. **Standardize Naming**: Fix capitalization and whitespace issues")
        report.append("2. **Add Source References**: Implement source_refs field for traceability")
        report.append("3. **Validate Entity Types**: Review and correct cross-type misclassifications")
        report.append("")

        # Data Completeness Score
        report.append("## Data Completeness Score")
        report.append("")

        total = self.results['summary'].get('total_entities', 0)
        if total > 0:
            total_with_uuid = sum(self.results[et]['with_uuid'] for et in ["biographies", "locations", "organizations"])
            total_with_classification = sum(self.results[et]['with_classification'] for et in ["biographies", "locations", "organizations"])
            total_with_biography = sum(self.results[et]['with_biography'] for et in ["biographies", "locations", "organizations"])

            uuid_score = (total_with_uuid / total) * 100
            classification_score = (total_with_classification / total) * 100
            biography_score = (total_with_biography / total) * 100

            overall_score = (uuid_score + classification_score + biography_score) / 3

            report.append(f"**Overall Completeness**: {overall_score:.1f}%")
            report.append("")
            report.append("| Metric | Score |")
            report.append("|--------|-------|")
            report.append(f"| UUID Coverage | {uuid_score:.1f}% |")
            report.append(f"| Classification Coverage | {classification_score:.1f}% |")
            report.append(f"| Biography Coverage | {biography_score:.1f}% |")
            report.append("")

        report.append("---")
        report.append("")
        report.append("*Report generated by `scripts/analysis/audit_entity_quality.py`*")

        return "\n".join(report)

    def run_audit(self):
        """Execute full audit"""
        from datetime import datetime

        print("=" * 60)
        print("ENTITY DATA QUALITY AUDIT")
        print("=" * 60)

        # Analyze each entity type
        people = self.load_entities("entity_biographies.json")
        self.results["biographies"] = self.analyze_entity_type(people, "biographies")

        locations = self.load_entities("entity_locations.json")
        self.results["locations"] = self.analyze_entity_type(locations, "locations")

        orgs = self.load_entities("entity_organizations.json")
        self.results["organizations"] = self.analyze_entity_type(orgs, "organizations")

        # Check cross-type issues
        print("\nChecking cross-type misclassifications...")
        cross_issues = self.check_cross_type_misclassifications()

        # Summary
        total_entities = (
            self.results["biographies"]["total_count"] +
            self.results["locations"]["total_count"] +
            self.results["organizations"]["total_count"]
        )

        self.results["summary"] = {
            "timestamp": datetime.now().isoformat(),
            "total_entities": total_entities,
            "cross_type_issues": cross_issues
        }

        print("\n" + "=" * 60)
        print(f"AUDIT COMPLETE: {total_entities:,} entities analyzed")
        print("=" * 60)

        return self.results


def main():
    """Main execution"""
    import sys
    from datetime import datetime

    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data" / "metadata"
    output_dir = project_root / "docs" / "audit"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run audit
    auditor = EntityQualityAuditor(data_dir)
    results = auditor.run_audit()

    # Generate report
    report = auditor.generate_report()

    # Save report
    output_file = output_dir / "entity-data-quality.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ Report saved to: {output_file}")

    # Print summary to console
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Entities: {results['summary']['total_entities']:,}")
    print()
    for entity_type in ["biographies", "locations", "organizations"]:
        metrics = results[entity_type]
        print(f"\n{entity_type.upper()}:")
        print(f"  Count: {metrics['total_count']:,}")
        print(f"  UUID Coverage: {metrics['field_stats']['uuid_coverage']}")
        print(f"  Classification Coverage: {metrics['field_stats']['classification_coverage']}")
        print(f"  Biography Coverage: {metrics['field_stats']['biography_coverage']}")
        print(f"  Duplicates: {len(metrics.get('duplicates', []))}")

    if results['summary'].get('cross_type_issues'):
        print("\n⚠️  CROSS-TYPE ISSUES:")
        for issue in results['summary']['cross_type_issues'][:5]:
            print(f"  {issue}")

    print("\n" + "=" * 60)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
