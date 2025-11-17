#!/usr/bin/env python3
"""
Changelog management script for Epstein Document Archive.

Manages CHANGELOG.md updates, version sections, and formatting.

Usage:
    python update_changelog.py [version] [--date DATE]
"""

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class ChangelogManager:
    """Manages CHANGELOG.md updates and formatting."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.changelog_file = project_root / "CHANGELOG.md"

    def read_changelog(self) -> str:
        """Read current changelog content."""
        if not self.changelog_file.exists():
            return self._create_default_changelog()

        return self.changelog_file.read_text()

    def write_changelog(self, content: str) -> None:
        """Write changelog content to file."""
        self.changelog_file.write_text(content)

    def _create_default_changelog(self) -> str:
        """Create default changelog structure."""
        return """# Changelog

All notable changes to the Epstein Document Archive will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

### Removed
"""

    def release_version(
        self, version: str, date: Optional[str] = None
    ) -> None:
        """
        Release a new version by moving [Unreleased] to version section.

        Args:
            version: Version number (e.g., '0.2.0')
            date: Release date in YYYY-MM-DD format (defaults to today)
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        content = self.read_changelog()

        # Check if version already exists
        version_pattern = rf"## \[{re.escape(version)}\]"
        if re.search(version_pattern, content):
            print(f"Error: Version {version} already exists in CHANGELOG.md")
            sys.exit(1)

        # Find [Unreleased] section
        unreleased_pattern = r"## \[Unreleased\]"
        if not re.search(unreleased_pattern, content):
            print("Error: [Unreleased] section not found in CHANGELOG.md")
            sys.exit(1)

        # Create new version header
        new_version_header = f"## [{version}] - {date}"

        # Create new [Unreleased] section
        new_unreleased = f"""## [Unreleased]

### Added

### Changed

### Fixed

### Removed

{new_version_header}"""

        # Replace [Unreleased] with new structure
        updated_content = re.sub(
            unreleased_pattern, new_unreleased, content, count=1
        )

        self.write_changelog(updated_content)
        print(f"Released version {version} in CHANGELOG.md")

    def add_entry(
        self, category: str, entry: str, version: str = "Unreleased"
    ) -> None:
        """
        Add an entry to a specific category.

        Args:
            category: One of 'Added', 'Changed', 'Fixed', 'Removed'
            entry: Entry text
            version: Version to add to (defaults to 'Unreleased')
        """
        valid_categories = ["Added", "Changed", "Fixed", "Removed"]
        if category not in valid_categories:
            print(f"Error: Invalid category: {category}")
            print(f"Valid categories: {', '.join(valid_categories)}")
            sys.exit(1)

        content = self.read_changelog()

        # Find the version section
        if version == "Unreleased":
            section_pattern = r"(## \[Unreleased\].*?)(## \[|\Z)"
        else:
            section_pattern = rf"(## \[{re.escape(version)}\].*?)(## \[|\Z)"

        section_match = re.search(section_pattern, content, re.DOTALL)
        if not section_match:
            print(f"Error: Version section [{version}] not found")
            sys.exit(1)

        section_content = section_match.group(1)

        # Find category within section
        category_pattern = rf"(### {category}\s*\n)(.*?)(###|\Z)"
        category_match = re.search(
            category_pattern, section_content, re.DOTALL
        )

        if not category_match:
            print(f"Error: Category '{category}' not found in [{version}]")
            sys.exit(1)

        # Add entry to category
        category_header = category_match.group(1)
        existing_entries = category_match.group(2).strip()
        next_section = category_match.group(3)

        if existing_entries:
            new_entries = f"{existing_entries}\n- {entry}\n"
        else:
            new_entries = f"- {entry}\n"

        new_category = f"{category_header}{new_entries}\n{next_section}"

        # Replace category in section
        updated_section = re.sub(
            category_pattern, new_category, section_content, count=1
        )

        # Replace section in content
        updated_content = content.replace(section_content, updated_section)

        self.write_changelog(updated_content)
        print(f"Added entry to [{version}] > {category}")

    def validate(self) -> bool:
        """
        Validate changelog format.

        Returns:
            True if valid, False otherwise
        """
        content = self.read_changelog()

        # Check for required sections
        if not re.search(r"# Changelog", content):
            print("Error: Missing '# Changelog' header")
            return False

        if not re.search(r"## \[Unreleased\]", content):
            print("Warning: Missing [Unreleased] section")

        # Check for valid categories in each version
        version_sections = re.findall(
            r"## \[(.*?)\].*?\n(.*?)(?=## \[|\Z)", content, re.DOTALL
        )

        for version, section_content in version_sections:
            valid_categories = ["Added", "Changed", "Fixed", "Removed"]
            for category in valid_categories:
                if f"### {category}" not in section_content:
                    print(
                        f"Warning: [{version}] missing category '{category}'"
                    )

        print("✅ Changelog format validated")
        return True


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python update_changelog.py [command] [args]")
        print()
        print("Commands:")
        print("  release VERSION [--date DATE]  - Release a new version")
        print("  add CATEGORY ENTRY             - Add entry to [Unreleased]")
        print("  validate                       - Validate changelog format")
        print()
        print("Examples:")
        print("  python update_changelog.py release 0.2.0")
        print(
            "  python update_changelog.py add Added 'New OCR pipeline'"
        )
        print("  python update_changelog.py validate")
        sys.exit(1)

    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    manager = ChangelogManager(project_root)
    command = sys.argv[1].lower()

    if command == "release":
        if len(sys.argv) < 3:
            print("Error: VERSION required for release command")
            sys.exit(1)

        version = sys.argv[2]
        date = None

        if len(sys.argv) >= 5 and sys.argv[3] == "--date":
            date = sys.argv[4]

        manager.release_version(version, date)

    elif command == "add":
        if len(sys.argv) < 4:
            print("Error: CATEGORY and ENTRY required for add command")
            sys.exit(1)

        category = sys.argv[2]
        entry = " ".join(sys.argv[3:])

        manager.add_entry(category, entry)

    elif command == "validate":
        manager.validate()

    else:
        print(f"Error: Unknown command: {command}")
        print("Valid commands: release, add, validate")
        sys.exit(1)


if __name__ == "__main__":
    main()
