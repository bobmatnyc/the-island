# Entity Biography Enhancement System - Comprehensive Design

**Quick Summary**: This document outlines a comprehensive system for enhancing entity profiles with AI-generated biographies and web-sourced enrichment data.  The system uses a two-phase approach:.

**Category**: Documentation
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Total Entities**: 1,637
- **Entities WITH Biographies**: 17 (1.0%)
- **Entities WITHOUT Biographies**: 1,620 (99.0%)
- **Priority Target**: Top 200 entities by connection_count + flight_count
- Phase 1: 200+ entities with AI-generated bios (2-3 days)

---

**Version**: 1.0
**Date**: 2025-11-21
**Status**: Design Phase

---

## Executive Summary

This document outlines a comprehensive system for enhancing entity profiles with AI-generated biographies and web-sourced enrichment data. The system uses a two-phase approach:

1. **Phase 1**: Grok-4.1-fast API integration for rapid bio generation from existing source material
2. **Phase 2**: Queue-based web enrichment system for ongoing data enhancement

**Current State**:
- **Total Entities**: 1,637
- **Entities WITH Biographies**: 17 (1.0%)
- **Entities WITHOUT Biographies**: 1,620 (99.0%)
- **Priority Target**: Top 200 entities by connection_count + flight_count

**Success Metrics**:
- Phase 1: 200+ entities with AI-generated bios (2-3 days)
- Phase 2: Continuous enrichment queue processing 50-100 entities/day
- Classification coverage: 80%+ entities with role/relationship tags

---

## 1. Current System Analysis

### 1.1 Entity Data Architecture

**Core Files**:
```
data/metadata/
├── entity_statistics.json          # 1,637 entities with connection/flight stats
├── entity_biographies.json         # 17 hand-curated biographies
├── entity_tags.json               # Classification/categorization tags
├── entity_name_mappings.json      # Name variation resolution
└── entity_network.json            # Relationship graph data
```

**Entity Model** (`server/models/entity.py`):
```python
class Entity(BaseModel):
    id: str                         # Unique identifier (snake_case)
    name: str                       # Display name
    normalized_name: Optional[str]  # Canonical name form
    name_variations: list[str]      # Alternative spellings
    entity_type: EntityType         # PERSON, ORGANIZATION, LOCATION, etc.

    # Flags
    in_black_book: bool
    is_billionaire: bool

    # Statistics
    connection_count: int           # Network connections
    flight_count: int              # Flight log appearances
    total_documents: int           # Document mentions

    # Sources
    sources: list[SourceType]      # black_book, flight_logs
    documents: list[DocumentReference]
    top_connections: list[TopConnection]
```

**Biography Model**:
```python
class EntityBiography(BaseModel):
    entity_name: str               # Must match Entity.name
    biography: str                 # Descriptive paragraph (min 10 chars)
    last_updated: Optional[str]    # ISO timestamp
```

### 1.2 Source Material Inventory

**Available Context per Entity**:

1. **Flight Logs** (`data/md/entities/flight_logs.md`):
   - 358 unique passengers
   - 3,721 flight records (1996-2002)
   - Co-passenger networks (top_connections)
   - Route patterns and frequency

2. **Black Book** (`data/md/entities/little_black_book.md`):
   - 1,422 entities
   - Contact information (redacted for privacy)
   - Page references

3. **Email Archive** (`data/emails/house_oversight_nov2025/`):
   - House Oversight Committee emails
   - Full text and body extracts
   - Date-organized folders
   - Subject lines and participants

4. **Court Documents** (various):
   - PDFs in `data/sources/`
   - OCR-extracted text
   - Metadata in all_documents.json

5. **News Articles** (`data/metadata/news_articles_index.json`):
   - Currently: 2 articles (limited)
   - Potential expansion source

6. **Existing Biographies** (`entity_biographies.json`):
   - 17 hand-curated examples
   - Template format for consistency
   - Source attribution model

### 1.3 Top Entities Without Biographies

| Rank | Entity ID | Name | Connections | Flights | Sources |
|------|-----------|------|-------------|---------|---------|
| 7 | larry_morrison | Larry Morrison | 33 | 95 | black_book, flight_logs |
| 8 | female_1 | Female (1) | 20 | 120 | flight_logs |
| 9 | teala_davies | Teala Davies | 20 | 48 | flight_logs |
| 10 | shelley_lewis | Shelley Lewis | 19 | 39 | flight_logs |
| 11 | brent_tindall | Brent Tindall | 16 | 60 | flight_logs |
| 12 | didier | Didier | 16 | 32 | flight_logs |
| 13 | andrea_mitrovich | Andrea Mitrovich | 15 | 58 | flight_logs |
| 14 | cindy_lopez | Cindy Lopez | 15 | 33 | flight_logs |
| 15 | gwendolyn_beck | Gwendolyn Beck | 14 | 27 | flight_logs |
| 16 | celina_dubin | Celina Dubin | 13 | 35 | flight_logs |
| 17 | eva_dubin | Eva Dubin | 13 | 36 | black_book, flight_logs |
| 18 | sophie_biddle | Sophie Biddle | 13 | 30 | flight_logs |
| 19 | celina_midelfart | Celina Midelfart | 12 | 18 | flight_logs |
| 20 | david_mullen | David Mullen | 12 | 23 | flight_logs |

**Note**: Entities 1-6 (Jeffrey Epstein, Ghislaine Maxwell, Emmy Tayler, Sarah Kellen, Larry Visoski, Nadia) already have comprehensive biographies.

---

## 2. Phase 1: Grok-4.1-fast Integration

### 2.1 API Specifications

**Model**: `x-ai/grok-4.1-fast:free` via OpenRouter

**Capabilities**:
- Context window: 2M tokens (2 million)
- Reasoning: Enable/disable via `reasoning_enabled` parameter
- Tool calling: Best-in-class agentic capabilities
- OpenAI-compatible API

**Pricing** (FREE until December 3, 2025):
- Input: $0.20 per million tokens (normally)
- Cached input: $0.05 per million tokens
- Output: $0.50 per million tokens
- Tool calls: $5 per 1,000 invocations (free until Dec 3)
- **Current Status**: Completely FREE on OpenRouter until December 3

**Rate Limits**:
- Not explicitly documented for free tier
- Managed by OpenRouter infrastructure
- Recommendation: Implement 1-2 second delays between requests
- Batch size: Process 10-20 entities per batch

### 2.2 Prompt Engineering Strategy

**Input Context Structure**:
```
Entity: {entity_name}
Role: Generate a concise biographical paragraph for use in an investigation archive

Context Available:
1. Flight Logs:
   - Total flights: {flight_count}
   - Date range: {date_range}
   - Co-passengers: {top_connections[:10]}
   - Routes: {common_routes}

2. Black Book:
   - Listed: {in_black_book}
   - Page references: {black_book_pages}

3. Network Statistics:
   - Direct connections: {connection_count}
   - Document mentions: {total_documents}
   - Sources: {sources}

4. Additional Context:
   - Document excerpts: {relevant_doc_snippets}
   - Email mentions: {email_context}

Requirements:
- Length: 150-300 words
- Style: Factual, investigative journalism tone
- Focus: Relationship to Epstein, role in network, key activities
- Include: Approximate timeframe of involvement
- Avoid: Speculation beyond documented evidence
- Format: Single paragraph, dense with verifiable facts

Constraints:
- Privacy-respecting for alleged victims
- No unsubstantiated allegations
- Clear distinction between documented facts and allegations
- Source material references where possible
```

