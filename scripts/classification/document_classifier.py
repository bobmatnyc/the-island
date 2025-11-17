#!/usr/bin/env python3
"""
Document Classification System for Epstein Archive
Classifies documents into 11 primary categories with confidence scoring
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple


class DocumentType(Enum):
    """Document classification categories"""
    EMAIL = "email"
    COURT_FILING = "court_filing"
    FINANCIAL = "financial"
    FLIGHT_LOG = "flight_log"
    CONTACT_BOOK = "contact_book"
    INVESTIGATIVE = "investigative"
    LEGAL_AGREEMENT = "legal_agreement"
    PERSONAL = "personal"
    MEDIA = "media"
    ADMINISTRATIVE = "administrative"
    UNKNOWN = "unknown"

@dataclass
class ClassificationResult:
    """Result of document classification"""
    document_type: DocumentType
    confidence: float
    secondary_types: List[Tuple[DocumentType, float]]
    keywords_found: List[str]
    metadata: Dict

class DocumentClassifier:
    """Classifies documents based on content analysis"""

    # Keyword patterns for each document type
    PATTERNS = {
        DocumentType.EMAIL: {
            "keywords": [
                r"From:\s*[\w\s@.-]+",
                r"To:\s*[\w\s@.-]+",
                r"Subject:\s*.+",
                r"Date:\s*\d{1,2}/\d{1,2}/\d{2,4}",
                r"Sent:\s*\w+",
                r"CC:\s*[\w\s@.-]+",
                r"@\w+\.\w+",  # Email addresses
                r"Re:\s*.+",
                r"Fwd:\s*.+"
            ],
            "weight": 1.0,
            "min_matches": 3
        },
        DocumentType.COURT_FILING: {
            "keywords": [
                r"UNITED STATES DISTRICT COURT",
                r"SOUTHERN DISTRICT OF",
                r"CASE NO\.",
                r"Plaintiff[s]?",
                r"Defendant[s]?",
                r"MOTION TO",
                r"COMPLAINT",
                r"DEPOSITION",
                r"AFFIDAVIT",
                r"EXHIBIT\s+[A-Z0-9]+",
                r"WHEREFORE",
                r"Respectfully submitted",
                r"DECLARATION OF",
                r"COMES NOW",
                r"v\.",  # versus in case names
                r"Counsel for"
            ],
            "weight": 1.0,
            "min_matches": 4
        },
        DocumentType.FINANCIAL: {
            "keywords": [
                r"\$[\d,]+\.?\d*",  # Dollar amounts
                r"INVOICE",
                r"STATEMENT",
                r"WIRE TRANSFER",
                r"ACCOUNT NUMBER",
                r"ROUTING NUMBER",
                r"TAX RETURN",
                r"BALANCE",
                r"PAYMENT",
                r"TRANSACTION",
                r"CREDIT",
                r"DEBIT",
                r"JPMorgan",
                r"Deutsche Bank",
                r"Chase",
                r"SWIFT"
            ],
            "weight": 0.9,
            "min_matches": 3
        },
        DocumentType.FLIGHT_LOG: {
            "keywords": [
                r"PASSENGER",
                r"DEPARTURE",
                r"ARRIVAL",
                r"AIRCRAFT",
                r"TAIL NUMBER",
                r"N\d{3,5}[A-Z]{1,2}",  # Tail number pattern
                r"FLIGHT\s+LOG",
                r"MANIFEST",
                r"CREW",
                r"ROUTE",
                r"TEB",  # Teterboro Airport
                r"PBI",  # Palm Beach Airport
                r"Gulfstream"
            ],
            "weight": 1.0,
            "min_matches": 4
        },
        DocumentType.CONTACT_BOOK: {
            "keywords": [
                r"ADDRESS BOOK",
                r"CONTACTS",
                r"PHONE:\s*[\d\s\-\(\)]+",
                r"MOBILE:\s*[\d\s\-\(\)]+",
                r"EMAIL:\s*[\w@.-]+",
                r"ADDRESS:",
                r"FAX:\s*[\d\s\-\(\)]+",
                r"ASSISTANT:",
                r"BLACK BOOK",
                r"LITTLE BLACK BOOK"
            ],
            "weight": 1.0,
            "min_matches": 4
        },
        DocumentType.INVESTIGATIVE: {
            "keywords": [
                r"FBI",
                r"INVESTIGATION",
                r"AGENT",
                r"INTERVIEW",
                r"WITNESS",
                r"EVIDENCE",
                r"SURVEILLANCE",
                r"SUBPOENA",
                r"GRAND JURY",
                r"SEARCH WARRANT",
                r"PROBABLE CAUSE",
                r"CONFIDENTIAL",
                r"CLASSIFIED"
            ],
            "weight": 0.95,
            "min_matches": 3
        },
        DocumentType.LEGAL_AGREEMENT: {
            "keywords": [
                r"AGREEMENT",
                r"CONTRACT",
                r"WHEREAS",
                r"NOW THEREFORE",
                r"PARTY OF THE FIRST PART",
                r"CONSIDERATION",
                r"NON-DISCLOSURE",
                r"NDA",
                r"SETTLEMENT",
                r"INDEMNIFICATION",
                r"BINDING",
                r"EXECUTED THIS"
            ],
            "weight": 0.95,
            "min_matches": 4
        },
        DocumentType.PERSONAL: {
            "keywords": [
                r"DIARY",
                r"JOURNAL",
                r"PERSONAL NOTE",
                r"BIRTHDAY",
                r"CALENDAR",
                r"SCHEDULE",
                r"APPOINTMENT",
                r"REMINDER",
                r"TO DO",
                r"MEMO TO SELF"
            ],
            "weight": 0.85,
            "min_matches": 2
        },
        DocumentType.MEDIA: {
            "keywords": [
                r"PRESS RELEASE",
                r"NEWS ARTICLE",
                r"JOURNALIST",
                r"REPORTER",
                r"PUBLICATION",
                r"New York Times",
                r"Washington Post",
                r"Bloomberg",
                r"Miami Herald",
                r"INTERVIEW TRANSCRIPT",
                r"ON THE RECORD"
            ],
            "weight": 0.9,
            "min_matches": 2
        },
        DocumentType.ADMINISTRATIVE: {
            "keywords": [
                r"MEMORANDUM",
                r"POLICY",
                r"PROCEDURE",
                r"GUIDELINES",
                r"INTERNAL",
                r"HR",
                r"EMPLOYEE",
                r"STAFF",
                r"OFFICE",
                r"ADMINISTRATIVE"
            ],
            "weight": 0.8,
            "min_matches": 2
        }
    }

    def __init__(self):
        """Initialize classifier"""
        self.compiled_patterns = {}
        for doc_type, config in self.PATTERNS.items():
            self.compiled_patterns[doc_type] = {
                "patterns": [re.compile(pattern, re.IGNORECASE) for pattern in config["keywords"]],
                "weight": config["weight"],
                "min_matches": config["min_matches"]
            }

    def classify(self, text: str, filename: str = "") -> ClassificationResult:
        """
        Classify a document based on its text content

        Args:
            text: Document text content
            filename: Optional filename for additional context

        Returns:
            ClassificationResult with primary and secondary classifications
        """
        scores = {}
        keywords_found = {}

        # Score each document type
        for doc_type, config in self.compiled_patterns.items():
            matches = []
            for pattern in config["patterns"]:
                if pattern.search(text):
                    matches.append(pattern.pattern)

            match_count = len(matches)

            # Calculate confidence score
            if match_count >= config["min_matches"]:
                # Confidence based on match percentage and weight
                max_possible = len(config["patterns"])
                match_ratio = match_count / max_possible
                confidence = match_ratio * config["weight"]
                scores[doc_type] = confidence
                keywords_found[doc_type] = matches
            else:
                scores[doc_type] = 0.0

        # Filename-based hints
        filename_lower = filename.lower()
        if "email" in filename_lower:
            scores[DocumentType.EMAIL] = scores.get(DocumentType.EMAIL, 0) + 0.2
        if "flight" in filename_lower or "manifest" in filename_lower:
            scores[DocumentType.FLIGHT_LOG] = scores.get(DocumentType.FLIGHT_LOG, 0) + 0.2
        if "black_book" in filename_lower or "contact" in filename_lower:
            scores[DocumentType.CONTACT_BOOK] = scores.get(DocumentType.CONTACT_BOOK, 0) + 0.2

        # Sort by confidence
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Primary classification
        if sorted_scores[0][1] > 0.0:
            primary_type = sorted_scores[0][0]
            primary_confidence = sorted_scores[0][1]
        else:
            primary_type = DocumentType.UNKNOWN
            primary_confidence = 0.0

        # Secondary classifications (confidence > 0.3)
        secondary_types = [
            (doc_type, confidence)
            for doc_type, confidence in sorted_scores[1:6]
            if confidence > 0.3
        ]

        return ClassificationResult(
            document_type=primary_type,
            confidence=min(1.0, primary_confidence),  # Cap at 1.0
            secondary_types=secondary_types,
            keywords_found=keywords_found.get(primary_type, []),
            metadata={
                "all_scores": {dt.value: score for dt, score in sorted_scores},
                "filename": filename
            }
        )

    def classify_file(self, filepath: Path) -> ClassificationResult:
        """Classify a file by reading its content"""
        try:
            text = filepath.read_text(encoding="utf-8", errors="ignore")
            return self.classify(text, filepath.name)
        except Exception as e:
            return ClassificationResult(
                document_type=DocumentType.UNKNOWN,
                confidence=0.0,
                secondary_types=[],
                keywords_found=[],
                metadata={"error": str(e), "filename": str(filepath)}
            )

    def classify_batch(self, filepaths: List[Path]) -> Dict[str, ClassificationResult]:
        """Classify multiple files"""
        results = {}
        for filepath in filepaths:
            results[str(filepath)] = self.classify_file(filepath)
        return results

def generate_classification_report(results: Dict[str, ClassificationResult]) -> str:
    """Generate a human-readable classification report"""

    # Count by type
    type_counts = {}
    for result in results.values():
        doc_type = result.document_type
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

    # Generate report
    report = ["DOCUMENT CLASSIFICATION REPORT", "=" * 70, ""]
    report.append(f"Total documents classified: {len(results)}")
    report.append("")
    report.append("Classification breakdown:")
    for doc_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(results)) * 100
        report.append(f"  {doc_type.value:20s}: {count:5d} ({percentage:5.1f}%)")

    report.append("")
    report.append("High-confidence classifications (>0.8):")
    high_conf = [
        (path, result)
        for path, result in results.items()
        if result.confidence > 0.8
    ]
    report.append(f"  Count: {len(high_conf)}")

    report.append("")
    report.append("Low-confidence classifications (<0.5):")
    low_conf = [
        (path, result)
        for path, result in results.items()
        if result.confidence < 0.5
    ]
    report.append(f"  Count: {len(low_conf)} (require manual review)")

    return "\n".join(report)

def main():
    """Example usage"""
    classifier = DocumentClassifier()

    # Test classification
    test_email = """
    From: john.doe@example.com
    To: jane.smith@company.com
    Subject: Meeting Tomorrow
    Date: 01/15/2024

    Hi Jane,

    Let's meet tomorrow at 3pm to discuss the project.

    Best,
    John
    """

    result = classifier.classify(test_email, "email_example.txt")
    print(f"Document Type: {result.document_type.value}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Keywords Found: {result.keywords_found[:5]}")

if __name__ == "__main__":
    main()
