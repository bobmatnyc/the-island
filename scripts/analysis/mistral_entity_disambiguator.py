#!/usr/bin/env python3
"""
Mistral Entity Disambiguation Service

Uses local Mistral LLM to:
1. Disambiguate short names (e.g., "Maxwell" → "Maxwell, Ghislaine")
2. Classify entity roles (victim, associate, employee, etc.)
3. Detect duplicate entities
4. Suggest entity relationships from context

Design Decision: Local Mistral for Privacy & Control
- Rationale: Epstein case data is sensitive; local processing ensures privacy
- Trade-offs: Slower than API calls, but no data leaves system
- Alternative: OpenAI API rejected due to privacy concerns and cost
- Model Choice: Mistral-7B-Instruct for balance of quality and speed

Performance:
- Expected: 2-5 seconds per disambiguation (depends on hardware)
- Batch processing: ~100-200 entities/hour on M1 Mac
- Memory: ~16GB RAM recommended for Mistral-7B

Ethical Guidelines:
- Only use documented evidence from public records
- Clearly indicate confidence levels
- Require human confirmation for all changes
- Do not speculate beyond available evidence
"""

import json
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import re

# Mistral/Transformers imports
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False
    print("Warning: transformers/torch not installed. Install with:")
    print("  pip install transformers torch accelerate")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DisambiguationResult:
    """Result of entity disambiguation attempt"""
    original_name: str
    suggested_name: str
    confidence: float
    reasoning: str
    sources_used: List[str]


@dataclass
class EntityRole:
    """Classification of entity role"""
    entity_name: str
    role: str  # victim, associate, employee, witness, investigator, other
    confidence: float
    reasoning: str


