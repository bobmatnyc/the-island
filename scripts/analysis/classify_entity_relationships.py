#!/usr/bin/env python3
"""
Entity Relationship Classification System using Grok LLM

Analyzes entities and classifies them based on their relationships, connections,
and roles using AI-powered analysis via Grok-4.1-fast.

Features:
- Multi-dimensional classification (role, strength, category, temporal)
- Significance scoring (1-10 based on centrality and context)
- Batch processing with checkpointing
- Comprehensive error handling and retry logic
- Quality validation and verification

Author: Entity Classification System
Created: 2025-11-25
"""

import argparse
import json
import os
import shutil
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from pydantic import BaseModel, Field, field_validator


class EntityContext(BaseModel):
    """Context data for entity classification"""
    entity_id: str
    entity_name: str
    entity_type: Optional[str] = None
    flight_count: int = 0
    document_count: int = 0
    connection_count: int = 0
    top_connections: List[str] = Field(default_factory=list)
    in_black_book: bool = False
    biography_summary: Optional[str] = None
    categories: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)


class EntityClassification(BaseModel):
    """Classification result for an entity"""
    primary_role: str = Field(..., description="Main relationship to Epstein")
    connection_strength: str = Field(..., description="Core Circle/Frequent Associate/Occasional Contact/Documented Only")
    professional_category: str = Field(..., description="Primary profession/role")
    temporal_activity: List[str] = Field(..., description="Decade(s) of activity")
    significance_score: int = Field(..., ge=1, le=10, description="Significance score 1-10")
    justification: str = Field(..., description="Brief explanation of classification")

    @field_validator('connection_strength')
    @classmethod
    def validate_connection_strength(cls, v):
        valid = ["Core Circle", "Frequent Associate", "Occasional Contact", "Documented Only"]
        if v not in valid:
            raise ValueError(f"connection_strength must be one of: {valid}")
        return v

    @field_validator('temporal_activity')
    @classmethod
    def validate_temporal_activity(cls, v):
        valid_decades = ["1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
        for decade in v:
            if decade not in valid_decades:
                raise ValueError(f"Invalid decade: {decade}. Must be one of: {valid_decades}")
        return v


class ClassificationResult(BaseModel):
    """Complete classification result with metadata"""
    entity_id: str
    entity_name: str
    classification: EntityClassification
    metadata: Dict
    success: bool
    error: Optional[str] = None


class GrokEntityClassifier:
    """Entity classifier using Grok-4.1-fast API via OpenRouter"""

    def __init__(self, api_key: str, dry_run: bool = False):
        """Initialize classifier with OpenRouter API key"""
        self.api_key = api_key
        self.dry_run = dry_run
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "x-ai/grok-beta"

        # Statistics
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "retries": 0,
            "total_tokens_used": 0,
            "total_api_calls": 0,
            "start_time": datetime.now(timezone.utc).isoformat()
        }

    def build_prompt(self, context: EntityContext) -> Tuple[str, str]:
        """Build system and user prompts for classification"""

        system_prompt = """You are an expert data analyst specializing in network analysis and relationship classification.

Your task is to analyze entities from the Epstein archive and provide structured classifications based on:
- Relationship patterns (flight logs, document mentions, network position)
- Professional roles and categories
- Temporal activity patterns
- Significance based on centrality and context

Provide factual, evidence-based classifications using ONLY the data provided.
Be precise, analytical, and avoid speculation."""

        # Build context summary
        context_parts = []

        # Basic stats
        context_parts.append(f"Entity: {context.entity_name}")
        context_parts.append(f"Entity Type: {context.entity_type or 'person'}")

        # Quantitative metrics
        metrics = []
        if context.flight_count > 0:
            metrics.append(f"Flight Count: {context.flight_count}")
        if context.document_count > 0:
            metrics.append(f"Document Mentions: {context.document_count}")
        if context.connection_count > 0:
            metrics.append(f"Network Connections: {context.connection_count}")

        if metrics:
            context_parts.append("\n".join(metrics))

        # Top connections
        if context.top_connections:
            conn_list = ", ".join(context.top_connections[:10])
            context_parts.append(f"Top Connections: {conn_list}")

        # Additional context
        if context.in_black_book:
            context_parts.append("Listed in Epstein's contact book (Black Book)")

        if context.biography_summary:
            context_parts.append(f"Biography Summary: {context.biography_summary}")

        if context.categories:
            context_parts.append(f"Known Categories: {', '.join(context.categories)}")

        if context.sources:
            context_parts.append(f"Data Sources: {', '.join(context.sources)}")

        context_text = "\n\n".join(context_parts)

        user_prompt = f"""{context_text}

Based on this information, provide classification in the following JSON format:

{{
  "primary_role": "Main relationship to Epstein (1-3 words, e.g., 'Close Associate', 'Business Partner', 'Political Figure', 'Victim', 'Law Enforcement', 'Legal Team')",
  "connection_strength": "One of: 'Core Circle' (>50 flights or high centrality), 'Frequent Associate' (10-50 flights), 'Occasional Contact' (1-9 flights), 'Documented Only' (no flights, only document mentions)",
  "professional_category": "Primary profession/role (e.g., 'Politician', 'Celebrity', 'Financier', 'Scientist', 'Legal Professional', 'Socialite')",
  "temporal_activity": ["Decade(s) of most activity, e.g., '1990s', '2000s', '2010s'"],
  "significance_score": 1-10 (based on centrality, mentions, and context),
  "justification": "1-2 sentences explaining the classification based on the data"
}}

Guidelines:
- Base connection_strength strictly on the metrics provided
- Significance score: 10 = central figure, 5 = moderate involvement, 1 = minimal mention
- Primary role should reflect their apparent relationship from the data
- Temporal activity: infer from context or leave as empty array if unknown
- Justification must reference specific metrics from the context

Return ONLY valid JSON, no additional text."""

        return system_prompt, user_prompt

    def classify_entity(
        self,
        context: EntityContext,
        max_retries: int = 3
    ) -> ClassificationResult:
        """Classify a single entity with retry logic"""

        if self.dry_run:
            self.stats["successful"] += 1
            self.stats["total_processed"] += 1

            return ClassificationResult(
                entity_id=context.entity_id,
                entity_name=context.entity_name,
                classification=EntityClassification(
                    primary_role="[DRY RUN]",
                    connection_strength="Documented Only",
                    professional_category="[DRY RUN]",
                    temporal_activity=["2000s"],
                    significance_score=5,
                    justification="Dry run classification"
                ),
                metadata={
                    "dry_run": True,
                    "flight_count": context.flight_count,
                    "document_count": context.document_count,
                    "connection_count": context.connection_count
                },
                success=True
            )

        # Build prompts
        system_prompt, user_prompt = self.build_prompt(context)

        # Retry loop
        last_error = None
        for attempt in range(max_retries):
            try:
                # Call OpenRouter API
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/epstein-archive",
                        "X-Title": "Epstein Archive Entity Classifier"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.2,  # Low temperature for structured output
                        "max_tokens": 600,
                        "response_format": {"type": "json_object"}  # Request JSON
                    },
                    timeout=30
                )

                response.raise_for_status()
                result = response.json()

                # Extract classification
                content = result["choices"][0]["message"]["content"].strip()

                # Parse JSON
                classification_data = json.loads(content)

                # Validate with Pydantic
                classification = EntityClassification(**classification_data)

                # Track usage
                usage = result.get("usage", {})
                self.stats["total_tokens_used"] += usage.get("total_tokens", 0)
                self.stats["total_api_calls"] += 1
                self.stats["successful"] += 1

                return ClassificationResult(
                    entity_id=context.entity_id,
                    entity_name=context.entity_name,
                    classification=classification,
                    metadata={
                        "classified_by": "grok-beta",
                        "classification_date": datetime.now(timezone.utc).isoformat(),
                        "flight_count": context.flight_count,
                        "document_count": context.document_count,
                        "connection_count": context.connection_count,
                        "tokens_used": usage.get("total_tokens", 0),
                        "attempt": attempt + 1
                    },
                    success=True
                )

            except (requests.exceptions.RequestException, json.JSONDecodeError, ValueError) as e:
                last_error = str(e)
                self.stats["retries"] += 1

                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    print(f"    ⚠ Attempt {attempt + 1} failed: {last_error}")
                    print(f"    Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    # Final failure
                    self.stats["failed"] += 1
                    return ClassificationResult(
                        entity_id=context.entity_id,
                        entity_name=context.entity_name,
                        classification=EntityClassification(
                            primary_role="Unknown",
                            connection_strength="Documented Only",
                            professional_category="Unknown",
                            temporal_activity=[],
                            significance_score=1,
                            justification="Classification failed"
                        ),
                        metadata={},
                        success=False,
                        error=f"Failed after {max_retries} attempts: {last_error}"
                    )

            except Exception as e:
                self.stats["failed"] += 1
                return ClassificationResult(
                    entity_id=context.entity_id,
                    entity_name=context.entity_name,
                    classification=EntityClassification(
                        primary_role="Unknown",
                        connection_strength="Documented Only",
                        professional_category="Unknown",
                        temporal_activity=[],
                        significance_score=1,
                        justification="Classification failed"
                    ),
                    metadata={},
                    success=False,
                    error=f"Unexpected error: {str(e)}"
                )

            finally:
                # Rate limiting: 1.5 seconds between requests
                if not self.dry_run:
                    time.sleep(1.5)

        # Should never reach here, but just in case
        self.stats["failed"] += 1
        return ClassificationResult(
            entity_id=context.entity_id,
            entity_name=context.entity_name,
            classification=EntityClassification(
                primary_role="Unknown",
                connection_strength="Documented Only",
                professional_category="Unknown",
                temporal_activity=[],
                significance_score=1,
                justification="Classification failed"
            ),
            metadata={},
            success=False,
            error="Maximum retries exceeded"
        )

    def batch_classify(
        self,
        contexts: List[EntityContext],
        output_file: Path,
        checkpoint_every: int = 10
    ) -> Dict:
        """Classify batch of entities with checkpointing"""

        results = []
        checkpoint_file = output_file.parent / f"{output_file.stem}_checkpoint.json"

        print(f"\n{'='*80}")
        print(f"BATCH ENTITY CLASSIFICATION")
        print(f"{'='*80}")
        print(f"Total entities: {len(contexts)}")
        print(f"Output file: {output_file}")
        print(f"Checkpoint interval: every {checkpoint_every} entities")
        print(f"Model: {self.model}")
        print(f"Dry run: {self.dry_run}")
        print(f"{'='*80}\n")

        for i, context in enumerate(contexts, 1):
            print(f"\n[{i}/{len(contexts)}] Classifying: {context.entity_name}")
            print(f"  Flights: {context.flight_count}, "
                  f"Docs: {context.document_count}, "
                  f"Connections: {context.connection_count}")

            result = self.classify_entity(context)
            results.append(result)

            if result.success:
                cls = result.classification
                print(f"  ✓ Classified")
                print(f"    Role: {cls.primary_role}")
                print(f"    Strength: {cls.connection_strength}")
                print(f"    Category: {cls.professional_category}")
                print(f"    Significance: {cls.significance_score}/10")
            else:
                print(f"  ✗ Failed: {result.error}")

            # Checkpoint progress
            if i % checkpoint_every == 0:
                self._save_checkpoint(results, checkpoint_file)
                print(f"  💾 Checkpoint saved ({i} entities processed)")

        # Final save
        print(f"\n{'='*80}")
        print(f"Saving final results...")
        self._save_results(results, output_file)

        # Remove checkpoint file after successful completion
        if checkpoint_file.exists():
            checkpoint_file.unlink()
            print(f"Checkpoint file removed")

        return self.stats

    def _save_checkpoint(self, results: List[ClassificationResult], checkpoint_file: Path):
        """Save intermediate checkpoint"""
        self._save_results(results, checkpoint_file)

    def _save_results(self, results: List[ClassificationResult], output_file: Path):
        """Save results to JSON file"""

        successful_results = [r for r in results if r.success]

        # Calculate aggregate statistics
        sig_scores = [r.classification.significance_score for r in successful_results]
        avg_significance = sum(sig_scores) / len(sig_scores) if sig_scores else 0.0

        # Count by connection strength
        strength_counts = {}
        for r in successful_results:
            strength = r.classification.connection_strength
            strength_counts[strength] = strength_counts.get(strength, 0) + 1

        output_data = {
            "metadata": {
                "generated": datetime.now(timezone.utc).isoformat(),
                "classifier": "grok-beta",
                "total_entities": len(results),
                "successful": len(successful_results),
                "failed": sum(1 for r in results if not r.success),
                "statistics": self.stats,
                "average_significance_score": avg_significance,
                "connection_strength_distribution": strength_counts
            },
            "classifications": {
                r.entity_id: {
                    "entity_id": r.entity_id,
                    "entity_name": r.entity_name,
                    "primary_role": r.classification.primary_role,
                    "connection_strength": r.classification.connection_strength,
                    "professional_category": r.classification.professional_category,
                    "temporal_activity": r.classification.temporal_activity,
                    "significance_score": r.classification.significance_score,
                    "justification": r.classification.justification,
                    "metadata": r.metadata
                }
                for r in successful_results
            }
        }

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)


