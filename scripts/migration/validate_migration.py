#!/usr/bin/env python3
"""
Migration Validation Script

Comprehensive validation suite for entity ID migration.

Validation Checks:
1. Data Integrity (counts, uniqueness, references)
2. Schema Compliance (ID format, required fields)
3. Reference Integrity (network edges, cross-file links)
4. Performance Benchmarks (lookup times)

Usage:
    python validate_migration.py [--verbose] [--benchmark]

Output:
    - Validation report (console + JSON)
    - Performance metrics (if --benchmark)
    - Error details for failed checks
"""

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Optional


class MigrationValidator:
    """
    Comprehensive migration validation.

    Design Decision: Fail-fast validation with detailed reporting
    - All checks run even if one fails (complete error picture)
    - Performance benchmarks optional (--benchmark flag)
    - JSON report for automation integration

    Trade-offs:
    - Completeness vs Speed: Run all checks (slower but thorough)
    - Memory: Load all data (acceptable for dataset size)
    - Reporting: Detailed errors vs summary (detailed for debugging)
    """

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.checks_passed = 0
        self.checks_failed = 0

    def add_error(self, check: str, message: str):
        """Record validation error."""
        self.errors.append({"check": check, "message": message})
        self.checks_failed += 1
        logging.error(f"[{check}] {message}")

    def add_warning(self, check: str, message: str):
        """Record validation warning."""
        self.warnings.append({"check": check, "message": message})
        logging.warning(f"[{check}] {message}")

    def pass_check(self, check: str):
        """Record successful check."""
        self.checks_passed += 1
        logging.info(f"[{check}] ✅ PASSED")

    def validate_id_format(self, entity_id: str, context: str) -> bool:
        """
        Validate entity ID format.

        Rules:
        - Must match ^[a-z0-9_]+$
        - Length 2-100 characters
        - No leading/trailing underscores
        - No consecutive underscores
        """
        if not entity_id:
            self.add_error("ID_FORMAT", f"Empty ID in {context}")
            return False

        if not re.match(r"^[a-z0-9_]+$", entity_id):
            self.add_error(
                "ID_FORMAT",
                f"Invalid ID format '{entity_id}' in {context} " f"(must match ^[a-z0-9_]+$)",
            )
            return False

        if len(entity_id) < 2 or len(entity_id) > 100:
            self.add_error(
                "ID_FORMAT",
                f"Invalid ID length '{entity_id}' ({len(entity_id)} chars) "
                f"in {context} (must be 2-100)",
            )
            return False

        if entity_id.startswith("_") or entity_id.endswith("_"):
            self.add_error(
                "ID_FORMAT", f"ID '{entity_id}' has leading/trailing underscore in {context}"
            )
            return False

        if "__" in entity_id:
            self.add_error(
                "ID_FORMAT", f"ID '{entity_id}' has consecutive underscores in {context}"
            )
            return False

        return True

    def validate_statistics(self, filepath: Path) -> dict:
        """Validate entity_statistics.json."""
        check_name = "STATISTICS_FILE"
        logging.info(f"Validating {filepath}...")

        try:
            with open(filepath) as f:
                data = json.load(f)

            statistics = data.get("statistics", {})

            if not statistics:
                self.add_error(check_name, "Empty statistics dictionary")
                return {}

            # Check all keys are valid IDs
            for entity_id in statistics:
                self.validate_id_format(entity_id, "statistics key")

            # Check all entities have 'id' field
            missing_id = [
                entity_id
                for entity_id, entity_data in statistics.items()
                if entity_data.get("id") != entity_id
            ]

            if missing_id:
                self.add_error(
                    check_name,
                    f"{len(missing_id)} entities with mismatched ID field: "
                    f"{', '.join(missing_id[:5])}",
                )

            # Check required fields
            required_fields = ["name", "name_variations", "sources"]

            for entity_id, entity_data in statistics.items():
                missing_fields = [field for field in required_fields if field not in entity_data]

                if missing_fields:
                    self.add_error(
                        check_name,
                        f"Entity '{entity_id}' missing fields: " f"{', '.join(missing_fields)}",
                    )
                    break  # Only report first instance

            self.pass_check(check_name)
            return statistics

        except Exception as e:
            self.add_error(check_name, f"Failed to load/validate: {e}")
            return {}

    def validate_network(self, filepath: Path) -> tuple[list, list]:
        """Validate entity_network.json."""
        check_name = "NETWORK_FILE"
        logging.info(f"Validating {filepath}...")

        try:
            with open(filepath) as f:
                data = json.load(f)

            nodes = data.get("nodes", [])
            edges = data.get("edges", [])

            if not nodes:
                self.add_error(check_name, "Empty nodes list")
                return [], []

            # Validate node IDs
            node_ids = set()
            for node in nodes:
                node_id = node.get("id")

                if self.validate_id_format(node_id, "network node"):
                    node_ids.add(node_id)

                if "name" not in node:
                    self.add_warning(check_name, f"Node '{node_id}' missing 'name' field")

            # Check node ID uniqueness
            if len(nodes) != len(node_ids):
                self.add_error(
                    check_name,
                    f"Duplicate node IDs: {len(nodes)} nodes, " f"{len(node_ids)} unique IDs",
                )

            # Validate edges
            orphaned_edges = []

            for edge in edges:
                source = edge.get("source")
                target = edge.get("target")

                if source not in node_ids:
                    orphaned_edges.append(f"{source} (source)")

                if target not in node_ids:
                    orphaned_edges.append(f"{target} (target)")

            if orphaned_edges:
                self.add_error(
                    check_name,
                    f"{len(orphaned_edges)} orphaned edge references: "
                    f"{', '.join(orphaned_edges[:5])}",
                )

            self.pass_check(check_name)
            return nodes, edges

        except Exception as e:
            self.add_error(check_name, f"Failed to load/validate: {e}")
            return [], []

    def validate_cross_file_integrity(
        self, statistics: dict, nodes: list, biographies: dict, tags: dict
    ):
        """Validate references between files."""
        check_name = "CROSS_FILE_INTEGRITY"
        logging.info("Validating cross-file references...")

        stats_ids = set(statistics.keys())
        network_ids = {node["id"] for node in nodes}

        # Check network nodes exist in statistics
        missing_in_stats = network_ids - stats_ids

        if missing_in_stats:
            self.add_error(
                check_name,
                f"{len(missing_in_stats)} network nodes not in statistics: "
                f"{', '.join(list(missing_in_stats)[:5])}",
            )

        # Check biographies reference valid entities
        if biographies:
            bio_ids = set(biographies.get("entities", {}).keys())
            invalid_bio_ids = bio_ids - stats_ids

            if invalid_bio_ids:
                self.add_warning(
                    check_name, f"{len(invalid_bio_ids)} biographies for non-existent entities"
                )

        # Check tags reference valid entities
        if tags:
            tag_ids = set(tags.get("entities", {}).keys())
            invalid_tag_ids = tag_ids - stats_ids

            if invalid_tag_ids:
                self.add_warning(
                    check_name, f"{len(invalid_tag_ids)} tags for non-existent entities"
                )

        self.pass_check(check_name)

    def benchmark_performance(self, statistics: dict) -> dict:
        """
        Benchmark ID lookup performance.

        Performance Targets:
        - ID lookup: <1ms (O(1) dict access)
        - Name→ID translation: <5ms
        - 1000 lookups: <100ms total
        """
        logging.info("Running performance benchmarks...")

        if not statistics:
            self.add_warning("PERFORMANCE", "No data for benchmarking")
            return {}

        # Benchmark 1: Direct ID lookup
        sample_ids = list(statistics.keys())[:100]

        start = time.perf_counter()
        for _ in range(1000):
            for entity_id in sample_ids:
                _ = statistics.get(entity_id)
        elapsed = time.perf_counter() - start

        avg_lookup_ms = (elapsed / (1000 * len(sample_ids))) * 1000

        # Benchmark 2: Name-based search (worst case)
        sample_names = [statistics[eid]["name"] for eid in sample_ids[:10]]

        start = time.perf_counter()
        for name in sample_names:
            # Linear search (worst case, should be avoided)
            for entity in statistics.values():
                if entity["name"] == name:
                    break
        elapsed = time.perf_counter() - start

        avg_name_search_ms = (elapsed / len(sample_names)) * 1000

        metrics = {
            "id_lookup_ms": round(avg_lookup_ms, 3),
            "name_search_ms": round(avg_name_search_ms, 3),
            "speedup_factor": round(avg_name_search_ms / avg_lookup_ms, 1),
        }

        logging.info(f"ID lookup: {metrics['id_lookup_ms']}ms")
        logging.info(f"Name search: {metrics['name_search_ms']}ms")
        logging.info(f"Speedup: {metrics['speedup_factor']}x faster")

        # Validate performance targets
        if avg_lookup_ms > 1.0:
            self.add_warning(
                "PERFORMANCE", f"ID lookup slower than target: {avg_lookup_ms}ms > 1.0ms"
            )

        return metrics

    def generate_report(self, performance_metrics: Optional[dict] = None) -> dict:
        """Generate validation report."""
        total_checks = self.checks_passed + self.checks_failed

        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "status": "PASSED" if self.checks_failed == 0 else "FAILED",
                "total_checks": total_checks,
                "passed": self.checks_passed,
                "failed": self.checks_failed,
                "warnings": len(self.warnings),
            },
            "errors": self.errors,
            "warnings": self.warnings,
        }

        if performance_metrics:
            report["performance"] = performance_metrics

        return report


