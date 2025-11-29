#!/usr/bin/env python3
"""
Convert Epstein email page text files to individual markdown documents.

Based on Research agent's analysis: 17 distinct documents spanning 87 pages.
Extracts metadata, cleans OCR artifacts, and creates structured markdown files.
"""

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class DocumentMetadata:
    """Metadata for a single document."""

    document_id: int
    doc_type: str
    pages: list[int]
    source: str = "Public Records Request 19-372"

    # Email-specific fields
    from_field: Optional[str] = None
    to_field: Optional[str] = None
    cc_field: Optional[str] = None
    date: Optional[str] = None
    subject: Optional[str] = None

    # Legal document fields
    case_number: Optional[str] = None
    court: Optional[str] = None
    attorney: Optional[str] = None

    # Cross-references
    annotations: Optional[list[dict]] = None
    references: Optional[list[str]] = None

    def to_frontmatter(self) -> str:
        """Convert metadata to YAML frontmatter."""
        lines = ["---"]
        lines.append(f"document_id: {self.document_id}")
        lines.append(f"type: {self.doc_type}")

        if self.from_field:
            lines.append(f'from: "{self.from_field}"')
        if self.to_field:
            lines.append(f'to: "{self.to_field}"')
        if self.cc_field:
            lines.append(f'cc: "{self.cc_field}"')
        if self.date:
            lines.append(f'date: "{self.date}"')
        if self.subject:
            lines.append(f'subject: "{self.subject}"')
        if self.case_number:
            lines.append(f'case_number: "{self.case_number}"')
        if self.court:
            lines.append(f'court: "{self.court}"')
        if self.attorney:
            lines.append(f'attorney: "{self.attorney}"')

        lines.append(f"pages: {self.pages}")
        lines.append(f'source: "{self.source}"')

        if self.annotations:
            lines.append("annotations:")
            for note in self.annotations:
                lines.append(f"  - page: {note['page_number']}")
                lines.append(f"    title: \"{note['title']}\"")

        if self.references:
            lines.append("references:")
            for ref in self.references:
                lines.append(f'  - "{ref}"')

        lines.append("---")
        return "\n".join(lines)