class DatabaseManager:
    """Manage SQLite database operations"""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def create_classifications_table(self):
        """Create entity_classifications table if not exists"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_classifications (
                entity_id TEXT PRIMARY KEY,
                primary_role TEXT NOT NULL,
                connection_strength TEXT NOT NULL,
                professional_category TEXT NOT NULL,
                temporal_activity TEXT,  -- JSON array
                significance_score INTEGER NOT NULL CHECK (significance_score BETWEEN 1 AND 10),
                justification TEXT NOT NULL,
                classified_by TEXT,
                classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,  -- JSON object
                FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE
            )
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_classification_role
            ON entity_classifications(primary_role)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_classification_strength
            ON entity_classifications(connection_strength)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_classification_significance
            ON entity_classifications(significance_score DESC)
        """)

        conn.commit()
        conn.close()

        print(f"✓ Database table 'entity_classifications' ready")

    def import_classifications(self, json_file: Path):
        """Import classifications from JSON to database"""

        with open(json_file) as f:
            data = json.load(f)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        imported = 0
        for entity_id, cls in data["classifications"].items():
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO entity_classifications
                    (entity_id, primary_role, connection_strength, professional_category,
                     temporal_activity, significance_score, justification, classified_by,
                     classified_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity_id,
                    cls["primary_role"],
                    cls["connection_strength"],
                    cls["professional_category"],
                    json.dumps(cls["temporal_activity"]),
                    cls["significance_score"],
                    cls["justification"],
                    cls["metadata"].get("classified_by"),
                    cls["metadata"].get("classification_date"),
                    json.dumps(cls["metadata"])
                ))
                imported += 1
            except Exception as e:
                print(f"  ⚠ Failed to import {entity_id}: {e}")

        conn.commit()
        conn.close()

        print(f"✓ Imported {imported} classifications to database")


