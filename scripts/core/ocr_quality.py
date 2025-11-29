"""
OCR Quality Assessment

Calculates quality scores for OCR'd documents using multiple metrics:
1. Dictionary word matching
2. Character corruption detection (mojibake)
3. Line break consistency
4. Whitespace normalization
"""

import re
import unicodedata
from pathlib import Path


class OCRQualityAssessor:
    """
    Assess OCR quality of extracted text.

    Design Decision: Multi-Metric Assessment
    Rationale: Single metric insufficient to judge OCR quality.
    Combines multiple signals:
    - Word dictionary matching (lexical correctness)
    - Character corruption (encoding issues)
    - Line breaks (layout preservation)

    Trade-offs:
    - Performance: Multiple checks slower vs. better accuracy
    - Threshold: Quality score affects version selection
    - Dictionary: English-only vs. multi-language support

    Optimization Opportunity:
    - Cache dictionary lookups
    - Use Bloom filter for word dictionary (faster membership testing)
    """

    def __init__(self, dictionary_path: Optional[Path] = None):
        """
        Initialize OCR quality assessor.

        Args:
            dictionary_path: Path to word dictionary file (one word per line)
                           If None, uses built-in common words
        """
        self.dictionary = self._load_dictionary(dictionary_path)

    def _load_dictionary(self, dictionary_path: Optional[Path]) -> set[str]:
        """
        Load word dictionary for lexical validation.

        Performance: O(n) where n is dictionary size.
        Memory: ~10MB for 100,000 words (English dictionary).
        """
        if dictionary_path and dictionary_path.exists():
            with open(dictionary_path) as f:
                return {line.strip().lower() for line in f if line.strip()}

        # Built-in common words (reduced set for performance)
        return {
            "the",
            "be",
            "to",
            "of",
            "and",
            "a",
            "in",
            "that",
            "have",
            "i",
            "it",
            "for",
            "not",
            "on",
            "with",
            "he",
            "as",
            "you",
            "do",
            "at",
            "this",
            "but",
            "his",
            "by",
            "from",
            "they",
            "we",
            "say",
            "her",
            "she",
            "or",
            "an",
            "will",
            "my",
            "one",
            "all",
            "would",
            "there",
            "their",
            "email",
            "subject",
            "sent",
            "date",
            "cc",
            "bcc",
            "dear",
            "sincerely",
            "regards",
            "thank",
            "please",
            "attached",
            # Common legal terms
            "court",
            "judge",
            "case",
            "defendant",
            "plaintiff",
            "attorney",
            "subpoena",
            "deposition",
            "motion",
            "order",
            "counsel",
            # Common names in Epstein docs
            "epstein",
            "maxwell",
            "giuffre",
            "clinton",
            "trump",
            "andrew",
        }

    def assess(self, text: str) -> dict[str, float]:
        """
        Assess OCR quality of text.

        Args:
            text: Extracted text from OCR

        Returns:
            Dictionary with quality metrics:
            {
                'word_score': 0.0-1.0,
                'corruption_score': 0.0-1.0,
                'line_score': 0.0-1.0,
                'overall_score': 0.0-1.0
            }

        Usage:
            assessor = OCRQualityAssessor()
            quality = assessor.assess(ocr_text)
            print(f"Overall quality: {quality['overall_score']:.2f}")
        """
        # Individual metrics
        word_score = self._assess_word_quality(text)
        corruption_score = self._assess_corruption(text)
        line_score = self._assess_line_breaks(text)

        # Weighted combination
        overall_score = word_score * 0.5 + corruption_score * 0.3 + line_score * 0.2

        return {
            "word_score": word_score,
            "corruption_score": corruption_score,
            "line_score": line_score,
            "overall_score": overall_score,
        }

    def _assess_word_quality(self, text: str) -> float:
        """
        Assess quality based on dictionary word matching.

        Metric: Percentage of words found in dictionary.
        High score = most words are valid English words.
        Low score = lots of OCR garbage.

        Performance: O(n * m) where n = num words, m = avg word length
        Optimization: Use Bloom filter for O(n) average case
        """
        words = self._extract_words(text)

        if not words:
            return 0.0

        valid_words = sum(1 for word in words if self._is_valid_word(word))

        return valid_words / len(words)

    def _extract_words(self, text: str) -> list:
        """
        Extract words from text.

        Filters out:
        - Very short words (<2 chars)
        - Numbers
        - Special characters

        Returns:
            List of normalized words
        """
        # Extract alphanumeric sequences
        words = re.findall(r"\b[a-z]+\b", text.lower())

        # Filter short words and numbers
        words = [w for w in words if len(w) >= 2 and not w.isdigit()]

        return words

    def _is_valid_word(self, word: str) -> bool:
        """
        Check if word is valid (in dictionary or looks valid).

        Args:
            word: Lowercase word

        Returns:
            True if valid
        """
        # In dictionary
        if word in self.dictionary:
            return True

        # Common patterns that look valid
        # Email addresses, URLs, file extensions
        if "@" in word or "." in word or word.endswith((".com", ".org", ".pdf")):
            return True

        # Common abbreviations (all caps, 2-4 chars)
        if word.isupper() and 2 <= len(word) <= 4:
            return True

        # Numbers with letters (dates, IDs, etc.)
        return bool(any(c.isdigit() for c in word) and any(c.isalpha() for c in word))

    def _assess_corruption(self, text: str) -> float:
        """
        Detect character corruption (mojibake, encoding errors).

        Checks for:
        - Unexpected Unicode characters
        - Control characters
        - Replacement characters (�)
        - Excessive special characters

        Returns:
            Score (0.0-1.0), where 1.0 = no corruption
        """
        if not text:
            return 0.0

        corruption_count = 0
        total_chars = len(text)

        for char in text:
            # Replacement character (�)
            if char == "\ufffd":
                corruption_count += 5  # Heavy penalty

            # Control characters (except newline, tab)
            elif unicodedata.category(char).startswith("C") and char not in "\n\t\r":
                corruption_count += 3

            # Unexpected unicode categories
            category = unicodedata.category(char)
            if category in ("Co", "Cn"):  # Private use, not assigned
                corruption_count += 2

        # Calculate corruption rate
        corruption_rate = corruption_count / total_chars if total_chars > 0 else 0

        # Convert to score (inverse of corruption rate)
        score = max(0.0, 1.0 - corruption_rate * 10)  # Scale up for sensitivity

        return score

    def _assess_line_breaks(self, text: str) -> float:
        """
        Assess line break consistency.

        Good OCR maintains proper line breaks.
        Poor OCR breaks lines randomly or inconsistently.

        Metrics:
        - Average line length consistency
        - Proper paragraph breaks
        - No mid-word breaks

        Returns:
            Score (0.0-1.0)
        """
        if not text:
            return 0.0

        lines = text.split("\n")

        if len(lines) < 2:
            return 1.0  # Single line, no breaks to assess

        # Calculate line length variance
        lengths = [len(line) for line in lines if line.strip()]

        if not lengths:
            return 0.0

        avg_length = sum(lengths) / len(lengths)

        # Check for mid-word breaks (lines ending without punctuation)
        mid_word_breaks = sum(
            1
            for line in lines
            if line
            and not line.rstrip().endswith((".", "!", "?", ":", ";", ","))
            and len(line) > 10
        )

        # Score based on consistency
        # Prefer documents with consistent line lengths or proper breaks
        variance_score = min(1.0, avg_length / 100)  # Longer lines often better
        break_score = 1.0 - (mid_word_breaks / max(len(lines), 1))

        return (variance_score + break_score) / 2

    def categorize_quality(self, score: float) -> str:
        """
        Categorize quality score into human-readable levels.

        Args:
            score: Quality score (0.0-1.0)

        Returns:
            'high'|'medium'|'low'
        """
        if score >= 0.9:
            return "high"
        if score >= 0.7:
            return "medium"
        return "low"


