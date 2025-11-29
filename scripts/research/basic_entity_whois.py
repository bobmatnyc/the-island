#!/usr/bin/env python3
"""
Task 3: Implement Basic WHOIS Lookup for ALL Entities

Enriches entities with basic biographical information from Wikipedia and other
public sources. Uses respectful rate limiting.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import requests


# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENTITIES_INDEX = PROJECT_ROOT / "data/md/entities/ENTITIES_INDEX.json"
PROGRESS_FILE = PROJECT_ROOT / "data/metadata/whois_progress.json"
REPORT_FILE = PROJECT_ROOT / "data/metadata/whois_report.txt"

# Constants
WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
MIN_BIO_LENGTH = 50  # Minimum bio length before enrichment
RATE_LIMIT_SECONDS = 0.5  # 0.5 seconds per request (respectful but faster)
PROGRESS_CHECKPOINT_INTERVAL = 25  # Save progress every 25 entities
MAX_ENTITIES_TO_PROCESS = None  # Set to None for all, or a number for testing


def load_json(filepath):
    """Load JSON file"""
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath, data):
    """Save JSON file with formatting"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def search_wikipedia(entity_name: str) -> Optional[str]:
    """
    Search Wikipedia for entity and extract summary.

    Args:
        entity_name: Name of entity to search

    Returns:
        First 2-3 sentences of Wikipedia summary, or None if not found
    """
    try:
        # User-Agent header required by Wikipedia API
        headers = {
            "User-Agent": "EpsteinArchiveBot/1.0 (https://github.com/epstein-archive; research@epstein-archive.org)"
        }

        # Search for the page
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

        # Get the first result's title
        page_title = search_results["query"]["search"][0]["title"]

        # Get the page extract
        extract_params = {
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "exsentences": 3,  # First 3 sentences
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

        # Get the first page
        page = next(iter(pages.values()))
        extract = page.get("extract", "").strip()

        if extract:
            # Add source attribution
            return f"{extract}\n\nSource: Wikipedia - {page_title}"

        return None

    except Exception as e:
        print(f"  Error searching Wikipedia for '{entity_name}': {e}")
        return None


def is_generic_entity(name: str) -> bool:
    """
    Check if entity name is too generic for Wikipedia lookup.

    Args:
        name: Entity name

    Returns:
        True if entity should be skipped
    """
    name_lower = name.lower().strip()

    # Skip generic patterns
    generic_patterns = [
        "female (",
        "male (",
        "passenger ",
        "unknown",
        "unidentified",
        "guest",
        "crew",
        "staff",
        "pilot",
        "copilot",
    ]

    for pattern in generic_patterns:
        if pattern in name_lower:
            return True

    # Skip single names (too generic)
    return bool("," not in name and " " not in name and len(name) < 15)


def clean_entity_name(name: str) -> str:
    """
    Clean entity name for better Wikipedia search results.

    Args:
        name: Raw entity name

    Returns:
        Cleaned name for search
    """
    # Remove common suffixes that might confuse search
    name = name.strip()

    # Handle "Last, First" format
    if "," in name:
        parts = name.split(",", 1)
        if len(parts) == 2:
            last, first = parts
            # Try "First Last" format for Wikipedia
            return f"{first.strip()} {last.strip()}"

    return name


def load_progress() -> dict[str, Any]:
    """Load progress checkpoint if exists"""
    if PROGRESS_FILE.exists():
        return load_json(PROGRESS_FILE)
    return {
        "last_processed_index": -1,
        "entities_processed": 0,
        "bios_added": 0,
        "bios_skipped": 0,
        "generic_skipped": 0,
        "errors": 0,
        "start_time": datetime.now().isoformat(),
    }


def save_progress(progress: dict[str, Any]):
    """Save progress checkpoint"""
    progress["last_checkpoint"] = datetime.now().isoformat()
    save_json(PROGRESS_FILE, progress)


def enrich_entities():
    """Main function to enrich all entities with Wikipedia bios"""
    print("=" * 80)
    print("ENTITY WHOIS ENRICHMENT")
    print("=" * 80)
    print(f"Rate limit: {RATE_LIMIT_SECONDS}s per request")
    print(f"Progress checkpoint interval: {PROGRESS_CHECKPOINT_INTERVAL} entities")
    print()

    # Load data
    print("Loading ENTITIES_INDEX.json...")
    entities_data = load_json(ENTITIES_INDEX)
    entities = entities_data.get("entities", [])
    total_entities = len(entities)

    # Load progress
    progress = load_progress()
    start_index = progress["last_processed_index"] + 1

    if start_index > 0:
        print(
            f"Resuming from entity #{start_index} (previously processed {progress['entities_processed']})"
        )
    else:
        print(f"Starting fresh enrichment for {total_entities} entities")

    print()

    # Process entities
    end_index = MAX_ENTITIES_TO_PROCESS if MAX_ENTITIES_TO_PROCESS else total_entities

    for i in range(start_index, min(end_index, total_entities)):
        entity = entities[i]
        name = entity.get("name", "Unknown")
        current_bio = entity.get("bio", "").strip()

        progress["entities_processed"] += 1

        # Skip generic entities
        if is_generic_entity(name):
            progress["generic_skipped"] += 1
            entity["whois_checked"] = True
            entity["whois_source"] = "skipped_generic"
            entity["whois_date"] = datetime.now().isoformat()

            if progress["entities_processed"] % 100 == 0:
                print(
                    f"[{progress['entities_processed']}/{total_entities}] Skipped (generic): {name}"
                )
            continue

        # Check if bio already exists and is sufficient
        if current_bio and len(current_bio) >= MIN_BIO_LENGTH:
            progress["bios_skipped"] += 1
            entity["whois_checked"] = True
            entity["whois_source"] = "existing"
            entity["whois_date"] = datetime.now().isoformat()

            if progress["entities_processed"] % 100 == 0:
                print(
                    f"[{progress['entities_processed']}/{total_entities}] Skipped (has bio): {name}"
                )
        else:
            # Need to enrich
            print(f"[{progress['entities_processed']}/{total_entities}] Enriching: {name}")

            # Search Wikipedia
            cleaned_name = clean_entity_name(name)
            bio = search_wikipedia(cleaned_name)

            if bio:
                entity["bio"] = bio
                entity["whois_checked"] = True
                entity["whois_source"] = "wikipedia"
                entity["whois_date"] = datetime.now().isoformat()
                progress["bios_added"] += 1
                print(f"  ✓ Added bio ({len(bio)} chars)")
            else:
                # Mark as checked even if no bio found
                entity["whois_checked"] = True
                entity["whois_source"] = "none"
                entity["whois_date"] = datetime.now().isoformat()
                progress["errors"] += 1
                print("  ✗ No Wikipedia entry found")

            # Rate limiting
            time.sleep(RATE_LIMIT_SECONDS)

        # Update progress
        progress["last_processed_index"] = i

        # Checkpoint save
        if progress["entities_processed"] % PROGRESS_CHECKPOINT_INTERVAL == 0:
            print("\n--- Checkpoint: Saving progress ---")
            entities_data["entities"] = entities
            save_json(ENTITIES_INDEX, entities_data)
            save_progress(progress)
            print(f"Processed: {progress['entities_processed']}/{total_entities}")
            print(f"Bios added: {progress['bios_added']}")
            print(f"Bios skipped: {progress['bios_skipped']}")
            print(f"Errors: {progress['errors']}")
            print()

    # Final save
    print("\n" + "=" * 80)
    print("SAVING FINAL RESULTS")
    print("=" * 80)

    entities_data["entities"] = entities
    save_json(ENTITIES_INDEX, entities_data)
    save_progress(progress)

    # Generate report
    end_time = datetime.now()
    start_time = datetime.fromisoformat(progress["start_time"])
    duration = (end_time - start_time).total_seconds()

    bio_coverage = progress["bios_added"] + progress["bios_skipped"]
    coverage_pct = (bio_coverage / total_entities) * 100 if total_entities > 0 else 0

    report_lines = [
        "=" * 80,
        "ENTITY WHOIS ENRICHMENT REPORT",
        "=" * 80,
        f"Generated: {end_time.isoformat()}",
        f"Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)",
        "",
        "SUMMARY",
        "-" * 80,
        f"Total entities: {total_entities}",
        f"Entities processed: {progress['entities_processed']}",
        f"Bios added: {progress['bios_added']}",
        f"Bios skipped (already sufficient): {progress['bios_skipped']}",
        f"Generic entities skipped: {progress['generic_skipped']}",
        f"Errors (no Wikipedia entry): {progress['errors']}",
        "",
        "COVERAGE",
        "-" * 80,
        f"Entities with bios: {bio_coverage}/{total_entities} ({coverage_pct:.1f}%)",
        "Target coverage: 80%",
        f"Status: {'✓ TARGET MET' if coverage_pct >= 80 else '✗ BELOW TARGET'}",
        "",
        "PERFORMANCE",
        "-" * 80,
        f"Average time per entity: {duration/total_entities:.2f}s" if total_entities > 0 else "N/A",
        f"Entities per minute: {(total_entities/duration)*60:.1f}" if duration > 0 else "N/A",
        "",
        "SUCCESS CRITERIA",
        "-" * 80,
        f"✓ All entities have whois_checked flag: {all(e.get('whois_checked', False) for e in entities)}",
        f"✓ Bio coverage ≥ 80%: {coverage_pct >= 80}",
        "",
        "=" * 80,
    ]

    report_text = "\n".join(report_lines)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(report_text)
    print(f"\nReport saved to: {REPORT_FILE}")

    # Clean up progress file on successful completion
    if PROGRESS_FILE.exists():
        PROGRESS_FILE.unlink()
        print("Progress file cleaned up")


if __name__ == "__main__":
    try:
        enrich_entities()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Progress has been saved.")
        print("Run this script again to resume from where you left off.")
    except Exception as e:
        print(f"\n\nERROR: {e}")
        print("Progress has been saved. You can resume by running this script again.")
        raise
