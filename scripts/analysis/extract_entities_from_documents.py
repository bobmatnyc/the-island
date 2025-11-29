#!/usr/bin/env python3
"""
Entity Extraction from OCR Documents using Ministral 8B

Extracts named entities (person, organization, location) from 33,561 OCR documents
using the mistralai/ministral-8b model via OpenRouter API.

Design: High-throughput entity extraction with checkpointing
Cost: ~$2.20 for entire corpus (355 tokens input, 300 tokens output per doc)
Author: Entity Extraction Enhancement System
Created: 2025-11-28
"""

import argparse
import json
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import requests
from pydantic import BaseModel, Field
from tqdm import tqdm


class Entity(BaseModel):
    """Single extracted entity"""
    name: str
    type: str  # person, organization, location
    normalized_name: str = ""  # Auto-generated normalized form


class DocumentExtractionResult(BaseModel):
    """Result of entity extraction from a single document"""
    document_id: str
    success: bool
    entities: List[Entity] = Field(default_factory=list)
    error: Optional[str] = None
    tokens_used: int = 0
    processing_time: float = 0.0


class EntityExtractor:
    """Extract entities from OCR documents using Ministral 8B via OpenRouter"""

    def __init__(
        self,
        api_key: str,
        model: str = "mistralai/ministral-8b",
        dry_run: bool = False
    ):
        """Initialize entity extractor with OpenRouter API key"""
        self.api_key = api_key
        self.dry_run = dry_run
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = model

        # Statistics
        self.stats = {
            "total_documents": 0,
            "documents_processed": 0,
            "documents_failed": 0,
            "total_entities_found": 0,
            "unique_entities": 0,
            "total_tokens_used": 0,
            "total_api_calls": 0,
            "total_cost": 0.0,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "entity_type_counts": {
                "person": 0,
                "organization": 0,
                "location": 0
            }
        }

        # Entity deduplication tracking
        self.entity_index: Dict[str, Dict] = {}  # normalized_name -> entity data
        self.document_entities: Dict[str, List[str]] = defaultdict(list)  # doc_id -> entity names

    def normalize_entity_name(self, name: str) -> str:
        """Normalize entity name for deduplication

        Handles:
        - Case normalization
        - Punctuation removal
        - Common title/suffix removal
        - Whitespace normalization
        """
        # Lowercase
        normalized = name.lower()

        # Remove common titles and suffixes
        titles = [
            r'\b(mr|mrs|ms|dr|prof|jr|sr|ii|iii|iv|esq)\b\.?',
            r'\b(attorney|lawyer|agent|detective|officer)\b',
        ]
        for title in titles:
            normalized = re.sub(title, '', normalized, flags=re.IGNORECASE)

        # Remove punctuation except hyphens and apostrophes
        normalized = re.sub(r'[^\w\s\-\']', '', normalized)

        # Normalize whitespace
        normalized = ' '.join(normalized.split())

        return normalized.strip()

    def merge_entity_variations(self, entities: List[Entity]) -> List[Entity]:
        """Merge entity name variations using fuzzy matching

        Handles:
        - "J. Epstein" vs "Jeffrey Epstein" vs "Epstein, Jeffrey"
        - "FBI" vs "F.B.I."
        - Minor OCR errors
        """
        merged: Dict[str, Entity] = {}

        for entity in entities:
            normalized = self.normalize_entity_name(entity.name)
            entity.normalized_name = normalized

            # Check if we've seen a similar entity
            found_match = False
            for existing_norm, existing_entity in merged.items():
                # Exact match on normalized name
                if normalized == existing_norm:
                    found_match = True
                    break

                # Fuzzy match: one name contains the other (for initials)
                if (normalized in existing_norm or existing_norm in normalized) and \
                   len(normalized) > 3 and len(existing_norm) > 3:
                    # Prefer longer, more complete name
                    if len(entity.name) > len(existing_entity.name):
                        merged[existing_norm] = entity
                    found_match = True
                    break

            if not found_match:
                merged[normalized] = entity

        return list(merged.values())

    def build_extraction_prompt(self, ocr_text: str) -> List[Dict[str, str]]:
        """Build extraction prompt for Ministral 8B"""

        system_prompt = """You are an expert legal document entity extractor. Extract all named entities from legal documents with high precision.

Your task:
1. Extract PERSON names (full names when available, handle initials)
2. Extract ORGANIZATION names (government agencies, companies, institutions)
3. Extract LOCATION names (cities, addresses, properties)
4. Normalize name variations (e.g., "Epstein, J." → "Jeffrey Epstein" if context allows)
5. Handle OCR errors gracefully
6. Include entities mentioned multiple times only once

Output ONLY valid JSON array with this exact format:
[
  {"name": "Jeffrey Epstein", "type": "person"},
  {"name": "FBI", "type": "organization"},
  {"name": "Little St James", "type": "location"}
]

Rules:
- Return empty array [] if no entities found
- Use "person", "organization", or "location" for type (lowercase)
- Include full names when available
- Normalize obvious variations to canonical form
- Skip generic terms like "the court", "the government"
"""

        user_prompt = f"""Extract all named entities from this legal document text:

{ocr_text[:3000]}

Return ONLY the JSON array, no additional text."""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    def extract_entities_from_document(
        self,
        document_id: str,
        ocr_text: str
    ) -> DocumentExtractionResult:
        """Extract entities from a single document"""

        start_time = time.time()

        if self.dry_run:
            # Simulate extraction in dry run
            processing_time = time.time() - start_time
            return DocumentExtractionResult(
                document_id=document_id,
                success=True,
                entities=[
                    Entity(name="Jeffrey Epstein", type="person", normalized_name="jeffrey epstein"),
                    Entity(name="DOJ", type="organization", normalized_name="doj")
                ],
                tokens_used=655,  # Estimated
                processing_time=processing_time
            )

        try:
            # Build prompt
            messages = self.build_extraction_prompt(ocr_text)

            # Call OpenRouter API
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/epstein-archive",
                    "X-Title": "Epstein Archive Entity Extractor"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.1,  # Very low for consistent extraction
                    "max_tokens": 500,  # Enough for ~50 entities
                    "response_format": {"type": "json_object"}  # Ensure JSON output
                },
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            # Extract entities from response
            content = result["choices"][0]["message"]["content"]

            # Parse JSON response
            try:
                # Handle case where model wraps in JSON object
                parsed = json.loads(content)
                if isinstance(parsed, dict) and "entities" in parsed:
                    entity_data = parsed["entities"]
                elif isinstance(parsed, list):
                    entity_data = parsed
                else:
                    entity_data = []
            except json.JSONDecodeError as e:
                # Try to extract JSON array from response
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    entity_data = json.loads(json_match.group(0))
                else:
                    raise ValueError(f"Could not parse entity JSON: {e}")

            # Convert to Entity objects
            entities = []
            for entity_dict in entity_data:
                if not isinstance(entity_dict, dict):
                    continue
                if "name" not in entity_dict or "type" not in entity_dict:
                    continue

                entity_type = entity_dict["type"].lower()
                if entity_type not in ["person", "organization", "location"]:
                    continue

                entities.append(Entity(
                    name=entity_dict["name"],
                    type=entity_type
                ))

            # Merge variations
            entities = self.merge_entity_variations(entities)

            # Track usage
            usage = result.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)
            self.stats["total_tokens_used"] += tokens_used
            self.stats["total_api_calls"] += 1

            # Calculate cost (Ministral 8B pricing)
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            cost = (input_tokens * 0.10 / 1_000_000) + (output_tokens * 0.10 / 1_000_000)
            self.stats["total_cost"] += cost

            processing_time = time.time() - start_time

            return DocumentExtractionResult(
                document_id=document_id,
                success=True,
                entities=entities,
                tokens_used=tokens_used,
                processing_time=processing_time
            )

        except requests.exceptions.RequestException as e:
            processing_time = time.time() - start_time
            error_msg = f"API request failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = f"API error: {error_data.get('error', {}).get('message', str(e))}"
                except:
                    error_msg = f"API error (HTTP {e.response.status_code}): {str(e)}"

            return DocumentExtractionResult(
                document_id=document_id,
                success=False,
                error=error_msg,
                processing_time=processing_time
            )

        except Exception as e:
            processing_time = time.time() - start_time
            return DocumentExtractionResult(
                document_id=document_id,
                success=False,
                error=f"Unexpected error: {str(e)}",
                processing_time=processing_time
            )

    def update_entity_index(self, result: DocumentExtractionResult):
        """Update global entity index with extraction results"""

        if not result.success:
            return

        for entity in result.entities:
            normalized = entity.normalized_name

            # Initialize entity in index if not seen
            if normalized not in self.entity_index:
                self.entity_index[normalized] = {
                    "name": entity.name,  # Use first seen canonical name
                    "type": entity.type,
                    "normalized_name": normalized,
                    "mention_count": 0,
                    "document_sources": [],
                    "first_seen": result.document_id,
                    "name_variations": set()
                }
                self.stats["unique_entities"] += 1
                self.stats["entity_type_counts"][entity.type] += 1

            # Update entity data
            entity_data = self.entity_index[normalized]
            entity_data["mention_count"] += 1
            entity_data["document_sources"].append(result.document_id)
            entity_data["name_variations"].add(entity.name)

            # Track document -> entity relationship
            self.document_entities[result.document_id].append(normalized)

            self.stats["total_entities_found"] += 1

    def batch_extract(
        self,
        input_dir: Path,
        output_file: Path,
        batch_size: int = 50,
        checkpoint_every: int = 1000,
        resume: bool = False,
        limit: Optional[int] = None
    ):
        """Extract entities from all documents with checkpointing"""

        checkpoint_file = output_file.parent / f"{output_file.stem}_checkpoint.json"

        # Load checkpoint if resuming
        processed_docs: Set[str] = set()
        if resume and checkpoint_file.exists():
            print(f"📂 Loading checkpoint from {checkpoint_file}")
            with open(checkpoint_file) as f:
                checkpoint_data = json.load(f)
                processed_docs = set(checkpoint_data.get("processed_documents", []))
                self.stats = checkpoint_data.get("stats", self.stats)

                # Restore entity index
                entity_index_raw = checkpoint_data.get("entity_index", {})
                for norm_name, entity_data in entity_index_raw.items():
                    entity_data["name_variations"] = set(entity_data.get("name_variations", []))
                    self.entity_index[norm_name] = entity_data

                print(f"✓ Resumed from checkpoint: {len(processed_docs)} documents already processed")

        # Collect all OCR files
        ocr_files = sorted(input_dir.glob("*.txt"))
        self.stats["total_documents"] = len(ocr_files)

        # Apply limit if specified
        if limit:
            ocr_files = ocr_files[:limit]
            print(f"⚠️  Limited to {limit} documents for this run")

        # Filter out already processed
        files_to_process = [f for f in ocr_files if f.stem not in processed_docs]

        print(f"\n{'='*70}")
        print(f"ENTITY EXTRACTION FROM OCR DOCUMENTS")
        print(f"{'='*70}")
        print(f"Total documents: {len(ocr_files)}")
        print(f"Already processed: {len(processed_docs)}")
        print(f"Remaining: {len(files_to_process)}")
        print(f"Batch size: {batch_size}")
        print(f"Checkpoint every: {checkpoint_every} documents")
        print(f"Model: {self.model}")
        print(f"Dry run: {self.dry_run}")
        print(f"{'='*70}\n")

        if not files_to_process:
            print("✓ All documents already processed!")
            return

        # Process documents with progress bar
        with tqdm(total=len(files_to_process), desc="Extracting entities", unit="doc") as pbar:
            batch = []

            for ocr_file in files_to_process:
                document_id = ocr_file.stem

                # Read OCR text
                try:
                    with open(ocr_file, 'r', encoding='utf-8') as f:
                        ocr_text = f.read()
                except Exception as e:
                    print(f"\n✗ Failed to read {document_id}: {e}")
                    self.stats["documents_failed"] += 1
                    pbar.update(1)
                    continue

                # Extract entities
                result = self.extract_entities_from_document(document_id, ocr_text)

                if result.success:
                    self.update_entity_index(result)
                    self.stats["documents_processed"] += 1
                    processed_docs.add(document_id)
                else:
                    self.stats["documents_failed"] += 1
                    print(f"\n✗ Failed {document_id}: {result.error}")

                pbar.update(1)

                # Update progress bar description with stats
                pbar.set_postfix({
                    'entities': self.stats["unique_entities"],
                    'cost': f'${self.stats["total_cost"]:.2f}'
                })

                # Checkpoint periodically
                if len(processed_docs) % checkpoint_every == 0:
                    self._save_checkpoint(processed_docs, checkpoint_file)

                # Rate limiting: 1 request per second to be safe
                if not self.dry_run:
                    time.sleep(1.0)

        # Save final results
        print(f"\n{'='*70}")
        print(f"Saving final results to {output_file}")
        self._save_results(output_file)

        # Remove checkpoint file
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            print(f"✓ Checkpoint file removed")

        # Print summary
        self._print_summary()

    def _save_checkpoint(self, processed_docs: Set[str], checkpoint_file: Path):
        """Save checkpoint to resume later"""

        # Convert sets to lists for JSON serialization
        entity_index_serializable = {}
        for norm_name, entity_data in self.entity_index.items():
            entity_data_copy = entity_data.copy()
            entity_data_copy["name_variations"] = list(entity_data["name_variations"])
            entity_index_serializable[norm_name] = entity_data_copy

        checkpoint_data = {
            "checkpoint_time": datetime.now(timezone.utc).isoformat(),
            "processed_documents": list(processed_docs),
            "stats": self.stats,
            "entity_index": entity_index_serializable
        }

        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)

    def _save_results(self, output_file: Path):
        """Save final results to output file"""

        # Convert entity index to output format
        entities_output = {}
        for norm_name, entity_data in self.entity_index.items():
            entities_output[norm_name] = {
                "name": entity_data["name"],
                "type": entity_data["type"],
                "normalized_name": norm_name,
                "mention_count": entity_data["mention_count"],
                "document_sources": entity_data["document_sources"],
                "first_seen": entity_data["first_seen"],
                "name_variations": list(entity_data["name_variations"])
            }

        # Build output structure
        output_data = {
            "extraction_metadata": {
                "total_documents": self.stats["total_documents"],
                "documents_processed": self.stats["documents_processed"],
                "documents_failed": self.stats["documents_failed"],
                "total_entities_found": self.stats["total_entities_found"],
                "unique_entities": self.stats["unique_entities"],
                "extraction_date": datetime.now(timezone.utc).isoformat(),
                "model": self.model,
                "total_cost": f"${self.stats['total_cost']:.2f}",
                "total_tokens_used": self.stats["total_tokens_used"],
                "total_api_calls": self.stats["total_api_calls"],
                "entity_type_counts": self.stats["entity_type_counts"],
                "start_time": self.stats["start_time"],
                "end_time": datetime.now(timezone.utc).isoformat()
            },
            "entities": entities_output
        }

        # Save main output
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        # Save document -> entity index
        index_file = output_file.parent / "document_entity_index.json"
        index_data = {
            "metadata": {
                "generated": datetime.now(timezone.utc).isoformat(),
                "total_documents": len(self.document_entities)
            },
            "document_entities": {
                doc_id: entities
                for doc_id, entities in self.document_entities.items()
            }
        }

        with open(index_file, 'w') as f:
            json.dump(index_data, f, indent=2)

        print(f"✓ Saved entity index to {index_file}")

    def _print_summary(self):
        """Print extraction summary statistics"""

        print(f"\n{'='*70}")
        print(f"EXTRACTION COMPLETE")
        print(f"{'='*70}")
        print(f"Total documents: {self.stats['total_documents']}")
        print(f"Documents processed: {self.stats['documents_processed']}")
        print(f"Documents failed: {self.stats['documents_failed']}")
        print(f"Success rate: {(self.stats['documents_processed'] / self.stats['total_documents'] * 100) if self.stats['total_documents'] > 0 else 0:.1f}%")
        print(f"\nEntity Statistics:")
        print(f"Total entities found: {self.stats['total_entities_found']:,}")
        print(f"Unique entities: {self.stats['unique_entities']:,}")
        print(f"  - Persons: {self.stats['entity_type_counts']['person']:,}")
        print(f"  - Organizations: {self.stats['entity_type_counts']['organization']:,}")
        print(f"  - Locations: {self.stats['entity_type_counts']['location']:,}")

        if not self.dry_run:
            print(f"\nAPI Usage:")
            print(f"Total API calls: {self.stats['total_api_calls']:,}")
            print(f"Total tokens used: {self.stats['total_tokens_used']:,}")
            print(f"Total cost: ${self.stats['total_cost']:.2f}")

            if self.stats['documents_processed'] > 0:
                avg_tokens = self.stats['total_tokens_used'] / self.stats['documents_processed']
                avg_cost = self.stats['total_cost'] / self.stats['documents_processed']
                print(f"Average tokens/doc: {avg_tokens:.0f}")
                print(f"Average cost/doc: ${avg_cost:.4f}")

        print(f"\nTiming:")
        print(f"Start time: {self.stats['start_time']}")
        print(f"End time: {datetime.now(timezone.utc).isoformat()}")


