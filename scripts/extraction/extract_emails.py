#!/usr/bin/env python3
"""Extract detected emails from OCR results into organized directory.

This script processes email candidates identified during OCR processing
and extracts them into a structured directory with:
- Organized subdirectories by date (YYYY-MM format)
- Metadata JSON with parsed email headers
- Full OCR text and body-only text files

Author: Claude Code (Python Engineer)
Created: 2025-11-16
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class EmailMetadata:
    """Structured email metadata extracted from OCR text."""
    document_id: str
    email_index: int
    extracted_at: str
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    cc_address: Optional[str] = None
    subject: Optional[str] = None
    date: Optional[str] = None
    body: Optional[str] = None
    confidence: float = 0.0
    email_addresses: List[str] = None

    def __post_init__(self):
        if self.email_addresses is None:
            self.email_addresses = []


def load_email_candidates(jsonl_path: Path) -> List[Dict]:
    """Load email candidates from JSONL file."""
    candidates = []
    with open(jsonl_path) as f:
        for line in f:
            if line.strip():
                candidates.append(json.loads(line))
    return candidates


def extract_email_field(text: str, field: str) -> Optional[str]:
    """Extract email header field from text."""
    patterns = [
        rf'{field}:\s*(.+?)(?=\n[A-Z][a-z]+:|$)',
        rf'{field}:\s*(.+?)(?=\n\n|$)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            value = match.group(1).strip()
            # Clean up
            value = re.sub(r'\s+', ' ', value)
            value = re.sub(r'\|+', '', value)
            return value if value else None

    return None


def extract_date(text: str) -> Optional[str]:
    """Extract date from email text."""
    # Try "Date:" or "Sent:" headers first
    for pattern in [r'Date:\s*(.+?)(?=\n|$)', r'Sent:\s*(.+?)(?=\n|$)']:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Try date patterns
    date_patterns = [
        r'(\d{1,2}/\d{1,2}/\d{2,4})',
        r'(\d{4}-\d{2}-\d{2})',
        r'([A-Z][a-z]+\s+\d{1,2},\s*\d{4})',
    ]

    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)

    return None


def parse_date_to_subdirectory(date_str: Optional[str]) -> str:
    """Parse date string to YYYY-MM subdirectory name."""
    if not date_str:
        return "undated"

    try:
        # Extract year
        year_match = re.search(r'(20\d{2}|19\d{2})', date_str)
        if not year_match:
            return "undated"

        year = year_match.group(1)

        # Extract month
        month_match = re.search(r'/(\d{1,2})/', date_str)
        if month_match:
            month = month_match.group(1).zfill(2)
            return f"{year}-{month}"

        month_match = re.search(r'-(\d{2})-', date_str)
        if month_match:
            month = month_match.group(1)
            return f"{year}-{month}"

        # Try month names
        months = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12',
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09',
            'oct': '10', 'nov': '11', 'dec': '12'
        }

        for month_name, month_num in months.items():
            if month_name in date_str.lower():
                return f"{year}-{month_num}"

        return f"{year}-00"

    except Exception as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return "undated"


def extract_email_body(text: str) -> Optional[str]:
    """Extract email body text (content after headers)."""
    header_patterns = ['from:', 'to:', 'cc:', 'subject:', 'date:', 'sent:']
    last_header_pos = 0

    for pattern in header_patterns:
        pos = text.lower().rfind(pattern)
        if pos > last_header_pos:
            last_header_pos = pos

    if last_header_pos == 0:
        return None

    body_start = text.find('\n', last_header_pos)
    if body_start == -1:
        return None

    body = text[body_start:].strip()

    # Remove common footer artifacts
    body = re.sub(r'DOJ-OGR-\d+\s*$', '', body, flags=re.IGNORECASE)
    body = re.sub(r'RFP.*?\d+\s*$', '', body, flags=re.IGNORECASE)

    return body.strip() if body else None


def extract_email_metadata(text: str, candidate: Dict, index: int) -> EmailMetadata:
    """Extract complete email metadata from OCR text."""
    doc_id = Path(candidate.get("file", "unknown")).stem

    metadata = EmailMetadata(
        document_id=doc_id,
        email_index=index,
        extracted_at=datetime.utcnow().isoformat(),
        confidence=candidate.get("confidence", 0.0),
        email_addresses=candidate.get("email_addresses", [])
    )

    metadata.from_address = extract_email_field(text, "From")
    metadata.to_address = extract_email_field(text, "To")
    metadata.cc_address = extract_email_field(text, "CC")
    metadata.subject = extract_email_field(text, "Subject")
    metadata.date = extract_date(text)
    metadata.body = extract_email_body(text)

    return metadata


def save_email(email_dir: Path, metadata: EmailMetadata, ocr_text: str) -> None:
    """Save email with metadata to directory structure."""
    subdirname = parse_date_to_subdirectory(metadata.date)
    subdir = email_dir / subdirname
    subdir.mkdir(parents=True, exist_ok=True)

    # Save metadata JSON
    metadata_path = subdir / f"{metadata.document_id}_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(asdict(metadata), f, indent=2)

    # Save full OCR text
    text_path = subdir / f"{metadata.document_id}_full.txt"
    with open(text_path, 'w') as f:
        f.write(ocr_text)

    # Save body only
    if metadata.body:
        body_path = subdir / f"{metadata.document_id}_body.txt"
        with open(body_path, 'w') as f:
            f.write(metadata.body)


def generate_email_index(email_dir: Path, metadata_list: List[EmailMetadata]) -> Dict:
    """Generate email index with statistics."""
    index = {
        "total_emails": len(metadata_list),
        "extraction_date": datetime.utcnow().isoformat(),
        "by_date": {},
        "by_sender": {},
        "by_confidence": {
            "high": 0,
            "medium": 0,
            "low": 0
        }
    }

    for metadata in metadata_list:
        subdir = parse_date_to_subdirectory(metadata.date)
        index["by_date"][subdir] = index["by_date"].get(subdir, 0) + 1

        if metadata.from_address:
            sender = metadata.from_address[:50]
            index["by_sender"][sender] = index["by_sender"].get(sender, 0) + 1

        if metadata.confidence >= 0.8:
            index["by_confidence"]["high"] += 1
        elif metadata.confidence >= 0.6:
            index["by_confidence"]["medium"] += 1
        else:
            index["by_confidence"]["low"] += 1

    return index


def main():
    """Main extraction workflow."""
    base_dir = Path(__file__).parent.parent.parent
    ocr_text_dir = base_dir / "data" / "sources" / "house_oversight_nov2025" / "ocr_text"
    candidates_file = base_dir / "data" / "sources" / "house_oversight_nov2025" / "email_candidates.jsonl"
    email_output_dir = base_dir / "data" / "emails" / "house_oversight_nov2025"

    email_output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading email candidates from: {candidates_file}")
    candidates = load_email_candidates(candidates_file)
    logger.info(f"Found {len(candidates)} email candidates")

    extracted = 0
    failed = 0
    metadata_list = []

    for i, candidate in enumerate(candidates, 1):
        try:
            file_path = candidate.get("file", "")
            doc_id = Path(file_path).stem

            ocr_text_path = ocr_text_dir / f"{doc_id}.txt"
            if not ocr_text_path.exists():
                logger.warning(f"OCR text file not found: {ocr_text_path}")
                failed += 1
                continue

            with open(ocr_text_path) as f:
                ocr_text = f.read()

            if not ocr_text:
                logger.warning(f"Empty OCR text for {doc_id}")
                failed += 1
                continue

            metadata = extract_email_metadata(ocr_text, candidate, i)
            save_email(email_output_dir, metadata, ocr_text)
            metadata_list.append(metadata)
            extracted += 1

            if i % 50 == 0:
                logger.info(f"Progress: {i}/{len(candidates)} ({extracted} extracted, {failed} failed)")

        except Exception as e:
            logger.error(f"Error processing {candidate.get('file')}: {e}")
            failed += 1

    logger.info(f"\nExtraction complete!")
    logger.info(f"Total: {len(candidates)} | Extracted: {extracted} | Failed: {failed}")

    # Generate email index
    email_index = generate_email_index(email_output_dir, metadata_list)
    index_path = email_output_dir / "EMAIL_INDEX.json"
    with open(index_path, 'w') as f:
        json.dump(email_index, f, indent=2)

    logger.info(f"Email index saved to: {index_path}")

    # Generate summary report
    summary_path = email_output_dir / "EXTRACTION_SUMMARY.md"
    with open(summary_path, 'w') as f:
        f.write(f"# Email Extraction Summary\n\n")
        f.write(f"**Extraction Date**: {datetime.utcnow().isoformat()}\n\n")
        f.write(f"## Statistics\n\n")
        f.write(f"- **Total candidates**: {len(candidates)}\n")
        f.write(f"- **Successfully extracted**: {extracted}\n")
        f.write(f"- **Failed**: {failed}\n")
        f.write(f"- **Success rate**: {extracted/len(candidates)*100:.1f}%\n\n")

        f.write(f"## Confidence Distribution\n\n")
        f.write(f"- **High (≥0.8)**: {email_index['by_confidence']['high']} emails\n")
        f.write(f"- **Medium (≥0.6)**: {email_index['by_confidence']['medium']} emails\n")
        f.write(f"- **Low (<0.6)**: {email_index['by_confidence']['low']} emails\n\n")

        f.write(f"## Date Distribution\n\n")
        sorted_dates = sorted(email_index['by_date'].items())
        for date_dir, count in sorted_dates:
            f.write(f"- **{date_dir}**: {count} emails\n")

        f.write(f"\n## Top Senders\n\n")
        sorted_senders = sorted(email_index['by_sender'].items(), key=lambda x: x[1], reverse=True)
        for sender, count in sorted_senders[:20]:
            f.write(f"- **{sender}**: {count} emails\n")

        f.write(f"\n## Output Structure\n\n```\n")
        f.write(f"data/emails/house_oversight_nov2025/\n")
        f.write(f"├── YYYY-MM/\n")
        f.write(f"│   ├── DOC-ID_metadata.json\n")
        f.write(f"│   ├── DOC-ID_full.txt\n")
        f.write(f"│   └── DOC-ID_body.txt\n")
        f.write(f"└── undated/\n```\n")

    logger.info(f"Summary report saved to: {summary_path}")
    logger.info("\n✅ Email extraction complete!")


if __name__ == "__main__":
    main()