**Example Prompt** (Larry Morrison):
```
Entity: Larry Morrison
Role: Generate biographical paragraph for investigation archive

Context:
- Flight logs: 95 flights between 1996-2002
- Black Book: Listed (contact information redacted)
- Network: 33 direct connections including Epstein, Maxwell
- Co-passengers: Frequently flew with core Epstein circle
- Role: Appears to be pilot or flight crew based on frequency and patterns

Generate a 150-300 word biographical paragraph focusing on:
1. Apparent role in Epstein's operations
2. Timeframe of involvement (1996-2002)
3. Network position (frequent flyer, 95 trips)
4. Notable co-passengers or connections
5. Public records (if any)

Style: Factual investigative journalism. Avoid speculation.
```

**Expected Output Format**:
```json
{
  "entity_id": "larry_morrison",
  "entity_name": "Larry Morrison",
  "biography": "Larry Morrison appears in Epstein flight logs 95 times between 1996 and 2002, making him one of the most frequent passengers on Epstein's private jets. His consistent presence alongside Jeffrey Epstein, Ghislaine Maxwell, and other core network members suggests a professional or operational role within Epstein's circle. Morrison is also listed in Epstein's contact book, indicating direct communication access. Flight log patterns show regular routes between key Epstein properties (Palm Beach, New York, New Mexico). Public records do not reveal extensive biographical information, suggesting Morrison maintained a relatively private profile. His frequency of travel and close network connections position him as a significant figure in Epstein's operations during this period, though specific details about his role remain limited to documented flight records and contact information.",
  "metadata": {
    "generated_by": "grok-4.1-fast",
    "generation_date": "2025-11-21T14:30:00Z",
    "source_material": ["flight_logs", "black_book"],
    "confidence_score": 0.85,
    "word_count": 145,
    "needs_web_enrichment": true
  }
}
```

### 2.3 Implementation Architecture

**Script**: `scripts/analysis/generate_entity_bios_grok.py`

```python
#!/usr/bin/env python3
"""
Entity Biography Generator using Grok-4.1-fast

Generates descriptive biographies for entities based on available source material.
Uses OpenRouter API to access x-ai/grok-4.1-fast:free model.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from pydantic import BaseModel


class BiographyGenerationRequest(BaseModel):
    """Request structure for biography generation"""
    entity_id: str
    entity_name: str
    flight_count: int
    connection_count: int
    top_connections: List[str]
    in_black_book: bool
    sources: List[str]
    additional_context: Optional[str] = None


class BiographyGenerationResult(BaseModel):
    """Result structure for generated biography"""
    entity_id: str
    entity_name: str
    biography: str
    metadata: Dict
    success: bool
    error: Optional[str] = None


class GrokBiographyGenerator:
    """Biography generator using Grok-4.1-fast API"""

    def __init__(self, api_key: str, dry_run: bool = False):
        """Initialize generator with OpenRouter API key"""
        self.api_key = api_key
        self.dry_run = dry_run
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "x-ai/grok-4.1-fast:free"

        # Statistics
        self.stats = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "total_tokens_used": 0,
            "total_api_calls": 0
        }

    def build_context(self, entity_data: Dict) -> str:
        """Build rich context from entity data"""
        context_parts = []

        # Flight log context
        if entity_data.get("flight_count", 0) > 0:
            context_parts.append(
                f"Flight Logs:\n"
                f"- Total flights: {entity_data['flight_count']}\n"
                f"- Top co-passengers: {', '.join(entity_data.get('top_connections', [])[:10])}"
            )

        # Black book context
        if entity_data.get("in_black_book"):
            context_parts.append("Black Book: Listed in Epstein's contact book")

        # Network statistics
        context_parts.append(
            f"Network Statistics:\n"
            f"- Direct connections: {entity_data.get('connection_count', 0)}\n"
            f"- Document mentions: {entity_data.get('total_documents', 0)}\n"
            f"- Data sources: {', '.join(entity_data.get('sources', []))}"
        )

        return "\n\n".join(context_parts)

    def generate_biography(self, request: BiographyGenerationRequest) -> BiographyGenerationResult:
        """Generate biography for single entity"""

        if self.dry_run:
            return BiographyGenerationResult(
                entity_id=request.entity_id,
                entity_name=request.entity_name,
                biography=f"[DRY RUN] Biography would be generated for {request.entity_name}",
                metadata={"dry_run": True},
                success=True
            )

        # Build prompt
        context = self.build_context(request.dict())

        prompt = f"""Entity: {request.entity_name}
Role: Generate a concise biographical paragraph for an investigation archive

{context}

Requirements:
- Length: 150-300 words
- Style: Factual investigative journalism
- Focus: Relationship to Epstein, role in network, key activities
- Include: Timeframe of involvement (approximate)
- Avoid: Speculation beyond documented evidence
- Format: Single dense paragraph

Generate biography:"""

        try:
            # Call OpenRouter API
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/epstein-project",  # Optional
                    "X-Title": "Epstein Archive Entity Bio Generator"     # Optional
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert investigative journalist writing factual biographical summaries for a public interest archive. Be precise, factual, and avoid speculation."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,  # Lower temperature for factual content
                    "max_tokens": 500
                }
            )

            response.raise_for_status()
            result = response.json()

            # Extract biography
            biography = result["choices"][0]["message"]["content"].strip()

            # Track usage
            usage = result.get("usage", {})
            self.stats["total_tokens_used"] += usage.get("total_tokens", 0)
            self.stats["total_api_calls"] += 1
            self.stats["successful"] += 1

            return BiographyGenerationResult(
                entity_id=request.entity_id,
                entity_name=request.entity_name,
                biography=biography,
                metadata={
                    "generated_by": "grok-4.1-fast",
                    "generation_date": datetime.utcnow().isoformat() + "Z",
                    "source_material": request.sources,
                    "word_count": len(biography.split()),
                    "tokens_used": usage.get("total_tokens", 0),
                    "needs_web_enrichment": True
                },
                success=True
            )

        except Exception as e:
            self.stats["failed"] += 1
            return BiographyGenerationResult(
                entity_id=request.entity_id,
                entity_name=request.entity_name,
                biography="",
                metadata={},
                success=False,
                error=str(e)
            )

        finally:
            self.stats["total_processed"] += 1
            # Rate limiting: 1 second between requests
            time.sleep(1.0)

    def batch_generate(
        self,
        entities: List[Dict],
        output_file: Path,
        checkpoint_every: int = 10
    ) -> Dict:
        """Generate biographies for batch of entities with checkpointing"""

        results = []

        for i, entity in enumerate(entities, 1):
            print(f"\n[{i}/{len(entities)}] Processing: {entity['name']}")

            request = BiographyGenerationRequest(
                entity_id=entity["id"],
                entity_name=entity["name"],
                flight_count=entity.get("flight_count", 0),
                connection_count=entity.get("connection_count", 0),
                top_connections=[c["name"] for c in entity.get("top_connections", [])[:10]],
                in_black_book=entity.get("in_black_book", False),
                sources=entity.get("sources", [])
            )

            result = self.generate_biography(request)
            results.append(result)

            if result.success:
                print(f"  ✓ Generated ({result.metadata.get('word_count', 0)} words)")
            else:
                print(f"  ✗ Failed: {result.error}")

            # Checkpoint progress
            if i % checkpoint_every == 0:
                self._save_checkpoint(results, output_file)
                print(f"  💾 Checkpoint saved ({i} entities)")

        # Final save
        self._save_results(results, output_file)

        return self.stats

    def _save_checkpoint(self, results: List[BiographyGenerationResult], output_file: Path):
        """Save intermediate results"""
        checkpoint_file = output_file.parent / f"{output_file.stem}_checkpoint.json"
        self._save_results(results, checkpoint_file)

    def _save_results(self, results: List[BiographyGenerationResult], output_file: Path):
        """Save results to file"""
        output_data = {
            "metadata": {
                "generated": datetime.utcnow().isoformat() + "Z",
                "generator": "grok-4.1-fast",
                "total_entities": len(results),
                "successful": sum(1 for r in results if r.success),
                "failed": sum(1 for r in results if not r.success),
                "statistics": self.stats
            },
            "entities": {
                r.entity_id: {
                    "id": r.entity_id,
                    "display_name": r.entity_name,
                    "biography": r.biography,
                    **r.metadata
                }
                for r in results if r.success
            }
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2)


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate entity biographies using Grok-4.1-fast")
    parser.add_argument("--api-key", help="OpenRouter API key (or set OPENROUTER_API_KEY env var)")
    parser.add_argument("--limit", type=int, default=200, help="Number of entities to process")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without API calls")
    parser.add_argument("--min-connections", type=int, default=10, help="Minimum connection count")
    parser.add_argument("--output", default="data/metadata/entity_biographies_grok.json")

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key and not args.dry_run:
        raise ValueError("API key required (--api-key or OPENROUTER_API_KEY env var)")

    # Load entities
    stats_file = Path("data/metadata/entity_statistics.json")
    with open(stats_file) as f:
        data = json.load(f)

    # Load existing biographies to skip
    bios_file = Path("data/metadata/entity_biographies.json")
    with open(bios_file) as f:
        existing_bios = json.load(f).get("entities", {})

    # Filter and sort entities
    entities = []
    for entity_id, entity_data in data["statistics"].items():
        # Skip if already has bio
        if entity_id in existing_bios:
            continue

        # Filter by connection count
        if entity_data.get("connection_count", 0) < args.min_connections:
            continue

        # Calculate priority score
        priority_score = (
            entity_data.get("connection_count", 0) * 2 +
            entity_data.get("flight_count", 0)
        )

        entities.append({
            **entity_data,
            "priority_score": priority_score
        })

    # Sort by priority
    entities.sort(key=lambda x: x["priority_score"], reverse=True)
    entities = entities[:args.limit]

    print(f"Processing {len(entities)} entities")
    print(f"API: {api_key[:10]}..." if api_key else "DRY RUN")
    print(f"Output: {args.output}\n")

    # Generate biographies
    generator = GrokBiographyGenerator(api_key=api_key or "", dry_run=args.dry_run)
    stats = generator.batch_generate(
        entities=entities,
        output_file=Path(args.output),
        checkpoint_every=10
    )

    # Print summary
    print("\n" + "="*70)
    print("GENERATION COMPLETE")
    print("="*70)
    print(f"Total processed: {stats['total_processed']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Total API calls: {stats['total_api_calls']}")
    print(f"Total tokens used: {stats['total_tokens_used']:,}")
    print(f"Output file: {args.output}")


if __name__ == "__main__":
    main()
```

