#!/usr/bin/env python3
"""
Entity Biography Enrichment from Document Context
Epstein Archive - Extract contextual information from documents using Grok AI

This script enriches existing entity biographies by:
1. Reading all documents that mention each entity
2. Extracting relevant passages mentioning the entity
3. Using Grok AI to analyze and summarize contextual information
4. Adding document-derived context to biography metadata

Design Decision: Document-First Enrichment
Rationale: Existing biographies are web-sourced. Documents contain specific
contextual details (dates, relationships, events) that can enhance biographies
with archive-specific information.

Trade-offs:
- Performance: API rate limiting (1 req/sec) makes this slow for large batches
- Quality: Grok quality depends on document excerpt relevance
- Cost: Free tier usage (x-ai/grok-2-1212:free)

Architecture:
- Read entity biographies from JSON
- Find documents mentioning each entity
- Extract paragraphs containing entity name
- Send to Grok for contextual analysis
- Merge results back into biography JSON

Author: Python Engineer
Created: 2025-11-22
"""

import argparse
import json
import logging
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel, Field
from tqdm import tqdm


# ============================================================================
# Configuration
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
BIOGRAPHY_PATH = PROJECT_ROOT / "data/metadata/entity_biographies.json"
ENTITY_STATS_PATH = PROJECT_ROOT / "data/metadata/entity_statistics.json"
MARKDOWN_BASE = PROJECT_ROOT / "data"

# OpenRouter configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
GROK_MODEL = "x-ai/grok-4.1-fast:free"  # Grok 4.1 Fast - Free tier model
RATE_LIMIT_DELAY = 1.0  # Seconds between API calls

# Logging
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"enrich_bios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"


# ============================================================================
# Pydantic Models
# ============================================================================


class DocumentExcerpt(BaseModel):
    """Excerpt from a document mentioning the entity"""

    document_path: str
    document_type: str
    excerpts: List[str] = Field(default_factory=list)
    relevance_score: float = 0.0


class GrokExtractionRequest(BaseModel):
    """Request to Grok for context extraction"""

    entity_id: str
    entity_name: str
    current_biography: str
    document_excerpts: List[DocumentExcerpt]


class GrokExtractionResponse(BaseModel):
    """Response from Grok with extracted context"""

    additional_context: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class EnrichmentResult(BaseModel):
    """Result of enriching a single entity"""

    entity_id: str
    entity_name: str
    success: bool
    document_context: List[str] = Field(default_factory=list)
    documents_analyzed: int = 0
    confidence: float = 0.0
    error: Optional[str] = None


