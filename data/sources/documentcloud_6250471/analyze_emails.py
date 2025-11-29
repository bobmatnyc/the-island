#!/usr/bin/env python3
"""
Analyze DocumentCloud 6250471 PDF to identify and extract emails.
"""

import pdfplumber
import re
import json
from collections import defaultdict
from datetime import datetime
import sys

# Email pattern regex
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

# Email header patterns
HEADER_PATTERNS = {
    'from': re.compile(r'^From:\s*(.+?)$', re.MULTILINE | re.IGNORECASE),
    'to': re.compile(r'^To:\s*(.+?)$', re.MULTILINE | re.IGNORECASE),
    'subject': re.compile(r'^Subject:\s*(.+?)$', re.MULTILINE | re.IGNORECASE),
    'date': re.compile(r'^Date:\s*(.+?)$', re.MULTILINE | re.IGNORECASE),
    'sent': re.compile(r'^Sent:\s*(.+?)$', re.MULTILINE | re.IGNORECASE),
    'cc': re.compile(r'^Cc:\s*(.+?)$', re.MULTILINE | re.IGNORECASE),
}

class EmailAnalyzer:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.emails = []
        self.document_types = defaultdict(int)
        self.all_email_addresses = set()
        self.page_texts = {}

    def extract_text_from_pdf(self):
        """Extract text from all pages."""
        print(f"Extracting text from {self.pdf_path}...")
        print("This may take several minutes for 2,024 pages...")

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"Total pages: {total_pages}")

                for page_num, page in enumerate(pdf.pages, 1):
                    if page_num % 100 == 0:
                        print(f"Processing page {page_num}/{total_pages}...")

                    text = page.extract_text()
                    if text:
                        self.page_texts[page_num] = text

                print(f"Extracted text from {len(self.page_texts)} pages")
        except Exception as e:
            print(f"Error extracting text: {e}")
            sys.exit(1)

    def is_email_page(self, text):
        """Determine if page contains email content."""
        if not text:
            return False

        # Count email indicators
        indicators = 0
        text_lower = text.lower()

        # Check for email headers
        if re.search(r'^from:\s*', text, re.MULTILINE | re.IGNORECASE):
            indicators += 2
        if re.search(r'^to:\s*', text, re.MULTILINE | re.IGNORECASE):
            indicators += 2
        if re.search(r'^subject:\s*', text, re.MULTILINE | re.IGNORECASE):
            indicators += 2
        if re.search(r'^date:\s*', text, re.MULTILINE | re.IGNORECASE) or \
           re.search(r'^sent:\s*', text, re.MULTILINE | re.IGNORECASE):
            indicators += 2

        # Check for email addresses
        email_matches = EMAIL_PATTERN.findall(text)
        if len(email_matches) >= 2:
            indicators += 1

        return indicators >= 3

    def is_court_filing(self, text):
        """Determine if page contains court filing content."""
        if not text:
            return False

        text_lower = text.lower()
        court_indicators = [
            'case no.', 'case number', 'plaintiff', 'defendant',
            'united states district court', 'circuit court',
            'declaration of', 'affidavit', 'complaint', 'motion',
            'honorable', 'your honor', 'hereby certify'
        ]

        count = sum(1 for indicator in court_indicators if indicator in text_lower)
        return count >= 2

    def extract_email_metadata(self, text, start_page):
        """Extract email metadata from text."""
        metadata = {
            'start_page': start_page,
            'end_page': start_page,
            'from': None,
            'to': None,
            'subject': None,
            'date': None,
            'cc': None,
            'participants': set(),
        }

        # Extract headers
        for header_name, pattern in HEADER_PATTERNS.items():
            match = pattern.search(text)
            if match:
                metadata[header_name] = match.group(1).strip()

        # Extract email addresses
        email_addresses = EMAIL_PATTERN.findall(text)
        for addr in email_addresses:
            self.all_email_addresses.add(addr.lower())
            metadata['participants'].add(addr.lower())

        # Convert set to list for JSON serialization
        metadata['participants'] = sorted(list(metadata['participants']))

        return metadata

    def identify_emails(self):
        """Identify and extract all emails from the document."""
        print("\nIdentifying emails...")

        email_count = 0
        current_email = None

        for page_num in sorted(self.page_texts.keys()):
            text = self.page_texts[page_num]

            # Classify document type
            if self.is_email_page(text):
                self.document_types['email'] += 1

                # Check if this is a new email or continuation
                has_headers = any(pattern.search(text) for pattern in HEADER_PATTERNS.values())

                if has_headers:
                    # Save previous email if exists
                    if current_email:
                        self.emails.append(current_email)
                        email_count += 1

                    # Start new email
                    current_email = self.extract_email_metadata(text, page_num)
                elif current_email:
                    # Continuation of current email
                    current_email['end_page'] = page_num
                    # Extract additional email addresses
                    email_addresses = EMAIL_PATTERN.findall(text)
                    for addr in email_addresses:
                        self.all_email_addresses.add(addr.lower())
                        if addr.lower() not in current_email['participants']:
                            current_email['participants'].append(addr.lower())

            elif self.is_court_filing(text):
                self.document_types['court_filing'] += 1
                # Court filing ends any current email
                if current_email:
                    self.emails.append(current_email)
                    email_count += 1
                    current_email = None
            else:
                self.document_types['other'] += 1

        # Save last email if exists
        if current_email:
            self.emails.append(current_email)
            email_count += 1

        print(f"Found {len(self.emails)} distinct emails")
        print(f"Found {len(self.all_email_addresses)} unique email addresses")

    def assess_quality(self):
        """Assess the quality of the extraction."""
        quality = {
            'total_pages': len(self.page_texts),
            'pages_with_text': sum(1 for text in self.page_texts.values() if text.strip()),
            'avg_chars_per_page': sum(len(text) for text in self.page_texts.values()) / len(self.page_texts) if self.page_texts else 0,
            'emails_with_complete_headers': 0,
            'emails_with_from': sum(1 for e in self.emails if e['from']),
            'emails_with_to': sum(1 for e in self.emails if e['to']),
            'emails_with_subject': sum(1 for e in self.emails if e['subject']),
            'emails_with_date': sum(1 for e in self.emails if e['date']),
        }

        quality['emails_with_complete_headers'] = sum(
            1 for e in self.emails
            if e['from'] and e['to'] and e['subject'] and e['date']
        )

        return quality

    def generate_report(self):
        """Generate comprehensive analysis report."""
        quality = self.assess_quality()

        report = {
            'analysis_date': datetime.now().isoformat(),
            'source_file': self.pdf_path,
            'summary': {
                'total_pages': len(self.page_texts),
                'total_emails': len(self.emails),
                'unique_email_addresses': len(self.all_email_addresses),
            },
            'document_type_breakdown': dict(self.document_types),
            'quality_metrics': quality,
            'email_addresses': sorted(list(self.all_email_addresses)),
            'emails': self.emails,
        }

        return report

    def print_summary(self, report):
        """Print human-readable summary."""
        print("\n" + "="*80)
        print("EMAIL ANALYSIS SUMMARY - DocumentCloud 6250471")
        print("="*80)

        print(f"\n📊 OVERALL STATISTICS:")
        print(f"  Total Pages: {report['summary']['total_pages']:,}")
        print(f"  Total Emails Found: {report['summary']['total_emails']:,}")
        print(f"  Unique Email Addresses: {report['summary']['unique_email_addresses']:,}")

        print(f"\n📋 DOCUMENT TYPE BREAKDOWN:")
        total_classified = sum(report['document_type_breakdown'].values())
        for doc_type, count in sorted(report['document_type_breakdown'].items()):
            pct = (count / total_classified * 100) if total_classified > 0 else 0
            print(f"  {doc_type.replace('_', ' ').title()}: {count:,} pages ({pct:.1f}%)")

        print(f"\n✅ QUALITY ASSESSMENT:")
        quality = report['quality_metrics']
        print(f"  Pages with text: {quality['pages_with_text']:,}/{quality['total_pages']:,}")
        print(f"  Avg characters per page: {quality['avg_chars_per_page']:.0f}")
        print(f"  Emails with complete headers: {quality['emails_with_complete_headers']}/{len(self.emails)}")
        print(f"  Emails with From: {quality['emails_with_from']}/{len(self.emails)}")
        print(f"  Emails with To: {quality['emails_with_to']}/{len(self.emails)}")
        print(f"  Emails with Subject: {quality['emails_with_subject']}/{len(self.emails)}")
        print(f"  Emails with Date: {quality['emails_with_date']}/{len(self.emails)}")

        print(f"\n📧 TOP EMAIL PARTICIPANTS:")
        # Count participation
        participation = defaultdict(int)
        for email in self.emails:
            for participant in email['participants']:
                participation[participant] += 1

        top_participants = sorted(participation.items(), key=lambda x: x[1], reverse=True)[:20]
        for addr, count in top_participants:
            print(f"  {addr}: {count} emails")

        print(f"\n📝 SAMPLE EMAILS:")
        for i, email in enumerate(self.emails[:5], 1):
            print(f"\n  Email #{i} (Pages {email['start_page']}-{email['end_page']}):")
            print(f"    From: {email['from'] or 'N/A'}")
            print(f"    To: {email['to'] or 'N/A'}")
            print(f"    Subject: {email['subject'] or 'N/A'}")
            print(f"    Date: {email['date'] or 'N/A'}")
            print(f"    Participants: {len(email['participants'])}")

        print("\n" + "="*80)
        print("✅ Analysis complete!")
        print("="*80)

