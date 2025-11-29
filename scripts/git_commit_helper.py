#!/usr/bin/env python3
"""
Git commit message helper for conventional commits.

Provides interactive prompts for creating well-formatted commit messages
following the Conventional Commits specification.

Usage:
    python git_commit_helper.py [--type TYPE] [--scope SCOPE] [--message MESSAGE]
"""

import subprocess
import sys
from typing import Optional


class CommitHelper:
    """Helps create conventional commit messages."""

    COMMIT_TYPES = {
        "feat": "A new feature",
        "fix": "A bug fix",
        "docs": "Documentation only changes",
        "style": "Changes that don't affect code meaning (formatting, etc)",
        "refactor": "Code change that neither fixes a bug nor adds a feature",
        "perf": "Performance improvement",
        "test": "Adding missing tests or correcting existing tests",
        "build": "Changes to build system or dependencies",
        "ci": "Changes to CI configuration files and scripts",
        "chore": "Other changes that don't modify src or test files",
        "revert": "Reverts a previous commit",
    }

    SCOPES = [
        "ocr",
        "classification",
        "extraction",
        "network",
        "search",
        "database",
        "api",
        "docs",
        "scripts",
    ]

    def __init__(self):
        self.commit_type: Optional[str] = None
        self.scope: Optional[str] = None
        self.message: Optional[str] = None
        self.body: Optional[str] = None
        self.breaking: bool = False

    def prompt_type(self) -> str:
        """Prompt user to select commit type."""
        print("\n📝 Select commit type:")
        print()
        for i, (type_name, description) in enumerate(self.COMMIT_TYPES.items(), 1):
            print(f"  {i:2d}. {type_name:10s} - {description}")

        print()
        choice = input("Enter number (1-11) or type name: ").strip()

        # Handle numeric choice
        if choice.isdigit():
            choice_num = int(choice)
            if 1 <= choice_num <= len(self.COMMIT_TYPES):
                return list(self.COMMIT_TYPES.keys())[choice_num - 1]

        # Handle type name
        if choice in self.COMMIT_TYPES:
            return choice

        print(f"❌ Invalid choice: {choice}")
        sys.exit(1)

    def prompt_scope(self) -> Optional[str]:
        """Prompt user to select scope (optional)."""
        print("\n🎯 Select scope (optional):")
        print()
        print("  0. No scope")
        for i, scope in enumerate(self.SCOPES, 1):
            print(f"  {i:2d}. {scope}")
        print(f"  {len(self.SCOPES) + 1:2d}. Other (custom)")

        print()
        choice = input(f"Enter number (0-{len(self.SCOPES) + 1}) or scope name: ").strip()

        if choice in {"0", ""}:
            return None

        # Handle numeric choice
        if choice.isdigit():
            choice_num = int(choice)
            if choice_num == len(self.SCOPES) + 1:
                custom = input("Enter custom scope: ").strip()
                return custom if custom else None
            if 1 <= choice_num <= len(self.SCOPES):
                return self.SCOPES[choice_num - 1]

        # Handle scope name
        return choice

    def prompt_message(self) -> str:
        """Prompt user for commit message."""
        print("\n💬 Enter commit message:")
        print("   (brief description in imperative mood)")
        print()
        message = input("Message: ").strip()

        if not message:
            print("❌ Message cannot be empty")
            sys.exit(1)

        return message

    def prompt_body(self) -> Optional[str]:
        """Prompt user for commit body (optional)."""
        print("\n📄 Enter commit body (optional, press Enter to skip):")
        print("   (detailed explanation of changes)")
        print()
        body = input("Body: ").strip()
        return body if body else None

    def prompt_breaking(self) -> bool:
        """Prompt user if this is a breaking change."""
        print("\n⚠️  Is this a breaking change? (y/N): ")
        response = input().strip().lower()
        return response in ["y", "yes"]

    def build_commit_message(self) -> str:
        """Build formatted commit message."""
        # Build header
        if self.scope:
            header = f"{self.commit_type}({self.scope}): {self.message}"
        else:
            header = f"{self.commit_type}: {self.message}"

        if self.breaking:
            header += " [BREAKING]"

        # Build full message
        lines = [header]

        if self.body:
            lines.append("")
            lines.append(self.body)

        if self.breaking:
            lines.append("")
            lines.append("BREAKING CHANGE: This commit introduces breaking changes")

        # Add footer
        lines.append("")
        lines.append("🤖 Generated with [Claude Code](https://claude.ai/code)")
        lines.append("")
        lines.append("Co-Authored-By: Claude <noreply@anthropic.com>")

        return "\n".join(lines)

    def commit(self, message: str, auto_add: bool = False) -> None:
        """Execute git commit with message."""
        try:
            if auto_add:
                print("\n📦 Staging all changes...")
                subprocess.run(["git", "add", "."], check=True)

            print("\n✅ Creating commit...")
            subprocess.run(["git", "commit", "-m", message], check=True)
            print("\n🎉 Commit created successfully!")

        except subprocess.CalledProcessError as e:
            print(f"\n❌ Git command failed: {e}")
            sys.exit(1)

    def interactive(self) -> None:
        """Run interactive commit helper."""
        print("=" * 60)
        print("  Git Commit Helper - Conventional Commits")
        print("=" * 60)

        self.commit_type = self.prompt_type()
        self.scope = self.prompt_scope()
        self.message = self.prompt_message()
        self.body = self.prompt_body()
        self.breaking = self.prompt_breaking()

        # Build and preview message
        commit_message = self.build_commit_message()

        print("\n" + "=" * 60)
        print("  Commit Message Preview")
        print("=" * 60)
        print(commit_message)
        print("=" * 60)

        # Confirm
        print("\n✅ Create this commit? (Y/n): ")
        confirm = input().strip().lower()

        if confirm in ["", "y", "yes"]:
            auto_add = False
            print("\n📦 Stage all changes before committing? (y/N): ")
            stage_response = input().strip().lower()
            if stage_response in ["y", "yes"]:
                auto_add = True

            self.commit(commit_message, auto_add)
        else:
            print("\n❌ Commit cancelled")
            sys.exit(0)