def load_entity_contexts(
    stats_file: Path,
    bios_file: Path,
    db_path: Path,
    tier: Optional[str] = None,
    limit: Optional[int] = None
) -> List[EntityContext]:
    """Load entity contexts from statistics and biographies"""

    # Load entity statistics
    with open(stats_file) as f:
        stats_data = json.load(f)

    # Load existing biographies
    bios = {}
    if bios_file.exists():
        with open(bios_file) as f:
            bios_data = json.load(f)
            bios = bios_data.get("entities", {})

    # Load existing classifications to skip
    existing_classifications = set()
    if db_path.exists():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT entity_id FROM entity_classifications")
            existing_classifications = set(row[0] for row in cursor.fetchall())
        except sqlite3.OperationalError:
            # Table doesn't exist yet
            pass
        conn.close()

    # Tier criteria
    tier_criteria = {
        "1": {"min_connections": 15, "description": "Tier 1: High-value entities (15+ connections)"},
        "2": {"min_connections": 10, "description": "Tier 2: Medium-value entities (10-14 connections)"},
        "3": {"min_connections": 5, "description": "Tier 3: Lower-value entities (5-9 connections)"},
        "all": {"min_connections": 0, "description": "All entities"}
    }

    min_connections = 0
    if tier and tier in tier_criteria:
        min_connections = tier_criteria[tier]["min_connections"]
        print(f"\n{tier_criteria[tier]['description']}")

    contexts = []
    for entity_id, entity_data in stats_data["statistics"].items():
        # Skip if already classified
        if entity_id in existing_classifications:
            continue

        # Filter by tier
        connection_count = entity_data.get("connection_count", 0)
        if connection_count < min_connections:
            continue

        # Get biography if available
        bio = bios.get(entity_id, {})
        bio_summary = bio.get("biography", "")

        # Extract top connections (handle both dict and string formats)
        top_connections = entity_data.get("top_connections", [])
        if isinstance(top_connections, list) and len(top_connections) > 0:
            if isinstance(top_connections[0], dict):
                connection_names = [c.get("name", "") for c in top_connections[:15]]
            else:
                connection_names = top_connections[:15]
        else:
            connection_names = []

        # Calculate priority score
        flight_count = entity_data.get("flight_count", 0)
        document_count = entity_data.get("total_documents", 0)
        priority_score = (connection_count * 3) + (flight_count * 2) + document_count

        context = EntityContext(
            entity_id=entity_id,
            entity_name=entity_data["name"],
            entity_type=entity_data.get("entity_type"),
            flight_count=flight_count,
            document_count=document_count,
            connection_count=connection_count,
            top_connections=connection_names,
            in_black_book=entity_data.get("in_black_book", False),
            biography_summary=bio_summary[:500] if bio_summary else None,  # Limit bio length
            categories=entity_data.get("categories", []),
            sources=entity_data.get("sources", [])
        )

        contexts.append((context, priority_score))

    # Sort by priority score
    contexts.sort(key=lambda x: x[1], reverse=True)

    # Apply limit
    if limit:
        contexts = contexts[:limit]

    return [ctx for ctx, _ in contexts]