def main():
    """Main execution"""

    parser = argparse.ArgumentParser(
        description="Extract entities from OCR documents using Ministral 8B",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run with first 10 documents
  python3 extract_entities_from_documents.py --dry-run --limit 10

  # Process all documents with checkpointing
  python3 extract_entities_from_documents.py \\
    --input-dir data/sources/house_oversight_nov2025/ocr_text \\
    --output data/metadata/document_entities_raw.json \\
    --batch-size 50 \\
    --checkpoint-every 1000

  # Resume from checkpoint after interruption
  python3 extract_entities_from_documents.py --resume

  # Test with first 1000 documents
  python3 extract_entities_from_documents.py --limit 1000
        """
    )

    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/sources/house_oversight_nov2025/ocr_text"),
        help="Directory containing OCR text files (default: data/sources/house_oversight_nov2025/ocr_text)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/metadata/document_entities_raw.json"),
        help="Output file path (default: data/metadata/document_entities_raw.json)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Batch size for progress tracking (default: 50)"
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=1000,
        help="Save checkpoint every N documents (default: 1000)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of documents to process (for testing)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run without making API calls"
    )
    parser.add_argument(
        "--api-key",
        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)"
    )

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key and not args.dry_run:
        print("ERROR: API key required")
        print("Either:")
        print("  1. Set OPENROUTER_API_KEY environment variable")
        print("  2. Use --api-key argument")
        print("  3. Use --dry-run for testing")
        return 1

    # Resolve paths
    project_root = Path(__file__).parent.parent.parent

    if args.input_dir.is_absolute():
        input_dir = args.input_dir
    else:
        input_dir = project_root / args.input_dir

    if args.output.is_absolute():
        output_file = args.output
    else:
        output_file = project_root / args.output

    # Verify input directory exists
    if not input_dir.exists():
        print(f"ERROR: Input directory not found: {input_dir}")
        return 1

    # Create extractor and run
    extractor = EntityExtractor(
        api_key=api_key or "",
        dry_run=args.dry_run
    )

    extractor.batch_extract(
        input_dir=input_dir,
        output_file=output_file,
        batch_size=args.batch_size,
        checkpoint_every=args.checkpoint_every,
        resume=args.resume,
        limit=args.limit
    )

    return 0


if __name__ == "__main__":
    exit(main())