### 2.4 Batch Processing Strategy

**Priority Tiers**:
```python
# Tier 1: High-value entities (Batch 1)
- connection_count >= 15 OR flight_count >= 40
- Estimated: 50-75 entities
- Priority: Immediate

# Tier 2: Medium-value entities (Batch 2)
- connection_count >= 10 OR flight_count >= 20
- Estimated: 100-150 entities
- Priority: Within 24 hours

# Tier 3: Lower-value entities (Batch 3)
- connection_count >= 5 OR flight_count >= 10
- Estimated: 200-300 entities
- Priority: Within 72 hours

# Tier 4: Long tail (Deferred to Phase 2)
- Remaining entities (black book only, minimal connections)
- Process via web enrichment queue as needed
```

**Execution Plan**:
```bash
# Test with dry run
python3 scripts/analysis/generate_entity_bios_grok.py \
  --dry-run \
  --limit 10

# Tier 1: High-value entities
python3 scripts/analysis/generate_entity_bios_grok.py \
  --api-key "$OPENROUTER_API_KEY" \
  --min-connections 15 \
  --limit 75 \
  --output data/metadata/entity_biographies_grok_tier1.json

# Tier 2: Medium-value entities
python3 scripts/analysis/generate_entity_bios_grok.py \
  --api-key "$OPENROUTER_API_KEY" \
  --min-connections 10 \
  --limit 150 \
  --output data/metadata/entity_biographies_grok_tier2.json

# Tier 3: Lower-value entities
python3 scripts/analysis/generate_entity_bios_grok.py \
  --api-key "$OPENROUTER_API_KEY" \
  --min-connections 5 \
  --limit 300 \
  --output data/metadata/entity_biographies_grok_tier3.json
```

### 2.5 Quality Control & Validation

**Automated Validation**:
```python
def validate_biography(bio: str, entity_data: Dict) -> Dict:
    """Validate generated biography quality"""

    issues = []
    warnings = []

    # Length check
    word_count = len(bio.split())
    if word_count < 100:
        issues.append(f"Too short: {word_count} words (min 100)")
    elif word_count > 400:
        warnings.append(f"Long biography: {word_count} words")

    # Entity name check
    entity_name = entity_data["name"]
    if entity_name.lower() not in bio.lower():
        issues.append(f"Entity name '{entity_name}' not found in biography")

    # Epstein mention check
    if "epstein" not in bio.lower():
        warnings.append("No mention of Epstein relationship")

    # Speculation detection
    speculation_keywords = ["allegedly", "supposedly", "rumored", "believed to be", "may have"]
    speculation_count = sum(1 for kw in speculation_keywords if kw in bio.lower())
    if speculation_count > 3:
        warnings.append(f"High speculation count: {speculation_count} instances")

    # Vague language detection
    vague_terms = ["appears to", "seems to", "possibly", "might have"]
    vague_count = sum(1 for term in vague_terms if term in bio.lower())
    if vague_count > 2:
        warnings.append(f"Vague language detected: {vague_count} instances")

    # Fact density check
    has_dates = bool(re.search(r'\b(19|20)\d{2}\b', bio))
    has_numbers = bool(re.search(r'\b\d+\b', bio))

    if not (has_dates or has_numbers):
        warnings.append("Low fact density: no dates or statistics")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "quality_score": 1.0 - (len(issues) * 0.2 + len(warnings) * 0.05)
    }
```

**Human Review Workflow**:
1. Automated validation flags issues
2. Sample review of 10% of generated bios
3. Manual verification of Tier 1 entities (high-value)
4. Corrections fed back into prompt engineering

### 2.6 Cost Analysis (Phase 1)

**FREE TIER** (until December 3, 2025):
- ✅ Input tokens: FREE
- ✅ Output tokens: FREE
- ✅ Tool calls: FREE
- ✅ Total cost: $0.00

**Post-December 3 Pricing** (for reference):
```
Assumptions:
- 200 entities
- Average context: 1,500 tokens/entity
- Average output: 300 tokens/entity

Input tokens: 200 * 1,500 = 300,000 tokens
Output tokens: 200 * 300 = 60,000 tokens

Costs:
- Input: 300,000 / 1,000,000 * $0.20 = $0.06
- Output: 60,000 / 1,000,000 * $0.50 = $0.03
Total: $0.09

For 1,000 entities: ~$0.45
For all 1,620 entities: ~$0.73
```

**Recommendation**: Execute Phase 1 BEFORE December 3, 2025 to maximize free tier benefit.

### 2.7 Performance Projections

**Throughput Estimates**:
```
API latency: ~2-4 seconds per request
Rate limiting delay: 1 second between requests
Total time per entity: ~3-5 seconds

Batch sizes:
- 50 entities: 2.5-4 minutes
- 100 entities: 5-8 minutes
- 200 entities: 10-17 minutes
- 500 entities: 25-42 minutes

Realistic daily throughput:
- Conservative (with breaks): 400-500 entities/day
- Aggressive (continuous): 800-1,000 entities/day

Phase 1 completion timeline:
- Tier 1 (75 entities): 4-6 minutes
- Tier 2 (150 entities): 8-13 minutes
- Tier 3 (300 entities): 15-25 minutes
- Total: ~30-45 minutes for 525 entities
```

