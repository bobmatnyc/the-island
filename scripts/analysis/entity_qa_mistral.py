#!/usr/bin/env python3
"""
Entity QA using Mistral via Ollama
Focuses on: Punctuation, Deduplication, Classification
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENTITIES_INDEX = PROJECT_ROOT / "data/md/entities/ENTITIES_INDEX.json"
ENTITY_STATS = PROJECT_ROOT / "data/metadata/entity_statistics.json"
QA_REPORT = PROJECT_ROOT / "data/metadata/entity_qa_report.json"
QA_FIXES = PROJECT_ROOT / "data/metadata/entity_qa_fixes.json"

class EntityQA:
    def __init__(self, model="mistral-small3.2:latest"):
        self.model = model
        self.issues = {
            "punctuation_errors": [],
            "duplicates": [],
            "classification_errors": []
        }
        self.fixes = []

    def call_ollama(self, prompt: str) -> str:
        """Call Ollama API with prompt"""
        try:
            result = subprocess.run(
                ["ollama", "run", self.model, prompt],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return ""

    def check_punctuation(self, name: str) -> Tuple[bool, str]:
        """Check if entity name has punctuation errors"""
        prompt = f"""Check if this entity name has punctuation errors:
Name: "{name}"

Rules:
1. Names should be "LastName, FirstName" format
2. Should have exactly ONE comma
3. No double commas, periods, or extra punctuation
4. No trailing/leading whitespace

Respond with ONLY:
- "OK" if correct
- "FIX: [corrected name]" if needs fixing

Name: "{name}"
Response:"""

        response = self.call_ollama(prompt)
        if response.startswith("FIX:"):
            corrected = response.replace("FIX:", "").strip()
            return False, corrected
        return True, name

    def find_duplicates(self, entities: Dict) -> List[List[str]]:
        """Find potential duplicate entities"""
        names = list(entities.keys())
        duplicates = []

        # Batch check for efficiency
        batch_size = 10
        for i in range(0, len(names), batch_size):
            batch = names[i:i+batch_size]
            batch_str = "\n".join([f"{idx+1}. {name}" for idx, name in enumerate(batch)])

            prompt = f"""Find duplicate entities in this list:
{batch_str}

Rules:
1. Same person with different spellings (e.g., "Smith, John" and "Smith, Jon")
2. Same person with nickname (e.g., "Maxwell, Ghislaine" and "Ghislaine")
3. Name variations (e.g., "Smith, J." and "Smith, John")

Respond with ONLY groups of duplicates:
- Format: "GROUP: [name1] = [name2] = [name3]"
- If no duplicates, respond: "NONE"

Response:"""

            response = self.call_ollama(prompt)
            if response != "NONE" and "GROUP:" in response:
                for line in response.split("\n"):
                    if line.startswith("GROUP:"):
                        group = [n.strip() for n in line.replace("GROUP:", "").split("=")]
                        duplicates.append(group)

        return duplicates

    def classify_entity(self, name: str, stats: Dict) -> str:
        """Classify entity type using LLM"""
        context = {
            "flight_count": stats.get("flight_count", 0),
            "sources": stats.get("sources", []),
            "appears_in_black_book": "black_book" in stats.get("sources", [])
        }

        prompt = f"""Classify this entity:
Name: "{name}"
Flight count: {context['flight_count']}
Appears in black book: {context['appears_in_black_book']}

Classify as ONE of:
- PERSON: Individual person
- ORGANIZATION: Company, foundation, entity
- LOCATION: Place or property
- AIRCRAFT: Plane or vehicle
- UNKNOWN: Cannot determine

Respond with ONLY the classification word.

