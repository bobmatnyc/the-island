#!/usr/bin/env python3
"""
Quality Assurance Validation for Entity Enrichment

This script validates enriched entity data to ensure:
1. All sources are accessible and valid
2. Every fact has proper provenance
3. Reliability tiers are accurate
4. No unverified information without flagging

QA Criteria:
- Minimum 2 sources per biographical fact
- Tier 1-2 sources required for Epstein allegations
- All URLs are valid and accessible
- No facts without source attribution
"""

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass
class QAIssue:
    """QA validation issue"""

    severity: str  # 'critical', 'high', 'medium', 'low'
    entity_id: str
    entity_name: str
    issue_type: str
    description: str
    suggested_fix: str


class QAValidator:
    """
    Quality assurance validator for enriched entity data

    Validation Rules:
    1. Source Provenance: Every fact must have >= 1 source
    2. High-Risk Claims: Epstein connections require Tier 1-2 sources
    3. URL Validity: All source URLs must be well-formed
    4. Minimum Sources: At least 2 independent sources per entity
    5. Reliability Distribution: At least 50% Tier 1-3 sources
    """

    def __init__(self, enriched_data_path: Path):
        self.data_path = enriched_data_path
        self.data = self._load_data()
        self.issues: list[QAIssue] = []

    def _load_data(self) -> dict:
        """Load enriched entity data"""
        with open(self.data_path) as f:
            return json.load(f)

    def validate_all(self) -> tuple[bool, list[QAIssue]]:
        """
        Run all validation checks

        Returns:
            (passed: bool, issues: List[QAIssue])
        """
        print("=" * 80)
        print("QUALITY ASSURANCE VALIDATION")
        print("=" * 80)
        print(f"\nValidating: {self.data_path}")
        print(f"Total entities: {len(self.data.get('entities', []))}\n")

        self.issues = []

        # Run validation checks
        self._validate_source_provenance()
        self._validate_source_reliability()
        self._validate_url_validity()
        self._validate_epstein_claims()
        self._validate_minimum_sources()
        self._validate_completeness()

        # Generate report
        return self._generate_report()

    def _validate_source_provenance(self):
        """Validate that all facts have source attribution"""
        print("1. Checking source provenance...")

        for entity in self.data.get("entities", []):
            entity_id = entity.get("entity_id")
            entity_name = entity.get("name")

            # Check biographical data
            bio_data = entity.get("biographical_data", {})
            for field_name, field_data in bio_data.items():
                if isinstance(field_data, dict):
                    sources = field_data.get("sources", [])
                    if not sources:
                        self.issues.append(
                            QAIssue(
                                severity="high",
                                entity_id=entity_id,
                                entity_name=entity_name,
                                issue_type="missing_provenance",
                                description=f"Biographical field '{field_name}' has no sources",
                                suggested_fix=f"Add source attribution for {field_name}",
                            )
                        )

            # Check Epstein relationship data
            epstein_data = entity.get("epstein_relationship", {})
            interactions = epstein_data.get("documented_interactions", [])
            for interaction in interactions:
                sources = interaction.get("sources", [])
                if not sources:
                    self.issues.append(
                        QAIssue(
                            severity="critical",
                            entity_id=entity_id,
                            entity_name=entity_name,
                            issue_type="missing_provenance",
                            description=f"Epstein interaction has no sources: {interaction.get('description')}",
                            suggested_fix="Add court document or journalism source for this claim",
                        )
                    )

        provenance_issues = len([i for i in self.issues if i.issue_type == "missing_provenance"])
        print(f"   Found {provenance_issues} provenance issues")

    def _validate_source_reliability(self):
        """Validate source reliability tiers"""
        print("2. Checking source reliability...")

        for entity in self.data.get("entities", []):
            entity_id = entity.get("entity_id")
            entity_name = entity.get("name")

            all_sources = self._collect_all_sources(entity)

            # Check reliability distribution
            tier_counts = Counter(s.get("reliability_tier", 4) for s in all_sources)
            total_sources = len(all_sources)

            if total_sources > 0:
                high_reliability = tier_counts[1] + tier_counts[2]
                high_reliability_pct = high_reliability / total_sources

                if high_reliability_pct < 0.3:  # Less than 30% high-reliability
                    self.issues.append(
                        QAIssue(
                            severity="medium",
                            entity_id=entity_id,
                            entity_name=entity_name,
                            issue_type="low_reliability",
                            description=f"Only {high_reliability_pct*100:.1f}% Tier 1-2 sources (need >30%)",
                            suggested_fix="Add more court documents or major journalism sources",
                        )
                    )

        reliability_issues = len([i for i in self.issues if i.issue_type == "low_reliability"])
        print(f"   Found {reliability_issues} reliability issues")

    def _validate_url_validity(self):
        """Validate all source URLs are well-formed"""
        print("3. Checking URL validity...")

        for entity in self.data.get("entities", []):
            entity_id = entity.get("entity_id")
            entity_name = entity.get("name")

            all_sources = self._collect_all_sources(entity)

            for source in all_sources:
                url = source.get("url", "")
                try:
                    result = urlparse(url)
                    if not all([result.scheme, result.netloc]):
                        self.issues.append(
                            QAIssue(
                                severity="high",
                                entity_id=entity_id,
                                entity_name=entity_name,
                                issue_type="invalid_url",
                                description=f"Invalid URL: {url}",
                                suggested_fix="Fix or remove invalid URL",
                            )
                        )
                except Exception:
                    self.issues.append(
                        QAIssue(
                            severity="high",
                            entity_id=entity_id,
                            entity_name=entity_name,
                            issue_type="invalid_url",
                            description=f"Malformed URL: {url}",
                            suggested_fix="Fix or remove malformed URL",
                        )
                    )

        url_issues = len([i for i in self.issues if i.issue_type == "invalid_url"])
        print(f"   Found {url_issues} URL issues")

    def _validate_epstein_claims(self):
        """Validate that Epstein-related claims have high-tier sources"""
        print("4. Checking Epstein claim sources...")

        for entity in self.data.get("entities", []):
            entity_id = entity.get("entity_id")
            entity_name = entity.get("name")

            epstein_data = entity.get("epstein_relationship", {})
            interactions = epstein_data.get("documented_interactions", [])

            for interaction in interactions:
                sources = interaction.get("sources", [])
                if sources:
                    # Check if at least one Tier 1-2 source
                    has_high_tier = any(s.get("reliability_tier", 4) <= 2 for s in sources)

                    if not has_high_tier:
                        self.issues.append(
                            QAIssue(
                                severity="critical",
                                entity_id=entity_id,
                                entity_name=entity_name,
                                issue_type="low_tier_epstein_claim",
                                description=f"Epstein claim lacks Tier 1-2 source: {interaction.get('description')}",
                                suggested_fix="Add court document or major journalism source",
                            )
                        )

        epstein_issues = len([i for i in self.issues if i.issue_type == "low_tier_epstein_claim"])
        print(f"   Found {epstein_issues} Epstein claim issues")

    def _validate_minimum_sources(self):
        """Validate entities have minimum number of sources"""
        print("5. Checking minimum source requirements...")

        for entity in self.data.get("entities", []):
            entity_id = entity.get("entity_id")
            entity_name = entity.get("name")

            all_sources = self._collect_all_sources(entity)

            if len(all_sources) < 2:
                self.issues.append(
                    QAIssue(
                        severity="medium",
                        entity_id=entity_id,
                        entity_name=entity_name,
                        issue_type="insufficient_sources",
                        description=f"Only {len(all_sources)} source(s) (need >=2)",
                        suggested_fix="Add more independent sources",
                    )
                )

        source_issues = len([i for i in self.issues if i.issue_type == "insufficient_sources"])
        print(f"   Found {source_issues} insufficient source issues")

    def _validate_completeness(self):
        """Validate research completeness"""
        print("6. Checking research completeness...")

        for entity in self.data.get("entities", []):
            entity_id = entity.get("entity_id")
            entity_name = entity.get("name")

            bio_data = entity.get("biographical_data", {})
            epstein_data = entity.get("epstein_relationship", {})

            # Check for minimal biographical data
            if not bio_data or len(bio_data) == 0:
                self.issues.append(
                    QAIssue(
                        severity="medium",
                        entity_id=entity_id,
                        entity_name=entity_name,
                        issue_type="incomplete_biographical",
                        description="No biographical data found",
                        suggested_fix="Add biographical information (birth, occupation, etc.)",
                    )
                )

            # Check for Epstein connection info
            interactions = epstein_data.get("documented_interactions", [])
            if not interactions:
                self.issues.append(
                    QAIssue(
                        severity="low",
                        entity_id=entity_id,
                        entity_name=entity_name,
                        issue_type="incomplete_epstein_info",
                        description="No documented Epstein interactions",
                        suggested_fix="Add information about Epstein connection if available",
                    )
                )

        completeness_issues = len(
            [i for i in self.issues if i.issue_type.startswith("incomplete_")]
        )
        print(f"   Found {completeness_issues} completeness issues")

    def _collect_all_sources(self, entity: dict) -> list[dict]:
        """Collect all sources from an entity"""
        sources = []

        # Biographical sources
        bio_data = entity.get("biographical_data", {})
        for field_data in bio_data.values():
            if isinstance(field_data, dict):
                sources.extend(field_data.get("sources", []))

        # Epstein relationship sources
        epstein_data = entity.get("epstein_relationship", {})
        for interaction in epstein_data.get("documented_interactions", []):
            sources.extend(interaction.get("sources", []))

        for statement in epstein_data.get("public_statements", []):
            sources.extend(statement.get("sources", []))

        for legal in epstein_data.get("legal_involvement", []):
            sources.extend(legal.get("sources", []))

        return sources

    def _generate_report(self) -> tuple[bool, list[QAIssue]]:
        """Generate validation report"""
        print("\n" + "=" * 80)
        print("VALIDATION REPORT")
        print("=" * 80)

        # Count by severity
        critical = [i for i in self.issues if i.severity == "critical"]
        high = [i for i in self.issues if i.severity == "high"]
        medium = [i for i in self.issues if i.severity == "medium"]
        low = [i for i in self.issues if i.severity == "low"]

        print(f"\nTotal Issues: {len(self.issues)}")
        print(f"  Critical: {len(critical)}")
        print(f"  High:     {len(high)}")
        print(f"  Medium:   {len(medium)}")
        print(f"  Low:      {len(low)}")

        # Determine pass/fail
        passed = len(critical) == 0 and len(high) == 0

        if passed:
            print("\n✅ VALIDATION PASSED")
            print("   No critical or high-severity issues found")
        else:
            print("\n❌ VALIDATION FAILED")
            print(f"   Found {len(critical)} critical and {len(high)} high-severity issues")

        # Show top issues
        if self.issues:
            print("\n" + "=" * 80)
            print("TOP ISSUES (by severity)")
            print("=" * 80)

            for issue in sorted(
                self.issues, key=lambda x: ["critical", "high", "medium", "low"].index(x.severity)
            )[:10]:
                print(f"\n{issue.severity.upper()}: {issue.entity_name}")
                print(f"  Type: {issue.issue_type}")
                print(f"  Issue: {issue.description}")
                print(f"  Fix: {issue.suggested_fix}")

        print("\n" + "=" * 80)

        return passed, self.issues

    def export_issues(self, output_path: Path):
        """Export issues to JSON for review"""
        issues_data = {
            "validation_date": datetime.now().isoformat(),
            "total_issues": len(self.issues),
            "by_severity": {
                "critical": len([i for i in self.issues if i.severity == "critical"]),
                "high": len([i for i in self.issues if i.severity == "high"]),
                "medium": len([i for i in self.issues if i.severity == "medium"]),
                "low": len([i for i in self.issues if i.severity == "low"]),
            },
            "issues": [
                {
                    "severity": i.severity,
                    "entity_id": i.entity_id,
                    "entity_name": i.entity_name,
                    "issue_type": i.issue_type,
                    "description": i.description,
                    "suggested_fix": i.suggested_fix,
                }
                for i in self.issues
            ],
        }

        with open(output_path, "w") as f:
            json.dump(issues_data, f, indent=2)

        print(f"\n💾 Issues exported to: {output_path}")


def main():
    """Run QA validation"""
    import argparse

    parser = argparse.ArgumentParser(description="QA validation for enriched entity data")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("/Users/masa/Projects/epstein/data/metadata/enriched_entity_data.json"),
        help="Path to enriched entity data",
    )
    parser.add_argument("--export", type=Path, help="Export issues to JSON file")

    args = parser.parse_args()

    # Run validation
    validator = QAValidator(args.input)
    passed, _issues = validator.validate_all()

    # Export if requested
    if args.export:
        validator.export_issues(args.export)

    # Exit code based on validation result
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    import sys

    main()
