#!/usr/bin/env python3
"""
Version validation script for Epstein Document Archive.

Validates version consistency across VERSION file, CHANGELOG.md,
and git tags.

Usage:
    python validate_version.py [--fix]
"""

import sys
import re
import subprocess
from pathlib import Path
from typing import Optional


class VersionValidator:
    """Validates version consistency across project files."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.version_file = project_root / "VERSION"
        self.changelog_file = project_root / "CHANGELOG.md"
        self.errors = []
        self.warnings = []

    def read_version_file(self) -> Optional[str]:
        """Read version from VERSION file."""
        if not self.version_file.exists():
            self.errors.append("VERSION file not found")
            return None

        version = self.version_file.read_text().strip()

        if not re.match(r"^\d+\.\d+\.\d+$", version):
            self.errors.append(
                f"Invalid version format in VERSION: {version}"
            )
            return None

        return version

    def read_changelog_version(self) -> Optional[str]:
        """Read latest version from CHANGELOG.md."""
        if not self.changelog_file.exists():
            self.warnings.append("CHANGELOG.md not found")
            return None

        content = self.changelog_file.read_text()

        # Find first version after [Unreleased]
        pattern = r"## \[(\d+\.\d+\.\d+)\]"
        matches = re.findall(pattern, content)

        if not matches:
            self.warnings.append("No versions found in CHANGELOG.md")
            return None

        return matches[0]

    def get_git_tags(self) -> list[str]:
        """Get all git tags matching version pattern."""
        try:
            result = subprocess.run(
                ["git", "tag", "-l", "v*"],
                capture_output=True,
                text=True,
                check=True,
            )

            tags = [
                tag.strip().lstrip("v")
                for tag in result.stdout.split("\n")
                if tag.strip()
            ]

            # Filter valid version tags
            version_tags = [
                tag
                for tag in tags
                if re.match(r"^\d+\.\d+\.\d+$", tag)
            ]

            return version_tags

        except subprocess.CalledProcessError:
            self.warnings.append("Not in a git repository")
            return []

    def validate(self) -> bool:
        """
        Validate version consistency.

        Returns:
            True if valid, False otherwise
        """
        # Read versions from different sources
        version_file = self.read_version_file()
        changelog_version = self.read_changelog_version()
        git_tags = self.get_git_tags()

        if not version_file:
            return False

        print(f"✓ VERSION file: {version_file}")

        # Check CHANGELOG.md
        if changelog_version:
            print(f"✓ CHANGELOG.md: {changelog_version}")

            if version_file != changelog_version:
                self.warnings.append(
                    f"VERSION ({version_file}) != CHANGELOG ({changelog_version})"
                )
        else:
            print("⚠ CHANGELOG.md: Not found or no versions")

        # Check git tags
        if git_tags:
            print(f"✓ Git tags: {len(git_tags)} found")

            if version_file in git_tags:
                print(f"✓ Current version has tag: v{version_file}")
            else:
                self.warnings.append(
                    f"Current version {version_file} not tagged"
                )

            # Check for unreleased tags
            latest_tag = max(
                git_tags, key=lambda v: [int(x) for x in v.split(".")]
            )
            print(f"✓ Latest git tag: v{latest_tag}")

            if version_file != latest_tag:
                self.warnings.append(
                    f"VERSION ({version_file}) != latest tag ({latest_tag})"
                )
        else:
            print("⚠ Git tags: None found")

        # Display validation results
        print()
        if self.errors:
            print("❌ Validation Errors:")
            for error in self.errors:
                print(f"  - {error}")
            return False

        if self.warnings:
            print("⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")

        if not self.errors and not self.warnings:
            print("✅ All version checks passed!")

        return len(self.errors) == 0

    def fix_issues(self) -> None:
        """Attempt to fix version inconsistencies."""
        version_file = self.read_version_file()

        if not version_file:
            print("❌ Cannot fix: VERSION file invalid or missing")
            return

        print(f"\n🔧 Fixing version inconsistencies for {version_file}...")

        # Fix CHANGELOG.md if needed
        changelog_version = self.read_changelog_version()
        if changelog_version and changelog_version != version_file:
            print(
                f"⚠️  CHANGELOG.md version mismatch: {changelog_version} → {version_file}"
            )
            print("   Manual fix required: Update CHANGELOG.md")

        # Suggest git tag if missing
        git_tags = self.get_git_tags()
        if version_file not in git_tags:
            print(
                f"\n💡 Suggested fix: Create git tag for v{version_file}"
            )
            print(f"   git tag -a v{version_file} -m 'Release {version_file}'")


def main():
    """Main entry point."""
    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    validator = VersionValidator(project_root)

    print("=" * 60)
    print("  Version Validation")
    print("=" * 60)
    print()

    # Check for --fix flag
    fix_mode = "--fix" in sys.argv

    # Run validation
    is_valid = validator.validate()

    # Fix issues if requested
    if fix_mode and not is_valid:
        validator.fix_issues()

    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
