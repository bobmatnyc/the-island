#!/usr/bin/env python3
"""
Comprehensive Entity QA using Mistral via Ollama

Single-prompt system for: Disambiguation, Classification, Punctuation, Deduplication

Using Ollama CLI instead of API because:
1. No need to keep Ollama app running
2. Direct command execution
3. Better error handling
4. Simpler dependency management
5. Works the same on all platforms
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import sys

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENTITIES_INDEX = PROJECT_ROOT / "data/md/entities/ENTITIES_INDEX.json"
ENTITY_STATS = PROJECT_ROOT / "data/metadata/entity_statistics.json"
QA_REPORT = PROJECT_ROOT / "data/metadata/comprehensive_entity_qa_report.json"
BACKUP_DIR = PROJECT_ROOT / "data/metadata/entity_backups"

def check_ollama_cli(model: str = "mistral-small3.2:latest") -> bool:
    """Verify ollama CLI is available and model exists."""
    try:
        # Check if ollama command exists by trying to run a simple command
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            print("❌ Ollama CLI not working properly")
            if result.stderr:
                print(f"   Error: {result.stderr}")
            return False

        print("✅ Ollama CLI available")

        # Check if model exists by trying to show it
        # This is more reliable than parsing 'ollama list' output
        model_check = subprocess.run(
            ['ollama', 'show', model],
            capture_output=True,
            text=True,
            timeout=10
        )

        if model_check.returncode == 0:
            print(f"✅ Model {model} is available")
            return True
        else:
            print(f"⚠️  Warning: {model} not found")
            print(f"   To install: ollama pull {model}")

            # Show available models for reference
            if result.stdout:
                print("\n   Available models:")
                for line in result.stdout.split('\n')[1:]:  # Skip header
                    line = line.strip()
                    if line and not line.startswith('NAME'):
                        model_name = line.split()[0] if line.split() else line
                        if model_name:
                            print(f"     - {model_name}")
            return False

    except FileNotFoundError:
        print("❌ Ollama not installed")
        print("   Install from: https://ollama.ai")
        print("   macOS: brew install ollama")
        print("   Linux: curl https://ollama.ai/install.sh | sh")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Ollama CLI timeout")
        print("   Ollama may not be responding properly")
        return False
    except Exception as e:
        print(f"❌ Unexpected error checking Ollama: {e}")
        return False

class ComprehensiveEntityQA:
    def __init__(self, model="mistral-small3.2:latest"):
        self.model = model
        self.entities = []
        self.stats = {}
        self.qa_results = []
        self.issues_found = {
            "punctuation": 0,
            "disambiguation": 0,
            "classification": 0,
            "duplicates": 0
        }

    def load_data(self):
        """Load entity data"""
        print("Loading entity data...")

        with open(ENTITIES_INDEX) as f:
            data = json.load(f)
            self.entities = data.get("entities", [])

        if ENTITY_STATS.exists():
            with open(ENTITY_STATS) as f:
                stats_data = json.load(f)
                self.stats = stats_data.get("statistics", {})

        print(f"✓ Loaded {len(self.entities)} entities")
        print(f"✓ Loaded stats for {len(self.stats)} entities\n")

    def call_ollama(self, prompt: str, timeout=45) -> str:
        """
        Call Ollama via CLI command.

        Uses subprocess to run 'ollama run <model> <prompt>' directly.
        This approach requires no API server and works immediately.

        Args:
            prompt: The prompt to send to the model
            timeout: Maximum seconds to wait for response (default: 45)

        Returns:
            Model response text, or "TIMEOUT"/"ERROR" on failure
        """
        try:
            result = subprocess.run(
                ["ollama", "run", self.model, prompt],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True  # Raises CalledProcessError on non-zero exit
            )
            return result.stdout.strip()

        except subprocess.TimeoutExpired:
            print(f"\n⏱️  Timeout after {timeout}s")
            return "TIMEOUT"

        except subprocess.CalledProcessError as e:
            print(f"\n❌ Ollama CLI error (exit code {e.returncode})")
            if e.stderr:
                print(f"   Error output: {e.stderr.strip()}")
            return "ERROR"

        except FileNotFoundError:
            print("\n❌ Ollama command not found")
            print("   Is ollama installed and in PATH?")
            return "ERROR"

        except Exception as e:
            print(f"\n❌ Unexpected error calling Ollama: {e}")
            return "ERROR"

    def analyze_entity(self, entity: Dict) -> Dict:
        """Comprehensive analysis of single entity using one LLM call"""
        name = entity.get("name", "")
        sources = entity.get("sources", [])
        flight_count = entity.get("flights", 0)

        # Get additional context from stats
        entity_stats = self.stats.get(name, {})

        # Build comprehensive prompt
        prompt = f"""Analyze this entity from the Epstein case files:

Name: "{name}"
Sources: {', '.join(sources)}
Flight count: {flight_count}
Black book page: {entity.get('black_book_page', 'N/A')}

Perform 4 analyses:

1. PUNCTUATION CHECK
   - Should be "LastName, FirstName" format
   - Check for: double commas, extra spaces, wrong format
   - ONLY flag if there's an actual error

2. DISAMBIGUATION
   - If single name (e.g., "Ghislaine"), suggest full name
   - Use ONLY documented evidence from Epstein case
   - Common single names to expand:
     * "Ghislaine" → "Maxwell, Ghislaine"
     * "Nadia" → Check if this is Nadia Marcinkova
     * Generic names like "Female (1)" need identification

3. CLASSIFICATION
   - Classify as: PERSON | ORGANIZATION | LOCATION | AIRCRAFT | UNKNOWN
   - Use flight count and sources as clues

4. POTENTIAL DUPLICATE
   - Could this be a duplicate of another entry?
   - Check for: nicknames, abbreviations, misspellings

Respond in EXACT format:
PUNCTUATION: OK|FIX:[corrected name]
DISAMBIGUATION: OK|SUGGEST:[full name]|REASON:[brief reason]
CLASSIFICATION: [PERSON|ORGANIZATION|LOCATION|AIRCRAFT|UNKNOWN]
DUPLICATE: NONE|POSSIBLE:[other entity name]

Example response:
PUNCTUATION: OK
DISAMBIGUATION: SUGGEST:Maxwell, Ghislaine|REASON:Ghislaine Maxwell documented in 520+ flights
CLASSIFICATION: PERSON
DUPLICATE: NONE