---

## 3. Phase 2: Web Enrichment Queue System

### 3.1 Architecture Overview

**Queue-Based Processing**:
```
┌─────────────────────────────────────────────────────────────┐
│                    Enrichment Queue                         │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │ Entity 1 │ -> │ Entity 2 │ -> │ Entity 3 │ -> ...      │
│  └──────────┘    └──────────┘    └──────────┘             │
│      │                │                │                    │
│      v                v                v                    │
│  ┌─────────────────────────────────────────────────┐      │
│  │         Source Priority Manager                  │      │
│  │  1. Wikipedia API                                │      │
│  │  2. Wikidata SPARQL                             │      │
│  │  3. News API (existing news_articles_index)      │      │
│  │  4. Court records (PACER/CourtListener)          │      │
│  │  5. Public databases (companies house, etc)      │      │
│  └─────────────────────────────────────────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────────┐
│                  Enrichment Processor                        │
│                                                             │
│  1. Query web sources                                       │
│  2. Extract biographical data                                │
│  3. Verify and deduplicate                                  │
│  4. Merge with existing biography                           │
│  5. Update classifications                                  │
│  6. Store results                                           │
└─────────────────────────────────────────────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────────┐
│                   Data Storage                              │
│                                                             │
│  - entity_biographies.json (merged bios)                    │
│  - entity_tags.json (classifications)                       │
│  - entity_enrichment_log.json (audit trail)                 │
│  - entity_enrichment_cache.json (source data cache)         │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Queue Management System

**Database Schema** (SQLite for simplicity):
```sql
CREATE TABLE enrichment_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL UNIQUE,
    entity_name TEXT NOT NULL,
    priority INTEGER DEFAULT 0,  -- Higher = more important
    status TEXT DEFAULT 'pending',  -- pending, processing, completed, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_attempt_at TIMESTAMP,
    attempt_count INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSON
);

CREATE TABLE enrichment_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    source TEXT NOT NULL,  -- wikipedia, wikidata, news, court_records
    data_type TEXT,  -- biography, occupation, relationship, event
    content TEXT,
    confidence_score REAL,
    source_url TEXT,
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (entity_id) REFERENCES enrichment_queue(entity_id)
);

CREATE TABLE enrichment_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL,
    action TEXT,  -- queued, started, completed, failed, updated
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details JSON
);

CREATE INDEX idx_queue_status ON enrichment_queue(status);
CREATE INDEX idx_queue_priority ON enrichment_queue(priority DESC);
CREATE INDEX idx_results_entity ON enrichment_results(entity_id);
CREATE INDEX idx_results_source ON enrichment_results(source);
```

**Priority Scoring**:
```python
def calculate_enrichment_priority(entity_data: Dict) -> int:
    """Calculate priority for enrichment queue"""
    score = 0

    # Connection count (0-100 points)
    score += min(entity_data.get("connection_count", 0) * 2, 100)

    # Flight count (0-50 points)
    score += min(entity_data.get("flight_count", 0), 50)

    # Multiple sources bonus (20 points)
    if len(entity_data.get("sources", [])) > 1:
        score += 20

    # Black book listing (10 points)
    if entity_data.get("in_black_book"):
        score += 10

    # Billionaire flag (15 points - high-value target)
    if entity_data.get("is_billionaire"):
        score += 15

    # Existing biography penalty (-50 points, but still queue for enrichment)
    if entity_data.get("has_biography"):
        score -= 50

    # Boost for entities with document mentions
    score += min(entity_data.get("total_documents", 0) * 3, 30)

    return score
```

### 3.3 Web Source Integrations

#### 3.3.1 Wikipedia API

**API Endpoint**: `https://en.wikipedia.org/w/api.php`

**Implementation**:
```python
import requests
from typing import Optional, Dict

class WikipediaEnricher:
    """Enrich entities using Wikipedia API"""

    API_ENDPOINT = "https://en.wikipedia.org/w/api.php"

    def __init__(self, user_agent: str = "EpsteinArchive/1.0"):
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def search_entity(self, entity_name: str) -> Optional[str]:
        """Search for entity page title"""
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": entity_name,
            "srlimit": 5
        }

        response = self.session.get(self.API_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()

        results = data.get("query", {}).get("search", [])
        if results:
            return results[0]["title"]  # Best match
        return None

    def get_page_summary(self, page_title: str) -> Dict:
        """Get page summary and extract"""
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts|pageimages|info",
            "exintro": True,  # Intro section only
            "explaintext": True,  # Plain text
            "titles": page_title,
            "inprop": "url"
        }

        response = self.session.get(self.API_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()

        pages = data.get("query", {}).get("pages", {})
        page_data = next(iter(pages.values()))

        return {
            "title": page_data.get("title"),
            "extract": page_data.get("extract", ""),
            "url": page_data.get("fullurl"),
            "pageid": page_data.get("pageid")
        }

    def enrich_entity(self, entity_name: str) -> Optional[Dict]:
        """Full enrichment workflow"""
        try:
            # Search for page
            page_title = self.search_entity(entity_name)
            if not page_title:
                return None

            # Get summary
            summary = self.get_page_summary(page_title)

            return {
                "source": "wikipedia",
                "entity_name": entity_name,
                "page_title": page_title,
                "summary": summary["extract"],
                "url": summary["url"],
                "retrieved_at": datetime.utcnow().isoformat() + "Z",
                "confidence": self._calculate_match_confidence(entity_name, page_title)
            }

        except Exception as e:
            return {
                "source": "wikipedia",
                "entity_name": entity_name,
                "error": str(e),
                "success": False
            }

        finally:
            # Rate limiting: Wikipedia allows 200 req/sec, but be conservative
            time.sleep(0.1)

    def _calculate_match_confidence(self, query: str, result: str) -> float:
        """Calculate confidence that result matches query"""
        query_lower = query.lower()
        result_lower = result.lower()

        # Exact match
        if query_lower == result_lower:
            return 1.0

        # Query is substring of result
        if query_lower in result_lower:
            return 0.9

        # Result is substring of query
        if result_lower in query_lower:
            return 0.85

        # Calculate Jaccard similarity on words
        query_words = set(query_lower.split())
        result_words = set(result_lower.split())

        intersection = query_words & result_words
        union = query_words | result_words

        if not union:
            return 0.0

        jaccard = len(intersection) / len(union)
        return max(0.5, jaccard)  # Minimum 0.5 if we got a result
```

**Rate Limits**: 200 requests/second (be conservative: 10 req/sec)

#### 3.3.2 Wikidata SPARQL

**Endpoint**: `https://query.wikidata.org/sparql`

