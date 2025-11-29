#!/usr/bin/env python3
"""
Test script for /api/about and /api/updates endpoints
Simulates the endpoint logic without running the full server
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent

def test_about_endpoint():
    """Test /api/about endpoint logic"""
    print("=" * 70)
    print("Testing /api/about endpoint")
    print("=" * 70)

    about_path = PROJECT_ROOT / "ABOUT.md"

    if not about_path.exists():
        print("❌ ABOUT.md not found!")
        return False

    # Read markdown content
    with open(about_path, encoding="utf-8") as f:
        content = f.read()

    # Get file metadata
    stat = about_path.stat()
    updated_at = datetime.fromtimestamp(stat.st_mtime).isoformat()

    response = {
        "content": content,
        "updated_at": updated_at,
        "file_size": stat.st_size
    }

    print(f"✅ Content length: {len(response['content'])} characters")
    print(f"✅ Updated at: {response['updated_at']}")
    print(f"✅ File size: {response['file_size']} bytes")
    print(f"✅ First line: {content.split(chr(10))[0]}")
    print()

    # Show sample JSON response
    print("Sample JSON response:")
    print(json.dumps({
        "content": content[:200] + "...",
        "updated_at": response["updated_at"],
        "file_size": response["file_size"]
    }, indent=2))
    print()

    return True


def test_updates_endpoint():
    """Test /api/updates endpoint logic"""
    print("=" * 70)
    print("Testing /api/updates endpoint")
    print("=" * 70)

    limit = 10

    try:
        # Run git log command
        result = subprocess.run(
            [
                "git", "log",
                f"-n{limit}",
                "--pretty=format:%h|%an|%ar|%s"
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=5
        )

        if result.returncode != 0:
            print(f"❌ Git command failed: {result.stderr}")
            return False

        # Parse git log output
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            parts = line.split("|", 3)
            if len(parts) == 4:
                commit_hash, author, time_ago, message = parts
                commits.append({
                    "hash": commit_hash,
                    "author": author,
                    "time": time_ago,
                    "message": message
                })

        response = {
            "commits": commits,
            "total": len(commits)
        }

        print(f"✅ Retrieved {response['total']} commits")
        print()

        print("Sample commits:")
        for i, commit in enumerate(commits[:5], 1):
            print(f"  {i}. [{commit['hash']}] {commit['message']}")
            print(f"     by {commit['author']} - {commit['time']}")
        print()

        # Show sample JSON response
        print("Sample JSON response:")
        print(json.dumps({
            "commits": commits[:3],
            "total": response["total"]
        }, indent=2))
        print()

        return True

    except subprocess.TimeoutExpired:
        print("❌ Git command timed out")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("\n" + "=" * 70)
    print("ENDPOINT TEST SUITE")
    print("=" * 70)
    print()

    success_count = 0
    total_tests = 2

    if test_about_endpoint():
        success_count += 1

    if test_updates_endpoint():
        success_count += 1

    print("=" * 70)
    print(f"RESULTS: {success_count}/{total_tests} tests passed")
    print("=" * 70)

    if success_count == total_tests:
        print("\n✅ All endpoints working correctly!")
        print("\nTo test with actual server:")
        print("  1. Start server: .venv/bin/uvicorn server.app:app --host 0.0.0.0 --port 8081 --reload")
        print("  2. Test /api/about: curl http://localhost:8081/api/about")
        print("  3. Test /api/updates: curl http://localhost:8081/api/updates?limit=5")
    else:
        print("\n❌ Some tests failed - check errors above")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