def calculate_ocr_quality(text: str) -> tuple[float, str]:
    """
    Convenience function to calculate OCR quality.

    Args:
        text: Extracted text

    Returns:
        Tuple of (score, category)

    Usage:
        score, category = calculate_ocr_quality(ocr_text)
        print(f"Quality: {category} ({score:.2f})")
    """
    assessor = OCRQualityAssessor()
    metrics = assessor.assess(text)
    score = metrics["overall_score"]
    category = assessor.categorize_quality(score)

    return score, category


if __name__ == "__main__":
    # Example usage
    assessor = OCRQualityAssessor()

    # High quality text
    high_quality = """
    This is a well-formatted email with proper line breaks and clear text.
    The OCR quality is excellent with no corruption or artifacts.
    All words are properly recognized and the layout is preserved.
    """

    # Low quality text (simulated poor OCR)
    low_quality = """
    Th1s i5 a p00r1y
    0CR'd d0cum3nt w1th
    many err0rs and c0rrupt10n.
    L1n3s ar3 br0k3n r4nd0m1y.
    """

    for name, text in [("High Quality", high_quality), ("Low Quality", low_quality)]:
        metrics = assessor.assess(text)
        category = assessor.categorize_quality(metrics["overall_score"])

        print(f"\n{name}:")
        print(f"  Overall Score: {metrics['overall_score']:.2f} ({category})")
        print(f"  Word Score: {metrics['word_score']:.2f}")
        print(f"  Corruption Score: {metrics['corruption_score']:.2f}")
        print(f"  Line Score: {metrics['line_score']:.2f}")