class MistralEntityDisambiguator:
    """
    Entity disambiguation using local Mistral LLM

    Design Pattern: Singleton for model loading
    - Loads model once on initialization (expensive operation)
    - Reuses loaded model for all disambiguation requests
    - Estimated load time: 30-60 seconds on M1 Mac
    """

    def __init__(self, model_name: str = "mistralai/Mistral-7B-Instruct-v0.2"):
        """
        Initialize Mistral model for entity disambiguation

        Args:
            model_name: HuggingFace model identifier

        Performance Notes:
        - Initial load: 30-60 seconds
        - Memory footprint: ~14GB for Mistral-7B
        - GPU highly recommended (10x speedup over CPU)
        """
        if not MISTRAL_AVAILABLE:
            raise ImportError("transformers and torch required. Install with: pip install transformers torch")

        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")

        # Load tokenizer and model
        logger.info(f"Loading Mistral model: {model_name}")
        logger.info("This may take 30-60 seconds on first run...")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            torch_dtype=torch.float16 if self.device != "cpu" else torch.float32,
        )

        logger.info("Model loaded successfully")

        # Load entity context from project data
        self.entity_context = self._load_entity_context()

    def _load_entity_context(self) -> Dict[str, any]:
        """
        Load entity data for context in disambiguation

        Returns:
            Dictionary with entity index, network, and flight logs
        """
        base_path = Path(__file__).parent.parent.parent

        context = {}

        # Load entity index
        entity_index_path = base_path / "data/md/entities/ENTITIES_INDEX.json"
        if entity_index_path.exists():
            with open(entity_index_path) as f:
                context['entity_index'] = json.load(f)
            logger.info(f"Loaded {len(context['entity_index'].get('entities', []))} entities")

        # Load flight logs for context
        flight_logs_path = base_path / "data/md/entities/flight_logs_by_flight.json"
        if flight_logs_path.exists():
            with open(flight_logs_path) as f:
                context['flight_logs'] = json.load(f)
            logger.info(f"Loaded {len(context['flight_logs'])} flight records")

        return context

    def _generate_response(self, prompt: str, max_tokens: int = 150) -> str:
        """
        Generate response from Mistral model

        Args:
            prompt: Input prompt for the model
            max_tokens: Maximum tokens in response

        Returns:
            Model's text response

        Performance:
        - CPU: 5-10 seconds per request
        - GPU/MPS: 1-2 seconds per request
        """
        # Format for Mistral-Instruct
        formatted_prompt = f"<s>[INST] {prompt} [/INST]"

        inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=0.3,  # Lower temperature for more deterministic results
                top_p=0.9,
                do_sample=True,
            )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract just the model's response (after [/INST])
        if "[/INST]" in response:
            response = response.split("[/INST]")[-1].strip()

        return response

    def disambiguate_entity(self, short_name: str, context: Optional[str] = None) -> DisambiguationResult:
        """
        Disambiguate a short entity name to full name

        Args:
            short_name: Ambiguous name (e.g., "Maxwell", "Ghislaine")
            context: Additional context (e.g., "appeared in flight logs 520 times")

        Returns:
            DisambiguationResult with suggested full name and confidence

        Example:
            >>> disambiguator.disambiguate_entity("Maxwell", "520 flights with Epstein")
            DisambiguationResult(
                original_name="Maxwell",
                suggested_name="Maxwell, Ghislaine",
                confidence=0.95,
                reasoning="Ghislaine Maxwell is documented in court records..."
            )
        """
        logger.info(f"Disambiguating: {short_name}")

        # Build context from entity data
        entity_matches = self._find_similar_entities(short_name)

        context_info = context or ""
        if entity_matches:
            context_info += f"\n\nKnown entities with similar names:\n"
            for match in entity_matches[:5]:
                context_info += f"- {match['name']}: {match.get('flights', 0)} flights, sources: {match.get('sources', [])}\n"

        prompt = f"""Based on public Epstein case documents, disambiguate this entity name to standard "Last, First" format.

Entity: "{short_name}"

Context: {context_info}

Rules:
1. Use ONLY documented names from public records
2. Format as "Last, First" (e.g., "Maxwell, Ghislaine")
3. If uncertain, indicate confidence level
4. Do not speculate beyond available evidence

Response format:
Full name: [Last, First]
Confidence: [0.0-1.0]
Reasoning: [brief explanation]
"""

        response = self._generate_response(prompt, max_tokens=200)

        # Parse response
        full_name, confidence, reasoning = self._parse_disambiguation_response(response, short_name)

        return DisambiguationResult(
            original_name=short_name,
            suggested_name=full_name,
            confidence=confidence,
            reasoning=reasoning,
            sources_used=["entity_index", "flight_logs"] if entity_matches else []
        )

    def _find_similar_entities(self, name: str) -> List[Dict]:
        """Find entities with similar names in the index"""
        entities = self.entity_context.get('entity_index', {}).get('entities', [])

        # Simple similarity: contains or starts with
        similar = []
        name_lower = name.lower()

        for entity in entities:
            entity_name = entity.get('name', '').lower()
            if name_lower in entity_name or entity_name.startswith(name_lower):
                similar.append(entity)

        # Sort by flight count (more flights = more significant)
        return sorted(similar, key=lambda x: x.get('flights', 0), reverse=True)

    def _parse_disambiguation_response(self, response: str, original_name: str) -> Tuple[str, float, str]:
        """
        Parse Mistral's disambiguation response

        Returns:
            (full_name, confidence, reasoning)
        """
        full_name = original_name  # Default to original if parsing fails
        confidence = 0.5
        reasoning = response

        # Extract full name
        name_match = re.search(r'Full name:\s*([^\n]+)', response, re.IGNORECASE)
        if name_match:
            full_name = name_match.group(1).strip()

        # Extract confidence
        conf_match = re.search(r'Confidence:\s*([\d.]+)', response, re.IGNORECASE)
        if conf_match:
            try:
                confidence = float(conf_match.group(1))
            except ValueError:
                pass

        # Extract reasoning
        reason_match = re.search(r'Reasoning:\s*([^\n]+)', response, re.IGNORECASE)
        if reason_match:
            reasoning = reason_match.group(1).strip()

        return full_name, confidence, reasoning

    def classify_entity_role(self, entity_name: str, mentions: Optional[List[str]] = None) -> EntityRole:
        """
        Classify entity role based on public documents

        Args:
            entity_name: Entity to classify
            mentions: List of document excerpts mentioning the entity

        Returns:
            EntityRole with classification and confidence

        Ethical Constraint:
            - Only classifies based on documented court records
            - Does NOT speculate about victim status
            - Requires explicit court designation for victim classification
        """
        logger.info(f"Classifying role for: {entity_name}")

        # Build context from mentions
        context_info = f"Entity: {entity_name}\n\n"

        if mentions:
            context_info += "Document mentions:\n"
            for mention in mentions[:10]:  # Limit to 10 mentions
                context_info += f"- {mention[:200]}...\n"

        # Get flight/contact data
        entity_data = self._find_entity_in_index(entity_name)
        if entity_data:
            context_info += f"\nFlight appearances: {entity_data.get('flights', 0)}\n"
            context_info += f"Sources: {entity_data.get('sources', [])}\n"

        prompt = f"""Based ONLY on public Epstein case court documents, classify this entity's role.

{context_info}

Possible roles:
- victim: ONLY if explicitly designated in court filings
- associate: Known associate of Epstein
- employee: Staff or employee
- witness: Testified in legal proceedings
- investigator: Law enforcement or investigative role
- other: Unclear or minimal documentation

Rules:
1. Use ONLY documented evidence from court records
2. Do NOT speculate about victim status
3. Indicate confidence level
4. If insufficient evidence, use "other"

Response format:
Role: [role]
Confidence: [0.0-1.0]
Reasoning: [brief explanation with source]
"""

        response = self._generate_response(prompt, max_tokens=200)

        # Parse response
        role, confidence, reasoning = self._parse_role_response(response)

        return EntityRole(
            entity_name=entity_name,
            role=role,
            confidence=confidence,
            reasoning=reasoning
        )

    def _find_entity_in_index(self, name: str) -> Optional[Dict]:
        """Find entity in loaded index"""
        entities = self.entity_context.get('entity_index', {}).get('entities', [])

        for entity in entities:
            if entity.get('name', '').lower() == name.lower():
                return entity

        return None

    def _parse_role_response(self, response: str) -> Tuple[str, float, str]:
        """Parse role classification response"""
        role = "other"
        confidence = 0.5
        reasoning = response

        # Extract role
        role_match = re.search(r'Role:\s*([^\n]+)', response, re.IGNORECASE)
        if role_match:
            role = role_match.group(1).strip().lower()

        # Extract confidence
        conf_match = re.search(r'Confidence:\s*([\d.]+)', response, re.IGNORECASE)
        if conf_match:
            try:
                confidence = float(conf_match.group(1))
            except ValueError:
                pass

        # Extract reasoning
        reason_match = re.search(r'Reasoning:\s*([^\n]+)', response, re.IGNORECASE)
        if reason_match:
            reasoning = reason_match.group(1).strip()

        return role, confidence, reasoning

    def find_duplicate_entities(self, entity_list: List[str]) -> List[Tuple[str, str, float]]:
        """
        Find duplicate entity entries that refer to same person

        Args:
            entity_list: List of entity names to check

        Returns:
            List of (entity1, canonical_name, confidence) tuples

        Example:
            >>> duplicates = disambiguator.find_duplicate_entities([
            ...     "Maxwell, Ghislaine", "Ghislaine", "Maxwell"
            ... ])
            >>> duplicates
            [("Ghislaine", "Maxwell, Ghislaine", 0.95),
             ("Maxwell", "Maxwell, Ghislaine", 0.90)]
        """
        logger.info(f"Checking for duplicates among {len(entity_list)} entities")

        # Group by potential duplicates
        prompt = f"""Analyze these entity names from the Epstein case and identify duplicates that refer to the same person.

Entities:
{chr(10).join(f'- {name}' for name in entity_list[:50])}

Rules:
1. Only identify duplicates if you're confident they're the same person
2. Prefer "Last, First" format as canonical
3. Consider name variations (nicknames, misspellings)

Response format (one per line):
"[Duplicate]" -> "[Canonical Name]" (confidence: [0.0-1.0])
"""

        response = self._generate_response(prompt, max_tokens=500)

        # Parse duplicates
        duplicates = []
        for line in response.split('\n'):
            match = re.search(r'"([^"]+)"\s*->\s*"([^"]+)"\s*\(confidence:\s*([\d.]+)\)', line)
            if match:
                dup_name = match.group(1).strip()
                canonical = match.group(2).strip()
                try:
                    conf = float(match.group(3))
                    duplicates.append((dup_name, canonical, conf))
                except ValueError:
                    pass

        return duplicates


