#!/usr/bin/env python3
"""
Deep search for emails and email addresses in the PDF.
"""

import pdfplumber
import re
import json
from collections import defaultdict, Counter

EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

def search_pdf_for_emails(pdf_path):
    """Search every page for email indicators."""

    print(f"Opening PDF: {pdf_path}")

    pages_with_at = []
    pages_with_emails = []
    all_email_addresses = set()
    email_pages = defaultdict(list)

    # Various email header patterns
    header_patterns = [
        (r'^\s*From:\s*(.+?)$', 'From'),
        (r'^\s*To:\s*(.+?)$', 'To'),
        (r'^\s*Subject:\s*(.+?)$', 'Subject'),
        (r'^\s*Date:\s*(.+?)$', 'Date'),
        (r'^\s*Sent:\s*(.+?)$', 'Sent'),
        (r'^\s*Cc:\s*(.+?)$', 'Cc'),
        (r'^\s*Bcc:\s*(.+?)$', 'Bcc'),
    ]

    pages_with_headers = defaultdict(list)

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Total pages: {total_pages}")

        for page_num, page in enumerate(pdf.pages, 1):
            if page_num % 200 == 0:
                print(f"Processing page {page_num}/{total_pages}...")

            text = page.extract_text()
            if not text:
                continue

            # Check for @ symbol
            if '@' in text:
                pages_with_at.append(page_num)

                # Extract email addresses
                emails = EMAIL_PATTERN.findall(text)
                if emails:
                    pages_with_emails.append((page_num, len(emails)))
                    for email in emails:
                        all_email_addresses.add(email.lower())
                        email_pages[email.lower()].append(page_num)

            # Check for email headers
            for pattern, header_name in header_patterns:
                matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
                if matches:
                    pages_with_headers[header_name].append(page_num)

    return {
        'total_pages': total_pages,
        'pages_with_at': pages_with_at,
        'pages_with_emails': pages_with_emails,
        'all_email_addresses': sorted(list(all_email_addresses)),
        'email_pages': dict(email_pages),
        'pages_with_headers': dict(pages_with_headers),
    }

def analyze_email_sections(pdf_path, email_data):
    """Extract and analyze sections that contain emails."""

    print("\nExtracting email sections...")

    # Get pages that likely contain emails (have both @ and headers)
    pages_with_headers = set()
    for header, pages in email_data['pages_with_headers'].items():
        pages_with_headers.update(pages)

    pages_with_at_set = set(email_data['pages_with_at'])

    likely_email_pages = pages_with_headers & pages_with_at_set

    print(f"Pages with both headers and @: {len(likely_email_pages)}")

    # Extract text from these pages
    email_sections = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in sorted(likely_email_pages):
            page = pdf.pages[page_num - 1]  # 0-indexed
            text = page.extract_text()

            # Extract metadata
            metadata = {
                'page': page_num,
                'from': None,
                'to': None,
                'subject': None,
                'date': None,
                'sent': None,
                'email_addresses': EMAIL_PATTERN.findall(text),
            }

            # Try to extract headers
            from_match = re.search(r'^\s*From:\s*(.+?)$', text, re.MULTILINE | re.IGNORECASE)
            if from_match:
                metadata['from'] = from_match.group(1).strip()

            to_match = re.search(r'^\s*To:\s*(.+?)$', text, re.MULTILINE | re.IGNORECASE)
            if to_match:
                metadata['to'] = to_match.group(1).strip()

            subject_match = re.search(r'^\s*Subject:\s*(.+?)$', text, re.MULTILINE | re.IGNORECASE)
            if subject_match:
                metadata['subject'] = subject_match.group(1).strip()

            date_match = re.search(r'^\s*Date:\s*(.+?)$', text, re.MULTILINE | re.IGNORECASE)
            if date_match:
                metadata['date'] = date_match.group(1).strip()
            else:
                sent_match = re.search(r'^\s*Sent:\s*(.+?)$', text, re.MULTILINE | re.IGNORECASE)
                if sent_match:
                    metadata['sent'] = sent_match.group(1).strip()

            email_sections.append(metadata)

    return email_sections

