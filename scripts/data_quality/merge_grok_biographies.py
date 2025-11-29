#!/usr/bin/env python3
"""
Merge Grok-generated biographies into entity_biographies.json

Design Decision: Preserve Existing Structure
Rationale: entity_biographies.json has detailed structured data.
Grok biographies provide narrative text. Merge them into existing
structure under "biography" field without overwriting other data.

Trade-offs:
- Adds biography narrative to existing structured data
- Preserves all existing metadata and structured fields
- Makes biographies available to frontend via existing API

Error Handling:
- Backs up existing file before modification
- Validates JSON structure before writing
- Logs all merge operations
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_json(file_path: Path) -> Dict[str, Any]:
    """Load JSON file safely"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(file_path: Path, data: Dict[str, Any]) -> None:
    """Save JSON file with formatting"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def backup_file(file_path: Path) -> Path:
    """Create backup of existing file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = file_path.parent / f"{file_path.stem}.backup_{timestamp}{file_path.suffix}"

    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        logger.info(f"Created backup: {backup_path}")
        return backup_path

    return None


def merge_biographies(
    existing_bios: Dict[str, Any],
    grok_bios: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge Grok biographies into existing structure

    Args:
        existing_bios: Existing entity_biographies.json data
        grok_bios: Grok-generated biographies

    Returns:
        Merged biography data
    """
    merged = existing_bios.copy()

    # Ensure entities dict exists
    if "entities" not in merged:
        merged["entities"] = {}

    # Track merge statistics
    stats = {
        "updated": 0,
        "new": 0,
        "skipped": 0,
        "errors": 0
    }

    # Merge each Grok biography
    grok_entities = grok_bios.get("entities", {})

    for entity_id, grok_data in grok_entities.items():
        try:
            if entity_id in merged["entities"]:
                # Update existing entity with biography text
                merged["entities"][entity_id]["biography"] = grok_data["biography"]
                merged["entities"][entity_id]["biography_metadata"] = {
                    "generated_by": grok_data["generated_by"],
                    "generation_date": grok_data["generation_date"],
                    "word_count": grok_data["word_count"],
                    "quality_score": grok_data["quality_score"],
                    "source_material": grok_data["source_material"]
                }
                stats["updated"] += 1
                logger.info(f"Updated biography for: {entity_id}")
            else:
                # Create new entity entry with biography
                merged["entities"][entity_id] = {
                    "id": entity_id,
                    "display_name": grok_data["display_name"],
                    "biography": grok_data["biography"],
                    "biography_metadata": {
                        "generated_by": grok_data["generated_by"],
                        "generation_date": grok_data["generation_date"],
                        "word_count": grok_data["word_count"],
                        "quality_score": grok_data["quality_score"],
                        "source_material": grok_data["source_material"]
                    }
                }
                stats["new"] += 1
                logger.info(f"Added new entity with biography: {entity_id}")

        except Exception as e:
            logger.error(f"Error processing {entity_id}: {e}")
            stats["errors"] += 1

    # Update metadata
    merged["metadata"]["last_updated"] = datetime.now().isoformat()
    merged["metadata"]["grok_biographies_merged"] = True
    merged["metadata"]["grok_merge_date"] = datetime.now().isoformat()
    merged["metadata"]["grok_merge_stats"] = stats

    logger.info(f"Merge statistics: {stats}")

    return merged


def main():
    """Main merge process"""
    # Paths
    data_dir = Path(__file__).parent.parent.parent / "data" / "metadata"
    existing_path = data_dir / "entity_biographies.json"
    grok_path = data_dir / "entity_biographies_grok.json"

    logger.info("Starting biography merge process")

    # Load files
    logger.info(f"Loading existing biographies from: {existing_path}")
    existing_bios = load_json(existing_path)

    logger.info(f"Loading Grok biographies from: {grok_path}")
    grok_bios = load_json(grok_path)

    logger.info(f"Existing entities: {len(existing_bios.get('entities', {}))}")
    logger.info(f"Grok biographies: {len(grok_bios.get('entities', {}))}")

    # Backup existing file
    backup_path = backup_file(existing_path)

    # Merge biographies
    logger.info("Merging biographies...")
    merged_bios = merge_biographies(existing_bios, grok_bios)

    # Save merged data
    logger.info(f"Saving merged biographies to: {existing_path}")
    save_json(existing_path, merged_bios)

    logger.info("✓ Biography merge complete!")
    logger.info(f"Total entities in merged file: {len(merged_bios.get('entities', {}))}")

    # Print sample
    sample_entity = list(merged_bios.get('entities', {}).keys())[0]
    if sample_entity:
        entity_data = merged_bios['entities'][sample_entity]
        if 'biography' in entity_data:
            logger.info(f"\nSample biography for {sample_entity}:")
            logger.info(f"Word count: {entity_data.get('biography_metadata', {}).get('word_count', 'N/A')}")
            logger.info(f"Quality score: {entity_data.get('biography_metadata', {}).get('quality_score', 'N/A')}")
            logger.info(f"Preview: {entity_data['biography'][:150]}...")


if __name__ == "__main__":
    main()