Response:"""

        response = self.call_ollama(prompt)
        classifications = ["PERSON", "ORGANIZATION", "LOCATION", "AIRCRAFT", "UNKNOWN"]
        for c in classifications:
            if c in response.upper():
                return c
        return "UNKNOWN"

    def qa_all_entities(self):
        """Run QA on all entities"""
        print("Loading entity data...")

        # Load entities index
        with open(ENTITIES_INDEX) as f:
            entities_data = json.load(f)
            entities = entities_data.get("entities", {})

        # Load entity statistics
        with open(ENTITY_STATS) as f:
            stats_data = json.load(f)
            stats = stats_data.get("statistics", {})

        total = len(entities)
        print(f"\nFound {total} entities to QA\n")

        # Phase 1: Check punctuation
        print("=" * 80)
        print("PHASE 1: Checking Punctuation")
        print("=" * 80)

        for idx, (name, entity_data) in enumerate(entities.items(), 1):
            print(f"\r[{idx}/{total}] Checking: {name[:50]}", end="", flush=True)

            is_ok, corrected = self.check_punctuation(name)
            if not is_ok:
                self.issues["punctuation_errors"].append({
                    "original": name,
                    "corrected": corrected,
                    "entity_data": entity_data
                })
                self.fixes.append({
                    "type": "punctuation",
                    "original": name,
                    "fixed": corrected
                })

        print(f"\n✓ Found {len(self.issues['punctuation_errors'])} punctuation errors\n")

        # Phase 2: Find duplicates
        print("=" * 80)
        print("PHASE 2: Finding Duplicates")
        print("=" * 80)

        duplicate_groups = self.find_duplicates(entities)
        self.issues["duplicates"] = duplicate_groups
        print(f"\n✓ Found {len(duplicate_groups)} potential duplicate groups\n")

        # Phase 3: Verify classifications
        print("=" * 80)
        print("PHASE 3: Verifying Classifications")
        print("=" * 80)

        for idx, (name, entity_data) in enumerate(entities.items(), 1):
            print(f"\r[{idx}/{total}] Classifying: {name[:50]}", end="", flush=True)

            entity_stats = stats.get(name, {})
            llm_classification = self.classify_entity(name, entity_stats)
            current_classification = entity_data.get("entity_type", "UNKNOWN")

            if llm_classification != current_classification and llm_classification != "UNKNOWN":
                self.issues["classification_errors"].append({
                    "name": name,
                    "current": current_classification,
                    "suggested": llm_classification,
                    "stats": entity_stats
                })
                self.fixes.append({
                    "type": "classification",
                    "entity": name,
                    "from": current_classification,
                    "to": llm_classification
                })

        print(f"\n✓ Found {len(self.issues['classification_errors'])} classification mismatches\n")

        # Save reports
        self.save_reports()

    def save_reports(self):
        """Save QA reports"""
        print("=" * 80)
        print("SAVING REPORTS")
        print("=" * 80)

        # Save detailed issue report
        report = {
            "timestamp": datetime.now().isoformat(),
            "model": self.model,
            "summary": {
                "total_punctuation_errors": len(self.issues["punctuation_errors"]),
                "total_duplicate_groups": len(self.issues["duplicates"]),
                "total_classification_errors": len(self.issues["classification_errors"])
            },
            "issues": self.issues
        }

        with open(QA_REPORT, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✓ Saved detailed report: {QA_REPORT}")

        # Save fixes
        fixes_data = {
            "timestamp": datetime.now().isoformat(),
            "total_fixes": len(self.fixes),
            "fixes": self.fixes
        }

        with open(QA_FIXES, 'w') as f:
            json.dump(fixes_data, f, indent=2)
        print(f"✓ Saved fixes: {QA_FIXES}")

        # Print summary
        print("\n" + "=" * 80)
        print("QA SUMMARY")
        print("=" * 80)
        print(f"Punctuation Errors: {len(self.issues['punctuation_errors'])}")
        print(f"Duplicate Groups: {len(self.issues['duplicates'])}")
        print(f"Classification Errors: {len(self.issues['classification_errors'])}")
        print(f"Total Fixes Recommended: {len(self.fixes)}")
        print("=" * 80)

        # Show examples
        if self.issues["punctuation_errors"]:
            print("\nSample Punctuation Errors:")
            for error in self.issues["punctuation_errors"][:5]:
                print(f"  {error['original']} → {error['corrected']}")

        if self.issues["duplicates"]:
            print("\nSample Duplicate Groups:")
            for group in self.issues["duplicates"][:5]:
                print(f"  {' = '.join(group)}")

        if self.issues["classification_errors"]:
            print("\nSample Classification Errors:")
            for error in self.issues["classification_errors"][:5]:
                print(f"  {error['name']}: {error['current']} → {error['suggested']}")

if __name__ == "__main__":
    print("Entity QA using Mistral via Ollama")
    print("Focus: Punctuation, Deduplication, Classification")
    print()

    qa = EntityQA()
    qa.qa_all_entities()

    print("\n✓ QA Complete!")
    print(f"\nReports saved to:")
    print(f"  - {QA_REPORT}")
    print(f"  - {QA_FIXES}")