Your response:"""

        response = self.call_ollama(prompt)

        # Parse response
        result = {
            "name": name,
            "original_entity": entity,
            "punctuation_ok": True,
            "punctuation_fix": None,
            "disambiguation_ok": True,
            "disambiguation_suggestion": None,
            "disambiguation_reason": None,
            "classification": "UNKNOWN",
            "duplicate_of": None,
            "raw_response": response
        }

        if response in ["TIMEOUT", "ERROR"]:
            result["error"] = response
            return result

        # Parse each line
        for line in response.split("\n"):
            line = line.strip()

            if line.startswith("PUNCTUATION:"):
                content = line.replace("PUNCTUATION:", "").strip()
                if content.startswith("FIX:"):
                    result["punctuation_ok"] = False
                    result["punctuation_fix"] = content.replace("FIX:", "").strip()
                    self.issues_found["punctuation"] += 1

            elif line.startswith("DISAMBIGUATION:"):
                content = line.replace("DISAMBIGUATION:", "").strip()
                if content.startswith("SUGGEST:"):
                    result["disambiguation_ok"] = False
                    parts = content.split("|")
                    if len(parts) >= 2:
                        result["disambiguation_suggestion"] = parts[0].replace("SUGGEST:", "").strip()
                        if len(parts) >= 2 and "REASON:" in parts[1]:
                            result["disambiguation_reason"] = parts[1].replace("REASON:", "").strip()
                    self.issues_found["disambiguation"] += 1

            elif line.startswith("CLASSIFICATION:"):
                classification = line.replace("CLASSIFICATION:", "").strip().upper()
                valid_classifications = ["PERSON", "ORGANIZATION", "LOCATION", "AIRCRAFT", "UNKNOWN"]
                if classification in valid_classifications:
                    result["classification"] = classification
                    # Check if different from existing
                    if entity.get("entity_type") and entity.get("entity_type") != classification:
                        self.issues_found["classification"] += 1

            elif line.startswith("DUPLICATE:"):
                content = line.replace("DUPLICATE:", "").strip()
                if content.startswith("POSSIBLE:"):
                    result["duplicate_of"] = content.replace("POSSIBLE:", "").strip()
                    self.issues_found["duplicates"] += 1

        return result

    def run_qa(self, max_entities: Optional[int] = None, start_from: int = 0):
        """Run comprehensive QA on all entities"""
        print("=" * 80)
        print("COMPREHENSIVE ENTITY QA")
        print("Using:", self.model)
        print("=" * 80)
        print()

        self.load_data()

        # Limit if specified
        entities_to_check = self.entities[start_from:]
        if max_entities:
            entities_to_check = entities_to_check[:max_entities]

        total = len(entities_to_check)
        print(f"Analyzing {total} entities (starting from #{start_from})...\n")

        for idx, entity in enumerate(entities_to_check, 1):
            name = entity.get("name", "")
            actual_idx = start_from + idx

            print(f"\r[{idx}/{total}] Analyzing: {name[:60]}", end="", flush=True)

            result = self.analyze_entity(entity)
            self.qa_results.append(result)

            # Show interesting findings immediately
            if not result["punctuation_ok"]:
                print(f"\n  ⚠️  Punctuation: {name} → {result['punctuation_fix']}")
            if not result["disambiguation_ok"]:
                print(f"\n  💡 Disambiguation: {name} → {result['disambiguation_suggestion']}")
                if result["disambiguation_reason"]:
                    print(f"     Reason: {result['disambiguation_reason']}")
            if result["duplicate_of"]:
                print(f"\n  🔄 Possible duplicate of: {result['duplicate_of']}")

            # Periodic save
            if idx % 100 == 0:
                print(f"\n  💾 Checkpoint: Saving progress...")
                self.save_report(checkpoint=True)

        print("\n")
        self.save_report()

    def save_report(self, checkpoint=False):
        """Save comprehensive QA report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "model": self.model,
            "total_analyzed": len(self.qa_results),
            "issues_found": self.issues_found,
            "summary": {
                "punctuation_errors": self.issues_found["punctuation"],
                "disambiguation_needed": self.issues_found["disambiguation"],
                "classification_suggestions": self.issues_found["classification"],
                "possible_duplicates": self.issues_found["duplicates"]
            },
            "results": self.qa_results
        }

        # Save main report
        report_path = QA_REPORT if not checkpoint else QA_REPORT.with_suffix('.checkpoint.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        if not checkpoint:
            print("\n" + "=" * 80)
            print("QA REPORT SAVED")
            print("=" * 80)
            print(f"📊 Total entities analyzed: {report['total_analyzed']}")
            print(f"📝 Punctuation errors: {self.issues_found['punctuation']}")
            print(f"🔍 Disambiguation needed: {self.issues_found['disambiguation']}")
            print(f"🏷️  Classification suggestions: {self.issues_found['classification']}")
            print(f"🔄 Possible duplicates: {self.issues_found['duplicates']}")
            print(f"\n📄 Report: {report_path}")
            print("=" * 80)

            # Show top issues
            self.print_top_issues()

    def print_top_issues(self):
        """Print top issues found"""
        print("\n🔝 TOP ISSUES:")
        print("=" * 80)

        # Punctuation errors
        punct_errors = [r for r in self.qa_results if not r["punctuation_ok"]]
        if punct_errors:
            print(f"\n📝 Punctuation Errors ({len(punct_errors)}):")
            for result in punct_errors[:10]:
                print(f"  • {result['name']} → {result['punctuation_fix']}")

        # Disambiguation
        disambig = [r for r in self.qa_results if not r["disambiguation_ok"]]
        if disambig:
            print(f"\n🔍 Disambiguation Needed ({len(disambig)}):")
            for result in disambig[:10]:
                reason = f" ({result['disambiguation_reason']})" if result['disambiguation_reason'] else ""
                print(f"  • {result['name']} → {result['disambiguation_suggestion']}{reason}")

        # Duplicates
        duplicates = [r for r in self.qa_results if r["duplicate_of"]]
        if duplicates:
            print(f"\n🔄 Possible Duplicates ({len(duplicates)}):")
            for result in duplicates[:10]:
                print(f"  • {result['name']} ≈ {result['duplicate_of']}")

        print()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Comprehensive Entity QA using Mistral via Ollama CLI")
    parser.add_argument("--max", type=int, help="Max entities to analyze (for testing)")
    parser.add_argument("--start", type=int, default=0, help="Start from entity N")
    parser.add_argument("--model", default="mistral-small3.2:latest", help="Ollama model to use")
    parser.add_argument("--skip-check", action="store_true", help="Skip Ollama availability check")

    args = parser.parse_args()

    print("=" * 80)
    print("COMPREHENSIVE ENTITY QA")
    print("Disambiguation | Classification | Punctuation | Deduplication")
    print("Using Ollama CLI (no API server required)")
    print("=" * 80)
    print()

    # Check Ollama CLI availability
    if not args.skip_check:
        print("Checking Ollama CLI availability...")
        if not check_ollama_cli(model=args.model):
            print("\n❌ Ollama CLI check failed. Cannot proceed.")
            print("   Use --skip-check to bypass this check (not recommended)")
            sys.exit(1)
        print()

    qa = ComprehensiveEntityQA(model=args.model)
    qa.run_qa(max_entities=args.max, start_from=args.start)

    print("\n✅ QA Complete!")
    print(f"\n📄 Report saved to: {QA_REPORT}")