# ============================================================================
# Logging Setup
# ============================================================================


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging with file and console output"""

    logger = logging.getLogger("enrich_bios")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # File handler (detailed logs)
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Console handler (user-friendly)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# ============================================================================
# Document Extraction
# ============================================================================


class DocumentExtractor:
    """Extract relevant excerpts from documents mentioning entities"""

    def __init__(self, markdown_base: Path, logger: logging.Logger):
        self.markdown_base = markdown_base
        self.logger = logger

    def find_documents_for_entity(
        self, entity_id: str, entity_stats: Dict[str, Any]
    ) -> List[DocumentExcerpt]:
        """Find all documents mentioning this entity

        Args:
            entity_id: Entity identifier
            entity_stats: Entity statistics data

        Returns:
            List of document excerpts mentioning the entity
        """

        entity_data = entity_stats.get(entity_id)
        if not entity_data:
            self.logger.warning(f"Entity {entity_id} not found in statistics")
            return []

        documents = entity_data.get("documents", [])
        if not documents:
            self.logger.debug(f"No documents found for {entity_id}")
            return []

        entity_name = entity_data.get("name", entity_id)
        excerpts = []

        # Process up to 3 most relevant documents
        for doc_ref in documents[:3]:
            doc_path = doc_ref.get("path", "")
            doc_type = doc_ref.get("type", "unknown")

            # TEMPORARY WORKAROUND: Fix incorrect paths in entity_statistics.json
            # Remove "data/" prefix if present (causes duplication)
            if doc_path.startswith("data/"):
                doc_path = doc_path[5:]  # Strip "data/" prefix

            # Map incorrect "ocr/" paths to actual location
            if doc_path.startswith("ocr/"):
                doc_path = "sources/house_oversight_nov2025/ocr_text/" + doc_path[4:]

            # Try to read document
            full_path = self.markdown_base / doc_path
            if not full_path.exists():
                self.logger.debug(f"Document not found: {full_path}")
                continue

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract paragraphs mentioning entity
                relevant_paragraphs = self._extract_mentions(content, entity_name)

                if relevant_paragraphs:
                    excerpts.append(
                        DocumentExcerpt(
                            document_path=doc_path,
                            document_type=doc_type,
                            excerpts=relevant_paragraphs,
                            relevance_score=len(relevant_paragraphs) / 10.0,
                        )
                    )
                    self.logger.debug(
                        f"Extracted {len(relevant_paragraphs)} paragraphs from {doc_path}"
                    )

            except Exception as e:
                self.logger.error(f"Error reading {full_path}: {e}")
                continue

        return excerpts

    def _extract_mentions(self, content: str, entity_name: str) -> List[str]:
        """Extract paragraphs mentioning entity name

        Args:
            content: Document content
            entity_name: Entity name to search for

        Returns:
            List of relevant paragraphs (max 5)
        """

        # Split content into paragraphs
        paragraphs = re.split(r"\n\n+", content)

        # Find paragraphs mentioning entity (case-insensitive)
        # Handle name variations (e.g., "Epstein, Jeffrey" vs "Jeffrey Epstein")
        name_parts = entity_name.replace(",", "").split()

        relevant = []
        for para in paragraphs:
            # Skip YAML frontmatter and headers
            if para.startswith("---") or para.startswith("#"):
                continue

            # Check if any significant part of name appears
            para_lower = para.lower()
            if any(
                part.lower() in para_lower for part in name_parts if len(part) > 2
            ):
                # Clean up paragraph
                cleaned = re.sub(r"\s+", " ", para).strip()
                if len(cleaned) > 50:  # Ignore very short snippets
                    relevant.append(cleaned[:500])  # Limit length

        return relevant[:5]  # Max 5 paragraphs per document


# ============================================================================
# Grok AI Integration
# ============================================================================


class GrokEnricher:
    """Use Grok AI to extract contextual information from documents"""

    def __init__(
        self, api_key: str, dry_run: bool = False, logger: Optional[logging.Logger] = None
    ):
        self.api_key = api_key
        self.dry_run = dry_run
        self.logger = logger or logging.getLogger(__name__)

        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "total_tokens": 0,
            "entities_with_context": 0,
            "entities_without_context": 0,
        }

    def enrich_entity(
        self, request: GrokExtractionRequest
    ) -> GrokExtractionResponse:
        """Use Grok to extract additional context from documents

        Args:
            request: Extraction request with entity and document data

        Returns:
            Extracted contextual information
        """

        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would enrich {request.entity_name}")
            self.stats["successful"] += 1
            return GrokExtractionResponse(
                additional_context=["[DRY RUN] Sample context"], confidence=0.5
            )

        # Build prompt
        system_prompt = """You are analyzing documents from the Epstein archive to enrich entity biographies.

Your task: Extract 2-3 specific factual details from document excerpts that would enhance the biography.

Focus on:
- Specific events or dates mentioned in documents
- Relationships or interactions described
- Roles, positions, or affiliations
- Notable activities or behaviors documented

Requirements:
- Be precise and cite what you find
- Use ONLY information from the excerpts provided
- Maintain factual, investigative journalism tone
- Avoid speculation beyond what documents show
- If excerpts don't provide useful additional context, return empty list

Output format: Valid JSON only
{
  "additional_context": [
    "Specific detail 1 from documents",
    "Specific detail 2 from documents"
  ],
  "confidence": 0.0-1.0
}"""

        # Format excerpts
        excerpt_text = self._format_excerpts(request.document_excerpts)

        user_prompt = f"""Entity: {request.entity_name}

Current Biography: {request.current_biography}

Document Excerpts Mentioning This Entity:
{excerpt_text}