def main():
    """Main entry point."""
    helper = CommitHelper()

    # Check if in git repository
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        print("❌ Not in a git repository")
        sys.exit(1)

    # Parse arguments for non-interactive mode
    if len(sys.argv) > 1:
        if "--help" in sys.argv or "-h" in sys.argv:
            print("Git Commit Helper")
            print()
            print("Usage:")
            print("  python git_commit_helper.py")
            print("    (interactive mode)")
            print()
            print("  python git_commit_helper.py --type TYPE --message MESSAGE")
            print("    (non-interactive mode)")
            print()
            print("Arguments:")
            print("  --type TYPE       Commit type (feat, fix, docs, etc.)")
            print("  --scope SCOPE     Commit scope (optional)")
            print("  --message MSG     Commit message")
            print("  --body BODY       Commit body (optional)")
            print("  --breaking        Mark as breaking change")
            sys.exit(0)

        # Non-interactive mode
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg == "--type" and i < len(sys.argv) - 1:
                helper.commit_type = sys.argv[i + 1]
            elif arg == "--scope" and i < len(sys.argv) - 1:
                helper.scope = sys.argv[i + 1]
            elif arg == "--message" and i < len(sys.argv) - 1:
                helper.message = sys.argv[i + 1]
            elif arg == "--body" and i < len(sys.argv) - 1:
                helper.body = sys.argv[i + 1]
            elif arg == "--breaking":
                helper.breaking = True

        if not helper.commit_type or not helper.message:
            print("❌ --type and --message required in non-interactive mode")
            sys.exit(1)

        commit_message = helper.build_commit_message()
        helper.commit(commit_message)
    else:
        # Interactive mode
        helper.interactive()


if __name__ == "__main__":
    main()
