"""
Entity Service - Business logic for entity operations

Design Decision: Centralized Entity Management
Rationale: All entity-related business logic in one place for consistency,
testability, and easy modification. Frontend makes simple API calls.

Handles:
- Entity filtering and searching
- Type detection (person, business, location, organization)
- Biography and tag integration
- Connection graph queries

Pydantic Integration (Phase 1):
- Feature flag: USE_PYDANTIC environment variable
- Backward compatible: Falls back to dict if validation fails
- Dual storage: Both dict and Pydantic models during migration
- Performance: <20% overhead with validation enabled
"""

import json
import logging
import os
import re
import requests
import sys
from pathlib import Path
from typing import Literal, Optional, Union


# Import entity filtering utility
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts/utils"))
from entity_filtering import EntityFilter

# Import Pydantic models
from models import Entity, EntityBiography, EntityTag, NetworkEdge, NetworkGraph, NetworkNode
from pydantic import ValidationError


# Feature flags
USE_PYDANTIC = os.getenv("USE_PYDANTIC", "false").lower() == "true"
ENABLE_LLM_CLASSIFICATION = os.getenv("ENABLE_LLM_CLASSIFICATION", "true").lower() == "true"
ENABLE_NLP_CLASSIFICATION = os.getenv("ENABLE_NLP_CLASSIFICATION", "true").lower() == "true"

# Setup logging
logger = logging.getLogger(__name__)

# Type alias for entity classification
EntityType = Literal['person', 'organization', 'location']

# OpenRouter availability check (no import needed, just HTTP requests)
OPENROUTER_AVAILABLE = True  # requests library is always available

try:
    import spacy
    # Try to load spaCy model at module level (once)
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except:
    nlp = None
    SPACY_AVAILABLE = False
    logger.warning("spaCy model not available, NLP fallback disabled")