Extract 2-3 specific factual details from these excerpts that would enhance the biography.
Output valid JSON only."""

        try:
            response = requests.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/epstein-archive",
                    "X-Title": "Epstein Archive Bio Enrichment",
                },
                json={
                    "model": GROK_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.2,  # Low temperature for factual extraction
                    "max_tokens": 300,
                    "response_format": {"type": "json_object"},
                },
                timeout=30,
            )

            response.raise_for_status()
            result = response.json()

            # Extract and parse response
            content = result["choices"][0]["message"]["content"].strip()
            self.logger.debug(f"Grok response: {content}")

            # Parse JSON response
            try:
                parsed = json.loads(content)
                extraction = GrokExtractionResponse(**parsed)
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.error(f"Failed to parse Grok response: {e}")
                self.logger.debug(f"Raw response: {content}")
                extraction = GrokExtractionResponse(
                    additional_context=[], confidence=0.0
                )

            # Update stats
            usage = result.get("usage", {})
            self.stats["total_tokens"] += usage.get("total_tokens", 0)
            self.stats["total_requests"] += 1
            self.stats["successful"] += 1

            if extraction.additional_context:
                self.stats["entities_with_context"] += 1
            else:
                self.stats["entities_without_context"] += 1

            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)

            return extraction

        except requests.exceptions.RequestException as e:
            self.stats["failed"] += 1
            self.stats["total_requests"] += 1
            self.logger.error(f"API request failed for {request.entity_name}: {e}")

            return GrokExtractionResponse(additional_context=[], confidence=0.0)

        except Exception as e:
            self.stats["failed"] += 1
            self.stats["total_requests"] += 1
            self.logger.error(
                f"Unexpected error enriching {request.entity_name}: {e}"
            )

            return GrokExtractionResponse(additional_context=[], confidence=0.0)

    def _format_excerpts(self, excerpts: List[DocumentExcerpt]) -> str:
        """Format document excerpts for prompt"""

        if not excerpts:
            return "No document excerpts available."

        formatted = []
        for i, excerpt in enumerate(excerpts, 1):
            formatted.append(f"Document {i}: {excerpt.document_type}")
            for j, para in enumerate(excerpt.excerpts, 1):
                formatted.append(f"  Excerpt {j}: {para}")
            formatted.append("")

        return "\n".join(formatted)


# ============================================================================
# Biography Enrichment Orchestrator
# ============================================================================


class BiographyEnricher:
    """Main orchestrator for enriching biographies from documents"""

    def __init__(
        self,
        biography_path: Path,
        entity_stats_path: Path,
        markdown_base: Path,
        api_key: str,
        dry_run: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        self.biography_path = biography_path
        self.entity_stats_path = entity_stats_path
        self.markdown_base = markdown_base
        self.dry_run = dry_run
        self.logger = logger or logging.getLogger(__name__)

        # Load data
        self.biographies = self._load_biographies()
        self.entity_stats = self._load_entity_stats()

        # Initialize components
        self.document_extractor = DocumentExtractor(markdown_base, self.logger)
        self.grok_enricher = GrokEnricher(api_key, dry_run, self.logger)

    def _load_biographies(self) -> Dict[str, Any]:
        """Load entity biographies from JSON"""

        if not self.biography_path.exists():
            self.logger.error(f"Biography file not found: {self.biography_path}")
            return {}

        with open(self.biography_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle both formats: {"entities": {...}} and {...}
        if "entities" in data:
            biographies = data["entities"]
        else:
            biographies = data

        self.logger.info(f"Loaded {len(biographies)} entity biographies")
        return biographies

    def _load_entity_stats(self) -> Dict[str, Any]:
        """Load entity statistics (document references)"""

        if not self.entity_stats_path.exists():
            self.logger.error(f"Entity stats file not found: {self.entity_stats_path}")
            return {}

        with open(self.entity_stats_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle structure with "statistics" key
        if "statistics" in data:
            stats = data["statistics"]
        else:
            stats = data

        self.logger.info(f"Loaded statistics for {len(stats)} entities")
        return stats

    def enrich_entity(self, entity_id: str) -> EnrichmentResult:
        """Enrich a single entity biography

        Args:
            entity_id: Entity identifier

        Returns:
            Enrichment result with extracted context
        """

        # Get biography
        bio_data = self.biographies.get(entity_id)
        if not bio_data:
            self.logger.warning(f"No biography found for {entity_id}")
            return EnrichmentResult(
                entity_id=entity_id,
                entity_name=entity_id,
                success=False,
                error="Biography not found",
            )

        # Check if already enriched
        if "document_context" in bio_data and not self.dry_run:
            self.logger.debug(f"Entity {entity_id} already enriched, skipping")
            return EnrichmentResult(
                entity_id=entity_id,
                entity_name=bio_data.get("display_name", entity_id),
                success=True,
                document_context=bio_data.get("document_context", []),
                documents_analyzed=0,
            )

        # Get current biography text
        current_bio = bio_data.get("summary", "")
        if not current_bio:
            self.logger.warning(f"No biography summary for {entity_id}")
            return EnrichmentResult(
                entity_id=entity_id,
                entity_name=bio_data.get("display_name", entity_id),
                success=False,
                error="No biography summary available",
            )

        # Find documents
        document_excerpts = self.document_extractor.find_documents_for_entity(
            entity_id, self.entity_stats
        )

        if not document_excerpts:
            self.logger.debug(f"No documents found for {entity_id}")
            return EnrichmentResult(
                entity_id=entity_id,
                entity_name=bio_data.get("display_name", entity_id),
                success=True,
                document_context=[],
                documents_analyzed=0,
            )

        # Extract context with Grok
        request = GrokExtractionRequest(
            entity_id=entity_id,
            entity_name=bio_data.get("display_name", entity_id),
            current_biography=current_bio,
            document_excerpts=document_excerpts,
        )

        extraction = self.grok_enricher.enrich_entity(request)

        return EnrichmentResult(
            entity_id=entity_id,
            entity_name=bio_data.get("display_name", entity_id),
            success=True,
            document_context=extraction.additional_context,
            documents_analyzed=len(document_excerpts),
            confidence=extraction.confidence,
        )

    def enrich_all(
        self, entity_ids: Optional[List[str]] = None, limit: Optional[int] = None
    ) -> List[EnrichmentResult]:
        """Enrich multiple entities

        Args:
            entity_ids: Specific entity IDs to enrich (None = all with biographies)
            limit: Maximum number to process (None = all)

        Returns:
            List of enrichment results
        """

        # Determine which entities to process
        if entity_ids:
            to_process = entity_ids
        else:
            # All entities with biographies
            to_process = list(self.biographies.keys())

        # Apply limit
        if limit:
            to_process = to_process[:limit]

        self.logger.info(f"Processing {len(to_process)} entities")

        # Process with progress bar
        results = []
        for entity_id in tqdm(to_process, desc="Enriching biographies"):
            result = self.enrich_entity(entity_id)
            results.append(result)

            # Log progress
            if result.success and result.document_context:
                self.logger.info(
                    f"✓ {result.entity_name}: {len(result.document_context)} details extracted"
                )
            elif not result.success:
                self.logger.warning(f"✗ {result.entity_name}: {result.error}")

        return results

    def save_results(
        self, results: List[EnrichmentResult], output_path: Optional[Path] = None
    ) -> None:
        """Save enrichment results back to biography file

        Args:
            results: List of enrichment results
            output_path: Output file path (None = overwrite original)
        """

        if self.dry_run:
            self.logger.info("[DRY RUN] Would save results to biography file")
            return

        output_path = output_path or self.biography_path

        # Update biographies with document context
        for result in results:
            if not result.success:
                continue

            bio_data = self.biographies.get(result.entity_id)
            if not bio_data:
                continue

            # Add document context
            bio_data["document_context"] = result.document_context
            bio_data["context_metadata"] = {
                "extraction_date": datetime.now(timezone.utc).isoformat(),
                "documents_analyzed": result.documents_analyzed,
                "model": GROK_MODEL,
                "confidence": result.confidence,
            }

        # Create backup if not already done
        if output_path == self.biography_path:
            backup_path = self.biography_path.with_suffix(
                f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            shutil.copy2(self.biography_path, backup_path)
            self.logger.info(f"Backup created: {backup_path}")

        # Save updated biographies
        # Load original to preserve structure
        with open(self.biography_path, "r", encoding="utf-8") as f:
            original_data = json.load(f)

        # Update entities section
        if "entities" in original_data:
            original_data["entities"] = self.biographies
        else:
            original_data = self.biographies

        # Update metadata
        if isinstance(original_data, dict) and "metadata" in original_data:
            original_data["metadata"]["last_updated"] = datetime.now(
                timezone.utc
            ).isoformat()
            original_data["metadata"]["document_enrichment_applied"] = True
            original_data["metadata"]["enrichment_date"] = datetime.now(
                timezone.utc
            ).isoformat()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(original_data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Results saved to {output_path}")

    def print_summary(self, results: List[EnrichmentResult]) -> None:
        """Print summary statistics

        Args:
            results: List of enrichment results
        """

        successful = sum(1 for r in results if r.success)
        with_context = sum(1 for r in results if r.document_context)
        total_details = sum(len(r.document_context) for r in results)

        print("\n" + "=" * 70)
        print("ENRICHMENT SUMMARY")
        print("=" * 70)
        print(f"Total entities processed: {len(results)}")
        print(f"Successful: {successful}")
        print(f"With additional context: {with_context}")
        print(f"Total details extracted: {total_details}")
        print(f"Average details per entity: {total_details / len(results):.2f}")
        print()

        # Grok stats
        print("Grok API Statistics:")
        print(f"  Total requests: {self.grok_enricher.stats['total_requests']}")
        print(f"  Successful: {self.grok_enricher.stats['successful']}")
        print(f"  Failed: {self.grok_enricher.stats['failed']}")
        print(f"  Total tokens used: {self.grok_enricher.stats['total_tokens']}")
        print(f"  Entities with context: {self.grok_enricher.stats['entities_with_context']}")
        print(
            f"  Entities without context: {self.grok_enricher.stats['entities_without_context']}"
        )
        print("=" * 70)


# ============================================================================
# CLI
# ============================================================================


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(
        description="Enrich entity biographies with document context using Grok AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run for top 5 entities
  %(prog)s --dry-run --limit 5

  # Enrich specific entity with backup
  %(prog)s --entity-id jeffrey_epstein --backup

  # Enrich all with biographies (first 100)
  %(prog)s --limit 100 --backup

  # Output to custom file
  %(prog)s --limit 20 --output /tmp/enriched_bios.json
        """,
    )

    parser.add_argument(
        "--entity-id", type=str, help="Process single entity by ID"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Process first N entities (default: 10)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be extracted without API calls",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup before modifying biography file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path (default: overwrite entity_biographies.json)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.verbose)

    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key and not args.dry_run:
        logger.error("OPENROUTER_API_KEY environment variable not set")
        logger.error("Set it in .env.local or export it before running")
        sys.exit(1)

    # Initialize enricher
    enricher = BiographyEnricher(
        biography_path=BIOGRAPHY_PATH,
        entity_stats_path=ENTITY_STATS_PATH,
        markdown_base=MARKDOWN_BASE,
        api_key=api_key or "dry-run-key",
        dry_run=args.dry_run,
        logger=logger,
    )

    # Create backup if requested
    if args.backup and not args.dry_run:
        backup_path = BIOGRAPHY_PATH.with_suffix(
            f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        shutil.copy2(BIOGRAPHY_PATH, backup_path)
        logger.info(f"Backup created: {backup_path}")

    # Process entities
    if args.entity_id:
        # Single entity
        logger.info(f"Enriching single entity: {args.entity_id}")
        result = enricher.enrich_entity(args.entity_id)
        results = [result]
    else:
        # Multiple entities
        results = enricher.enrich_all(limit=args.limit)

    # Save results
    enricher.save_results(results, args.output)

    # Print summary
    enricher.print_summary(results)

    logger.info(f"Log file: {LOG_FILE}")
    logger.info("✓ Enrichment complete")


if __name__ == "__main__":
    main()