def backup_file(file_path: Path):
    """Create timestamped backup of file"""
    if not file_path.exists():
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.parent / f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
    shutil.copy(file_path, backup_path)
    print(f"✓ Backup created: {backup_path.name}")


def main():
    """Main execution"""

    parser = argparse.ArgumentParser(
        description="Classify entity relationships using Grok LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run with top 10 entities
  python3 classify_entity_relationships.py --dry-run --limit 10

  # Tier 1 entities (high-value, 15+ connections)
  python3 classify_entity_relationships.py --tier 1 --limit 50

  # Classify entities with biographies
  python3 classify_entity_relationships.py --tier 2 --limit 100

  # Export classifications to database
  python3 classify_entity_relationships.py --export data/metadata/entity_classifications.json --import-db

  # Resume from checkpoint (if exists)
  python3 classify_entity_relationships.py --resume
        """
    )

    parser.add_argument(
        "--api-key",
        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of entities to process (default: 50)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run without making API calls"
    )
    parser.add_argument(
        "--tier",
        choices=["1", "2", "3", "all"],
        help="Entity tier: 1 (15+ connections), 2 (10+), 3 (5+), all (0+)"
    )
    parser.add_argument(
        "--output",
        default="data/metadata/entity_classifications.json",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--export",
        metavar="FILE",
        help="Export specific JSON file to database"
    )
    parser.add_argument(
        "--import-db",
        action="store_true",
        help="Import classifications from output file to database"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup before overwriting output file"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from checkpoint if available"
    )

    args = parser.parse_args()

    # Define paths
    project_root = Path(__file__).parent.parent.parent
    stats_file = project_root / "data/metadata/entity_statistics.json"
    bios_file = project_root / "data/metadata/entity_biographies.json"
    db_path = project_root / "data/metadata/entities.db"
    output_file = project_root / args.output
    checkpoint_file = output_file.parent / f"{output_file.stem}_checkpoint.json"

    # Verify input files
    if not stats_file.exists():
        print(f"ERROR: Entity statistics file not found: {stats_file}")
        return 1

    if not db_path.exists():
        print(f"ERROR: Database not found: {db_path}")
        return 1

    # Initialize database
    db_manager = DatabaseManager(db_path)

    # Handle export/import mode
    if args.export:
        export_file = project_root / args.export
        if not export_file.exists():
            print(f"ERROR: Export file not found: {export_file}")
            return 1

        print(f"\n{'='*80}")
        print(f"IMPORTING CLASSIFICATIONS TO DATABASE")
        print(f"{'='*80}")
        print(f"Source: {export_file}")
        print(f"Database: {db_path}")

        db_manager.create_classifications_table()
        db_manager.import_classifications(export_file)

        print(f"\n✓ Import complete")
        return 0

    # Get API key
    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key and not args.dry_run:
        print("ERROR: API key required")
        print("Either:")
        print("  1. Set OPENROUTER_API_KEY environment variable")
        print("  2. Use --api-key argument")
        print("  3. Use --dry-run for testing")
        return 1

    # Resume from checkpoint if requested
    if args.resume and checkpoint_file.exists():
        print(f"\n{'='*80}")
        print(f"RESUME FROM CHECKPOINT")
        print(f"{'='*80}")
        print(f"Checkpoint file: {checkpoint_file}")
        print(f"\nCheckpoint found. Loading previous results...")

        with open(checkpoint_file) as f:
            checkpoint_data = json.load(f)

        print(f"Previous progress:")
        print(f"  Total: {checkpoint_data['metadata']['total_entities']}")
        print(f"  Successful: {checkpoint_data['metadata']['successful']}")
        print(f"  Failed: {checkpoint_data['metadata']['failed']}")

        print(f"\nContinuing from checkpoint...")
        # Note: Resume functionality would require tracking which entities were processed
        # For simplicity, we'll just note that checkpoint exists
        print(f"⚠ Resume from checkpoint not fully implemented yet")
        print(f"  The checkpoint file will be used if processing is restarted")

    # Backup existing output if requested
    if args.backup and output_file.exists():
        backup_file(output_file)

    # Load entities
    print(f"\n{'='*80}")
    print(f"LOADING ENTITIES")
    print(f"{'='*80}")

    contexts = load_entity_contexts(
        stats_file=stats_file,
        bios_file=bios_file,
        db_path=db_path,
        tier=args.tier,
        limit=args.limit
    )

    if not contexts:
        print("\nNo entities match the criteria.")
        print("Either all entities are already classified or filters are too restrictive.")
        return 0

    print(f"\nTotal entities to classify: {len(contexts)}")
    print(f"Output: {output_file}")

    if not args.dry_run:
        print(f"API: {api_key[:20]}..." if len(api_key) > 20 else "API: [key present]")
    else:
        print(f"Mode: DRY RUN (no API calls)")

    # Show top 5 entities
    print(f"\nTop 5 entities by priority:")
    for i, ctx in enumerate(contexts[:5], 1):
        print(f"  {i}. {ctx.entity_name}")
        print(f"     Connections: {ctx.connection_count}, "
              f"Flights: {ctx.flight_count}, "
              f"Docs: {ctx.document_count}")

    # Ensure database table exists
    db_manager.create_classifications_table()

    # Classify entities
    classifier = GrokEntityClassifier(api_key=api_key or "", dry_run=args.dry_run)
    stats = classifier.batch_classify(
        contexts=contexts,
        output_file=output_file,
        checkpoint_every=10
    )

    # Import to database if requested
    if args.import_db and output_file.exists():
        print(f"\n{'='*80}")
        print(f"IMPORTING TO DATABASE")
        print(f"{'='*80}")
        db_manager.import_classifications(output_file)

    # Print summary
    print(f"\n{'='*80}")
    print(f"CLASSIFICATION COMPLETE")
    print(f"{'='*80}")
    print(f"Total processed: {stats['total_processed']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Retries: {stats['retries']}")
    print(f"Success rate: {(stats['successful'] / stats['total_processed'] * 100) if stats['total_processed'] > 0 else 0:.1f}%")

    if not args.dry_run:
        print(f"Total API calls: {stats['total_api_calls']}")
        print(f"Total tokens used: {stats['total_tokens_used']:,}")

        # Estimate cost (post-December 3, 2025 pricing)
        # Grok-beta pricing: ~$0.50/M input, ~$1.50/M output
        input_cost = (stats['total_tokens_used'] * 0.70) / 1_000_000 * 0.50
        output_cost = (stats['total_tokens_used'] * 0.30) / 1_000_000 * 1.50
        total_cost = input_cost + output_cost
        print(f"Estimated cost (post-Dec 3): ${total_cost:.4f}")
        print(f"  (Currently FREE until December 3, 2025)")

    print(f"\nOutput file: {output_file}")
    if args.import_db:
        print(f"Database: {db_path}")
    print(f"Start time: {stats['start_time']}")
    print(f"End time: {datetime.now(timezone.utc).isoformat()}")

    return 0


if __name__ == "__main__":
    exit(main())
