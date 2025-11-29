#!/usr/bin/env python3
"""
Test WHOIS lookup on a few sample entities
"""

import json
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).parent.parent.parent
ENTITIES_INDEX = PROJECT_ROOT / "data/md/entities/ENTITIES_INDEX.json"
WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"


def load_json(filepath):
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def search_wikipedia(entity_name):
    try:
        headers = {
            "User-Agent": "EpsteinArchiveBot/1.0 (https://github.com/epstein-archive; research@epstein-archive.org)"
        }

        # Search
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": entity_name,
            "srlimit": 1,
        }
        response = requests.get(
            WIKIPEDIA_API_URL, params=search_params, headers=headers, timeout=10
        )
        response.raise_for_status()
        search_results = response.json()

        if not search_results.get("query", {}).get("search"):
            return None

        page_title = search_results["query"]["search"][0]["title"]

        # Get extract
        extract_params = {
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "exsentences": 3,
            "titles": page_title,
        }
        response = requests.get(
            WIKIPEDIA_API_URL, params=extract_params, headers=headers, timeout=10
        )
        response.raise_for_status()
        extract_data = response.json()

        pages = extract_data.get("query", {}).get("pages", {})
        if not pages:
            return None

        page = next(iter(pages.values()))
        extract = page.get("extract", "").strip()

        if extract:
            return f"{extract}\n\nSource: Wikipedia - {page_title}"
        return None

    except Exception as e:
        print(f"Error: {e}")
        return None


def clean_name(name):
    if "," in name:
        parts = name.split(",", 1)
        if len(parts) == 2:
            last, first = parts
            return f"{first.strip()} {last.strip()}"
    return name


# Test on 5 entities
entities_data = load_json(ENTITIES_INDEX)
entities = entities_data.get("entities", [])

test_entities = [
    "Trump, Donald",
    "Clinton, Bill",
    "Maxwell, Ghislaine",
    "Prince Andrew",
    "Wexner, Leslie",
]

print("Testing Wikipedia lookup on sample entities:\n")

for test_name in test_entities:
    # Find entity
    entity = next((e for e in entities if e.get("name") == test_name), None)

    if entity:
        print(f"Entity: {test_name}")
        print(f"Current bio: {entity.get('bio', 'NONE')[:100]}...")

        cleaned = clean_name(test_name)
        print(f"Searching Wikipedia for: {cleaned}")

        bio = search_wikipedia(cleaned)
        if bio:
            print(f"✓ Found bio ({len(bio)} chars)")
            print(f"Preview: {bio[:200]}...")
        else:
            print("✗ No Wikipedia entry found")
        print("-" * 80)
        print()

print("\nTest complete!")
