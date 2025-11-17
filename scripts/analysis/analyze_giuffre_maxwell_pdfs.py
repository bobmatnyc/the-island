#!/usr/bin/env python3
"""
Analyze Giuffre v. Maxwell PDF collection to identify and count emails.
Extract metadata and prepare for markdown conversion.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

import pdfplumber

# Email header patterns
EMAIL_PATTERNS = {
    'from': re.compile(r'^From:\s*(.+?)$', re.MULTILINE | re.IGNORECASE),
    'to': re.compile(r'^To:\s*(.+?)$', re.MULTILINE | re.IGNORECASE),
    'cc': re.compile(r'^Cc:\s*(.+?)$', re.MULTILINE | re.IGNORECASE),
    'date': re.compile(r'^(?:Date|Sent):\s*(.+?)$', re.MULTILINE | re.IGNORECASE),
    'subject': re.compile(r'^Subject:\s*(.+?)$', re.MULTILINE | re.IGNORECASE),
}

# Document type indicators
DOC_TYPE_PATTERNS = {
    'deposition': [r'deposition', r'sworn testimony', r'examination by', r'Q\..*A\.'],
    'court_filing': [r'united states district court', r'motion to', r'memorandum', r'plaintiff', r'defendant'],
    'exhibit': [r'exhibit\s+\w+', r'plaintiff.*exhibit', r'defendant.*exhibit'],
    'email': [r'from:.*to:.*subject:', r'sent:.*from:.*to:', r're:.*fw:'],
}


class PDFAnalyzer:
    def __init__(self, pdf_dir: str):
        self.pdf_dir = Path(pdf_dir)
        self.results = {
            'total_documents': 0,
            'documents': [],
            'statistics': defaultdict(int),
            'emails': [],
            'date_range': {'earliest': None, 'latest': None},
        }

    def extract_text_from_pdf(self, pdf_path: Path) -> Tuple[str, int]:
        """Extract text from PDF and return text + page count."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
                return text, len(pdf.pages)
        except Exception as e:
            print(f"Error reading {pdf_path.name}: {e}")
            return "", 0

    def detect_document_type(self, text: str) -> str:
        """Detect document type based on content patterns."""
        text_lower = text.lower()

        # Check for emails first (most specific)
        email_indicators = 0
        for pattern in EMAIL_PATTERNS.values():
            if pattern.search(text[:5000]):  # Check first 5000 chars
                email_indicators += 1

        if email_indicators >= 3:  # From, To, Subject/Date
            return 'email'

        # Check other document types
        for doc_type, patterns in DOC_TYPE_PATTERNS.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, text_lower[:5000]))
            if matches >= 2:
                return doc_type

        return 'other'

    def extract_email_metadata(self, text: str, filename: str) -> Optional[Dict]:
        """Extract email metadata from text."""
        metadata = {
            'filename': filename,
            'from': None,
            'to': None,
            'cc': None,
            'date': None,
            'subject': None,
            'has_attachments': False,
        }

        # Extract headers
        for field, pattern in EMAIL_PATTERNS.items():
            match = pattern.search(text[:3000])  # Check first 3000 chars
            if match:
                metadata[field] = match.group(1).strip()

        # Check for attachments
        if re.search(r'attachment|attached file', text[:5000], re.IGNORECASE):
            metadata['has_attachments'] = True

        # Only return if we have minimum email metadata
        if metadata['from'] or metadata['to'] or metadata['subject']:
            return metadata
        return None

    def find_emails_in_text(self, text: str, filename: str, page_count: int) -> List[Dict]:
        """Find all emails within a document (some PDFs contain multiple emails)."""
        emails = []

        # Split by common email separators
        sections = re.split(r'\n-{3,}\s*Original Message\s*-{3,}|\n={10,}|\nPage \d+ of \d+', text)

        for idx, section in enumerate(sections):
            if len(section.strip()) < 100:  # Skip tiny sections
                continue

            email_meta = self.extract_email_metadata(section, f"{filename}_email_{idx+1}")
            if email_meta:
                email_meta['page_count'] = page_count
                email_meta['section_index'] = idx
                email_meta['is_thread'] = '----Original Message----' in text or 'Re:' in str(email_meta.get('subject', ''))
                emails.append(email_meta)

        return emails

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse email date string."""
        if not date_str:
            return None

        # Common date formats
        formats = [
            '%m/%d/%Y %I:%M:%S %p',
            '%m/%d/%Y %I:%M %p',
            '%m/%d/%Y',
            '%B %d, %Y',
            '%d %B %Y',
            '%Y-%m-%d',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        return None

    def analyze_document(self, pdf_path: Path) -> Dict:
        """Analyze a single PDF document."""
        print(f"Analyzing: {pdf_path.name}")

        text, page_count = self.extract_text_from_pdf(pdf_path)
        doc_type = self.detect_document_type(text)

        doc_info = {
            'filename': pdf_path.name,
            'file_size': pdf_path.stat().st_size,
            'page_count': page_count,
            'type': doc_type,
            'has_redactions': 'redacted' in text.lower() or '█' in text,
            'ocr_quality': 'good' if len(text) > page_count * 100 else 'poor',
            'emails_found': 0,
        }

        # If it's an email document, extract all emails
        if doc_type == 'email':
            emails = self.find_emails_in_text(text, pdf_path.name, page_count)
            doc_info['emails_found'] = len(emails)
            self.results['emails'].extend(emails)

            # Update date range
            for email in emails:
                if email.get('date'):
                    parsed_date = self.parse_date(email['date'])
                    if parsed_date:
                        if not self.results['date_range']['earliest'] or parsed_date < self.results['date_range']['earliest']:
                            self.results['date_range']['earliest'] = parsed_date
                        if not self.results['date_range']['latest'] or parsed_date > self.results['date_range']['latest']:
                            self.results['date_range']['latest'] = parsed_date

        return doc_info

    def analyze_all_documents(self):
        """Analyze all PDFs in the directory."""
        pdf_files = sorted(self.pdf_dir.glob('*.pdf'))
        self.results['total_documents'] = len(pdf_files)

        print(f"\nAnalyzing {len(pdf_files)} PDF documents...\n")

        for pdf_path in pdf_files:
            doc_info = self.analyze_document(pdf_path)
            self.results['documents'].append(doc_info)
            self.results['statistics'][doc_info['type']] += 1

        # Calculate additional statistics
        self.results['statistics']['total_emails'] = len(self.results['emails'])
        self.results['statistics']['total_pages'] = sum(d['page_count'] for d in self.results['documents'])
        self.results['statistics']['documents_with_emails'] = sum(1 for d in self.results['documents'] if d['emails_found'] > 0)
        self.results['statistics']['poor_ocr_quality'] = sum(1 for d in self.results['documents'] if d['ocr_quality'] == 'poor')
        self.results['statistics']['redacted_documents'] = sum(1 for d in self.results['documents'] if d['has_redactions'])

    def generate_report(self) -> str:
        """Generate analysis report."""
        report = []
        report.append("=" * 80)
        report.append("GIUFFRE V. MAXWELL PDF COLLECTION ANALYSIS")
        report.append("=" * 80)
        report.append("")

        report.append("## DOCUMENT STATISTICS")
        report.append(f"Total Documents: {self.results['total_documents']}")
        report.append(f"Total Pages: {self.results['statistics']['total_pages']}")
        report.append("")

        report.append("## DOCUMENT TYPES")
        for doc_type in ['email', 'deposition', 'court_filing', 'exhibit', 'other']:
            count = self.results['statistics'].get(doc_type, 0)
            if count > 0:
                report.append(f"  {doc_type.replace('_', ' ').title()}: {count}")
        report.append("")

        report.append("## EMAIL STATISTICS")
        report.append(f"Total Emails Found: {self.results['statistics']['total_emails']}")
        report.append(f"Documents Containing Emails: {self.results['statistics']['documents_with_emails']}")

        if self.results['date_range']['earliest'] and self.results['date_range']['latest']:
            report.append(f"Date Range: {self.results['date_range']['earliest'].strftime('%Y-%m-%d')} to {self.results['date_range']['latest'].strftime('%Y-%m-%d')}")

        emails_with_threads = sum(1 for e in self.results['emails'] if e.get('is_thread'))
        report.append(f"Email Threads: {emails_with_threads}")

        emails_with_attachments = sum(1 for e in self.results['emails'] if e.get('has_attachments'))
        report.append(f"Emails with Attachments: {emails_with_attachments}")
        report.append("")

        report.append("## QUALITY INDICATORS")
        report.append(f"Documents with Redactions: {self.results['statistics']['redacted_documents']}")
        report.append(f"Poor OCR Quality: {self.results['statistics']['poor_ocr_quality']}")
        report.append("")

        report.append("## SAMPLE EMAIL METADATA (First 5)")
        for i, email in enumerate(self.results['emails'][:5], 1):
            report.append(f"\n{i}. {email['filename']}")
            report.append(f"   From: {email.get('from', 'N/A')}")
            report.append(f"   To: {email.get('to', 'N/A')}")
            report.append(f"   Date: {email.get('date', 'N/A')}")
            report.append(f"   Subject: {email.get('subject', 'N/A')}")
            report.append(f"   Thread: {email.get('is_thread', False)}")

        report.append("\n" + "=" * 80)
        report.append("## CONVERSION READINESS")
        report.append("=" * 80)

        issues = []
        if self.results['statistics']['poor_ocr_quality'] > 0:
            issues.append(f"⚠️  {self.results['statistics']['poor_ocr_quality']} documents have poor OCR quality")

        if self.results['statistics']['redacted_documents'] > 0:
            issues.append(f"⚠️  {self.results['statistics']['redacted_documents']} documents contain redactions")

        if not self.results['emails']:
            issues.append("⚠️  No emails found in collection")

        if issues:
            report.append("\nIssues to Address:")
            for issue in issues:
                report.append(f"  {issue}")
        else:
            report.append("\n✅ Collection ready for markdown conversion")

        report.append("\n" + "=" * 80)

        return "\n".join(report)

    def save_results(self, output_dir: Path):
        """Save analysis results."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save full JSON
        json_path = output_dir / 'pdf_analysis_results.json'
        with open(json_path, 'w') as f:
            # Convert datetime objects to strings
            results_copy = self.results.copy()
            if results_copy['date_range']['earliest']:
                results_copy['date_range']['earliest'] = results_copy['date_range']['earliest'].isoformat()
            if results_copy['date_range']['latest']:
                results_copy['date_range']['latest'] = results_copy['date_range']['latest'].isoformat()

            json.dump(results_copy, f, indent=2, default=str)

        # Save report
        report_path = output_dir / 'PDF_ANALYSIS_REPORT.md'
        with open(report_path, 'w') as f:
            f.write(self.generate_report())

        # Save email index
        email_index_path = output_dir / 'email_index.json'
        with open(email_index_path, 'w') as f:
            json.dump(self.results['emails'], f, indent=2, default=str)

        print(f"\n✅ Results saved to {output_dir}")
        print(f"   - {json_path.name}")
        print(f"   - {report_path.name}")
        print(f"   - {email_index_path.name}")


def main():
    pdf_dir = Path("/Users/masa/Projects/Epstein/data/sources/giuffre_maxwell/2024_unsealed_documents")
    output_dir = Path("/Users/masa/Projects/Epstein/data/sources/giuffre_maxwell/analysis")

    analyzer = PDFAnalyzer(pdf_dir)
    analyzer.analyze_all_documents()

    # Print report to console
    print("\n" + analyzer.generate_report())

    # Save results
    analyzer.save_results(output_dir)


if __name__ == "__main__":
    main()