class DocumentExtractor:
    """Extract and convert documents from page text files."""

    # Document definitions based on Research agent's analysis
    DOCUMENTS = [
        {
            "id": 1,
            "type": "Email",
            "pages": range(1, 6),
            "subject": "RE: Epstein",
            "category": "emails",
        },
        {
            "id": 2,
            "type": "Email",
            "pages": range(6, 9),
            "subject": "FW: Confidential",
            "category": "emails",
        },
        {
            "id": 3,
            "type": "Letter",
            "pages": range(9, 11),
            "subject": "Flight logs letter",
            "category": "legal",
        },
        {
            "id": 4,
            "type": "Invoice",
            "pages": range(11, 16),
            "subject": "Flight service invoices",
            "category": "records",
        },
        {
            "id": 5,
            "type": "Subpoena",
            "pages": range(16, 18),
            "subject": "Flight logs subpoena",
            "category": "legal",
        },
        {
            "id": 6,
            "type": "Report",
            "pages": range(18, 20),
            "subject": "DAVID Summary - Criminal database",
            "category": "records",
        },
        {
            "id": 7,
            "type": "Subpoena",
            "pages": [20],
            "subject": "Investigation assignment",
            "category": "legal",
        },
        {
            "id": 8,
            "type": "Note",
            "pages": [21],
            "subject": "Address location",
            "category": "notes",
        },
        {
            "id": 9,
            "type": "Report",
            "pages": range(22, 42),
            "subject": "FACTS Report - Background check",
            "category": "records",
        },
        {
            "id": 10,
            "type": "Letter",
            "pages": range(42, 46),
            "subject": "Legal correspondence",
            "category": "legal",
        },
        {
            "id": 11,
            "type": "Memo",
            "pages": range(46, 55),
            "subject": "State Attorney memo",
            "category": "legal",
        },
        {
            "id": 12,
            "type": "Directions",
            "pages": [55],
            "subject": "Driving directions",
            "category": "notes",
        },
        {
            "id": 13,
            "type": "Subpoena",
            "pages": [56],
            "subject": "Legal subpoena",
            "category": "legal",
        },
        {
            "id": 14,
            "type": "Memo",
            "pages": [57],
            "subject": "State Attorney document",
            "category": "legal",
        },
        {
            "id": 15,
            "type": "Subpoena",
            "pages": range(58, 60),
            "subject": "Legal subpoena",
            "category": "legal",
        },
        {
            "id": 16,
            "type": "Memo",
            "pages": range(60, 69),
            "subject": "Impeachment Material",
            "category": "legal",
        },
        {
            "id": 17,
            "type": "Email",
            "pages": range(69, 88),
            "subject": "RE: Meeting with Epstein's attorneys",
            "category": "emails",
        },
    ]

    def __init__(self, pages_dir: Path, notes_file: Path, output_dir: Path):
        self.pages_dir = pages_dir
        self.notes_file = notes_file
        self.output_dir = output_dir
        self.notes = self._load_notes()

    def _load_notes(self) -> list[dict]:
        """Load annotation notes from JSON file."""
        with open(self.notes_file) as f:
            data = json.load(f)
            return data.get("results", [])

    def _read_page(self, page_num: int) -> str:
        """Read text from a single page file."""
        page_file = self.pages_dir / f"page-{page_num:03d}.txt"
        if not page_file.exists():
            return ""
        with open(page_file, encoding="utf-8") as f:
            return f.read()

    def _clean_ocr_text(self, text: str) -> str:
        """Clean common OCR artifacts."""
        # Remove page headers
        text = re.sub(r"^Page \d+ of \d+\s*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"^Con?dential Page \d+ of \d+\s*$", "", text, flags=re.MULTILINE)

        # Fix common OCR errors
        text = text.replace("?", "'")  # Smart quotes OCR error
        text = text.replace("?le", "file")
        text = text.replace("fonivarding", "forwarding")
        text = text.replace("ankie", "ankle")
        text = text.replace("tetter", "letter")
        text = text.replace("eise", "else")

        # Clean up extra whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)

        return text.strip()

    def _extract_email_metadata(self, text: str) -> dict[str, Optional[str]]:
        """Extract email headers from text."""
        metadata = {
            "from_field": None,
            "to_field": None,
            "cc_field": None,
            "date": None,
            "subject": None,
        }

        # Extract From
        from_match = re.search(r"^From:\s*(.+?)$", text, re.MULTILINE)
        if from_match:
            metadata["from_field"] = from_match.group(1).strip()

        # Extract To
        to_match = re.search(r"^To:\s*(.+?)$", text, re.MULTILINE)
        if to_match:
            metadata["to_field"] = to_match.group(1).strip()

        # Extract Cc
        cc_match = re.search(r"^Cc:\s*(.+?)$", text, re.MULTILINE)
        if cc_match:
            metadata["cc_field"] = cc_match.group(1).strip()

        # Extract Date (Sent line)
        date_match = re.search(r"^Sent:\s*(.+?)$", text, re.MULTILINE)
        if date_match:
            metadata["date"] = date_match.group(1).strip()

        # Extract Subject
        subject_match = re.search(r"^Subject:\s*(.+?)$", text, re.MULTILINE)
        if subject_match:
            metadata["subject"] = subject_match.group(1).strip()

        return metadata

    def _extract_case_references(self, text: str) -> list[str]:
        """Extract case numbers and document references."""
        references = []

        # Case numbers (various formats)
        case_patterns = [
            r"Case No[.:]?\s*([A-Z0-9-]+)",
            r"Case Number[:]?\s*([A-Z0-9-]+)",
            r"\b(\d{2}-\d{4,6}[A-Z]*)\b",  # e.g., 19-372
        ]

        for pattern in case_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                ref = match.group(1).strip()
                if ref not in references:
                    references.append(ref)

        return references

    def _get_annotations_for_pages(self, pages: list[int]) -> list[dict]:
        """Get all annotations that apply to the given page range."""
        annotations = []
        for note in self.notes:
            if note["page_number"] in pages:
                annotations.append(
                    {
                        "page_number": note["page_number"],
                        "title": note["title"],
                        "content": note.get("content", ""),
                    }
                )
        return annotations

    def _create_filename(
        self, doc_id: int, doc_type: str, subject: str, date: Optional[str]
    ) -> str:
        """Generate descriptive filename."""
        # Create slug from subject
        slug = re.sub(r"[^\w\s-]", "", subject.lower())
        slug = re.sub(r"[-\s]+", "-", slug)
        slug = slug[:50]  # Limit length

        # Extract date for filename if available
        date_str = ""
        if date:
            # Try to parse date
            date_patterns = [
                (r"(\w+ \d{1,2}, \d{4})", "%B %d, %Y"),  # April 01, 2010
                (r"(\d{1,2}/\d{1,2}/\d{4})", "%m/%d/%Y"),  # 4/1/2010
            ]
            for pattern, fmt in date_patterns:
                match = re.search(pattern, date)
                if match:
                    try:
                        dt = datetime.strptime(match.group(1), fmt)
                        date_str = dt.strftime("%Y-%m-%d")
                        break
                    except:
                        pass

        # Build filename
        parts = [f"{doc_id:03d}", doc_type.lower()]
        if date_str:
            parts.append(date_str)
        parts.append(slug)

        return "_".join(parts) + ".md"

    def extract_document(self, doc_def: dict) -> tuple[str, str, DocumentMetadata]:
        """Extract a single document and return (filename, content, metadata)."""
        doc_id = doc_def["id"]
        doc_type = doc_def["type"]
        pages = list(doc_def["pages"])
        category = doc_def["category"]

        print(f"Extracting Document {doc_id}: {doc_type} (pages {pages[0]}-{pages[-1]})")

        # Read all pages for this document
        raw_text = ""
        for page_num in pages:
            page_text = self._read_page(page_num)
            raw_text += page_text + "\n\n"

        # Clean OCR artifacts
        cleaned_text = self._clean_ocr_text(raw_text)

        # Extract metadata based on document type
        metadata = DocumentMetadata(
            document_id=doc_id,
            doc_type=doc_type,
            pages=pages,
        )

        if doc_type == "Email":
            email_meta = self._extract_email_metadata(cleaned_text)
            metadata.from_field = email_meta["from_field"]
            metadata.to_field = email_meta["to_field"]
            metadata.cc_field = email_meta["cc_field"]
            metadata.date = email_meta["date"]
            metadata.subject = email_meta["subject"] or doc_def["subject"]
        else:
            metadata.subject = doc_def["subject"]

        # Extract references
        metadata.references = self._extract_case_references(cleaned_text)

        # Add annotations
        annotations = self._get_annotations_for_pages(pages)
        if annotations:
            metadata.annotations = annotations

        # Create filename
        filename = self._create_filename(
            doc_id, doc_type, metadata.subject or doc_def["subject"], metadata.date
        )

        # Build markdown content
        content_lines = [metadata.to_frontmatter(), ""]

        # Add title
        title = metadata.subject or doc_def["subject"]
        content_lines.append(f"# {title}")
        content_lines.append("")

        # Add document body
        content_lines.append(cleaned_text)

        content = "\n".join(content_lines)

        return filename, content, metadata, category

    def extract_all(self) -> dict:
        """Extract all documents and return statistics."""
        stats = {
            "total_documents": len(self.DOCUMENTS),
            "emails": 0,
            "legal_docs": 0,
            "records": 0,
            "notes": 0,
            "annotations_applied": 0,
            "files_created": [],
            "issues": [],
        }

        category_counts = defaultdict(int)

        for doc_def in self.DOCUMENTS:
            try:
                filename, content, metadata, category = self.extract_document(doc_def)

                # Save to appropriate subdirectory
                output_file = self.output_dir / category / filename
                output_file.parent.mkdir(parents=True, exist_ok=True)

                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(content)

                stats["files_created"].append(str(output_file.relative_to(self.output_dir.parent)))
                category_counts[category] += 1

                if metadata.annotations:
                    stats["annotations_applied"] += len(metadata.annotations)

            except Exception as e:
                error_msg = f"Error processing document {doc_def['id']}: {e!s}"
                print(f"ERROR: {error_msg}")
                stats["issues"].append(error_msg)

        stats["emails"] = category_counts["emails"]
        stats["legal_docs"] = category_counts["legal"]
        stats["records"] = category_counts["records"]
        stats["notes"] = category_counts["notes"]

        return stats


def create_index_file(output_dir: Path, stats: dict):
    """Create INDEX.md with document catalog."""

    index_lines = [
        "# Epstein Emails Document Index",
        "",
        "Source: Public Records Request No. 19-372",
        "",
        "## Summary Statistics",
        "",
        f"- **Total Documents**: {stats['total_documents']}",
        f"- **Emails**: {stats['emails']}",
        f"- **Legal Documents**: {stats['legal_docs']}",
        f"- **Records/Reports**: {stats['records']}",
        f"- **Notes**: {stats['notes']}",
        f"- **Annotations Applied**: {stats['annotations_applied']}",
        "",
        "## Document Catalog",
        "",
    ]

    # Group files by category
    categories = {"emails": [], "legal": [], "records": [], "notes": []}

    for filepath in sorted(stats["files_created"]):
        for category in categories:
            if f"/{category}/" in filepath:
                categories[category].append(filepath)
                break

    # Add each category
    category_titles = {
        "emails": "Emails",
        "legal": "Legal Documents",
        "records": "Reports & Records",
        "notes": "Notes & Miscellaneous",
    }

    for category, title in category_titles.items():
        if categories[category]:
            index_lines.append(f"### {title}")
            index_lines.append("")
            for filepath in categories[category]:
                filename = Path(filepath).name
                # Extract document number and title
                parts = filename.replace(".md", "").split("_")
                doc_num = parts[0]
                doc_type = parts[1].title()
                rest = " ".join(parts[2:]).replace("-", " ").title()

                index_lines.append(f"- [{doc_num}. {doc_type}: {rest}]({filepath})")
            index_lines.append("")

    if stats["issues"]:
        index_lines.append("## Issues Encountered")
        index_lines.append("")
        for issue in stats["issues"]:
            index_lines.append(f"- {issue}")
        index_lines.append("")

    index_file = output_dir / "INDEX.md"
    with open(index_file, "w", encoding="utf-8") as f:
        f.write("\n".join(index_lines))

    print(f"\nCreated index file: {index_file}")


def create_statistics_file(output_dir: Path, stats: dict):
    """Create detailed statistics summary."""

    lines = [
        "# Conversion Statistics",
        "",
        f"**Conversion Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Document Count by Type",
        "",
        f"- Total Documents Extracted: {stats['total_documents']}",
        f"- Emails: {stats['emails']}",
        f"- Legal Documents (Subpoenas, Memos, Letters): {stats['legal_docs']}",
        f"- Records/Reports: {stats['records']}",
        f"- Notes/Miscellaneous: {stats['notes']}",
        "",
        "## Annotation Integration",
        "",
        f"- Total Annotations Applied: {stats['annotations_applied']}",
        "- Annotations cross-referenced with corresponding documents",
        "",
        "## Document Breakdown",
        "",
        "### Emails (3 documents)",
        "1. RE: Epstein (pages 1-5)",
        "2. FW: Confidential (pages 6-8)",
        "3. RE: Meeting with Epstein's attorneys (pages 69-87)",
        "",
        "### Legal Documents (10 documents)",
        "- Subpoenas: 4 documents",
        "- Memos: 3 documents",
        "- Letters: 2 documents",
        "- Other: 1 document",
        "",
        "### Records (3 documents)",
        "- Flight service invoices",
        "- DAVID Criminal database summary",
        "- FACTS Background check report",
        "",
        "### Notes (1 document)",
        "- Address location note",
        "- Driving directions",
        "",
        "## Quality Metrics",
        "",
        f"- Files Created Successfully: {len(stats['files_created'])}",
        f"- Issues Encountered: {len(stats['issues'])}",
        "",
        "## OCR Quality Notes",
        "",
        "Common OCR artifacts cleaned:",
        "- Smart quotes (? → ')",
        "- Misspellings: 'fonivarding' → 'forwarding'",
        "- Misspellings: 'ankie' → 'ankle'",
        "- Misspellings: 'tetter' → 'letter'",
        "- Page headers removed",
        "- Whitespace normalized",
        "",
    ]

    if stats["issues"]:
        lines.append("## Issues Detail")
        lines.append("")
        for issue in stats["issues"]:
            lines.append(f"- {issue}")
        lines.append("")

    stats_file = output_dir / "STATISTICS.md"
    with open(stats_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Created statistics file: {stats_file}")


def main():
    """Main conversion process."""
    base_dir = Path("/Users/masa/Projects/Epstein")
    pages_dir = base_dir / "data/emails/pages"
    notes_file = base_dir / "data/emails/notes/epstein-emails-notes.json"
    output_dir = base_dir / "data/emails/markdown"

    print("=" * 70)
    print("Epstein Emails to Markdown Converter")
    print("=" * 70)
    print(f"\nSource: {pages_dir}")
    print(f"Notes: {notes_file}")
    print(f"Output: {output_dir}\n")

    # Initialize extractor
    extractor = DocumentExtractor(pages_dir, notes_file, output_dir)

    # Extract all documents
    print("Extracting documents...")
    print("-" * 70)
    stats = extractor.extract_all()

    print("\n" + "=" * 70)
    print("Creating index and statistics files...")
    print("=" * 70)

    # Create index and statistics
    create_index_file(output_dir, stats)
    create_statistics_file(output_dir, stats)

    print("\n" + "=" * 70)
    print("CONVERSION COMPLETE")
    print("=" * 70)
    print(f"\nTotal Documents: {stats['total_documents']}")
    print(f"  - Emails: {stats['emails']}")
    print(f"  - Legal Documents: {stats['legal_docs']}")
    print(f"  - Records: {stats['records']}")
    print(f"  - Notes: {stats['notes']}")
    print(f"\nAnnotations Applied: {stats['annotations_applied']}")
    print(f"Files Created: {len(stats['files_created'])}")
    if stats["issues"]:
        print(f"\n⚠️  Issues Encountered: {len(stats['issues'])}")
        for issue in stats["issues"]:
            print(f"  - {issue}")
    else:
        print("\n✓ No issues encountered")

    print(f"\nOutput directory: {output_dir}")
    print(f"Index file: {output_dir}/INDEX.md")
    print(f"Statistics: {output_dir}/STATISTICS.md")


if __name__ == "__main__":
    main()
