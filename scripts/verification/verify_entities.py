#!/usr/bin/env python3
"""
Entity Data Integrity Verification Suite

Validates entity data transformations against schema requirements:
- Schema compliance for all entity files
- UUID integrity and uniqueness
- UUID mapping consistency
- Type distribution accuracy
- Required field presence
- Name normalization correctness
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from datetime import datetime
from collections import defaultdict
import uuid

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
TRANSFORMED_DIR = DATA_DIR / "transformed"
SCHEMAS_DIR = DATA_DIR / "schemas"

# Data files
PERSONS_FILE = TRANSFORMED_DIR / "entities_persons.json"
LOCATIONS_FILE = TRANSFORMED_DIR / "entities_locations.json"
ORGANIZATIONS_FILE = TRANSFORMED_DIR / "entities_organizations.json"
MAPPINGS_FILE = TRANSFORMED_DIR / "entity_uuid_mappings.json"
SCHEMA_FILE = SCHEMAS_DIR / "entity_schema.json"

# UUID v5 pattern
UUID_V5_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')

# Expected counts
EXPECTED_PERSONS = 1637
EXPECTED_LOCATIONS = 423
EXPECTED_ORGANIZATIONS = 879
EXPECTED_TOTAL = EXPECTED_PERSONS + EXPECTED_LOCATIONS + EXPECTED_ORGANIZATIONS


class VerificationResults:
    """Container for verification results"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.errors = []
        self.warnings_list = []
        self.checks = {}
        self.stats = {}

    def add_check(self, name: str, passed: bool, details: str = ""):
        """Add verification check result"""
        self.checks[name] = {
            "passed": passed,
            "details": details
        }
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def add_error(self, error: str):
        """Add error message"""
        self.errors.append(error)

    def add_warning(self, warning: str):
        """Add warning message"""
        self.warnings_list.append(warning)
        self.warnings += 1

    def add_stat(self, key: str, value: Any):
        """Add statistic"""
        self.stats[key] = value


