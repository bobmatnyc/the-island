#!/usr/bin/env python3
"""
Test Disambiguation Setup (Without Full Model)

Verifies that the disambiguation system is properly set up
without requiring the full Mistral model to be downloaded.

Tests:
1. Script files exist and are executable
2. Entity index is loadable
3. Ambiguous entities are correctly identified
4. Backup/changelog directories can be created
5. Python dependencies are importable (basic ones)
"""

import json
import sys
from pathlib import Path


class SetupTester:
    """Test disambiguation setup"""

    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def test(self, name: str, condition: bool, error_msg: str = "", warning: bool = False):
        """Run a test and track results"""
        if condition:
            print(f"  ✅ {name}")
            self.passed += 1
        elif warning:
            print(f"  ⚠️  {name}: {error_msg}")
            self.warnings += 1
        else:
            print(f"  ❌ {name}: {error_msg}")
            self.failed += 1

    def run_all_tests(self):
        """Run all setup tests"""
        print("=" * 80)
        print("Disambiguation Setup Tests")
        print("=" * 80)

        # Test 1: File existence
        print("\n1️⃣  Testing file structure...")

        disambiguator_path = self.base_path / "scripts/analysis/mistral_entity_disambiguator.py"
        self.test(
            "Disambiguator script exists",
            disambiguator_path.exists(),
            f"Not found: {disambiguator_path}"
        )

        batch_script_path = self.base_path / "scripts/analysis/batch_entity_disambiguation.py"
        self.test(
            "Batch processing script exists",
            batch_script_path.exists(),
            f"Not found: {batch_script_path}"
        )

        setup_script_path = self.base_path / "scripts/analysis/setup_mistral.sh"
        self.test(
            "Setup script exists",
            setup_script_path.exists(),
            f"Not found: {setup_script_path}"
        )

        requirements_path = self.base_path / "requirements-mistral.txt"
        self.test(
            "Requirements file exists",
            requirements_path.exists(),
            f"Not found: {requirements_path}"
        )

        # Test 2: Documentation
        print("\n2️⃣  Testing documentation...")

        doc_path = self.base_path / "docs/MISTRAL_DISAMBIGUATION.md"
        self.test(
            "Full documentation exists",
            doc_path.exists(),
            f"Not found: {doc_path}"
        )

        readme_path = self.base_path / "scripts/analysis/README_MISTRAL.md"
        self.test(
            "Quick reference exists",
            readme_path.exists(),
            f"Not found: {readme_path}"
        )

        summary_path = self.base_path / "MISTRAL_INTEGRATION_SUMMARY.md"
        self.test(
            "Integration summary exists",
            summary_path.exists(),
            f"Not found: {summary_path}"
        )

        # Test 3: Entity index
        print("\n3️⃣  Testing entity index...")

        entity_index_path = self.base_path / "data/md/entities/ENTITIES_INDEX.json"
        entity_index_exists = entity_index_path.exists()
        self.test(
            "Entity index exists",
            entity_index_exists,
            f"Not found: {entity_index_path}"
        )

        if entity_index_exists:
            try:
                with open(entity_index_path) as f:
                    entity_index = json.load(f)

                entities = entity_index.get("entities", [])
                self.test(
                    f"Entity index loadable ({len(entities)} entities)",
                    len(entities) > 0,
                    "Entity index is empty"
                )

                # Count ambiguous entities
                ambiguous = self._count_ambiguous_entities(entities)
                self.test(
                    f"Ambiguous entities identified ({ambiguous['total']} total)",
                    ambiguous["total"] > 0,
                    "No ambiguous entities found"
                )

                print(f"     • High priority: {ambiguous['high']}")
                print(f"     • Medium priority: {ambiguous['medium']}")
                print(f"     • Low priority: {ambiguous['low']}")

            except Exception as e:
                self.test(
                    "Entity index parsable",
                    False,
                    f"Parse error: {e}"
                )

        # Test 4: Directory structure
        print("\n4️⃣  Testing directory structure...")

        metadata_dir = self.base_path / "data/metadata"
        self.test(
            "Metadata directory exists",
            metadata_dir.exists(),
            f"Not found: {metadata_dir}"
        )

        # Test 5: Python environment
        print("\n5️⃣  Testing Python environment...")

        python_version = sys.version_info
        version_ok = python_version.major == 3 and python_version.minor >= 9
        self.test(
            f"Python version ({python_version.major}.{python_version.minor})",
            version_ok,
            f"Python 3.9+ required, found {python_version.major}.{python_version.minor}"
        )

        # Test 6: Optional dependencies (warnings only)
        print("\n6️⃣  Testing optional dependencies...")

        try:
            import torch
            device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
            self.test(
                f"PyTorch installed (device: {device})",
                True,
                ""
            )
        except ImportError:
            self.test(
                "PyTorch installed",
                False,
                "Run: pip install torch",
                warning=True
            )

        try:
            import transformers
            self.test(
                "Transformers installed",
                True,
                ""
            )
        except ImportError:
            self.test(
                "Transformers installed",
                False,
                "Run: pip install transformers",
                warning=True
            )

        # Test 7: Write permissions
        print("\n7️⃣  Testing write permissions...")

        backup_dir = self.base_path / "data/metadata/entity_index_backups"
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            test_file = backup_dir / ".test_write"
            test_file.write_text("test")
            test_file.unlink()
            self.test(
                "Can create backup directory",
                True,
                ""
            )
        except Exception as e:
            self.test(
                "Can create backup directory",
                False,
                f"Permission error: {e}"
            )

        # Summary
        print("\n" + "=" * 80)
        print("Test Summary")
        print("=" * 80)
        print(f"  ✅ Passed: {self.passed}")
        print(f"  ❌ Failed: {self.failed}")
        print(f"  ⚠️  Warnings: {self.warnings}")

        if self.failed == 0 and self.warnings == 0:
            print("\n🎉 All tests passed! System is ready.")
            print("\nNext steps:")
            print("  1. Install dependencies: bash scripts/analysis/setup_mistral.sh")
            print("  2. Test disambiguation: python3 scripts/analysis/mistral_entity_disambiguator.py")
            print("  3. Process entities: python3 scripts/analysis/batch_entity_disambiguation.py --priority high --max-count 10")
            return 0
        if self.failed == 0:
            print("\n✅ Core tests passed. Warnings indicate missing optional dependencies.")
            print("\nNext steps:")
            print("  1. Install dependencies: bash scripts/analysis/setup_mistral.sh")
            print("  2. Test disambiguation: python3 scripts/analysis/mistral_entity_disambiguator.py")
            return 0
        print("\n❌ Some tests failed. Please fix issues before proceeding.")
        return 1

    def _count_ambiguous_entities(self, entities: list[dict]) -> dict[str, int]:
        """Count ambiguous entities by priority"""
        counts = {"high": 0, "medium": 0, "low": 0, "total": 0}

        for entity in entities:
            name = entity.get("name", "")
            flights = entity.get("flights", 0)

            is_ambiguous = False
            priority = "low"

            # Single name (no comma, no space)
            if "," not in name and " " not in name:
                is_ambiguous = True
                priority = "high" if flights > 10 else "medium"

            # Generic placeholder
            if "Female" in name or "Male" in name:
                is_ambiguous = True
                priority = "high"

            if is_ambiguous:
                counts[priority] += 1
                counts["total"] += 1

        return counts


def main():
    tester = SetupTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