def setup_logging(verbose: bool = False):
    """Configure logging."""
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_dir / "validation.log"), logging.StreamHandler()],
    )


def main():
    """Main validation execution."""
    parser = argparse.ArgumentParser(description="Validate entity ID migration")
    parser.add_argument("--benchmark", action="store_true", help="Run performance benchmarks")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--output", type=Path, help="Output report to JSON file")
    args = parser.parse_args()

    setup_logging(args.verbose)

    print("=" * 60)
    print("Entity ID Migration Validation")
    print("=" * 60)

    # Paths
    project_root = Path(__file__).parent.parent.parent
    metadata_dir = project_root / "data" / "metadata"

    statistics_file = metadata_dir / "entity_statistics.json"
    network_file = metadata_dir / "entity_network.json"
    biographies_file = metadata_dir / "entity_biographies.json"
    tags_file = metadata_dir / "entity_tags.json"

    # Validate
    validator = MigrationValidator()

    # Core files (required)
    statistics = validator.validate_statistics(statistics_file)
    nodes, _edges = validator.validate_network(network_file)

    # Optional files
    biographies = {}
    if biographies_file.exists():
        try:
            with open(biographies_file) as f:
                biographies = json.load(f)
        except Exception as e:
            validator.add_warning("BIOGRAPHIES", f"Failed to load: {e}")

    tags = {}
    if tags_file.exists():
        try:
            with open(tags_file) as f:
                tags = json.load(f)
        except Exception as e:
            validator.add_warning("TAGS", f"Failed to load: {e}")

    # Cross-file validation
    validator.validate_cross_file_integrity(statistics, nodes, biographies, tags)

    # Performance benchmarks
    performance_metrics = None
    if args.benchmark and statistics:
        performance_metrics = validator.benchmark_performance(statistics)

    # Generate report
    report = validator.generate_report(performance_metrics)

    # Print summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    print(f"Status: {report['summary']['status']}")
    print(f"Total checks: {report['summary']['total_checks']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Warnings: {report['summary']['warnings']}")

    if report["errors"]:
        print("\n❌ Errors:")
        for error in report["errors"][:10]:
            print(f"  [{error['check']}] {error['message']}")

        if len(report["errors"]) > 10:
            print(f"  ... and {len(report['errors']) - 10} more")

    if report["warnings"]:
        print("\n⚠️  Warnings:")
        for warning in report["warnings"][:5]:
            print(f"  [{warning['check']}] {warning['message']}")

    if performance_metrics:
        print("\n📊 Performance:")
        print(f"  ID lookup: {performance_metrics['id_lookup_ms']}ms")
        print(f"  Name search: {performance_metrics['name_search_ms']}ms")
        print(f"  Speedup: {performance_metrics['speedup_factor']}x")

    print("=" * 60)

    # Save report
    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved: {args.output}")

    return 0 if validator.checks_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