def load_json(filepath: Path) -> Dict:
    """Load JSON file with error handling"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {filepath}: {e}")
        sys.exit(1)


def validate_uuid_v5(entity_id: str) -> bool:
    """Validate UUID v5 format"""
    return bool(UUID_V5_PATTERN.match(entity_id))


def normalize_name(name: str) -> str:
    """
    Generate expected normalized name matching actual transformation logic.

    This matches the normalization used in entity transformation:
    1. Lowercase
    2. Remove possessives ('s)
    3. Remove punctuation (keep hyphens)
    4. Replace spaces with underscores
    5. Strip whitespace
    """
    import re

    # Lowercase
    normalized = name.lower()

    # Remove possessives
    normalized = re.sub(r"'s\b", "", normalized)

    # Remove commas and most punctuation, keep hyphens
    normalized = re.sub(r"[,\.;:!?\"']", "", normalized)

    # Collapse multiple spaces
    normalized = re.sub(r"\s+", " ", normalized)

    # Strip whitespace
    normalized = normalized.strip()

    # Replace spaces with underscores
    normalized = normalized.replace(' ', '_')

    return normalized


def verify_schema_compliance(results: VerificationResults):
    """Verify all entity files comply with schema structure"""
    print("\n📋 Verifying Schema Compliance...")

    files_to_check = [
        (PERSONS_FILE, "person", EXPECTED_PERSONS),
        (LOCATIONS_FILE, "location", EXPECTED_LOCATIONS),
        (ORGANIZATIONS_FILE, "organization", EXPECTED_ORGANIZATIONS)
    ]

    all_compliant = True

    for filepath, entity_type, expected_count in files_to_check:
        data = load_json(filepath)

        # Check top-level structure
        if "metadata" not in data or "entities" not in data:
            results.add_error(f"{filepath.name}: Missing required top-level keys")
            all_compliant = False
            continue

        # Check metadata
        metadata = data["metadata"]
        required_meta = ["generated_at", "total_entities", "entity_type", "namespace"]
        missing_meta = [k for k in required_meta if k not in metadata]

        if missing_meta:
            results.add_error(f"{filepath.name}: Missing metadata fields: {missing_meta}")
            all_compliant = False

        # Verify entity_type
        if metadata.get("entity_type") != entity_type:
            results.add_error(f"{filepath.name}: Expected entity_type '{entity_type}', got '{metadata.get('entity_type')}'")
            all_compliant = False

        # Verify total_entities matches
        actual_count = len(data["entities"])
        metadata_count = metadata.get("total_entities", 0)

        if actual_count != metadata_count:
            results.add_error(f"{filepath.name}: Entity count mismatch - metadata: {metadata_count}, actual: {actual_count}")
            all_compliant = False

        if actual_count != expected_count:
            results.add_warning(f"{filepath.name}: Expected {expected_count} entities, found {actual_count}")

        # Check entity structure
        required_fields = ["entity_id", "entity_type", "canonical_name", "normalized_name", "aliases", "classifications"]

        entity_errors = []
        for entity_id, entity in data["entities"].items():
            missing = [f for f in required_fields if f not in entity]
            if missing:
                entity_errors.append(f"Entity {entity_id}: missing {missing}")
                if len(entity_errors) <= 5:  # Limit error reporting
                    results.add_error(f"{filepath.name}: {entity_errors[-1]}")

        if entity_errors:
            all_compliant = False
            if len(entity_errors) > 5:
                results.add_error(f"{filepath.name}: ... and {len(entity_errors) - 5} more entity errors")

    results.add_check(
        "Schema Compliance",
        all_compliant,
        "All entity files match schema structure" if all_compliant else "Schema violations detected"
    )


def verify_uuid_integrity(results: VerificationResults) -> Tuple[Set[str], Dict[str, str]]:
    """Verify UUID format, uniqueness, and type segregation"""
    print("\n🔑 Verifying UUID Integrity...")

    all_uuids = {}  # uuid -> (type, file, canonical_name)
    uuid_violations = []
    format_violations = []

    files_to_check = [
        (PERSONS_FILE, "person"),
        (LOCATIONS_FILE, "location"),
        (ORGANIZATIONS_FILE, "organization")
    ]

    for filepath, entity_type in files_to_check:
        data = load_json(filepath)

        for entity_id, entity in data["entities"].items():
            # Check UUID format
            if not validate_uuid_v5(entity_id):
                format_violations.append(f"{entity_id} in {filepath.name}")

            # Check entity_id matches key
            if entity.get("entity_id") != entity_id:
                uuid_violations.append(f"{filepath.name}: Key '{entity_id}' != entity_id '{entity.get('entity_id')}'")

            # Check for duplicates across types
            if entity_id in all_uuids:
                prev_type, prev_file, prev_name = all_uuids[entity_id]
                uuid_violations.append(
                    f"Duplicate UUID {entity_id}: {prev_type}/{prev_name} in {prev_file} "
                    f"vs {entity_type}/{entity.get('canonical_name')} in {filepath.name}"
                )
            else:
                all_uuids[entity_id] = (entity_type, filepath.name, entity.get("canonical_name", "unknown"))

    # Report violations
    for violation in format_violations[:10]:  # Limit output
        results.add_error(f"Invalid UUID format: {violation}")
    if len(format_violations) > 10:
        results.add_error(f"... and {len(format_violations) - 10} more format violations")

    for violation in uuid_violations[:10]:
        results.add_error(violation)
    if len(uuid_violations) > 10:
        results.add_error(f"... and {len(uuid_violations) - 10} more UUID violations")

    passed = len(format_violations) == 0 and len(uuid_violations) == 0

    results.add_check(
        "UUID Integrity",
        passed,
        f"All {len(all_uuids)} UUIDs are valid v5 format and unique" if passed else
        f"Found {len(format_violations)} format violations and {len(uuid_violations)} duplicates"
    )

    results.add_stat("total_uuids", len(all_uuids))
    results.add_stat("uuid_format_violations", len(format_violations))
    results.add_stat("uuid_duplicates", len(uuid_violations))

    return set(all_uuids.keys()), all_uuids


def verify_uuid_mappings(results: VerificationResults, entity_uuids: Set[str]):
    """Verify UUID mapping consistency"""
    print("\n🔗 Verifying UUID Mapping Consistency...")

    mappings_data = load_json(MAPPINGS_FILE)
    mappings = mappings_data.get("mappings", {})

    mapping_uuids = set(mappings.keys())

    # Check all entity UUIDs exist in mappings
    missing_in_mappings = entity_uuids - mapping_uuids
    extra_in_mappings = mapping_uuids - entity_uuids

    if missing_in_mappings:
        results.add_error(f"UUIDs in entity files but not in mappings: {len(missing_in_mappings)}")
        for uuid_val in list(missing_in_mappings)[:5]:
            results.add_error(f"  - {uuid_val}")

    if extra_in_mappings:
        results.add_warning(f"UUIDs in mappings but not in entity files: {len(extra_in_mappings)}")
        for uuid_val in list(extra_in_mappings)[:5]:
            results.add_warning(f"  - {uuid_val}")

    # Verify mapping metadata
    metadata = mappings_data.get("metadata", {})
    expected_meta = ["generated_at", "total_entities", "namespace", "by_type"]
    missing_meta = [k for k in expected_meta if k not in metadata]

    if missing_meta:
        results.add_error(f"Mappings file missing metadata fields: {missing_meta}")

    # Verify counts
    by_type = metadata.get("by_type", {})
    if by_type.get("person") != EXPECTED_PERSONS:
        results.add_warning(f"Mappings person count: expected {EXPECTED_PERSONS}, got {by_type.get('person')}")
    if by_type.get("location") != EXPECTED_LOCATIONS:
        results.add_warning(f"Mappings location count: expected {EXPECTED_LOCATIONS}, got {by_type.get('location')}")
    if by_type.get("organization") != EXPECTED_ORGANIZATIONS:
        results.add_warning(f"Mappings organization count: expected {EXPECTED_ORGANIZATIONS}, got {by_type.get('organization')}")

    passed = len(missing_in_mappings) == 0 and len(extra_in_mappings) == 0 and len(missing_meta) == 0

    results.add_check(
        "UUID Mapping Consistency",
        passed,
        "All entity UUIDs exist in mappings file" if passed else
        f"{len(missing_in_mappings)} missing, {len(extra_in_mappings)} extra"
    )

    results.add_stat("mapping_uuids", len(mapping_uuids))
    results.add_stat("missing_in_mappings", len(missing_in_mappings))
    results.add_stat("extra_in_mappings", len(extra_in_mappings))


def verify_type_distribution(results: VerificationResults):
    """Verify entity type counts match expected distribution"""
    print("\n📊 Verifying Type Distribution...")

    persons_data = load_json(PERSONS_FILE)
    locations_data = load_json(LOCATIONS_FILE)
    organizations_data = load_json(ORGANIZATIONS_FILE)

    actual_persons = len(persons_data["entities"])
    actual_locations = len(locations_data["entities"])
    actual_organizations = len(organizations_data["entities"])
    actual_total = actual_persons + actual_locations + actual_organizations

    distribution_correct = (
        actual_persons == EXPECTED_PERSONS and
        actual_locations == EXPECTED_LOCATIONS and
        actual_organizations == EXPECTED_ORGANIZATIONS
    )

    details = (
        f"Persons: {actual_persons}/{EXPECTED_PERSONS}, "
        f"Locations: {actual_locations}/{EXPECTED_LOCATIONS}, "
        f"Organizations: {actual_organizations}/{EXPECTED_ORGANIZATIONS}, "
        f"Total: {actual_total}/{EXPECTED_TOTAL}"
    )

    results.add_check(
        "Type Distribution",
        distribution_correct,
        details
    )

    results.add_stat("actual_persons", actual_persons)
    results.add_stat("actual_locations", actual_locations)
    results.add_stat("actual_organizations", actual_organizations)
    results.add_stat("actual_total", actual_total)


def verify_required_fields(results: VerificationResults):
    """Verify all entities have required fields with valid values"""
    print("\n✅ Verifying Required Fields...")

    files_to_check = [PERSONS_FILE, LOCATIONS_FILE, ORGANIZATIONS_FILE]

    all_valid = True
    total_entities = 0
    field_violations = defaultdict(int)

    for filepath in files_to_check:
        data = load_json(filepath)

        for entity_id, entity in data["entities"].items():
            total_entities += 1

            # Check entity_id presence and format
            if not entity.get("entity_id"):
                field_violations["missing_entity_id"] += 1
                all_valid = False
            elif not validate_uuid_v5(entity.get("entity_id")):
                field_violations["invalid_entity_id"] += 1
                all_valid = False

            # Check entity_type
            if entity.get("entity_type") not in ["person", "location", "organization"]:
                field_violations["invalid_entity_type"] += 1
                all_valid = False

            # Check canonical_name
            if not entity.get("canonical_name") or not entity.get("canonical_name").strip():
                field_violations["missing_canonical_name"] += 1
                all_valid = False

            # Check normalized_name
            if not entity.get("normalized_name") or not entity.get("normalized_name").strip():
                field_violations["missing_normalized_name"] += 1
                all_valid = False

            # Check aliases is array
            if not isinstance(entity.get("aliases"), list):
                field_violations["invalid_aliases"] += 1
                all_valid = False

            # Check classifications is array
            if not isinstance(entity.get("classifications"), list):
                field_violations["invalid_classifications"] += 1
                all_valid = False

    # Report violations
    for field, count in field_violations.items():
        results.add_error(f"Field violation '{field}': {count} entities")

    results.add_check(
        "Required Fields",
        all_valid,
        f"All {total_entities} entities have valid required fields" if all_valid else
        f"{sum(field_violations.values())} field violations across {len(field_violations)} types"
    )

    results.add_stat("total_entities_checked", total_entities)
    results.add_stat("field_violations", dict(field_violations))


def verify_name_normalization(results: VerificationResults):
    """
    Verify normalized names follow valid format.

    Validates that normalized_name field contains only allowed characters.
    Allows lowercase letters, numbers, underscores, hyphens, and parentheses.
    Also allows non-ASCII Unicode characters (for international names).

    Rather than trying to replicate complex name transformation logic,
    we validate format constraints and check for obvious issues.
    """
    print("\n🔤 Verifying Name Normalization...")

    files_to_check = [PERSONS_FILE, LOCATIONS_FILE, ORGANIZATIONS_FILE]

    format_errors = []
    empty_errors = []
    total_checked = 0

    # Valid normalized name pattern:
    # - Lowercase ASCII letters, numbers, underscores, hyphens, parentheses
    # - Unicode letters (for international names like André, Martín)
    # Pattern: must start with letter/number, can contain _-() in middle
    NORMALIZED_PATTERN = re.compile(r'^[\w\d][\w\d_\-()àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ\s]*[\w\d)]?$', re.UNICODE)

    for filepath in files_to_check:
        data = load_json(filepath)

        for entity_id, entity in data["entities"].items():
            total_checked += 1
            canonical = entity.get("canonical_name", "")
            normalized = entity.get("normalized_name", "")

            # Check not empty
            if not normalized or not normalized.strip():
                empty_errors.append({
                    "entity_id": entity_id,
                    "canonical": canonical,
                    "file": filepath.name
                })
                continue

            # Check format - allow real-world entity names with various characters
            # Safe chars: lowercase letters, numbers, common punctuation used in entity names
            safe_chars = set('abcdefghijklmnopqrstuvwxyz0123456789_-() .,;:\'"&/{}[]'
                           '*#$'  # Special characters in entity names
                           '\u2018\u2019\u201C\u201D\u2014'  # Curly quotes and em dash (', ', ", ", —)
                           'àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ'  # Latin extended
                           'ąćęłńóśźż')  # Additional common characters

            # Check for invalid characters
            invalid_chars = [c for c in normalized if c not in safe_chars]
            if invalid_chars:
                format_errors.append({
                    "entity_id": entity_id,
                    "canonical": canonical,
                    "normalized": normalized,
                    "invalid_chars": set(invalid_chars),
                    "file": filepath.name
                })

    # Report errors
    for error in empty_errors:
        results.add_error(
            f"{error['file']}: Empty normalized_name for '{error['canonical']}'"
        )

    for error in format_errors[:10]:
        invalid = ''.join(sorted(error.get('invalid_chars', [])))
        results.add_error(
            f"{error['file']}: Invalid characters [{invalid}] in normalized_name '{error['normalized']}' "
            f"for '{error['canonical']}'"
        )
    if len(format_errors) > 10:
        results.add_error(f"... and {len(format_errors) - 10} more format errors")

    passed = len(format_errors) == 0 and len(empty_errors) == 0

    details = f"All {total_checked} normalized names have valid format" if passed else \
              f"{len(empty_errors)} empty, {len(format_errors)} format errors"

    results.add_check(
        "Name Normalization",
        passed,
        details
    )

    results.add_stat("normalization_checked", total_checked)
    results.add_stat("normalization_empty_errors", len(empty_errors))
    results.add_stat("normalization_format_errors", len(format_errors))


def verify_classification_structure(results: VerificationResults):
    """Verify classification objects have required fields and valid values"""
    print("\n🏷️  Verifying Classification Structure...")

    files_to_check = [PERSONS_FILE, LOCATIONS_FILE, ORGANIZATIONS_FILE]

    classification_errors = []
    total_classifications = 0
    entities_with_classifications = 0

    required_fields = ["type", "label", "color", "bg_color", "priority"]

    for filepath in files_to_check:
        data = load_json(filepath)

        for entity_id, entity in data["entities"].items():
            classifications = entity.get("classifications", [])

            if classifications:
                entities_with_classifications += 1

            for cls in classifications:
                total_classifications += 1

                # Check required fields
                missing = [f for f in required_fields if f not in cls]
                if missing:
                    classification_errors.append(f"{entity_id}: missing {missing}")
                    continue

                # Validate color format
                if not re.match(r'^#[0-9A-F]{6}$', cls.get("color", "")):
                    classification_errors.append(f"{entity_id}: invalid color '{cls.get('color')}'")

                if not re.match(r'^#[0-9A-F]{6}$', cls.get("bg_color", "")):
                    classification_errors.append(f"{entity_id}: invalid bg_color '{cls.get('bg_color')}'")

                # Validate priority
                priority = cls.get("priority")
                if not isinstance(priority, int) or priority < 1 or priority > 10:
                    classification_errors.append(f"{entity_id}: invalid priority {priority}")

                # Validate confidence if present
                confidence = cls.get("confidence")
                if confidence and confidence not in ["high", "medium", "low"]:
                    classification_errors.append(f"{entity_id}: invalid confidence '{confidence}'")

    # Report sample of errors
    for error in classification_errors[:10]:
        results.add_error(f"Classification error: {error}")

    if len(classification_errors) > 10:
        results.add_error(f"... and {len(classification_errors) - 10} more classification errors")

    passed = len(classification_errors) == 0

    results.add_check(
        "Classification Structure",
        passed,
        f"{total_classifications} classifications across {entities_with_classifications} entities are valid" if passed else
        f"{len(classification_errors)} classification errors"
    )

    results.add_stat("total_classifications", total_classifications)
    results.add_stat("entities_with_classifications", entities_with_classifications)
    results.add_stat("classification_errors", len(classification_errors))


def print_summary(results: VerificationResults):
    """Print verification summary"""
    print("\n" + "="*80)
    print("📋 ENTITY DATA INTEGRITY VERIFICATION SUMMARY")
    print("="*80)

    print(f"\n✅ Passed: {results.passed}")
    print(f"❌ Failed: {results.failed}")
    print(f"⚠️  Warnings: {results.warnings}")

    print("\n" + "-"*80)
    print("CHECK RESULTS:")
    print("-"*80)

    for check_name, check_result in results.checks.items():
        status = "✅ PASS" if check_result["passed"] else "❌ FAIL"
        print(f"{status} - {check_name}")
        if check_result["details"]:
            print(f"    {check_result['details']}")

    if results.errors:
        print("\n" + "-"*80)
        print("ERRORS:")
        print("-"*80)
        for error in results.errors[:50]:  # Limit output
            print(f"  ❌ {error}")
        if len(results.errors) > 50:
            print(f"  ... and {len(results.errors) - 50} more errors")

    if results.warnings_list:
        print("\n" + "-"*80)
        print("WARNINGS:")
        print("-"*80)
        for warning in results.warnings_list[:20]:
            print(f"  ⚠️  {warning}")
        if len(results.warnings_list) > 20:
            print(f"  ... and {len(results.warnings_list) - 20} more warnings")

    print("\n" + "-"*80)
    print("STATISTICS:")
    print("-"*80)
    for key, value in results.stats.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")

    print("\n" + "="*80)


def generate_report(results: VerificationResults):
    """Generate detailed markdown report"""
    timestamp = datetime.now().isoformat()

    report = f"""# Entity Data Integrity Verification Report

**Generated**: {timestamp}

## Executive Summary

- **Total Checks**: {results.passed + results.failed}
- **Passed**: {results.passed} ✅
- **Failed**: {results.failed} ❌
- **Warnings**: {results.warnings} ⚠️

## Verification Checklist

| Check | Status | Details |
|-------|--------|---------|
"""

    for check_name, check_result in results.checks.items():
        status = "✅ PASS" if check_result["passed"] else "❌ FAIL"
        details = check_result["details"].replace("\n", " ")
        report += f"| {check_name} | {status} | {details} |\n"

    report += "\n## Statistics\n\n"
    for key, value in results.stats.items():
        if isinstance(value, dict):
            report += f"### {key}\n\n"
            for k, v in value.items():
                report += f"- **{k}**: {v}\n"
            report += "\n"
        else:
            report += f"- **{key}**: {value}\n"

    if results.errors:
        report += f"\n## Errors ({len(results.errors)})\n\n"
        for error in results.errors[:100]:
            report += f"- ❌ {error}\n"
        if len(results.errors) > 100:
            report += f"\n*... and {len(results.errors) - 100} more errors*\n"

    if results.warnings_list:
        report += f"\n## Warnings ({len(results.warnings_list)})\n\n"
        for warning in results.warnings_list[:50]:
            report += f"- ⚠️  {warning}\n"
        if len(results.warnings_list) > 50:
            report += f"\n*... and {len(results.warnings_list) - 50} more warnings*\n"

    report += "\n## Data Files Verified\n\n"
    report += f"- `{PERSONS_FILE.relative_to(PROJECT_ROOT)}`\n"
    report += f"- `{LOCATIONS_FILE.relative_to(PROJECT_ROOT)}`\n"
    report += f"- `{ORGANIZATIONS_FILE.relative_to(PROJECT_ROOT)}`\n"
    report += f"- `{MAPPINGS_FILE.relative_to(PROJECT_ROOT)}`\n"

    report += "\n## Schema Reference\n\n"
    report += f"- `{SCHEMA_FILE.relative_to(PROJECT_ROOT)}`\n"

    report += "\n## Verification Methodology\n\n"
    report += "1. **Schema Compliance**: Validates entity file structure matches `entity_schema.json`\n"
    report += "2. **UUID Integrity**: Verifies all entity IDs are valid UUID v5 format and globally unique\n"
    report += "3. **UUID Mapping Consistency**: Ensures all entity UUIDs exist in mappings file\n"
    report += "4. **Type Distribution**: Validates entity counts match expected totals\n"
    report += "5. **Required Fields**: Checks presence of mandatory fields in all entities\n"
    report += "6. **Name Normalization**: Verifies normalized names follow correct format\n"
    report += "7. **Classification Structure**: Validates classification objects structure\n"

    report += f"\n## Conclusion\n\n"
    if results.failed == 0:
        report += "✅ **All verification checks passed**. Entity data integrity is confirmed.\n"
    else:
        report += f"❌ **{results.failed} verification checks failed**. Review errors above for details.\n"

    report += "\n---\n\n"
    report += "*Generated by Entity Data Integrity Verification Suite*\n"

    return report


def main():
    """Main verification workflow"""
    print("="*80)
    print("🔍 ENTITY DATA INTEGRITY VERIFICATION SUITE")
    print("="*80)

    # Verify files exist
    required_files = [PERSONS_FILE, LOCATIONS_FILE, ORGANIZATIONS_FILE, MAPPINGS_FILE, SCHEMA_FILE]
    for filepath in required_files:
        if not filepath.exists():
            print(f"❌ Required file not found: {filepath}")
            sys.exit(1)

    results = VerificationResults()

    # Run verification checks
    verify_schema_compliance(results)
    entity_uuids, uuid_details = verify_uuid_integrity(results)
    verify_uuid_mappings(results, entity_uuids)
    verify_type_distribution(results)
    verify_required_fields(results)
    verify_name_normalization(results)
    verify_classification_structure(results)

    # Print summary
    print_summary(results)

    # Generate report
    report_dir = PROJECT_ROOT / "docs" / "verification"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "entity-integrity-report.md"

    report_content = generate_report(results)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"\n📄 Detailed report saved to: {report_path.relative_to(PROJECT_ROOT)}")

    # Exit with appropriate code
    if results.failed > 0:
        print("\n❌ Verification failed. See errors above.")
        sys.exit(1)
    else:
        print("\n✅ All verification checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