**Implementation**:
```python
from SPARQLWrapper import SPARQLWrapper, JSON

class WikidataEnricher:
    """Enrich entities using Wikidata SPARQL queries"""

    ENDPOINT = "https://query.wikidata.org/sparql"

    def __init__(self):
        self.sparql = SPARQLWrapper(self.ENDPOINT)
        self.sparql.setReturnFormat(JSON)

    def query_person(self, person_name: str) -> Dict:
        """Query Wikidata for person information"""

        query = f"""
        SELECT ?person ?personLabel ?birthDate ?deathDate ?occupation ?occupationLabel
               ?nationality ?nationalityLabel ?description
        WHERE {{
          ?person rdfs:label "{person_name}"@en .
          ?person wdt:P31 wd:Q5 .  # instance of human

          OPTIONAL {{ ?person wdt:P569 ?birthDate . }}
          OPTIONAL {{ ?person wdt:P570 ?deathDate . }}
          OPTIONAL {{ ?person wdt:P106 ?occupation . }}
          OPTIONAL {{ ?person wdt:P27 ?nationality . }}
          OPTIONAL {{ ?person schema:description ?description FILTER (LANG(?description) = "en") . }}

          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 5
        """

        self.sparql.setQuery(query)

        try:
            results = self.sparql.query().convert()
            return self._parse_results(results)
        except Exception as e:
            return {"error": str(e), "success": False}
        finally:
            time.sleep(0.5)  # Rate limiting

    def _parse_results(self, results: Dict) -> Dict:
        """Parse SPARQL results"""
        bindings = results.get("results", {}).get("bindings", [])

        if not bindings:
            return {"success": False, "message": "No results found"}

        # Take first result
        person = bindings[0]

        return {
            "source": "wikidata",
            "wikidata_id": person.get("person", {}).get("value", "").split("/")[-1],
            "name": person.get("personLabel", {}).get("value"),
            "description": person.get("description", {}).get("value"),
            "birth_date": person.get("birthDate", {}).get("value"),
            "death_date": person.get("deathDate", {}).get("value"),
            "occupation": person.get("occupationLabel", {}).get("value"),
            "nationality": person.get("nationalityLabel", {}).get("value"),
            "success": True
        }
```

**Rate Limits**: 60 requests/minute (conservative)

#### 3.3.3 News Archive Integration

**Existing Resource**: `data/metadata/news_articles_index.json`

**Implementation**:
```python
class NewsArchiveEnricher:
    """Enrich entities using existing news archive"""

    def __init__(self, news_index_path: Path):
        with open(news_index_path) as f:
            self.news_index = json.load(f)

    def find_entity_mentions(self, entity_name: str) -> List[Dict]:
        """Find news articles mentioning entity"""
        mentions = []

        for article in self.news_index:
            # Search in title, description, content
            searchable_text = " ".join([
                article.get("title", ""),
                article.get("description", ""),
                article.get("content", "")
            ]).lower()

            if entity_name.lower() in searchable_text:
                mentions.append({
                    "title": article.get("title"),
                    "url": article.get("url"),
                    "published_date": article.get("published_at"),
                    "source": article.get("source", {}).get("name"),
                    "description": article.get("description", "")[:200]
                })

        return mentions

    def enrich_entity(self, entity_name: str) -> Dict:
        """Enrich entity with news mentions"""
        mentions = self.find_entity_mentions(entity_name)

        return {
            "source": "news_archive",
            "entity_name": entity_name,
            "mention_count": len(mentions),
            "mentions": mentions[:10],  # Top 10
            "success": True
        }
```

#### 3.3.4 Public Records APIs

**Court Records** (PACER/CourtListener):
```python
class CourtRecordsEnricher:
    """Enrich entities using court records"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.courtlistener.com/api/rest/v3"

    def search_dockets(self, entity_name: str) -> List[Dict]:
        """Search for dockets mentioning entity"""
        headers = {"Authorization": f"Token {self.api_key}"}

        params = {
            "q": entity_name,
            "type": "r",  # Dockets
            "order_by": "dateFiled desc"
        }

        response = requests.get(
            f"{self.base_url}/search/",
            headers=headers,
            params=params
        )
        response.raise_for_status()

        return response.json().get("results", [])
```

**Companies House** (UK):
```python
class CompaniesHouseEnricher:
    """Enrich entities using UK Companies House"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.company-information.service.gov.uk"

    def search_officers(self, name: str) -> List[Dict]:
        """Search for company officers"""
        auth = (self.api_key, "")

        response = requests.get(
            f"{self.base_url}/search/officers",
            auth=auth,
            params={"q": name}
        )
        response.raise_for_status()

        return response.json().get("items", [])
```

### 3.4 Queue Processing Implementation

**Main Queue Processor**:
```python
#!/usr/bin/env python3
"""
Entity Enrichment Queue Processor

Continuously processes entity enrichment queue, querying web sources
and updating entity data.
"""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from wikipedia_enricher import WikipediaEnricher
from wikidata_enricher import WikidataEnricher
from news_enricher import NewsArchiveEnricher


class EnrichmentQueueProcessor:
    """Process entity enrichment queue"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

        # Initialize enrichers
        self.wikipedia = WikipediaEnricher()
        self.wikidata = WikidataEnricher()
        self.news = NewsArchiveEnricher(
            news_index_path=Path("data/metadata/news_articles_index.json")
        )

        self.stats = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0
        }

    def initialize_queue(self, entities: List[Dict]):
        """Initialize queue with entities"""
        cursor = self.conn.cursor()

        for entity in entities:
            priority = self._calculate_priority(entity)

            cursor.execute("""
                INSERT OR IGNORE INTO enrichment_queue
                (entity_id, entity_name, priority, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                entity["id"],
                entity["name"],
                priority,
                json.dumps(entity)
            ))

        self.conn.commit()
        print(f"Initialized queue with {len(entities)} entities")

    def _calculate_priority(self, entity: Dict) -> int:
        """Calculate enrichment priority"""
        score = 0
        score += min(entity.get("connection_count", 0) * 2, 100)
        score += min(entity.get("flight_count", 0), 50)

        if len(entity.get("sources", [])) > 1:
            score += 20
        if entity.get("in_black_book"):
            score += 10
        if entity.get("is_billionaire"):
            score += 15

        return score

    def get_next_batch(self, batch_size: int = 10) -> List[Dict]:
        """Get next batch of entities to process"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM enrichment_queue
            WHERE status = 'pending'
            ORDER BY priority DESC, created_at ASC
            LIMIT ?
        """, (batch_size,))

        return [dict(row) for row in cursor.fetchall()]

    def process_entity(self, entity: Dict) -> Dict:
        """Process single entity through enrichment pipeline"""

        entity_id = entity["entity_id"]
        entity_name = entity["entity_name"]

        print(f"\nProcessing: {entity_name} (priority: {entity['priority']})")

        # Update status to processing
        self._update_status(entity_id, "processing")

        results = []

        try:
            # 1. Wikipedia
            print("  Querying Wikipedia...")
            wiki_data = self.wikipedia.enrich_entity(entity_name)
            if wiki_data and wiki_data.get("success", True):
                results.append(wiki_data)
                self._store_result(entity_id, wiki_data)
                print(f"    ✓ Found: {wiki_data.get('page_title', 'N/A')}")
            else:
                print("    ✗ Not found")

            # 2. Wikidata
            print("  Querying Wikidata...")
            wikidata_result = self.wikidata.query_person(entity_name)
            if wikidata_result.get("success"):
                results.append(wikidata_result)
                self._store_result(entity_id, wikidata_result)
                print(f"    ✓ Found: {wikidata_result.get('description', 'N/A')}")
            else:
                print("    ✗ Not found")

            # 3. News archive
            print("  Searching news archive...")
            news_data = self.news.enrich_entity(entity_name)
            if news_data.get("mention_count", 0) > 0:
                results.append(news_data)
                self._store_result(entity_id, news_data)
                print(f"    ✓ {news_data['mention_count']} mentions found")
            else:
                print("    ✗ No mentions")

            # Mark as completed
            self._update_status(entity_id, "completed")
            self.stats["successful"] += 1

            return {
                "entity_id": entity_id,
                "entity_name": entity_name,
                "results": results,
                "success": True
            }

        except Exception as e:
            print(f"  ✗ Error: {e}")
            self._update_status(entity_id, "failed", error_message=str(e))
            self.stats["failed"] += 1

            return {
                "entity_id": entity_id,
                "entity_name": entity_name,
                "error": str(e),
                "success": False
            }

        finally:
            self.stats["processed"] += 1

    def _update_status(
        self,
        entity_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update entity queue status"""
        cursor = self.conn.cursor()

        cursor.execute("""
            UPDATE enrichment_queue
            SET status = ?,
                updated_at = CURRENT_TIMESTAMP,
                last_attempt_at = CURRENT_TIMESTAMP,
                attempt_count = attempt_count + 1,
                error_message = ?
            WHERE entity_id = ?
        """, (status, error_message, entity_id))

        self.conn.commit()

        # Log action
        cursor.execute("""
            INSERT INTO enrichment_log (entity_id, action, details)
            VALUES (?, ?, ?)
        """, (
            entity_id,
            status,
            json.dumps({"error": error_message} if error_message else {})
        ))

        self.conn.commit()

    def _store_result(self, entity_id: str, result_data: Dict):
        """Store enrichment result"""
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO enrichment_results
            (entity_id, source, data_type, content, confidence_score, source_url, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entity_id,
            result_data.get("source"),
            "biography",  # Default type
            json.dumps(result_data),
            result_data.get("confidence", 0.8),
            result_data.get("url"),
            json.dumps(result_data)
        ))

        self.conn.commit()

    def run_continuous(self, batch_size: int = 10, delay: int = 60):
        """Run continuous processing"""
        print("Starting continuous enrichment processor...")
        print(f"Batch size: {batch_size}")
        print(f"Delay between batches: {delay}s\n")

        while True:
            batch = self.get_next_batch(batch_size)

            if not batch:
                print("\nQueue empty. Waiting for new entities...")
                time.sleep(delay)
                continue

            print(f"\n{'='*70}")
            print(f"Processing batch of {len(batch)} entities")
            print(f"{'='*70}")

            for entity in batch:
                self.process_entity(entity)
                time.sleep(2)  # Delay between entities

            print(f"\nBatch complete. Waiting {delay}s before next batch...")
            print(f"Stats: {self.stats}")
            time.sleep(delay)

    def run_once(self, limit: int = 100):
        """Run single batch processing"""
        batch = self.get_next_batch(limit)

        print(f"Processing {len(batch)} entities")

        for entity in batch:
            self.process_entity(entity)
            time.sleep(2)

        print(f"\nProcessing complete!")
        print(f"Stats: {self.stats}")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Entity enrichment queue processor")
    parser.add_argument("--init", action="store_true", help="Initialize queue")
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    parser.add_argument("--limit", type=int, default=100, help="Batch limit")
    parser.add_argument("--db", default="data/enrichment_queue.db")

    args = parser.parse_args()

    processor = EnrichmentQueueProcessor(db_path=Path(args.db))

    if args.init:
        # Load entities and initialize queue
        with open("data/metadata/entity_statistics.json") as f:
            data = json.load(f)

        entities = [
            {**entity_data, "id": entity_id}
            for entity_id, entity_data in data["statistics"].items()
        ]

        processor.initialize_queue(entities)

    if args.continuous:
        processor.run_continuous(batch_size=10, delay=60)
    else:
        processor.run_once(limit=args.limit)


if __name__ == "__main__":
    main()
```