def main():
    pdf_path = "/Users/masa/Projects/Epstein/data/sources/documentcloud_6250471/epstein-docs-6250471.pdf"
    output_dir = "/Users/masa/Projects/Epstein/data/sources/documentcloud_6250471"

    # Search for emails
    print("="*80)
    print("DEEP EMAIL SEARCH - DocumentCloud 6250471")
    print("="*80)

    email_data = search_pdf_for_emails(pdf_path)

    # Print summary
    print("\n" + "="*80)
    print("SEARCH RESULTS")
    print("="*80)

    print(f"\n📊 OVERALL STATISTICS:")
    print(f"  Total pages: {email_data['total_pages']:,}")
    print(f"  Pages with @ symbol: {len(email_data['pages_with_at']):,}")
    print(f"  Pages with email addresses: {len(email_data['pages_with_emails']):,}")
    print(f"  Unique email addresses found: {len(email_data['all_email_addresses']):,}")

    print(f"\n📧 EMAIL ADDRESSES FOUND:")
    if email_data['all_email_addresses']:
        # Count occurrences
        occurrence_count = Counter()
        for email, pages in email_data['email_pages'].items():
            occurrence_count[email] = len(pages)

        # Sort by occurrence
        sorted_emails = sorted(occurrence_count.items(), key=lambda x: x[1], reverse=True)

        for email, count in sorted_emails:
            pages = email_data['email_pages'][email]
            page_range = f"{min(pages)}-{max(pages)}" if len(pages) > 1 else str(pages[0])
            print(f"  {email}: {count} occurrences (pages {page_range})")
    else:
        print("  No email addresses found")

    print(f"\n📝 EMAIL HEADER INDICATORS:")
    for header, pages in sorted(email_data['pages_with_headers'].items()):
        print(f"  {header}: {len(pages)} pages")
        if len(pages) <= 10:
            print(f"    Pages: {pages}")

    # Analyze email sections
    if email_data['pages_with_at']:
        email_sections = analyze_email_sections(pdf_path, email_data)

        print(f"\n📬 POTENTIAL EMAIL MESSAGES:")
        print(f"  Found {len(email_sections)} pages with email-like content")

        # Show sample
        print(f"\n  Sample emails (first 10):")
        for i, section in enumerate(email_sections[:10], 1):
            print(f"\n  Email #{i} (Page {section['page']}):")
            print(f"    From: {section['from'] or 'N/A'}")
            print(f"    To: {section['to'] or 'N/A'}")
            print(f"    Subject: {section['subject'] or 'N/A'}")
            print(f"    Date: {section['date'] or section['sent'] or 'N/A'}")
            print(f"    Email addresses on page: {len(section['email_addresses'])}")

    # Save results
    print("\n" + "="*80)
    print("SAVING RESULTS")
    print("="*80)

    output = {
        'analysis_date': '2025-11-16',
        'source': pdf_path,
        'summary': {
            'total_pages': email_data['total_pages'],
            'pages_with_at': len(email_data['pages_with_at']),
            'pages_with_emails': len(email_data['pages_with_emails']),
            'unique_email_addresses': len(email_data['all_email_addresses']),
        },
        'email_addresses': email_data['all_email_addresses'],
        'email_pages': email_data['email_pages'],
        'pages_with_headers': email_data['pages_with_headers'],
    }

    if email_data['pages_with_at']:
        output['email_sections'] = email_sections

    output_path = f"{output_dir}/deep_email_search_results.json"
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"✅ Results saved to: {output_path}")

    # Create summary for pages to examine
    if email_data['pages_with_at']:
        pages_to_check = sorted(email_data['pages_with_at'])

        print(f"\n📄 PAGES TO EXAMINE ({len(pages_to_check)} total):")

        # Group into ranges
        ranges = []
        start = pages_to_check[0]
        end = pages_to_check[0]

        for page in pages_to_check[1:]:
            if page == end + 1:
                end = page
            else:
                ranges.append((start, end))
                start = page
                end = page
        ranges.append((start, end))

        print("  Page ranges with email content:")
        for start, end in ranges[:50]:  # Show first 50 ranges
            if start == end:
                print(f"    Page {start}")
            else:
                print(f"    Pages {start}-{end}")

        if len(ranges) > 50:
            print(f"    ... and {len(ranges) - 50} more ranges")

    print("\n" + "="*80)
    print("✅ DEEP SEARCH COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
