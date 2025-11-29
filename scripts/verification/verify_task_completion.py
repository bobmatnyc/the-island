#!/usr/bin/env python3
"""
Verification Script for Task Completion
Validates that both tasks were completed successfully.
"""

import json
import sys
from pathlib import Path


# Base directory
BASE_DIR = Path("/Users/masa/Projects/Epstein")


def verify_entity_removal():
    """Verify that 'No Passengers' entity was removed"""
    print("\n" + "=" * 60)
    print("TASK 1: Entity Removal Verification")
    print("=" * 60)

    issues = []

    # Check ENTITIES_INDEX.json
    entities_file = BASE_DIR / "data/md/entities/ENTITIES_INDEX.json"
    with open(entities_file) as f:
        data = json.load(f)

    # Check entities list
    entities = data.get("entities", [])
    no_passengers_entities = [e for e in entities if "No Passenger" in e.get("name", "")]

    print("\n📊 ENTITIES_INDEX.json")
    print(f"  Total entities: {len(entities)}")
    print("  Expected total: 1639")
    print(f"  'No Passengers' entities found: {len(no_passengers_entities)}")

    if len(entities) != 1639:
        issues.append(f"Entity count mismatch: {len(entities)} (expected 1639)")

    if len(no_passengers_entities) > 0:
        issues.append(f"Found {len(no_passengers_entities)} 'No Passengers' entities (should be 0)")
    else:
        print("  ✅ No invalid entities found")

    # Check total_entities stat
    total_stat = data.get("total_entities")
    if total_stat != len(entities):
        issues.append(f"total_entities stat mismatch: {total_stat} != {len(entities)}")
    else:
        print(f"  ✅ total_entities stat matches: {total_stat}")

    # Check for backups
    backup_files = list((BASE_DIR / "data/md/entities").glob("*.backup_*"))
    print(f"\n💾 Backups created: {len(backup_files)}")
    for backup in backup_files:
        print(f"  - {backup.name}")

    if len(backup_files) == 0:
        issues.append("No backup files found")
    else:
        print("  ✅ Backups available for rollback")

    # Summary
    print(f"\n{'='*60}")
    if len(issues) == 0:
        print("✅ TASK 1 VERIFICATION: PASSED")
    else:
        print("❌ TASK 1 VERIFICATION: FAILED")
        for issue in issues:
            print(f"  - {issue}")
    print(f"{'='*60}")

    return len(issues) == 0


def verify_pinned_headers():
    """Verify that pinned headers were implemented"""
    print("\n" + "=" * 60)
    print("TASK 2: Pinned Headers Verification")
    print("=" * 60)

    issues = []

    # Check HTML file
    html_file = BASE_DIR / "server/web/index.html"
    with open(html_file) as f:
        html_content = f.read()

    print("\n📄 index.html")

    # Check for CSS classes
    css_checks = [
        ("position: sticky", "Sticky positioning CSS"),
        ("panel-header", "Panel header class"),
        ("panel-stats", "Panel stats class"),
        ("panel-scrollable-content", "Scrollable content wrapper"),
        ("z-index: 101", "Proper z-index hierarchy"),
    ]

    for pattern, description in css_checks:
        count = html_content.count(pattern)
        if count > 0:
            print(f"  ✅ {description}: {count} occurrence(s)")
        else:
            issues.append(f"Missing: {description}")
            print(f"  ❌ {description}: NOT FOUND")

    # Check JavaScript file
    js_file = BASE_DIR / "server/web/app.js"
    with open(js_file) as f:
        js_content = f.read()

    print("\n📄 app.js")

    js_checks = [
        ('class="panel-header"', "Panel header in JS"),
        ('class="panel-scrollable-content"', "Scrollable wrapper in JS"),
        ("closeConnectionDetails", "Connection details close function"),
    ]

    for pattern, description in js_checks:
        count = js_content.count(pattern)
        if count > 0:
            print(f"  ✅ {description}: {count} occurrence(s)")
        else:
            issues.append(f"Missing in JS: {description}")
            print(f"  ❌ {description}: NOT FOUND")

    # Check syntax
    print("\n🔍 Syntax Validation")
    import subprocess

    try:
        result = subprocess.run(
            ["node", "-c", str(js_file)], check=False, capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            print("  ✅ JavaScript syntax valid")
        else:
            issues.append(f"JavaScript syntax error: {result.stderr}")
            print("  ❌ JavaScript syntax error")
    except Exception as e:
        print(f"  ⚠️  Could not validate JS syntax: {e}")

    # Summary
    print(f"\n{'='*60}")
    if len(issues) == 0:
        print("✅ TASK 2 VERIFICATION: PASSED")
    else:
        print("❌ TASK 2 VERIFICATION: FAILED")
        for issue in issues:
            print(f"  - {issue}")
    print(f"{'='*60}")

    return len(issues) == 0


def main():
    """Run all verification checks"""
    print("\n" + "=" * 60)
    print("EPSTEIN ARCHIVE - TASK COMPLETION VERIFICATION")
    print("=" * 60)
    print("Date: 2025-11-17")
    print("Tasks:")
    print("  1. Remove 'No Passengers' entity from data files")
    print("  2. Format secondary windows with pinned headers")

    task1_passed = verify_entity_removal()
    task2_passed = verify_pinned_headers()

    # Overall summary
    print("\n" + "=" * 60)
    print("OVERALL VERIFICATION RESULTS")
    print("=" * 60)
    print(f"Task 1 (Entity Removal): {'✅ PASSED' if task1_passed else '❌ FAILED'}")
    print(f"Task 2 (Pinned Headers): {'✅ PASSED' if task2_passed else '❌ FAILED'}")
    print("=" * 60)

    if task1_passed and task2_passed:
        print("\n🎉 ALL TASKS COMPLETED SUCCESSFULLY!")
        print("\nNext steps:")
        print("  1. Test in browser at http://localhost:3000")
        print("  2. Click entities in network view to test pinned headers")
        print("  3. Verify 'No Passengers' no longer appears in entity list")
        print("  4. Check that all detail panels have sticky headers")
        return 0
    print("\n⚠️  SOME TASKS FAILED VERIFICATION")
    print("Please review the issues above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
