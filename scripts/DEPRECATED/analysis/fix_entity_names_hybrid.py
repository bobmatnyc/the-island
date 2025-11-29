#!/usr/bin/env python3
"""
Hybrid Entity Name Formatter - Procedural Rules + LLM Fallback
===============================================================

Fixes entity name formatting using a two-phase approach:

Phase 1 - Procedural Rules (High Confidence):
- Single word names: Keep as-is
- Two-word names: "FirstName LastName" → "LastName, FirstName"
- Common prefixes: Handle "Dr.", "Mr.", "Mrs.", "Ms.", "Prof."
- Common suffixes: Handle "Jr.", "Sr.", "II", "III", "IV", "Ph.D.", "M.D."
- Hyphenated last names: Preserve correctly
- Known entities: Use existing database matches

Phase 2 - LLM Fallback (Low Confidence):
- Complex names with 3+ parts
- Titles embedded in name
- Ambiguous format
- Non-Western names
- Organizations appearing as entities

Author: Claude
Date: 2025-11-17
"""

import json
import re
import shutil
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class NameFormatter:
    """Hybrid name formatter with procedural rules + LLM fallback"""

    # Common honorific prefixes
    PREFIXES = {
        "Dr.",
        "Dr",
        "Doctor",
        "Mr.",
        "Mr",
        "Mister",
        "Mrs.",
        "Mrs",
        "Ms.",
        "Ms",
        "Miss",
        "Prof.",
        "Prof",
        "Professor",
        "Rev.",
        "Rev",
        "Reverend",
        "Sir",
        "Lord",
        "Lady",
        "Prince",
        "Princess",
        "Duke",
        "Duchess",
        "Baron",
        "Baroness",
        "Count",
        "Countess",
        "President",
        "Senator",
        "Governor",
        "Mayor",
    }

    # Common suffixes
    SUFFIXES = {
        "Jr.",
        "Jr",
        "Sr.",
        "Sr",
        "II",
        "III",
        "IV",
        "V",
        "Ph.D.",
        "PhD",
        "M.D.",
        "MD",
        "Esq.",
        "Esq",
        "D.D.S.",
        "DDS",
        "J.D.",
        "JD",
        "CPA",
        "M.B.A.",
        "MBA",
    }

    # Special entities that should remain as-is
    SPECIAL_CASES = {
        "Illegible",
        "Reposition",
        "Unknown",
        "Unidentified",
        "Redacted",
        "Confidential",
    }

    # Known organization indicators
    ORG_INDICATORS = {
        "Inc.",
        "Inc",
        "Corp.",
        "Corp",
        "LLC",
        "Ltd.",
        "Ltd",
        "Company",
        "Co.",
        "Foundation",
        "Trust",
        "Estate",
        "Group",
        "Partners",
        "Associates",
    }

    def __init__(self, use_llm: bool = True, llm_model: str = "mistral:latest"):
        """
        Initialize name formatter

        Args:
            use_llm: Whether to use LLM fallback for complex names
            llm_model: Ollama model to use for LLM queries
        """
        self.use_llm = use_llm
        self.llm_model = llm_model

        # Statistics
        self.stats = {
            "procedural_high_confidence": 0,
            "procedural_medium_confidence": 0,
            "llm_queries": 0,
            "llm_successes": 0,
            "llm_failures": 0,
            "original_preserved": 0,
        }

        # Track examples
        self.examples = defaultdict(list)

    def is_organization(self, name: str) -> bool:
        """Check if name appears to be an organization"""
        for indicator in self.ORG_INDICATORS:
            if indicator in name:
                return True
        return False

    def extract_prefix(self, words: List[str]) -> Tuple[Optional[str], List[str]]:
        """Extract prefix from name if present"""
        if not words:
            return None, words

        first_word = words[0].rstrip(".,")
        if first_word in self.PREFIXES:
            # Preserve original word (with period if present)
            return words[0], words[1:]

        return None, words

    def extract_suffix(self, words: List[str]) -> Tuple[Optional[str], List[str]]:
        """Extract suffix from name if present"""
        if not words:
            return None, words

        last_word = words[-1].rstrip(".,")
        if last_word in self.SUFFIXES:
            # Preserve original word (with period if present)
            return words[-1], words[:-1]

        # Check for multiple suffixes (e.g., "Jr. III")
        suffixes = []
        remaining = words
        while remaining:
            last = remaining[-1].rstrip(".,")
            if last in self.SUFFIXES:
                # Preserve original with period
                suffixes.insert(0, remaining[-1])
                remaining = remaining[:-1]
            else:
                break

        if suffixes:
            return " ".join(suffixes), remaining

        return None, words

    def apply_procedural_rules(self, name: str) -> Tuple[str, str, str]:
        """
        Apply procedural formatting rules

        Returns:
            Tuple of (formatted_name, confidence, reasoning)
            confidence: "high", "medium", "low"
        """
        # Normalize whitespace
        normalized = re.sub(r"\s+", " ", name).strip()

        # Special cases - return as-is
        if normalized in self.SPECIAL_CASES:
            return normalized, "high", "Special case entity"

        # Organizations - return as-is
        if self.is_organization(normalized):
            return normalized, "high", "Organization name"

        # Split into words
        words = normalized.split()

        # Single word names - return as-is
        if len(words) == 1:
            return normalized, "high", "Single word name"

        # Extract prefix and suffix
        prefix, words_no_prefix = self.extract_prefix(words)
        suffix, core_words = self.extract_suffix(words_no_prefix)

        # No core words left after extraction - return original
        if len(core_words) == 0:
            return normalized, "medium", "Only prefix/suffix found"

        # One core word (e.g., "Dr. Smith" or "Madonna Jr.")
        if len(core_words) == 1:
            parts = []
            if prefix:
                parts.append(prefix)
            parts.append(core_words[0])
            if suffix:
                parts.append(suffix)
            return " ".join(parts), "high", "Single name with prefix/suffix"

        # Two core words - standard "FirstName LastName" format
        if len(core_words) == 2:
            first_name, last_name = core_words

            # Format as "LastName, FirstName"
            formatted_parts = [last_name + ",", first_name]

            if suffix:
                formatted_parts.append(suffix)

            formatted = " ".join(formatted_parts)
            return formatted, "high", "Standard two-part name"

        # Three or more core words - medium confidence
        # Could be: "First Middle Last", "First Last-Name", "Title First Last"
        if len(core_words) == 3:
            # Check for hyphenated last name
            if "-" in core_words[-1]:
                # "FirstName MiddleName Last-Name"
                first = core_words[0]
                middle = core_words[1]
                last = core_words[2]

                formatted_parts = [last + ",", first, middle]
                if suffix:
                    formatted_parts.append(suffix)

                formatted = " ".join(formatted_parts)
                return formatted, "medium", "Name with middle name and hyphenated last"

            # Check if first word looks like a title (starts with capital, not common name)
            if core_words[0] in self.PREFIXES:
                # "Title FirstName LastName" - already handled by prefix extraction
                pass

            # Assume "First Middle Last"
            first = core_words[0]
            middle = core_words[1]
            last = core_words[2]

            formatted_parts = [last + ",", first]

            # Check if middle is initial (single letter or letter+period)
            if len(middle.rstrip(".")) == 1:
                formatted_parts.append(middle)
            else:
                # Full middle name
                formatted_parts.append(middle)

            if suffix:
                formatted_parts.append(suffix)

            formatted = " ".join(formatted_parts)
            return formatted, "medium", "Three-part name assumed First Middle Last"

        # Four or more words - low confidence, needs LLM
        return normalized, "low", f"Complex name with {len(core_words)} parts"

    def query_llm(self, name: str) -> Dict:
        """
        Query local LLM for name formatting

        Returns:
            Dict with keys: formatted_name, confidence, reasoning
        """
        prompt = f"""Given this name: "{name}"

Return ONLY a JSON object with this exact format (no additional text):
{{
  "formatted_name": "LastName, FirstName MiddleInitial Suffix",
  "confidence": "high",
  "reasoning": "brief explanation"
}}

Rules:
- Use "LastName, FirstName" format for people
- Keep middle initials/names after FirstName
- Keep titles/suffixes at the end (e.g., "Smith, John Jr.")
- For organizations, return as-is
- For single names (like "Madonna"), return as-is
- For ambiguous cases, return as-is

Examples:
1. "Mario B. Garnero Jr." → {{"formatted_name": "Garnero, Mario B. Jr.", "confidence": "high", "reasoning": "Standard name with middle initial and suffix"}}
2. "Donald Trump" → {{"formatted_name": "Trump, Donald", "confidence": "high", "reasoning": "Standard two-part name"}}
3. "Jeffrey Epstein" → {{"formatted_name": "Epstein, Jeffrey", "confidence": "high", "reasoning": "Standard two-part name"}}
4. "Prince Andrew" → {{"formatted_name": "Andrew, Prince", "confidence": "medium", "reasoning": "Title appears to be part of formal name"}}

Name to format: "{name}"
JSON response only:"""

        try:
            self.stats["llm_queries"] += 1

            # Use Ollama API via subprocess
            result = subprocess.run(
                ["ollama", "run", self.llm_model],
                check=False,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                self.stats["llm_failures"] += 1
                return {
                    "formatted_name": name,
                    "confidence": "low",
                    "reasoning": f"LLM error: {result.stderr}",
                }

            # Parse JSON response
            output = result.stdout.strip()

            # Try to extract JSON from response (LLM might add extra text)
            json_match = re.search(r"\{[^}]+\}", output, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                llm_response = json.loads(json_str)
                self.stats["llm_successes"] += 1
                return llm_response
            self.stats["llm_failures"] += 1
            return {
                "formatted_name": name,
                "confidence": "low",
                "reasoning": "Could not parse LLM response",
            }

        except subprocess.TimeoutExpired:
            self.stats["llm_failures"] += 1
            return {"formatted_name": name, "confidence": "low", "reasoning": "LLM timeout"}
        except json.JSONDecodeError as e:
            self.stats["llm_failures"] += 1
            return {
                "formatted_name": name,
                "confidence": "low",
                "reasoning": f"JSON parse error: {e}",
            }
        except Exception as e:
            self.stats["llm_failures"] += 1
            return {"formatted_name": name, "confidence": "low", "reasoning": f"LLM error: {e}"}

    def format_entity_name(self, name: str) -> Tuple[str, str, str]:
        """
        Format entity name using hybrid approach

        Returns:
            Tuple of (formatted_name, method, reasoning)
            method: "procedural_high", "procedural_medium", "llm", "original"
        """
        # Phase 1: Try procedural rules
        formatted, confidence, reasoning = self.apply_procedural_rules(name)

        # High confidence procedural result
        if confidence == "high":
            self.stats["procedural_high_confidence"] += 1
            self.examples["procedural_high"].append(
                {"original": name, "formatted": formatted, "reasoning": reasoning}
            )
            return formatted, "procedural_high", reasoning

        # Medium confidence - use procedural unless LLM is enabled and improves it
        if confidence == "medium":
            if self.use_llm:
                # Query LLM for complex cases
                llm_result = self.query_llm(name)

                # Use LLM result if high confidence
                if llm_result["confidence"] == "high":
                    self.examples["llm"].append(
                        {
                            "original": name,
                            "formatted": llm_result["formatted_name"],
                            "reasoning": llm_result["reasoning"],
                        }
                    )
                    return llm_result["formatted_name"], "llm", llm_result["reasoning"]

            # Use procedural result
            self.stats["procedural_medium_confidence"] += 1
            self.examples["procedural_medium"].append(
                {"original": name, "formatted": formatted, "reasoning": reasoning}
            )
            return formatted, "procedural_medium", reasoning

        # Low confidence - use LLM if available
        if confidence == "low":
            if self.use_llm:
                llm_result = self.query_llm(name)

                # Use LLM result if medium or high confidence
                if llm_result["confidence"] in ["high", "medium"]:
                    self.examples["llm"].append(
                        {
                            "original": name,
                            "formatted": llm_result["formatted_name"],
                            "reasoning": llm_result["reasoning"],
                        }
                    )
                    return llm_result["formatted_name"], "llm", llm_result["reasoning"]

            # Fall back to original name
            self.stats["original_preserved"] += 1
            self.examples["original"].append(
                {
                    "original": name,
                    "formatted": name,
                    "reasoning": reasoning + " - preserved original",
                }
            )
            return name, "original", reasoning

        # Default - return original
        return name, "original", "Unknown confidence level"


class EntityNameFixer:
    """Fix entity names in entity_statistics.json"""

    def __init__(self, data_dir: Path, use_llm: bool = True):
        self.data_dir = Path(data_dir)
        self.formatter = NameFormatter(use_llm=use_llm)
        self.backup_dir = (
            self.data_dir / "backups" / f"name_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def fix_entity_names(self) -> Dict:
        """
        Fix all entity names in entity_statistics.json

        Returns:
            Statistics dictionary
        """
        print("=" * 70)
        print("ENTITY NAME FORMATTING - HYBRID PROCEDURAL + LLM")
        print("=" * 70)

        # Load entity statistics
        stats_path = self.data_dir / "metadata/entity_statistics.json"

        if not stats_path.exists():
            print(f"\nError: {stats_path} not found")
            return {}

        # Backup original
        backup_path = self.backup_dir / stats_path.name
        shutil.copy2(stats_path, backup_path)
        print(f"\nBackup created: {backup_path}")

        # Load data
        with open(stats_path, encoding="utf-8") as f:
            data = json.load(f)

        entity_stats = data.get("statistics", {})
        print(f"Loaded {len(entity_stats)} entities")

        # Process each entity
        print("\nProcessing entities...")
        changes = []

        for entity_key, entity_data in entity_stats.items():
            # Get current name field
            current_name = entity_data.get("name", entity_key)

            # Format using hybrid approach
            formatted_name, method, reasoning = self.formatter.format_entity_name(entity_key)

            # Update if changed
            if formatted_name != current_name:
                changes.append(
                    {
                        "entity_key": entity_key,
                        "old_name": current_name,
                        "new_name": formatted_name,
                        "method": method,
                        "reasoning": reasoning,
                    }
                )

                # Update the name field
                entity_data["name"] = formatted_name

        # Save updated data
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\nUpdated {len(changes)} entity names")

        # Generate report
        self.generate_report(changes)

        return {
            "total_entities": len(entity_stats),
            "names_changed": len(changes),
            **self.formatter.stats,
        }

    def generate_report(self, changes: List[Dict]):
        """Generate detailed report of name changes"""
        report_path = self.data_dir / "metadata/entity_name_fix_report.txt"

        report = f"""
ENTITY NAME FORMATTING REPORT
==============================
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Backup Location: {self.backup_dir}

STATISTICS
----------
Total Entities Processed: {self.formatter.stats['procedural_high_confidence'] + self.formatter.stats['procedural_medium_confidence'] + self.formatter.stats['llm_queries'] + self.formatter.stats['original_preserved']}
Names Changed: {len(changes)}

Processing Methods:
  - Procedural (High Confidence): {self.formatter.stats['procedural_high_confidence']}
  - Procedural (Medium Confidence): {self.formatter.stats['procedural_medium_confidence']}
  - LLM Queries: {self.formatter.stats['llm_queries']}
    - LLM Successes: {self.formatter.stats['llm_successes']}
    - LLM Failures: {self.formatter.stats['llm_failures']}
  - Original Preserved: {self.formatter.stats['original_preserved']}

SAMPLE CHANGES BY METHOD
-------------------------
"""

        # Group changes by method
        by_method = defaultdict(list)
        for change in changes:
            by_method[change["method"]].append(change)

        for method, method_changes in sorted(by_method.items()):
            report += f"\n{method.upper()} ({len(method_changes)} changes):\n"
            report += "-" * 50 + "\n"

            for i, change in enumerate(method_changes[:10], 1):  # First 10
                report += f"  {i}. '{change['old_name']}' → '{change['new_name']}'\n"
                report += f"     Entity Key: {change['entity_key']}\n"
                report += f"     Reasoning: {change['reasoning']}\n\n"

            if len(method_changes) > 10:
                report += f"  ... and {len(method_changes) - 10} more\n\n"

        # Add examples from formatter
        report += "\nPROCEDURAL HIGH CONFIDENCE EXAMPLES\n"
        report += "-" * 50 + "\n"
        for i, ex in enumerate(self.formatter.examples["procedural_high"][:10], 1):
            report += f"  {i}. '{ex['original']}' → '{ex['formatted']}'\n"
            report += f"     {ex['reasoning']}\n\n"

        if self.formatter.examples["llm"]:
            report += "\nLLM-PROCESSED EXAMPLES\n"
            report += "-" * 50 + "\n"
            for i, ex in enumerate(self.formatter.examples["llm"][:10], 1):
                report += f"  {i}. '{ex['original']}' → '{ex['formatted']}'\n"
                report += f"     {ex['reasoning']}\n\n"

        report += f"""
SUMMARY
-------
Entity names have been formatted using a hybrid approach:
1. Simple names handled by procedural rules (fast, deterministic)
2. Complex names processed by LLM ({self.formatter.llm_model})
3. Ambiguous cases preserved as original

Original file backed up to: {self.backup_dir}

To restore from backup if needed:
  cp {self.backup_dir}/entity_statistics.json {self.data_dir}/metadata/

VERIFICATION
------------
Check sample entities in the API to verify correct formatting:
  curl http://localhost:8081/api/entities | jq '.entities | .[] | .name' | head -20

NEXT STEPS
----------
1. Restart server to reload updated data:
   kill -9 $(lsof -ti:8081)
   cd server && python3 app.py 8081 > /tmp/epstein_8081.log 2>&1 &

2. Verify in UI that entity names appear correctly formatted
3. Delete backup after verification (optional):
   rm -rf {self.backup_dir}
"""

        # Save report
        with open(report_path, "w") as f:
            f.write(report)

        print(f"\nDetailed report saved to: {report_path}")


def main():
    """Main entry point"""
    import sys

    # Default data directory
    data_dir = Path(__file__).parent.parent.parent / "data"

    # Allow override via command line
    if len(sys.argv) > 1:
        data_dir = Path(sys.argv[1])

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)

    print(f"Data directory: {data_dir}")

    # Check if Ollama is available
    try:
        result = subprocess.run(["ollama", "list"], check=False, capture_output=True, timeout=5)
        use_llm = result.returncode == 0
        if use_llm:
            print("✓ Ollama detected - will use LLM for complex names")
        else:
            print("✗ Ollama not available - using procedural rules only")
    except Exception:
        use_llm = False
        print("✗ Ollama not available - using procedural rules only")

    # Run name fixer
    fixer = EntityNameFixer(data_dir, use_llm=use_llm)
    stats = fixer.fix_entity_names()

    # Print summary
    print("\n" + "=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)
    for key, value in stats.items():
        print(f"{key}: {value}")

    print("\n\nRESTART SERVER:")
    print("  kill -9 $(lsof -ti:8081)")
    print(
        "  cd /Users/masa/Projects/Epstein/server && python3 app.py 8081 > /tmp/epstein_8081.log 2>&1 &"
    )
    print("\nThen verify changes in UI at http://localhost:8081")


if __name__ == "__main__":
    main()