### 3.5 Deduplication & Verification

**Strategy**:
```python
class EnrichmentMerger:
    """Merge and deduplicate enrichment data"""

    def merge_sources(self, grok_bio: str, web_enrichments: List[Dict]) -> Dict:
        """Merge Grok-generated bio with web enrichments"""

        # Start with Grok bio as base
        merged_bio = grok_bio

        # Extract facts from web sources
        facts = self._extract_facts(web_enrichments)

        # Identify gaps in Grok bio
        gaps = self._identify_gaps(grok_bio, facts)

        # Append new information
        if gaps:
            additions = self._format_additions(gaps)
            merged_bio = f"{grok_bio} {additions}"

        return {
            "biography": merged_bio,
            "sources": self._compile_sources(grok_bio, web_enrichments),
            "confidence_score": self._calculate_confidence(facts),
            "fact_count": len(facts)
        }

    def _extract_facts(self, enrichments: List[Dict]) -> List[Dict]:
        """Extract structured facts from enrichments"""
        facts = []

        for enrichment in enrichments:
            source = enrichment.get("source")

            if source == "wikipedia":
                # Extract key facts from Wikipedia summary
                summary = enrichment.get("summary", "")
                facts.extend(self._parse_wikipedia_facts(summary))

            elif source == "wikidata":
                # Structured data from Wikidata
                facts.append({
                    "type": "occupation",
                    "value": enrichment.get("occupation"),
                    "source": "wikidata",
                    "confidence": 0.95
                })

                if enrichment.get("birth_date"):
                    facts.append({
                        "type": "birth_date",
                        "value": enrichment.get("birth_date"),
                        "source": "wikidata",
                        "confidence": 0.99
                    })

            elif source == "news_archive":
                # News mentions provide context
                facts.append({
                    "type": "media_coverage",
                    "value": f"{enrichment.get('mention_count')} news mentions",
                    "source": "news_archive",
                    "confidence": 1.0
                })

        return facts

    def _identify_gaps(self, bio: str, facts: List[Dict]) -> List[Dict]:
        """Identify facts not present in biography"""
        gaps = []

        bio_lower = bio.lower()

        for fact in facts:
            # Check if fact is already in bio
            value_str = str(fact.get("value", "")).lower()

            if value_str and value_str not in bio_lower:
                gaps.append(fact)

        return gaps

    def _format_additions(self, gaps: List[Dict]) -> str:
        """Format gap facts as addition to bio"""
        additions = []

        # Group by type
        by_type = {}
        for gap in gaps:
            fact_type = gap.get("type")
            if fact_type not in by_type:
                by_type[fact_type] = []
            by_type[fact_type].append(gap)

        # Format each type
        if "occupation" in by_type:
            occupations = [f.get("value") for f in by_type["occupation"] if f.get("value")]
            if occupations:
                additions.append(f"Occupation: {', '.join(occupations)}.")

        if "birth_date" in by_type:
            birth_date = by_type["birth_date"][0].get("value")
            if birth_date:
                additions.append(f"Born {birth_date}.")

        return " ".join(additions)
```

### 3.6 Update Scheduling

**Cron Schedule**:
```bash
# Daily queue processing
0 2 * * * python3 /path/to/enrichment_queue_processor.py --limit 100

# Weekly full refresh of high-priority entities
0 3 * * 0 python3 /path/to/refresh_priority_entities.py

# Monthly full queue processing
0 4 1 * * python3 /path/to/enrichment_queue_processor.py --continuous --limit 500
```

---

## 4. Classification Taxonomy System

### 4.1 Classification Categories

**Primary Categories**:
```json
{
  "role_categories": [
    "core_network",      // Epstein, Maxwell, inner circle
    "associate",         // Close associates, frequent contact
    "professional",      // Pilots, staff, employees
    "business_contact",  // Business relationships
    "political_figure",  // Politicians, government officials
    "celebrity",         // Public figures, entertainers
    "academic",          // Scientists, professors
    "legal",            // Lawyers, judges
    "financial",        // Bankers, investors, financiers
    "victim",           // Confirmed or alleged victims
    "witness",          // Court witnesses
    "unknown"           // Insufficient information
  ],

  "relationship_types": [
    "employee",
    "business_partner",
    "romantic_partner",
    "family_member",
    "legal_representative",
    "political_ally",
    "social_contact",
    "professional_service_provider",
    "co_conspirator",
    "accuser",
    "defendant"
  ],

  "time_periods": [
    "1970s",
    "1980s",
    "1990s",
    "2000s",
    "2010s",
    "unknown"
  ],

  "geographic_locations": [
    "new_york",
    "palm_beach",
    "new_mexico",
    "us_virgin_islands",
    "paris",
    "london",
    "other_international",
    "unknown"
  ],

  "legal_status": [
    "convicted",
    "charged",
    "alleged_victim",
    "witness",
    "granted_immunity",
    "never_charged",
    "deceased"
  ],

  "prominence_level": [
    "high_profile",      // Public figures, politicians, billionaires
    "medium_profile",    // Known professionals, local figures
    "low_profile",       // Private individuals
    "anonymous"          // Redacted or unnamed
  ]
}
```