class EntityService:
    """Service for entity data operations

    Pydantic Integration:
    - USE_PYDANTIC=true: Validates and stores Pydantic models
    - USE_PYDANTIC=false: Uses raw dicts (default, backward compatible)
    - Dual storage during migration for graceful fallback
    """

    def __init__(self, data_path: Path):
        """Initialize entity service

        Args:
            data_path: Path to data directory containing metadata
        """
        self.data_path = data_path
        self.metadata_dir = data_path / "metadata"
        self.md_dir = data_path / "md"

        # Initialize entity filter
        self.entity_filter = EntityFilter()

        # Data caches (dict storage - always maintained)
        self.entity_stats: dict = {}  # ID -> Entity dict
        self.entity_bios: dict = {}
        self.entity_tags: dict = {}
        self.network_data: dict = {}
        self.semantic_index: dict = {}

        # Reverse mappings for backward compatibility
        self.name_to_id: dict[str, str] = {}  # Name/variation -> ID
        self.id_to_name: dict[str, str] = {}  # ID -> Primary name

        # Pydantic model storage (when USE_PYDANTIC=true)
        self.entities_pydantic: dict[str, Entity] = {}
        self.bios_pydantic: dict[str, EntityBiography] = {}
        self.tags_pydantic: dict[str, EntityTag] = {}
        self.network_graph: Optional[NetworkGraph] = None

        # Validation statistics
        self.validation_stats = {
            "total_entities": 0,
            "valid_entities": 0,
            "failed_entities": 0,
            "validation_errors": [],
        }

        # Load data
        self.load_data()

    def load_data(self):
        """Load all entity-related data from JSON files

        If USE_PYDANTIC=true, validates data with Pydantic models.
        Falls back to dict storage if validation fails.
        """
        # Load entity statistics
        stats_path = self.metadata_dir / "entity_statistics.json"
        if stats_path.exists():
            with open(stats_path) as f:
                data = json.load(f)
                self.entity_stats = data.get("statistics", {})

            # Build reverse mappings for name-based lookups
            self._build_name_mappings()

            # Validate with Pydantic if enabled
            if USE_PYDANTIC:
                self._validate_entities()

        # Load biographies from all three entity files
        entity_files = [
            ("entity_biographies.json", "person"),      # 1,637 persons from contact books
            ("entity_organizations.json", "organization"),  # ~920 orgs from documents
            ("entity_locations.json", "location")       # ~458 locations from documents
        ]

        self.entity_bios = {}
        total_loaded = 0
        entity_type_counts = {}

        for filename, entity_type in entity_files:
            file_path = self.metadata_dir / filename
            if file_path.exists():
                try:
                    with open(file_path) as f:
                        data = json.load(f)
                        entities = data.get("entities", {})

                        # Merge entities, ensuring entity_type is set
                        for entity_key, entity_data in entities.items():
                            # Ensure entity_type field exists
                            if "entity_type" not in entity_data:
                                entity_data["entity_type"] = entity_type

                            self.entity_bios[entity_key] = entity_data

                        logger.info(f"Loaded {len(entities)} entities from {filename}")
                        total_loaded += len(entities)
                        entity_type_counts[entity_type] = len(entities)
                except Exception as e:
                    logger.error(f"Error loading {filename}: {e}")
            else:
                logger.warning(f"Entity file not found: {filename}")

        logger.info(f"Total entities loaded: {total_loaded}")
        logger.info(f"Entity type distribution: {entity_type_counts}")
        logger.info(f"Sample biography keys: {list(self.entity_bios.keys())[:5]}")

        # Check organization/location keys across all entities
        all_orgs = [k for k, v in self.entity_bios.items() if v.get("entity_type") == "organization"]
        all_locs = [k for k, v in self.entity_bios.items() if v.get("entity_type") == "location"]
        logger.info(f"Organizations in entity_bios: {len(all_orgs)} (sample: {all_orgs[:3]})")
        logger.info(f"Locations in entity_bios: {len(all_locs)} (sample: {all_locs[:3]})")

        # Check if larry_morrison bio exists
        if "larry_morrison" in self.entity_bios:
            logger.info(f"larry_morrison biography loaded successfully")
            logger.debug(f"larry_morrison bio keys: {list(self.entity_bios['larry_morrison'].keys())}")
        else:
            logger.warning("larry_morrison biography NOT found in loaded data")

        # Validate with Pydantic if enabled
        if USE_PYDANTIC:
            self._validate_biographies()

        # Load tags
        tags_path = self.metadata_dir / "entity_tags.json"
        if tags_path.exists():
            with open(tags_path) as f:
                data = json.load(f)
                self.entity_tags = data.get("entities", {})

            # Validate with Pydantic if enabled
            if USE_PYDANTIC:
                self._validate_tags()

        # Load network
        network_path = self.metadata_dir / "entity_network.json"
        if network_path.exists():
            with open(network_path) as f:
                self.network_data = json.load(f)

            # Validate with Pydantic if enabled
            if USE_PYDANTIC:
                self._validate_network()

        # Load semantic index
        semantic_path = self.metadata_dir / "semantic_index.json"
        if semantic_path.exists():
            with open(semantic_path) as f:
                data = json.load(f)
                self.semantic_index = data.get("entity_to_documents", {})

        # Load news and timeline data for counts
        self._load_news_and_timeline()

        # Log validation results if Pydantic enabled
        if USE_PYDANTIC:
            logger.info(
                f"Pydantic validation complete: "
                f"{self.validation_stats['valid_entities']}/{self.validation_stats['total_entities']} "
                f"entities valid, {self.validation_stats['failed_entities']} failed"
            )

    def _load_news_and_timeline(self):
        """Load news articles and timeline for entity counting

        Design Decision: Lazy load and cache for performance
        Rationale: Load once at startup and cache counts to avoid repeated file I/O
        """
        # Load news articles index
        self.news_data = {}
        news_path = self.metadata_dir / "news_articles_index.json"
        if news_path.exists():
            try:
                with open(news_path) as f:
                    self.news_data = json.load(f)
                logger.info(f"Loaded {len(self.news_data.get('articles', []))} news articles")
            except Exception as e:
                logger.error(f"Failed to load news articles: {e}")

        # Load timeline data
        self.timeline_data = {}
        timeline_path = self.metadata_dir / "timeline.json"
        if timeline_path.exists():
            try:
                with open(timeline_path) as f:
                    self.timeline_data = json.load(f)
                logger.info(f"Loaded {len(self.timeline_data.get('events', []))} timeline events")
            except Exception as e:
                logger.error(f"Failed to load timeline: {e}")

    def get_entity_news_count(self, entity_name: str) -> int:
        """Count news articles mentioning an entity

        Args:
            entity_name: Entity name (in "LastName, FirstName" or "FirstName LastName" format)

        Returns:
            Count of news articles mentioning this entity
        """
        try:
            articles = self.news_data.get("articles", [])

            # Count articles mentioning this entity
            # News articles use "FirstName LastName" format, entity stats use "LastName, FirstName"
            count = 0
            entity_name_reversed = None
            if ", " in entity_name:
                # Convert "Epstein, Jeffrey" -> "Jeffrey Epstein"
                parts = entity_name.split(", ", 1)
                entity_name_reversed = f"{parts[1]} {parts[0]}"

            for article in articles:
                entities_mentioned = article.get("entities_mentioned", [])
                # Check both formats
                if entity_name in entities_mentioned or (entity_name_reversed and entity_name_reversed in entities_mentioned):
                    count += 1

            return count
        except Exception as e:
            logger.error(f"Error counting news for entity {entity_name}: {e}")
            return 0

    def get_entity_timeline_count(self, entity_name: str) -> int:
        """Count timeline events mentioning an entity

        Args:
            entity_name: Entity name (in "LastName, FirstName" or "FirstName LastName" format)

        Returns:
            Count of timeline events mentioning this entity
        """
        try:
            events = self.timeline_data.get("events", [])

            # Count events mentioning this entity
            # Timeline uses "FirstName LastName" format
            count = 0
            entity_name_reversed = None
            if ", " in entity_name:
                # Convert "Epstein, Jeffrey" -> "Jeffrey Epstein"
                parts = entity_name.split(", ", 1)
                entity_name_reversed = f"{parts[1]} {parts[0]}"

            for event in events:
                related_entities = event.get("related_entities", [])
                # Check both formats
                if entity_name in related_entities or (entity_name_reversed and entity_name_reversed in related_entities):
                    count += 1

            return count
        except Exception as e:
            logger.error(f"Error counting timeline events for entity {entity_name}: {e}")
            return 0

    def _build_name_mappings(self):
        """Build reverse mappings from names to entity IDs for backward compatibility

        Creates indexes:
        - name_to_id: Maps all name variations to entity ID
        - id_to_name: Maps entity ID to primary display name

        This enables O(1) lookups by name while using IDs internally.
        """
        for entity_id, entity_data in self.entity_stats.items():
            # Map ID to primary name
            primary_name = entity_data.get("name", "")
            self.id_to_name[entity_id] = primary_name

            # Map primary name to ID
            self.name_to_id[primary_name] = entity_id

            # Map all name variations to ID
            for variation in entity_data.get("name_variations", []):
                if variation and variation not in self.name_to_id:
                    self.name_to_id[variation] = entity_id

            # Also map normalized name if different
            normalized = entity_data.get("normalized_name")
            if normalized and normalized != primary_name and normalized not in self.name_to_id:
                self.name_to_id[normalized] = entity_id

    def _validate_entities(self):
        """Validate entity_stats with Pydantic Entity model"""
        self.validation_stats["total_entities"] = len(self.entity_stats)

        for name, entity_data in self.entity_stats.items():
            try:
                # Convert dict to Pydantic model
                entity = Entity(**entity_data)
                self.entities_pydantic[name] = entity
                self.validation_stats["valid_entities"] += 1

            except ValidationError as e:
                self.validation_stats["failed_entities"] += 1
                self.validation_stats["validation_errors"].append(
                    {"entity": name, "error": str(e), "error_count": e.error_count()}
                )
                logger.warning(f"Validation failed for entity '{name}': {e}")

                # Fallback: Keep dict version
                # Entity remains in self.entity_stats for backward compat

    def _validate_biographies(self):
        """Validate entity_bios with Pydantic EntityBiography model"""
        for entity_name, bio_data in self.entity_bios.items():
            try:
                # Prepare data for Pydantic model
                bio_dict = {
                    "entity_name": entity_name,
                    "biography": bio_data.get("biography", ""),
                    "last_updated": bio_data.get("last_updated"),
                }
                bio = EntityBiography(**bio_dict)
                self.bios_pydantic[entity_name] = bio

            except ValidationError as e:
                logger.warning(f"Validation failed for biography '{entity_name}': {e}")

    def _validate_tags(self):
        """Validate entity_tags with Pydantic EntityTag model"""
        for entity_name, tag_data in self.entity_tags.items():
            try:
                # Prepare data for Pydantic model
                tag_dict = {
                    "entity_name": entity_name,
                    "tags": tag_data.get("tags", []),
                    "primary_tag": tag_data.get("primary_tag"),
                }
                tags = EntityTag(**tag_dict)
                self.tags_pydantic[entity_name] = tags

            except ValidationError as e:
                logger.warning(f"Validation failed for tags '{entity_name}': {e}")

    def _validate_network(self):
        """Validate network_data with Pydantic NetworkGraph model"""
        try:
            # Extract nodes and edges
            nodes_data = self.network_data.get("nodes", [])
            edges_data = self.network_data.get("edges", [])

            # Convert to Pydantic models
            nodes = [NetworkNode(**node) for node in nodes_data]
            edges = [NetworkEdge(**edge) for edge in edges_data]

            # Create graph with validation
            self.network_graph = NetworkGraph(
                nodes=nodes, edges=edges, metadata=self.network_data.get("metadata")
            )
            logger.info(f"Network graph validated: {len(nodes)} nodes, {len(edges)} edges")

        except ValidationError as e:
            logger.error(f"Network graph validation failed: {e}")
            # Fallback: Keep dict version in self.network_data

    def _classify_entity_type_llm(self, name: str, context: Optional[dict] = None) -> Optional[EntityType]:
        """Classify entity type using Claude Haiku via OpenRouter (Tier 1: Primary Method).

        Uses Claude Haiku via OpenRouter for fast, cheap, and accurate classification.
        Cost: ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens (very cheap for this use case)

        CRITICAL FIX (Linear 1M-364): Prioritization rules corrected to prevent keyword override.
        Previous bug: LLM would classify "Trump Organization" as person because "Trump" looks
        like a person's name, overriding the "Organization" keyword. Fix enforces strict keyword
        precedence over name format patterns.

        Research: See docs/research/entity-type-classification-llm-prompt-bug-2025-11-28.md

        Args:
            name: Entity name (e.g., "Epstein, Jeffrey" or "Clinton Foundation")
            context: Optional context (bio, sources, etc.) to improve accuracy

        Returns:
            'person', 'organization', or 'location', or None if LLM unavailable/failed
        """
        # Check if LLM classification is enabled
        if not ENABLE_LLM_CLASSIFICATION:
            return None

        # Check for API key
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            logger.debug("OPENROUTER_API_KEY not set, skipping LLM classification")
            return None

        try:
            # Build reasoning-based prompt that uses LLM intelligence
            prompt = f"""You are classifying entities from Jeffrey Epstein's contact records.

Entity name: "{name}"
"""

            if context and context.get('bio'):
                # Include full biographical context for accurate reasoning
                bio_excerpt = context['bio'][:1000]  # Use more context
                prompt += f"""\nBiographical information:
{bio_excerpt}"""

            prompt += """

Task: Classify this entity as EXACTLY ONE of: person, organization, location

Classification Guidelines:

**PERSON** - An individual human being
  - Someone with a personal biography, career, relationships
  - Entries in contact books are typically people
  - Names with "Last, First" format are usually people
  - Titles like Dr., Mr., Ms., Prince indicate people
  - Examples: "Epstein, Jeffrey", "Maxwell, Ghislaine", "Ann Stock", "Anh Duong"

**ORGANIZATION** - A company, institution, agency, foundation
  - Only use if explicitly an organization (has "Inc", "LLC", "Foundation", "Company", etc.)
  - Examples: "FBI", "CIA", "Clinton Foundation", "Trump Organization", "Interfor Inc"

**LOCATION** - A geographic place or property
  - Only use if explicitly a place (has "Island", "Beach", "City", "Street", etc.)
  - Examples: "Little St. James Island", "Zorro Ranch", "Palm Beach", "New York"

CRITICAL INSTRUCTIONS:
1. READ THE BIOGRAPHICAL CONTEXT CAREFULLY - use the content to determine the entity type
2. Personal names (even single names like "Lang", "Ariane", "Michelle") are PEOPLE unless proven otherwise
3. Context entries in Jeffrey Epstein's contact book are almost always PEOPLE
4. Only classify as organization/location if there's EXPLICIT evidence (keywords like "Inc", "Foundation", "Island", "Beach")
5. When in doubt between person and location/organization, choose PERSON

Common Mistakes to Avoid:
- "Lang" → DO NOT classify as location just because it sounds like a place. It's a person's name (likely surname).
- "Michelle" → DO NOT classify as location. It's a person's name.
- "Anh Duong" → DO NOT classify as location. It's a Vietnamese person's name.
- "Ariane" → DO NOT classify as location. It's a French person's name.

Return ONLY one word: person, organization, or location"""

            # Call OpenRouter API
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "http://localhost:8081",  # Optional, for rankings
                    "X-Title": "Epstein Archive Entity Classification",  # Optional, for rankings
                },
                json={
                    "model": "anthropic/claude-3-haiku",  # OpenRouter model identifier
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 10,
                    "temperature": 0,  # Deterministic
                }
            )

            response.raise_for_status()
            data = response.json()

            result = data['choices'][0]['message']['content'].strip().lower()

            if result in ['person', 'organization', 'location']:
                logger.debug(f"LLM (OpenRouter) classified '{name}' as '{result}'")
                return result
            else:
                # Invalid response, fall back
                logger.warning(f"LLM returned invalid result for '{name}': {result}")
                return None

        except requests.exceptions.RequestException as e:
            logger.warning(f"OpenRouter API error for '{name}': {e}")
            return None
        except Exception as e:
            logger.warning(f"LLM classification failed for '{name}': {e}")
            return None

    def _classify_entity_type_nlp(self, name: str) -> Optional[EntityType]:
        """Classify using spaCy NER (Tier 2: NLP Fallback).

        Uses spaCy's named entity recognition to classify entities.
        More accurate than keyword matching, but less accurate than LLM.

        IMPORTANT: When multiple entity labels detected (e.g., "Maxwell" = ORG + "Ghislaine" = PERSON),
        prioritize PERSON label since names like "Trump", "Maxwell", "Boardman" are also company names.

        Args:
            name: Entity name

        Returns:
            'person', 'organization', or 'location', or None if uncertain
        """
        if not ENABLE_NLP_CLASSIFICATION or not SPACY_AVAILABLE or not nlp:
            return None

        try:
            doc = nlp(name)

            # Collect all entity labels
            labels = [ent.label_ for ent in doc.ents]

            if not labels:
                logger.debug(f"NLP found no entities in '{name}'")
                return None

            # Prioritize PERSON if present (handles "Maxwell, Ghislaine" where "Maxwell"=ORG, "Ghislaine"=PERSON)
            if "PERSON" in labels:
                logger.debug(f"NLP classified '{name}' as 'person' (PERSON found in {labels})")
                return 'person'

            # Then check for locations
            if any(label in ["GPE", "LOC", "FAC"] for label in labels):
                logger.debug(f"NLP classified '{name}' as 'location' (found in {labels})")
                return 'location'

            # Finally organizations
            if any(label in ["ORG", "NORP"] for label in labels):
                logger.debug(f"NLP classified '{name}' as 'organization' (found in {labels})")
                return 'organization'

            # Unknown entity type
            logger.debug(f"NLP found entities but couldn't classify '{name}': {labels}")
            return None

        except Exception as e:
            logger.warning(f"NLP classification failed for '{name}': {e}")
            return None

    def _normalize_entity_name_for_classification(self, name: str) -> str:
        """Normalize entity name before classification (P1 Fix).

        Removes possessives and prefixes that break classification.

        Examples:
            "Ghislaine Maxwell's" -> "Ghislaine Maxwell"
            "A. Ghislaine Maxwell" -> "Ghislaine Maxwell"

        Args:
            name: Raw entity name

        Returns:
            Normalized name for classification
        """
        # Remove possessive 's
        name = re.sub(r"'s\b", '', name)
        # Remove leading initials (single letter followed by period and space)
        name = re.sub(r"^[A-Z]\.\s+", "", name)
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        return name

    def _is_valid_entity(self, name: str) -> bool:
        """Validate that name represents a real entity, not jargon/codes (P0 Fix).

        Filters out:
        - Generic legal/procedural terms
        - System codes and alphanumeric gibberish
        - All-caps multi-word patterns (likely codes)
        - Billing/system identifiers

        Args:
            name: Entity name to validate

        Returns:
            True if valid entity, False if should be filtered
        """
        # Invalid entity patterns (codes, jargon)
        INVALID_ENTITY_PATTERNS = [
            r'^[A-Z]{2,}\s+[A-Z]{2,}$',  # All caps multi-word (e.g., "ET AL")
            r'^\w{1,2}\s*-\s*\d+$',      # Codes like "b3 -1"
            r'^[A-Z]{3,}[0-9]',          # Alphanumeric codes (e.g., "SSR SSR TKNEAFHK1")
            r'\d{4,}',                    # Long number sequences
        ]

        # Generic terms that aren't entities
        GENERIC_TERMS = {
            "Transportation", "Defense Counsel", "Prosecution", "Court",
            "Government", "Administration", "ET AL", "VARIOUS", "UNKNOWN",
            "N/A", "TBD", "Pretrial Services", "Health Services",
            "the Federal Rules of Criminal Procedure", "Psychological Observation",
            "Department"  # Too generic without modifier
        }

        # Legal/billing terms
        LEGAL_BILLING_TERMS = {
            "UNLIMITED N/WKND MIN", "Bill 3rd Party"
        }

        # Check against invalid patterns
        for pattern in INVALID_ENTITY_PATTERNS:
            if re.match(pattern, name, re.IGNORECASE):
                logger.debug(f"Filtered invalid entity pattern: '{name}' (pattern: {pattern})")
                return False

        # Check against generic terms (case-insensitive)
        if name in GENERIC_TERMS or name.lower() in {t.lower() for t in GENERIC_TERMS}:
            logger.debug(f"Filtered generic term: '{name}'")
            return False

        # Check against legal/billing terms
        if name in LEGAL_BILLING_TERMS:
            logger.debug(f"Filtered legal/billing term: '{name}'")
            return False

        return True

    def _classify_entity_type_procedural(self, name: str) -> EntityType:
        """Classify using keyword matching with word boundaries (Tier 3: Last Resort).

        Improved keyword matching that uses word boundaries to avoid false positives.
        - "Boardman" will NOT match "board" (word boundary prevents it)
        - "Trump Organization" WILL match "organization" (whole word)

        P0 Fix: Added "LastName, FirstName" pattern detection
        P1 Fixes: Added missing location keywords, company database, surname recognition

        Args:
            name: Entity name

        Returns:
            'person', 'organization', or 'location' (always returns a result)
        """
        name_lower = name.lower()

        # P0 FIX: Check "LastName, FirstName" format FIRST (high confidence person)
        if re.match(r'^[A-Z][a-z]+,\s+[A-Z][a-z]+', name):
            logger.debug(f"Procedural classified '{name}' as 'person' (LastName, FirstName format)")
            return 'person'

        # Organization keywords (non-profit, government, etc.)
        organization_keywords = [
            'organization', 'foundation', 'institute', 'university', 'college',
            'school', 'department', 'agency', 'commission', 'board',
            'council', 'society', 'association', 'federation', 'alliance'
        ]

        # Business keywords (for-profit companies)
        business_keywords = [
            'corp', 'corporation', 'inc', 'incorporated', 'llc', 'ltd', 'limited',
            'company', 'co.', 'enterprises', 'group', 'holdings', 'international',
            'partners', 'associates', 'ventures', 'capital', 'investments',
            'trust', 'fund', 'bank', 'financial', 'consulting'
        ]

        # P1 FIX: Known company names without org keywords
        KNOWN_COMPANIES = {
            # Telecom
            "verizon", "at&t", "t-mobile", "sprint", "comcast", "verizon wireless",
            # Media
            "miami herald", "new york times", "washington post", "wall street journal",
            "cnn", "fox news", "msnbc", "the guardian", "reuters", "associated press",
            # Tech
            "microsoft", "apple", "google", "facebook", "amazon", "netflix",
            # Airlines
            "delta", "american airlines", "united airlines", "southwest", "jetblue",
            # Others
            "walmart", "target", "starbucks", "mcdonald's", "nike", "adidas"
        }

        # P1 FIX: Common surnames to prevent location misclassification
        COMMON_SURNAMES = {
            # Jewish surnames (common in this dataset)
            "lefkowitz", "dershowitz", "epstein", "weinstein", "goldstein",
            # Other common surnames in dataset
            "villafafia", "lugosch", "comey", "sternheim", "rocchio",
            "loftus", "landgraf", "haddon", "boardman"
        }

        # P1 FIX: Enhanced location keywords (added building, suite, floor, room, office, etc.)
        location_keywords = [
            'island', 'islands', 'ranch', 'estate', 'villa', 'villas',
            'hotel', 'resort', 'airport', 'beach', 'bay', 'tower', 'towers',
            'building', 'plaza', 'square', 'park', 'gardens',
            # P1 additions:
            'suite', 'floor', 'room', 'office', 'center', 'complex',
            'street', 'avenue', 'road', 'boulevard', 'drive', 'place',
            'manor', 'palace', 'club'
        ]

        # P1 FIX: Check if single-word name is a known surname (person)
        if ' ' not in name and name_lower in COMMON_SURNAMES:
            logger.debug(f"Procedural classified '{name}' as 'person' (known surname)")
            return 'person'

        # P1 FIX: Check if name is a known company
        if name_lower in KNOWN_COMPANIES:
            logger.debug(f"Procedural classified '{name}' as 'organization' (known company)")
            return 'organization'

        # Check for organization FIRST (with word boundaries)
        for keyword in organization_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, name_lower):
                logger.debug(f"Procedural classified '{name}' as 'organization' (keyword: {keyword})")
                return 'organization'

        # Check for business (also maps to organization)
        for keyword in business_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, name_lower):
                logger.debug(f"Procedural classified '{name}' as 'organization' (business keyword: {keyword})")
                return 'organization'

        # Check for location (with word boundaries)
        for keyword in location_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, name_lower):
                logger.debug(f"Procedural classified '{name}' as 'location' (keyword: {keyword})")
                return 'location'

        # Name format heuristic: any comma-separated name is likely person
        if ',' in name:
            logger.debug(f"Procedural classified '{name}' as 'person' (comma format)")
            return 'person'

        # Default to person
        logger.debug(f"Procedural classified '{name}' as 'person' (default)")
        return 'person'

    def _get_entity_type(self, entity_id: str, entity_name: str) -> str:
        """Get entity type from pre-classified data or fallback to detection.

        Uses pre-classified entity_type from biography data (from LLM classification script).
        Only falls back to dynamic detection if entity is not pre-classified.

        Args:
            entity_id: Entity ID (snake_case slug)
            entity_name: Entity display name

        Returns:
            Entity type: 'person', 'organization', or 'location'

        Design Decision: Pre-classified Data First
        Rationale: The entity_biographies.json contains accurate LLM-classified types
        from a batch classification process (ticket 1M-364). Using pre-classified data
        ensures consistency and avoids re-classification overhead. Only entities without
        pre-classification (new entities, old data) fallback to dynamic detection.
        """
        # Try to get from bio data by ID first (preferred lookup)
        if entity_id and entity_id in self.entity_bios:
            bio_type = self.entity_bios[entity_id].get('entity_type')
            if bio_type:
                logger.debug(f"Using pre-classified type for '{entity_name}' (ID: {entity_id}): {bio_type}")
                return bio_type

        # Fallback to name-based lookup (for backward compatibility)
        if entity_name and entity_name in self.entity_bios:
            bio_type = self.entity_bios[entity_name].get('entity_type')
            if bio_type:
                logger.debug(f"Using pre-classified type for '{entity_name}' (name lookup): {bio_type}")
                return bio_type

        # No pre-classified data found, fallback to dynamic detection
        logger.debug(f"No pre-classified type for '{entity_name}', using dynamic detection")

        # Build context for better LLM classification
        context = {}
        if entity_id and entity_id in self.entity_bios:
            context['bio'] = self.entity_bios[entity_id].get('biography', '')
        elif entity_name and entity_name in self.entity_bios:
            context['bio'] = self.entity_bios[entity_name].get('biography', '')

        return self.detect_entity_type(entity_name, context if context else None)

    def detect_entity_type(self, entity_name: str, context: Optional[dict] = None) -> str:
        """Detect entity type using tiered classification approach.

        Tier 1: LLM classification (Claude Haiku - fast, cheap, accurate)
        Tier 2: NLP/NER fallback (spaCy - good accuracy)
        Tier 3: Procedural fallback (keyword matching - always returns result)

        This replaces the old keyword-only approach with a robust 3-tier system
        that gracefully degrades if LLM/NLP are unavailable.

        P0 Fix: Added entity validation to filter non-entities
        P1 Fix: Added name normalization before classification

        Args:
            entity_name: Entity name to analyze
            context: Optional context (bio, sources) for better LLM accuracy

        Returns:
            Entity type: 'person', 'organization', or 'location'

        Design Decision: Tiered Approach
        Rationale: LLM provides best accuracy but may be unavailable (API key, quota).
        NLP provides good fallback. Procedural ensures we always return a result.
        """
        # P0 FIX: Validate entity before classification
        if not self._is_valid_entity(entity_name):
            # Return a special marker to signal this should be filtered
            # Callers should skip entities with this type
            return 'invalid'

        # P1 FIX: Normalize name before classification
        normalized_name = self._normalize_entity_name_for_classification(entity_name)

        # Tier 1: LLM classification (primary) - use normalized name
        result = self._classify_entity_type_llm(normalized_name, context)
        if result:
            return result

        # Tier 2: NLP fallback - use normalized name
        result = self._classify_entity_type_nlp(normalized_name)
        if result:
            return result

        # Tier 3: Procedural fallback (always returns result) - use ORIGINAL name for pattern matching
        # (because patterns like "LastName, FirstName" need exact format)
        return self._classify_entity_type_procedural(entity_name)

    def detect_entity_type_legacy(self, entity_name: str) -> str:
        """DEPRECATED: Old detect_entity_type implementation (keyword-only).

        Kept for backward compatibility testing. Use detect_entity_type() instead.

        Uses word boundary matching to avoid substring false positives:
        - "Boardman" will NOT match "board" (word boundary prevents it)
        - "Trump Organization" WILL match "organization" (whole word)
        - "Little St James Island" WILL match "island" (whole word)

        Args:
            entity_name: Entity name to analyze

        Returns:
            Entity type: 'person', 'business', 'location', or 'organization'
        """
        name = entity_name.lower()

        # Business/Organization indicators
        business_keywords = [
            "corp",
            "corporation",
            "inc",
            "incorporated",
            "llc",
            "ltd",
            "limited",
            "company",
            "co.",
            "enterprises",
            "group",
            "holdings",
            "international",
            "partners",
            "associates",
            "ventures",
            "capital",
            "investments",
            "trust",
            "fund",
            "bank",
            "financial",
            "consulting",
        ]

        # Location indicators
        location_keywords = [
            "island",
            "airport",
            "beach",
            "estate",
            "ranch",
            "street",
            "avenue",
            "road",
            "boulevard",
            "drive",
            "place",
            "manor",
            "villa",
            "palace",
            "hotel",
            "resort",
            "club",
        ]

        # Organization indicators (non-profit, government, etc.)
        # NOTE: "foundation" moved here from business_keywords to prioritize non-profits
        organization_keywords = [
            "organization",
            "foundation",
            "institute",
            "university",
            "college",
            "school",
            "department",
            "agency",
            "commission",
            "board",
            "council",
            "society",
            "association",
            "federation",
            "alliance",
        ]

        # Check for organization FIRST (with word boundaries)
        # Organizations checked before businesses to prioritize non-profits/gov
        for keyword in organization_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, name):
                return "organization"

        # Check for business (with word boundaries)
        for keyword in business_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, name):
                return "business"

        # Check for location (with word boundaries)
        for keyword in location_keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, name):
                return "location"

        # Default to person
        return "person"

    def get_entities(
        self,
        search: Optional[str] = None,
        entity_type: Optional[str] = None,
        tag: Optional[str] = None,
        source: Optional[str] = None,
        filter_billionaires: bool = False,
        filter_connected: bool = False,
        has_biography: bool = False,
        sort_by: str = "documents",
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Get filtered and sorted entity list

        Args:
            search: Text search in entity name
            entity_type: Filter by type (person, business, location, organization)
            tag: Filter by tag (from entity_tags.json)
            source: Filter by source (black_book, flight_logs, etc.)
            filter_billionaires: Only show billionaires
            filter_connected: Only show entities with connections
            has_biography: Only show entities with biography data
            sort_by: Sort field ('documents', 'connections', 'name')
            limit: Results per page
            offset: Pagination offset

        Returns:
            {
                "entities": List of entities,
                "total": Total matching entities,
                "offset": Pagination offset,
                "limit": Results per page
            }
        """
        # Start with entity_stats (persons with document statistics)
        entities_list = list(self.entity_stats.values())

        # Add organizations and locations from entity_bios that aren't in entity_stats
        entity_stats_names = {e.get("name", "") for e in entities_list}
        entity_stats_ids = {e.get("id", "") for e in entities_list}

        logger.info(f"Starting merge: entity_bios has {len(self.entity_bios)} items, entity_stats has {len(entities_list)} items")

        orgs_added = 0
        locs_added = 0
        skipped_in_stats = 0
        skipped_person = 0

        for entity_key, entity_data in self.entity_bios.items():
            # Skip if already in entity_stats (persons)
            if entity_key in entity_stats_names or entity_key in entity_stats_ids:
                skipped_in_stats += 1
                continue

            # Skip person entities (they should be in entity_stats)
            entity_type = entity_data.get("entity_type")
            if entity_type == "person":
                skipped_person += 1
                continue

            # Add organization/location entity with basic structure
            entities_list.append({
                "id": entity_key,
                "name": entity_data.get("name", entity_key),
                "entity_type": entity_type,
                "documents": 0,  # Organizations/locations don't have document counts yet
                "connections": 0,
                "sources": []
            })

            if entity_type == "organization":
                orgs_added += 1
                if orgs_added <= 3:
                    logger.info(f"Added org: {entity_key}")
            elif entity_type == "location":
                locs_added += 1
                if locs_added <= 3:
                    logger.info(f"Added loc: {entity_key}")

        logger.info(f"Merge complete: Added {orgs_added} organizations and {locs_added} locations to entity list")
        logger.info(f"Skipped: {skipped_in_stats} already in entity_stats, {skipped_person} person entities")

        # Filter out generic entities (Male, Female, etc.)
        entities_list = [
            e for e in entities_list if not self.entity_filter.is_generic(e.get("name", ""))
        ]

        # Text search
        if search:
            search_lower = search.lower()
            entities_list = [e for e in entities_list if search_lower in e.get("name", "").lower()]

        # Type filter
        if entity_type:
            entities_list = [
                e
                for e in entities_list
                if self._get_entity_type(e.get("id", ""), e.get("name", "")) == entity_type
            ]

        # Tag filter
        if tag:
            entities_list = [
                e
                for e in entities_list
                if tag in self.entity_tags.get(e.get("name", ""), {}).get("tags", [])
            ]

        # Source filter
        if source:
            entities_list = [e for e in entities_list if source in e.get("sources", [])]

        # Billionaire filter
        if filter_billionaires:
            entities_list = [e for e in entities_list if e.get("is_billionaire", False)]

        # Connected filter
        if filter_connected:
            entities_list = [e for e in entities_list if e.get("connection_count", 0) > 0]

        # Biography filter
        if has_biography:
            entities_list = [
                e
                for e in entities_list
                if e.get("id", "") in self.entity_bios or e.get("name", "") in self.entity_bios
            ]

        # Enrich with type and bio/tag data, filtering invalid entities
        enriched_entities = []
        for entity in entities_list:
            entity_name = entity.get("name", "")
            entity_id = entity.get("id", "")

            # Use pre-classified entity type from biography data (or detect if not available)
            detected_type = self._get_entity_type(entity_id, entity_name)

            # P0 FIX: Filter out invalid entities
            if detected_type == 'invalid':
                logger.debug(f"Filtering invalid entity: '{entity_name}'")
                continue  # Skip this entity entirely

            entity["entity_type"] = detected_type

            # Add bio if available (try ID first, then fallback to name)
            if entity_id in self.entity_bios:
                entity["bio"] = self.entity_bios[entity_id]
            elif entity_name in self.entity_bios:
                entity["bio"] = self.entity_bios[entity_name]

            # P0 FIX: Map relationship_categories to categories field (CRITICAL)
            # This fixes the empty categories[] issue reported in QA
            bio_data = None
            if entity_id in self.entity_bios:
                bio_data = self.entity_bios[entity_id]
            elif entity_name in self.entity_bios:
                bio_data = self.entity_bios[entity_name]

            if bio_data and "relationship_categories" in bio_data:
                # Extract just the 'type' field from relationship_categories
                # Convert from: [{"type": "co_conspirator", "label": "Co-Conspirator", ...}, ...]
                # To: ["co_conspirator", "frequent_travelers", ...]
                entity["categories"] = [cat.get("type") for cat in bio_data.get("relationship_categories", [])]
            else:
                entity["categories"] = []

            # Add tags if available (try ID first, then fallback to name)
            if entity_id in self.entity_tags:
                entity["tags"] = self.entity_tags[entity_id].get("tags", [])
                entity["primary_tag"] = self.entity_tags[entity_id].get("primary_tag")
            elif entity_name in self.entity_tags:
                entity["tags"] = self.entity_tags[entity_name].get("tags", [])
                entity["primary_tag"] = self.entity_tags[entity_name].get("primary_tag")

            # Add news and timeline counts
            entity["news_articles_count"] = self.get_entity_news_count(entity_name)
            entity["timeline_events_count"] = self.get_entity_timeline_count(entity_name)

            enriched_entities.append(entity)

        # Use enriched list for sorting and pagination
        entities_list = enriched_entities

        # Sort
        if sort_by == "documents":
            entities_list.sort(key=lambda e: e.get("total_documents", 0), reverse=True)
        elif sort_by == "connections":
            entities_list.sort(key=lambda e: e.get("connection_count", 0), reverse=True)
        elif sort_by == "name":
            entities_list.sort(key=lambda e: e.get("name", ""))

        # Paginate
        total = len(entities_list)
        entities_page = entities_list[offset : offset + limit]

        return {"entities": entities_page, "total": total, "offset": offset, "limit": limit}

    def get_entity_by_id(self, entity_id: str) -> Optional[Union[Entity, dict]]:
        """Get entity by ID (primary lookup method)

        Args:
            entity_id: Unique entity identifier (snake_case slug)

        Returns:
            Entity data (Pydantic model if USE_PYDANTIC=true, dict otherwise)
            or None if not found

        Performance: O(1) dictionary lookup
        """
        # Check Pydantic storage first if enabled
        if USE_PYDANTIC and entity_id in self.entities_pydantic:
            return self.entities_pydantic[entity_id]

        # Fallback to dict storage
        entity = self.entity_stats.get(entity_id)

        if not entity:
            return None

        # Enrich dict with additional data
        entity_name = entity.get("name", "")

        # Build context for better LLM classification
        context = {}
        if entity_id in self.entity_bios:
            context['bio'] = self.entity_bios[entity_id].get('biography', '')
        elif entity_name in self.entity_bios:
            context['bio'] = self.entity_bios[entity_name].get('biography', '')
        if entity.get('sources'):
            context['sources'] = entity.get('sources', [])

        entity["entity_type"] = self.detect_entity_type(entity_name, context if context else None)

        # Bio lookup by ID first, fallback to name
        if entity_id in self.entity_bios:
            entity["bio"] = self.entity_bios[entity_id]
            logger.debug(f"Found bio for {entity_id} (by ID)")
        elif entity_name in self.entity_bios:
            entity["bio"] = self.entity_bios[entity_name]
            logger.debug(f"Found bio for {entity_name} (by name)")
        else:
            logger.debug(f"No bio found for {entity_id} or {entity_name}")

        # Tags lookup by ID first, fallback to name
        if entity_id in self.entity_tags:
            entity["tags"] = self.entity_tags[entity_id].get("tags", [])
            entity["primary_tag"] = self.entity_tags[entity_id].get("primary_tag")
        elif entity_name in self.entity_tags:
            entity["tags"] = self.entity_tags[entity_name].get("tags", [])
            entity["primary_tag"] = self.entity_tags[entity_name].get("primary_tag")

        # Semantic index lookup
        if entity_id in self.semantic_index:
            entity["documents"] = self.semantic_index[entity_id]
        elif entity_name in self.semantic_index:
            entity["documents"] = self.semantic_index[entity_name]

        return entity

    def get_entity_by_name(self, name: str) -> Optional[Union[Entity, dict]]:
        """Get entity by name (backward compatibility)

        Args:
            name: Entity name or variation (exact match)

        Returns:
            Entity data (Pydantic model if USE_PYDANTIC=true, dict otherwise)
            or None if not found

        Performance: O(1) via name_to_id mapping + O(1) ID lookup
        """
        # Resolve name to ID
        entity_id = self.name_to_id.get(name)

        if not entity_id:
            logger.debug(f"Entity name '{name}' not found in name_to_id mapping")
            return None

        logger.debug(f"Resolved '{name}' to entity_id '{entity_id}'")

        # Use ID-based lookup
        return self.get_entity_by_id(entity_id)

    def resolve_name_to_id(self, name: str) -> Optional[str]:
        """Resolve entity name to ID

        Args:
            name: Entity name or variation

        Returns:
            Entity ID or None if not found

        Performance: O(1) dictionary lookup
        """
        return self.name_to_id.get(name)

    def get_validation_report(self) -> dict:
        """Get Pydantic validation statistics

        Returns:
            Validation stats including errors found during load

        Only available when USE_PYDANTIC=true
        """
        if not USE_PYDANTIC:
            return {
                "enabled": False,
                "message": "Pydantic validation not enabled (set USE_PYDANTIC=true)",
            }

        return {
            "enabled": True,
            "total_entities": self.validation_stats["total_entities"],
            "valid_entities": self.validation_stats["valid_entities"],
            "failed_entities": self.validation_stats["failed_entities"],
            "success_rate": (
                self.validation_stats["valid_entities"] / self.validation_stats["total_entities"]
                if self.validation_stats["total_entities"] > 0
                else 0
            ),
            "errors": self.validation_stats["validation_errors"][:10],  # First 10 errors
            "total_errors": len(self.validation_stats["validation_errors"]),
        }

    def to_dict(self, entity: Union[Entity, dict]) -> dict:
        """Convert entity to dict for API responses

        Args:
            entity: Entity (Pydantic model or dict)

        Returns:
            Dict representation

        Design Decision: Transparent serialization
        Rationale: API consumers don't need to know if Pydantic is enabled
        """
        if isinstance(entity, Entity):
            return entity.model_dump()
        return entity

    def get_entity_connections(
        self, entity_name: str, max_hops: int = 2, min_strength: int = 1
    ) -> dict:
        """Get entity's network connections

        Args:
            entity_name: Entity name
            max_hops: Maximum degrees of separation (1-3)
            min_strength: Minimum connection strength (number of flights)

        Returns:
            {
                "entity": Source entity,
                "direct_connections": List of directly connected entities,
                "network": Subgraph of connections up to max_hops
            }
        """
        # Find entity node
        entity_node = None
        for node in self.network_data.get("nodes", []):
            if node.get("name") == entity_name:
                entity_node = node
                break

        if not entity_node:
            return {"entity": None, "direct_connections": [], "network": {"nodes": [], "edges": []}}

        # Get direct connections (1 hop)
        direct_edges = [
            e
            for e in self.network_data.get("edges", [])
            if (e.get("source") == entity_node["id"] or e.get("target") == entity_node["id"])
            and e.get("flight_count", 0) >= min_strength
        ]

        # Get connected node IDs
        connected_ids = set()
        for edge in direct_edges:
            if edge["source"] == entity_node["id"]:
                connected_ids.add(edge["target"])
            else:
                connected_ids.add(edge["source"])

        # Get connected nodes
        connected_nodes = [
            n for n in self.network_data.get("nodes", []) if n["id"] in connected_ids
        ]

        # If max_hops > 1, expand network
        if max_hops > 1:
            # TODO: Implement multi-hop traversal
            pass

        return {
            "entity": entity_node,
            "direct_connections": connected_nodes,
            "network": {"nodes": [entity_node, *connected_nodes], "edges": direct_edges},
        }

    def get_statistics(self) -> dict:
        """Get entity statistics

        Returns:
            {
                "total_entities": Total count,
                "by_type": Count per type,
                "by_tag": Count per tag,
                "billionaires": Count,
                "connected": Count with connections
            }
        """
        all_entities = list(self.entity_stats.values())

        # Filter generic entities
        real_entities = [
            e for e in all_entities if not self.entity_filter.is_generic(e.get("name", ""))
        ]

        # Count by type
        by_type = {}
        for entity in real_entities:
            entity_type = self.detect_entity_type(entity.get("name", ""))
            by_type[entity_type] = by_type.get(entity_type, 0) + 1

        # Count by tag
        by_tag = {}
        for _entity_name, tag_data in self.entity_tags.items():
            for tag in tag_data.get("tags", []):
                by_tag[tag] = by_tag.get(tag, 0) + 1

        # Count billionaires
        billionaires = sum(1 for e in real_entities if e.get("is_billionaire", False))

        # Count connected
        connected = sum(1 for e in real_entities if e.get("connection_count", 0) > 0)

        return {
            "total_entities": len(real_entities),
            "by_type": by_type,
            "by_tag": by_tag,
            "billionaires": billionaires,
            "connected": connected,
            "network_nodes": len(self.network_data.get("nodes", [])),
            "network_edges": len(self.network_data.get("edges", [])),
        }
