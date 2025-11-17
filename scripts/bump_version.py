#!/usr/bin/env python3
"""
Version bumping script for Epstein Document Archive.

Supports semantic versioning (major.minor.patch) with automatic
CHANGELOG.md updates and git integration.

Usage:
    python bump_version.py [major|minor|patch]
"""

import re
import sys
from datetime import datetime
from pathlib import Path


class VersionBumper:
    """Handles semantic version bumping and changelog updates."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.version_file = project_root / "VERSION"
        self.changelog_file = project_root / "CHANGELOG.md"

    def read_version(self) -> tuple[int, int, int]:
        """Read current version from VERSION file."""
        if not self.version_file.exists():
            print(f"Error: VERSION file not found at {self.version_file}")
            sys.exit(1)

        version_str = self.version_file.read_text().strip()
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version_str)

        if not match:
            print(f"Error: Invalid version format: {version_str}")
            print("Expected format: major.minor.patch (e.g., 1.2.3)")
            sys.exit(1)

        major, minor, patch = map(int, match.groups())
        return major, minor, patch

    def write_version(self, major: int, minor: int, patch: int) -> str:
        """Write new version to VERSION file."""
        new_version = f"{major}.{minor}.{patch}"
        self.version_file.write_text(new_version)
        return new_version

    def bump_version(self, bump_type: str) -> str:
        """
        Bump version according to type.

        Args:
            bump_type: One of 'major', 'minor', or 'patch'

        Returns:
            New version string
        """
        major, minor, patch = self.read_version()
        old_version = f"{major}.{minor}.{patch}"

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        else:
            print(f"Error: Invalid bump type: {bump_type}")
            print("Valid types: major, minor, patch")
            sys.exit(1)

        new_version = self.write_version(major, minor, patch)
        print(f"Version bumped: {old_version} → {new_version}")
        return new_version

    def update_changelog(self, new_version: str) -> None:
        """
        Update CHANGELOG.md with new version section.

        Moves [Unreleased] items to new version section and creates
        new empty [Unreleased] section.
        """
        if not self.changelog_file.exists():
            print(f"Warning: CHANGELOG.md not found at {self.changelog_file}")
            print("Skipping changelog update")
            return

        content = self.changelog_file.read_text()
        today = datetime.now().strftime("%Y-%m-%d")

        # Replace [Unreleased] with new version
        unreleased_pattern = r"## \[Unreleased\]"
        new_version_header = f"## [{new_version}] - {today}"

        if not re.search(unreleased_pattern, content):
            print("Warning: [Unreleased] section not found in CHANGELOG.md")
            print("Skipping changelog update")
            return

        # Insert new [Unreleased] section before the new version
        new_unreleased = f"""## [Unreleased]

### Added

### Changed

### Fixed

### Removed

{new_version_header}"""

        updated_content = re.sub(
            unreleased_pattern, new_unreleased, content, count=1
        )

        self.changelog_file.write_text(updated_content)
        print(f"Updated CHANGELOG.md with version {new_version}")


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python bump_version.py [major|minor|patch]")
        print()
        print("Examples:")
        print("  python bump_version.py patch   # 0.1.0 → 0.1.1")
        print("  python bump_version.py minor   # 0.1.0 → 0.2.0")
        print("  python bump_version.py major   # 0.1.0 → 1.0.0")
        sys.exit(1)

    bump_type = sys.argv[1].lower()

    # Determine project root (parent of scripts directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    bumper = VersionBumper(project_root)

    # Bump version and update changelog
    new_version = bumper.bump_version(bump_type)
    bumper.update_changelog(new_version)

    print()
    print(f"✅ Version bumped to {new_version}")
    print("✅ CHANGELOG.md updated")
    print()
    print("Next steps:")
    print("  1. Review CHANGELOG.md")
    print("  2. Commit changes: git add VERSION CHANGELOG.md")
    print(f"  3. Commit: git commit -m 'chore: bump version to {new_version}'")
    print(f"  4. Tag release: git tag -a v{new_version} -m 'Release {new_version}'")
    print("  5. Push: git push && git push --tags")


if __name__ == "__main__":
    main()