### 4.2 Automated Classification Extraction

**NLP-Based Classification**:
```python
import re
from typing import List, Dict

class BiographyClassifier:
    """Extract classifications from biography text"""

    # Keywords for role detection
    ROLE_KEYWORDS = {
        "core_network": ["inner circle", "close associate", "key figure", "primary"],
        "professional": ["pilot", "assistant", "employee", "staff", "worked for"],
        "business_contact": ["business", "investor", "financier", "client"],
        "political_figure": ["president", "governor", "senator", "politician"],
        "celebrity": ["actor", "actress", "model", "entertainer"],
        "academic": ["professor", "researcher", "scientist", "academic"],
        "legal": ["lawyer", "attorney", "judge", "counsel"],
        "financial": ["banker", "hedge fund", "investor", "financier"]
    }

    # Relationship indicators
    RELATIONSHIP_KEYWORDS = {
        "employee": ["assistant", "employee", "worked for", "employed by"],
        "business_partner": ["partner", "co-founder", "business partner"],
        "romantic_partner": ["girlfriend", "boyfriend", "romantic", "dated"],
        "family_member": ["daughter", "son", "wife", "husband", "sibling"],
        "legal_representative": ["lawyer", "attorney", "represented"],
        "co_conspirator": ["accomplice", "co-conspirator", "alleged facilitator"]
    }

    # Time period detection
    DECADE_PATTERN = r'\b(19|20)\d{2}s?\b'

    # Location detection
    LOCATION_KEYWORDS = {
        "new_york": ["new york", "manhattan", "ny"],
        "palm_beach": ["palm beach", "florida"],
        "new_mexico": ["new mexico", "santa fe"],
        "us_virgin_islands": ["virgin islands", "little saint james", "island"],
        "paris": ["paris", "france"],
        "london": ["london", "england", "uk"]
    }

    def classify_biography(self, bio: str, entity_data: Dict) -> Dict:
        """Extract classifications from biography"""

        bio_lower = bio.lower()

        classifications = {
            "roles": [],
            "relationships": [],
            "time_periods": [],
            "locations": [],
            "legal_status": [],
            "prominence_level": self._classify_prominence(entity_data)
        }

        # Extract roles
        for role, keywords in self.ROLE_KEYWORDS.items():
            if any(kw in bio_lower for kw in keywords):
                classifications["roles"].append(role)

        # Extract relationships
        for rel_type, keywords in self.RELATIONSHIP_KEYWORDS.items():
            if any(kw in bio_lower for kw in keywords):
                classifications["relationships"].append(rel_type)

        # Extract time periods
        decades = re.findall(self.DECADE_PATTERN, bio)
        for decade in decades:
            decade_str = f"{decade}s" if not decade.endswith('s') else decade
            classifications["time_periods"].append(decade_str)

        # Extract locations
        for location, keywords in self.LOCATION_KEYWORDS.items():
            if any(kw in bio_lower for kw in keywords):
                classifications["locations"].append(location)

        # Infer legal status
        classifications["legal_status"] = self._infer_legal_status(bio_lower, entity_data)

        # Deduplicate
        for key in classifications:
            if isinstance(classifications[key], list):
                classifications[key] = list(set(classifications[key]))

        return classifications

    def _classify_prominence(self, entity_data: Dict) -> str:
        """Classify entity prominence level"""

        # Billionaire flag
        if entity_data.get("is_billionaire"):
            return "high_profile"

        # High connection count or flight count
        if entity_data.get("connection_count", 0) > 30:
            return "high_profile"
        if entity_data.get("flight_count", 0) > 50:
            return "high_profile"

        # Medium connections
        if entity_data.get("connection_count", 0) > 10:
            return "medium_profile"
        if entity_data.get("flight_count", 0) > 20:
            return "medium_profile"

        # Low profile
        if entity_data.get("connection_count", 0) > 0:
            return "low_profile"

        # Anonymous (black book only)
        return "low_profile"

    def _infer_legal_status(self, bio_lower: str, entity_data: Dict) -> List[str]:
        """Infer legal status from biography"""
        statuses = []

        if "convicted" in bio_lower:
            statuses.append("convicted")
        elif "charged" in bio_lower:
            statuses.append("charged")

        if "immunity" in bio_lower or "granted immunity" in bio_lower:
            statuses.append("granted_immunity")

        if "alleged victim" in bio_lower or "accuser" in bio_lower:
            statuses.append("alleged_victim")

        if "witness" in bio_lower or "testified" in bio_lower:
            statuses.append("witness")

        if "never charged" in bio_lower or "no charges" in bio_lower:
            statuses.append("never_charged")

        if "died" in bio_lower or "deceased" in bio_lower:
            statuses.append("deceased")

        return statuses if statuses else ["unknown"]
```

### 4.3 Entity Tags Integration

**Update entity_tags.json**:
```python
def update_entity_tags(entity_id: str, classifications: Dict):
    """Update entity_tags.json with new classifications"""

    tags_file = Path("data/metadata/entity_tags.json")

    # Load existing tags
    with open(tags_file) as f:
        tags_data = json.load(f)

    # Find or create entity entry
    entity_tags = None
    for tag_entry in tags_data:
        if tag_entry["entity_name"] == entity_id:
            entity_tags = tag_entry
            break

    if entity_tags is None:
        entity_tags = {
            "entity_name": entity_id,
            "tags": [],
            "primary_tag": None
        }
        tags_data.append(entity_tags)

    # Compile tags from classifications
    new_tags = set(entity_tags.get("tags", []))

    for category, values in classifications.items():
        if isinstance(values, list):
            new_tags.update(values)
        else:
            new_tags.add(values)

    entity_tags["tags"] = sorted(list(new_tags))

    # Set primary tag (first role if available)
    if classifications.get("roles"):
        entity_tags["primary_tag"] = classifications["roles"][0]

    # Save
    with open(tags_file, "w") as f:
        json.dump(tags_data, f, indent=2)
```

---

## 5. Implementation Roadmap

### 5.1 Phase 1: Grok-4.1 Bio Generation (Days 1-3)

**Day 1: Setup & Testing**
- [ ] Create `scripts/analysis/generate_entity_bios_grok.py`
- [ ] Set up OpenRouter API key
- [ ] Test with 5-10 sample entities
- [ ] Validate output format
- [ ] Tune prompt engineering

**Day 2: Tier 1 & 2 Processing**
- [ ] Process Tier 1 entities (75 entities, ~6 minutes)
- [ ] Manual quality review of Tier 1 bios
- [ ] Process Tier 2 entities (150 entities, ~13 minutes)
- [ ] Checkpoint validation

**Day 3: Tier 3 & Integration**
- [ ] Process Tier 3 entities (300 entities, ~25 minutes)
- [ ] Merge with existing entity_biographies.json
- [ ] Run automated quality checks
- [ ] Generate statistics report

**Success Metrics**:
- ✅ 525+ entities with AI-generated bios
- ✅ 80%+ quality score on automated validation
- ✅ All processed before December 3 (free tier deadline)

### 5.2 Phase 2: Queue System Development (Days 4-7)

**Day 4: Database Setup**
- [ ] Create SQLite database schema
- [ ] Create `scripts/analysis/enrichment_queue_processor.py`
- [ ] Initialize queue with all entities
- [ ] Test priority scoring

**Day 5: Web Source Integration**
- [ ] Implement Wikipedia enricher
- [ ] Implement Wikidata enricher
- [ ] Implement news archive search
- [ ] Test each source independently