def main():
    pdf_path = "/Users/masa/Projects/Epstein/data/sources/documentcloud_6250471/epstein-docs-6250471.pdf"
    output_dir = "/Users/masa/Projects/Epstein/data/sources/documentcloud_6250471"

    # Initialize analyzer
    analyzer = EmailAnalyzer(pdf_path)

    # Step 1: Extract text
    analyzer.extract_text_from_pdf()

    # Step 2: Identify emails
    analyzer.identify_emails()

    # Step 3: Generate report
    report = analyzer.generate_report()

    # Step 4: Save outputs
    print("\nSaving outputs...")

    # Save full report
    report_path = f"{output_dir}/email_analysis_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Saved full report: {report_path}")

    # Save email index (simplified)
    email_index = {
        'total_emails': len(analyzer.emails),
        'emails': [
            {
                'id': i,
                'pages': f"{e['start_page']}-{e['end_page']}",
                'from': e['from'],
                'to': e['to'],
                'subject': e['subject'],
                'date': e['date'],
                'participant_count': len(e['participants']),
            }
            for i, e in enumerate(analyzer.emails, 1)
        ]
    }

    index_path = f"{output_dir}/email_index.json"
    with open(index_path, 'w') as f:
        json.dump(email_index, f, indent=2)
    print(f"Saved email index: {index_path}")

    # Save extracted text (sample only - first 100 pages)
    text_sample = {
        'total_pages': len(analyzer.page_texts),
        'sample_pages': {
            str(page_num): text
            for page_num, text in list(analyzer.page_texts.items())[:100]
        }
    }

    text_path = f"{output_dir}/text_sample.json"
    with open(text_path, 'w') as f:
        json.dump(text_sample, f, indent=2)
    print(f"Saved text sample (100 pages): {text_path}")

    # Print summary
    analyzer.print_summary(report)

    print(f"\n📁 Output Files:")
    print(f"  - {report_path}")
    print(f"  - {index_path}")
    print(f"  - {text_path}")

if __name__ == "__main__":
    main()
