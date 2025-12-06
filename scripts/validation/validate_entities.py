#!/usr/bin/env python3
"""
Entity Schema Validation Script

Validates transformed entity files against canonical schema.
Generates compliance reports and identifies schema violations.

Usage:
    python scripts/validation/validate_entities.py
    python scripts/validation/validate_entities.py --file data/transformed/entities_persons.json
    python scripts/validation/validate_entities.py --verbose
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re

try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    print("ERROR: jsonschema library required. Install with: pip install jsonschema")
    sys.exit(1)


@dataclass
class ValidationResult:
    """Results from validating a single entity file."""
    file_path: str
    valid: bool
    total_entities: int
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)


class EntityValidator:
    """Validates entity files against canonical schema."""

    def __init__(self, schema_path: str = "data/schemas/entity_schema.json"):
        """Initialize validator with schema.

        Args:
            schema_path: Path to entity schema JSON file
        """
        self.schema_path = Path(schema_path)
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")

        with open(self.schema_path) as f:
            self.schema = json.load(f)

        self.validator = Draft7Validator(self.schema)

    def validate_file(self, file_path: str, verbose: bool = False) -> ValidationResult:
        """Validate a single entity file.

        Args:
            file_path: Path to entity JSON file
            verbose: Print detailed validation messages

        Returns:
            ValidationResult with errors, warnings, and statistics
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return ValidationResult(
                file_path=str(file_path),
                valid=False,
                total_entities=0,
                errors=[{"error": "File not found", "path": str(file_path)}]
            )

        if verbose:
            print(f"\n{'='*80}")
            print(f"Validating: {file_path.name}")
            print(f"{'='*80}")

        try:
            with open(file_path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return ValidationResult(
                file_path=str(file_path),
                valid=False,
                total_entities=0,
                errors=[{"error": f"Invalid JSON: {e}", "path": str(file_path)}]
            )

        result = ValidationResult(
            file_path=str(file_path),
            valid=True,
            total_entities=data.get("metadata", {}).get("total_entities", 0)
        )

        # Validate against schema
        errors = list(self.validator.iter_errors(data))
        if errors:
            result.valid = False
            for error in errors:
                result.errors.append({
                    "error": error.message,
                    "path": ".".join(str(p) for p in error.absolute_path),
                    "validator": error.validator,
                    "schema_path": ".".join(str(p) for p in error.schema_path)
                })
                if verbose:
                    print(f"❌ ERROR: {error.message}")
                    print(f"   Path: {'.'.join(str(p) for p in error.absolute_path)}")

        # Additional semantic validation
        self._validate_entity_consistency(data, result, verbose)
        self._validate_classifications(data, result, verbose)
        self._validate_uuids(data, result, verbose)

        # Gather statistics
        result.stats = self._gather_statistics(data)

        if verbose:
            print(f"\n{'='*80}")
            print(f"Summary for {file_path.name}")
            print(f"{'='*80}")
            print(f"Status: {'✅ VALID' if result.valid else '❌ INVALID'}")
            print(f"Total Entities: {result.total_entities}")
            print(f"Errors: {len(result.errors)}")
            print(f"Warnings: {len(result.warnings)}")

        return result

    def _validate_entity_consistency(
        self,
        data: Dict[str, Any],
        result: ValidationResult,
        verbose: bool
    ) -> None:
        """Validate entity-level consistency rules.

        Checks:
        - canonical_name appears in aliases
        - normalized_name appears in aliases
        - entity_id matches UUID v5 pattern
        - metadata counts match actual data
        """
        entities = data.get("entities", {})
        metadata = data.get("metadata", {})

        # Check entity count matches metadata
        actual_count = len(entities)
        declared_count = metadata.get("total_entities", 0)
        if actual_count != declared_count:
            result.warnings.append({
                "warning": f"Entity count mismatch: declared {declared_count}, found {actual_count}",
                "path": "metadata.total_entities"
            })
            if verbose:
                print(f"⚠️  WARNING: Entity count mismatch (declared: {declared_count}, actual: {actual_count})")

        # Check each entity
        for entity_id, entity in entities.items():
            entity_path = f"entities.{entity_id}"

            # Canonical name in aliases
            canonical = entity.get("canonical_name", "")
            aliases = entity.get("aliases", [])
            if canonical and canonical not in aliases:
                result.warnings.append({
                    "warning": f"canonical_name '{canonical}' not in aliases",
                    "path": f"{entity_path}.aliases",
                    "entity_id": entity_id
                })

            # Normalized name in aliases
            normalized = entity.get("normalized_name", "")
            if normalized and normalized not in aliases:
                result.warnings.append({
                    "warning": f"normalized_name '{normalized}' not in aliases",
                    "path": f"{entity_path}.aliases",
                    "entity_id": entity_id
                })

            # Check entity_id format
            if entity_id != entity.get("entity_id"):
                result.errors.append({
                    "error": f"Entity key '{entity_id}' does not match entity_id field '{entity.get('entity_id')}'",
                    "path": entity_path,
                    "entity_id": entity_id
                })
                result.valid = False

    def _validate_classifications(
        self,
        data: Dict[str, Any],
        result: ValidationResult,
        verbose: bool
    ) -> None:
        """Validate classification objects have required fields."""
        entities = data.get("entities", {})

        for entity_id, entity in entities.items():
            classifications = entity.get("classifications", [])
            for i, cls in enumerate(classifications):
                cls_path = f"entities.{entity_id}.classifications[{i}]"

                # Check required fields
                required_fields = ["type", "label", "color", "bg_color", "priority"]
                for field in required_fields:
                    if field not in cls:
                        result.errors.append({
                            "error": f"Missing required field '{field}' in classification",
                            "path": cls_path,
                            "entity_id": entity_id
                        })
                        result.valid = False

                # Validate color format
                for color_field in ["color", "bg_color"]:
                    if color_field in cls:
                        color = cls[color_field]
                        if not re.match(r"^#[0-9A-F]{6}$", color, re.IGNORECASE):
                            result.errors.append({
                                "error": f"Invalid hex color format: {color}",
                                "path": f"{cls_path}.{color_field}",
                                "entity_id": entity_id
                            })
                            result.valid = False

                # Validate priority range
                priority = cls.get("priority")
                if priority is not None and not (1 <= priority <= 10):
                    result.errors.append({
                        "error": f"Priority {priority} out of range (1-10)",
                        "path": f"{cls_path}.priority",
                        "entity_id": entity_id
                    })
                    result.valid = False

    def _validate_uuids(
        self,
        data: Dict[str, Any],
        result: ValidationResult,
        verbose: bool
    ) -> None:
        """Validate UUID format and version."""
        # UUID v5 pattern (version field = 5, variant field = [89ab])
        uuid_v5_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
            re.IGNORECASE
        )

        entities = data.get("entities", {})
        for entity_id, entity in entities.items():
            if not uuid_v5_pattern.match(entity_id):
                result.errors.append({
                    "error": f"Invalid UUID v5 format: {entity_id}",
                    "path": f"entities.{entity_id}",
                    "entity_id": entity_id
                })
                result.valid = False

        # Check namespace UUID
        namespace = data.get("metadata", {}).get("namespace")
        if namespace and not re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", namespace, re.IGNORECASE):
            result.warnings.append({
                "warning": f"Invalid namespace UUID format: {namespace}",
                "path": "metadata.namespace"
            })

    def _gather_statistics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Gather statistics about entity data.

        Returns:
            Dictionary with counts, distributions, and quality metrics
        """
        entities = data.get("entities", {})

        stats = {
            "total_entities": len(entities),
            "entity_type": data.get("metadata", {}).get("entity_type"),
            "classifications": {},
            "with_biography": 0,
            "with_connections": 0,
            "quality_scores": [],
            "word_counts": [],
            "source_refs_count": 0
        }

        for entity in entities.values():
            # Classification distribution
            for cls in entity.get("classifications", []):
                cls_type = cls.get("type", "unknown")
                stats["classifications"][cls_type] = stats["classifications"].get(cls_type, 0) + 1

            # Biography presence
            if entity.get("biography"):
                stats["with_biography"] += 1

            # Connection count
            if entity.get("connection_count", 0) > 0:
                stats["with_connections"] += 1

            # Quality scores
            if "quality_score" in entity and entity["quality_score"] is not None:
                stats["quality_scores"].append(entity["quality_score"])

            # Word counts
            if "word_count" in entity and entity["word_count"] is not None:
                stats["word_counts"].append(entity["word_count"])

            # Source refs
            stats["source_refs_count"] += len(entity.get("source_refs", []))

        # Calculate averages
        if stats["quality_scores"]:
            stats["avg_quality_score"] = sum(stats["quality_scores"]) / len(stats["quality_scores"])

        if stats["word_counts"]:
            stats["avg_word_count"] = sum(stats["word_counts"]) / len(stats["word_counts"])

        return stats

    def validate_all(
        self,
        directory: str = "data/transformed",
        verbose: bool = False
    ) -> List[ValidationResult]:
        """Validate all entity files in directory.

        Args:
            directory: Directory containing entity JSON files
            verbose: Print detailed validation messages

        Returns:
            List of ValidationResult objects
        """
        directory = Path(directory)
        if not directory.exists():
            print(f"ERROR: Directory not found: {directory}")
            return []

        entity_files = sorted(directory.glob("entities_*.json"))
        if not entity_files:
            print(f"WARNING: No entity files found in {directory}")
            return []

        results = []
        for file_path in entity_files:
            result = self.validate_file(str(file_path), verbose=verbose)
            results.append(result)

        return results

    def generate_report(
        self,
        results: List[ValidationResult],
        output_path: str = None
    ) -> str:
        """Generate validation report.

        Args:
            results: List of validation results
            output_path: Optional path to save report

        Returns:
            Report string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("ENTITY SCHEMA VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append(f"Schema: {self.schema_path}")
        lines.append(f"Files Validated: {len(results)}")
        lines.append("")

        # Overall summary
        total_entities = sum(r.total_entities for r in results)
        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)
        valid_files = sum(1 for r in results if r.valid)

        lines.append("OVERALL SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Total Entities: {total_entities:,}")
        lines.append(f"Valid Files: {valid_files}/{len(results)}")
        lines.append(f"Total Errors: {total_errors}")
        lines.append(f"Total Warnings: {total_warnings}")
        lines.append("")

        # Per-file results
        for result in results:
            file_name = Path(result.file_path).name
            status = "✅ VALID" if result.valid else "❌ INVALID"

            lines.append(f"{file_name}")
            lines.append("-" * 80)
            lines.append(f"Status: {status}")
            lines.append(f"Entities: {result.total_entities:,}")
            lines.append(f"Errors: {len(result.errors)}")
            lines.append(f"Warnings: {len(result.warnings)}")

            # Statistics
            stats = result.stats
            if stats:
                lines.append(f"\nStatistics:")
                lines.append(f"  - With Biography: {stats.get('with_biography', 0):,}")
                lines.append(f"  - With Connections: {stats.get('with_connections', 0):,}")
                if "avg_quality_score" in stats:
                    lines.append(f"  - Avg Quality Score: {stats['avg_quality_score']:.2f}")
                if "avg_word_count" in stats:
                    lines.append(f"  - Avg Word Count: {stats['avg_word_count']:.0f}")
                lines.append(f"  - Source References: {stats.get('source_refs_count', 0):,}")

                # Top classifications
                classifications = stats.get("classifications", {})
                if classifications:
                    lines.append(f"\n  Top Classifications:")
                    sorted_cls = sorted(classifications.items(), key=lambda x: x[1], reverse=True)
                    for cls_type, count in sorted_cls[:5]:
                        lines.append(f"    - {cls_type}: {count:,}")

            # Errors
            if result.errors:
                lines.append(f"\n  Errors ({len(result.errors)}):")
                for i, error in enumerate(result.errors[:10], 1):  # Show first 10
                    lines.append(f"    {i}. {error.get('error', 'Unknown error')}")
                    if 'path' in error:
                        lines.append(f"       Path: {error['path']}")
                if len(result.errors) > 10:
                    lines.append(f"    ... and {len(result.errors) - 10} more")

            # Warnings
            if result.warnings:
                lines.append(f"\n  Warnings ({len(result.warnings)}):")
                for i, warning in enumerate(result.warnings[:10], 1):  # Show first 10
                    lines.append(f"    {i}. {warning.get('warning', 'Unknown warning')}")
                    if 'path' in warning:
                        lines.append(f"       Path: {warning['path']}")
                if len(result.warnings) > 10:
                    lines.append(f"    ... and {len(result.warnings) - 10} more")

            lines.append("")

        report = "\n".join(lines)

        # Save to file if requested
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(report)
            print(f"Report saved to: {output_path}")

        return report


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate entity files against canonical schema"
    )
    parser.add_argument(
        "--file",
        help="Validate specific file (default: validate all in data/transformed/)"
    )
    parser.add_argument(
        "--schema",
        default="data/schemas/entity_schema.json",
        help="Path to schema file"
    )
    parser.add_argument(
        "--output",
        help="Save report to file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed validation messages"
    )

    args = parser.parse_args()

    try:
        validator = EntityValidator(schema_path=args.schema)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Validate files
    if args.file:
        results = [validator.validate_file(args.file, verbose=args.verbose)]
    else:
        results = validator.validate_all(verbose=args.verbose)

    if not results:
        print("No files validated")
        sys.exit(1)

    # Generate and display report
    report = validator.generate_report(results, output_path=args.output)

    if not args.output:
        print("\n" + report)

    # Exit with error code if any files invalid
    if any(not r.valid for r in results):
        sys.exit(1)

    print("\n✅ All files valid!")


if __name__ == "__main__":
    main()