def main():
    """Test the disambiguator on known cases"""
    print("=" * 80)
    print("Mistral Entity Disambiguator - Test Cases")
    print("=" * 80)

    # Check if Mistral is available
    if not MISTRAL_AVAILABLE:
        print("\n❌ ERROR: transformers/torch not installed")
        print("Install with: pip install transformers torch accelerate")
        return

    # Initialize (this will take 30-60 seconds)
    print("\n📦 Loading Mistral model (this may take 30-60 seconds)...")
    disambiguator = MistralEntityDisambiguator()

    print("\n✅ Model loaded successfully!")

    # Test case 1: Disambiguate "Ghislaine"
    print("\n" + "=" * 80)
    print("Test 1: Disambiguate 'Ghislaine'")
    print("=" * 80)

    result = disambiguator.disambiguate_entity("Ghislaine", "Appeared in flight logs 520 times")
    print(f"\nOriginal name: {result.original_name}")
    print(f"Suggested name: {result.suggested_name}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Reasoning: {result.reasoning}")

    # Test case 2: Classify Maxwell's role
    print("\n" + "=" * 80)
    print("Test 2: Classify role for 'Maxwell, Ghislaine'")
    print("=" * 80)

    role = disambiguator.classify_entity_role(
        "Maxwell, Ghislaine",
        mentions=["Appeared on 520 flights", "Convicted in 2021"]
    )
    print(f"\nEntity: {role.entity_name}")
    print(f"Role: {role.role}")
    print(f"Confidence: {role.confidence:.2f}")
    print(f"Reasoning: {role.reasoning}")

    # Test case 3: Find duplicates
    print("\n" + "=" * 80)
    print("Test 3: Find duplicates")
    print("=" * 80)

    test_entities = ["Maxwell, Ghislaine", "Ghislaine", "Maxwell"]
    duplicates = disambiguator.find_duplicate_entities(test_entities)

    print(f"\nFound {len(duplicates)} potential duplicates:")
    for dup, canonical, conf in duplicates:
        print(f"  '{dup}' -> '{canonical}' (confidence: {conf:.2f})")


if __name__ == "__main__":
    main()