**Day 6: Queue Processing**
- [ ] Test batch processing (10-20 entities)
- [ ] Implement checkpointing
- [ ] Add error handling and retry logic
- [ ] Test continuous processing mode

**Day 7: Classification System**
- [ ] Implement biography classifier
- [ ] Test classification extraction
- [ ] Integrate with entity_tags.json
- [ ] Generate classification statistics

### 5.3 Phase 3: Integration & Deployment (Days 8-10)

**Day 8: Data Merging**
- [ ] Create enrichment merger
- [ ] Merge Grok bios with web enrichments
- [ ] Update entity_biographies.json
- [ ] Update entity_tags.json

**Day 9: Quality Assurance**
- [ ] Manual review of high-priority entities
- [ ] Validate classification accuracy
- [ ] Test deduplication logic
- [ ] Fix any data quality issues

**Day 10: Documentation & Deployment**
- [ ] Document enrichment process
- [ ] Create user guide
- [ ] Set up cron jobs
- [ ] Deploy to production

---

## 6. Cost Analysis

### 6.1 Phase 1 Costs (Grok-4.1)

**Current (Before December 3, 2025)**:
- FREE on OpenRouter
- Estimated total value: ~$0.73 (for all 1,620 entities)

**Post-December 3, 2025**:
```
Tier 1 (75 entities):
- Input: 75 * 1,500 = 112,500 tokens → $0.0225
- Output: 75 * 300 = 22,500 tokens → $0.0113
- Subtotal: $0.0338

Tier 2 (150 entities):
- Input: 150 * 1,500 = 225,000 tokens → $0.045
- Output: 150 * 300 = 45,000 tokens → $0.0225
- Subtotal: $0.0675

Tier 3 (300 entities):
- Input: 300 * 1,500 = 450,000 tokens → $0.09
- Output: 300 * 300 = 90,000 tokens → $0.045
- Subtotal: $0.135

Phase 1 Total: $0.24 (525 entities)
```

### 6.2 Phase 2 Costs (Web APIs)

**Wikipedia & Wikidata**: FREE

**News APIs** (if expanding beyond existing archive):
- NewsAPI.org: $449/month (business plan)
- Alternative: Use existing archive (FREE)

**Court Records**:
- PACER: $0.10/page (capped at $3/document)
- CourtListener API: FREE

**Companies House**: FREE

**Estimated Monthly Ongoing Cost**: $0-50 (depending on expansion)

---

## 7. Quality Metrics & KPIs

### 7.1 Coverage Metrics

```python
def calculate_coverage_metrics():
    """Calculate biography coverage KPIs"""

    # Load data
    stats = load_entity_statistics()
    bios = load_entity_biographies()

    total_entities = len(stats)
    entities_with_bios = len(bios)
    coverage_percent = (entities_with_bios / total_entities) * 100

    # Coverage by tier
    high_value = sum(1 for e in stats.values() if e['connection_count'] >= 15)
    high_value_with_bios = sum(
        1 for eid, e in stats.items()
        if e['connection_count'] >= 15 and eid in bios
    )
    high_value_coverage = (high_value_with_bios / high_value) * 100

    return {
        "total_entities": total_entities,
        "entities_with_bios": entities_with_bios,
        "coverage_percent": coverage_percent,
        "high_value_entities": high_value,
        "high_value_coverage_percent": high_value_coverage
    }
```

**Target KPIs**:
- Overall coverage: 60%+ (980+ entities)
- High-value entity coverage: 95%+ (top 200 by priority)
- Classification coverage: 80%+ (1,300+ entities tagged)
- Average biography length: 150-300 words
- Quality score: 0.75+ average

### 7.2 Quality Metrics

```python
def calculate_quality_metrics():
    """Calculate biography quality metrics"""

    bios = load_entity_biographies()

    metrics = {
        "avg_word_count": 0,
        "avg_fact_density": 0,
        "speculation_rate": 0,
        "source_attribution_rate": 0,
        "classification_coverage": 0
    }

    total = 0
    for bio_data in bios.values():
        bio = bio_data.get("biography", "")

        # Word count
        word_count = len(bio.split())
        metrics["avg_word_count"] += word_count

        # Fact density (dates + numbers)
        has_dates = bool(re.search(r'\b(19|20)\d{2}\b', bio))
        has_numbers = bool(re.search(r'\b\d+\b', bio))
        metrics["avg_fact_density"] += 1 if (has_dates and has_numbers) else 0.5 if (has_dates or has_numbers) else 0

        # Speculation check
        speculation_kw = ["allegedly", "supposedly", "rumored"]
        speculation = sum(1 for kw in speculation_kw if kw in bio.lower())
        metrics["speculation_rate"] += 1 if speculation > 2 else 0

        total += 1

    # Calculate averages
    for key in metrics:
        metrics[key] = metrics[key] / total if total > 0 else 0

    return metrics
```

---

## 8. Risk Mitigation

### 8.1 Privacy & Ethics

**Victim Protection**:
- Minimal biographical information for alleged victims
- Respect privacy of individuals not in public record
- Clear distinction between documented facts and allegations
- Compliance with GDPR/privacy regulations

**Fact Verification**:
- Minimum 2 sources per fact
- Clear attribution of sources
- Avoid speculation beyond documented evidence
- Regular review of potentially defamatory content

### 8.2 Technical Risks

**API Rate Limits**:
- Implement exponential backoff
- Queue-based processing to avoid bursts
- Cache API responses
- Fallback to manual processing if APIs fail

**Data Quality**:
- Automated validation checks
- Manual review of high-priority entities
- Versioning and rollback capability
- Regular data integrity audits

**System Failures**:
- Checkpoint every 10 entities
- Atomic database transactions
- Backup before major updates
- Graceful degradation if enrichment fails

---

## 9. Future Enhancements

### 9.1 Phase 3: Advanced Features (Optional)

**AI-Powered Summarization**:
- Use Grok-4.1 for court document summarization
- Extract key events and timeline
- Generate relationship summaries

**Sentiment Analysis**:
- Analyze news coverage sentiment
- Track media narrative evolution
- Identify controversial entities

**Network Analysis Integration**:
- Enrich biographies with network statistics
- Highlight key bridge entities
- Visualize temporal network evolution

**Multi-Language Support**:
- Translate biographies to Spanish, French
- Query non-English sources
- Expand international coverage

### 9.2 Maintenance Plan

**Weekly Tasks**:
- Process 100-200 entities from queue
- Review failed enrichments
- Update classifications as needed

**Monthly Tasks**:
- Refresh high-priority entity data
- Audit biography quality
- Expand web source coverage
- Generate progress reports

**Quarterly Tasks**:
- Review and update taxonomy
- Re-process entities with new information
- Performance optimization
- Security audit

---

## 10. Conclusion

This comprehensive entity biography enhancement system provides a scalable, cost-effective approach to enriching 1,637 entities with descriptive biographies and structured classifications.

**Key Advantages**:
✅ **FREE** Phase 1 execution (before Dec 3, 2025)
✅ Rapid processing: 525 entities in <1 hour
✅ Scalable queue system for ongoing enrichment
✅ Automated classification extraction
✅ Minimal ongoing costs (~$0-50/month)

**Implementation Priority**:
1. **IMMEDIATE**: Execute Phase 1 before December 3 (free tier deadline)
2. **Week 1-2**: Develop and deploy Phase 2 queue system
3. **Month 1**: Achieve 60%+ coverage across all entities
4. **Ongoing**: Continuous enrichment and quality improvement

**Success Metrics**:
- 980+ entities with biographies (60% coverage)
- 95%+ high-value entity coverage
- 80%+ classification coverage
- Average quality score: 0.75+

This system positions the Epstein Archive for comprehensive entity profiling while maintaining high ethical standards and cost efficiency.
