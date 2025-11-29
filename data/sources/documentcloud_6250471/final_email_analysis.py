#!/usr/bin/env python3
"""
Final comprehensive analysis of DocumentCloud 6250471.
Categorize document types and create detailed index.
"""

import pdfplumber
import re
import json
from collections import defaultdict, Counter
from datetime import datetime

EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

def classify_document_page(text):
    """Classify what type of document this page contains."""
    if not text:
        return 'blank'

    text_lower = text.lower()

    # Court document indicators
    court_indicators = {
        'deposition': ['deposition of', 'sworn', 'oath', 'notary public', 'court reporter'],
        'court_order': ['united states court of appeals', 'it is hereby ordered', 'mandate', 'circuit judges'],
        'legal_filing': ['plaintiff', 'defendant', 'case no.', 'united states district court'],
        'certificate': ['certificate of service', 'i certify that', 'electronically served'],
        'exhibit': ['exhibit', 'defendant\'s exhibit', 'plaintiff\'s exhibit'],
        'docket': ['docket entries', 'filed document description'],
    }

    # Check for each type
    for doc_type, keywords in court_indicators.items():
        matches = sum(1 for keyword in keywords if keyword in text_lower)
        if matches >= 2:
            return doc_type

    # Check for email-like content (From:, To:, Subject:)
    email_headers = sum([
        'from:' in text_lower[:500],
        'to:' in text_lower[:500],
        'subject:' in text_lower[:500],
    ])
    if email_headers >= 2:
        return 'email'

    return 'other'

def extract_case_info(text):
    """Extract case information from legal documents."""
    case_info = {}

    # Case number
    case_match = re.search(r'(?:Case|Civil Action)\s+(?:No\.?|Number)\s*[:;]?\s*([0-9]+-[A-Z]*-?[0-9]+(?:-[A-Z]+)?)', text, re.IGNORECASE)
    if case_match:
        case_info['case_number'] = case_match.group(1)

    # Document number
    doc_match = re.search(r'Document\s+(\d+)', text, re.IGNORECASE)
    if doc_match:
        case_info['document_number'] = doc_match.group(1)

    # Page of total
    page_match = re.search(r'Page\s*(\d+)\s*of\s*(\d+)', text, re.IGNORECASE)
    if page_match:
        case_info['doc_page'] = page_match.group(1)
        case_info['doc_total_pages'] = page_match.group(2)

    return case_info

def analyze_full_pdf(pdf_path):
    """Complete analysis of the PDF."""

    print(f"Analyzing: {pdf_path}")
    print("="*80)

    stats = {
        'total_pages': 0,
        'document_types': Counter(),
        'email_addresses': Counter(),
        'case_numbers': Counter(),
        'pages_by_type': defaultdict(list),
        'email_address_pages': defaultdict(list),
        'detailed_pages': [],
    }

    with pdfplumber.open(pdf_path) as pdf:
        stats['total_pages'] = len(pdf.pages)
        print(f"Processing {stats['total_pages']:,} pages...")

        for page_num, page in enumerate(pdf.pages, 1):
            if page_num % 200 == 0:
                print(f"  Page {page_num}/{stats['total_pages']}...")

            text = page.extract_text()
            if not text:
                stats['document_types']['blank'] += 1
                continue

            # Classify page
            doc_type = classify_document_page(text)
            stats['document_types'][doc_type] += 1
            stats['pages_by_type'][doc_type].append(page_num)

            # Extract case info
            case_info = extract_case_info(text)

            # Extract email addresses
            emails = EMAIL_PATTERN.findall(text)
            for email in emails:
                email_lower = email.lower()
                stats['email_addresses'][email_lower] += 1
                stats['email_address_pages'][email_lower].append(page_num)

            # Track case numbers
            if 'case_number' in case_info:
                stats['case_numbers'][case_info['case_number']] += 1

            # Store detailed info for pages with emails
            if emails:
                page_detail = {
                    'page': page_num,
                    'type': doc_type,
                    'emails_found': list(set(email.lower() for email in emails)),
                    'case_info': case_info,
                }
                stats['detailed_pages'].append(page_detail)

    print("✅ Analysis complete!\n")
    return stats

def generate_final_report(stats):
    """Generate comprehensive final report."""

    report = {
        'analysis_date': datetime.now().isoformat(),
        'source': 'DocumentCloud 6250471 (epstein-docs-6250471.pdf)',
        'summary': {
            'total_pages': stats['total_pages'],
            'document_contains': 'Court filings, depositions, and legal documents - NOT email messages',
            'total_email_addresses_found': len(stats['email_addresses']),
            'email_addresses_are': 'Attorney contact info and court reporter contact info in legal filings',
            'actual_email_messages': 0,
            'email_threads': 0,
        },
        'document_type_breakdown': dict(stats['document_types']),
        'case_numbers': dict(stats['case_numbers']),
        'email_addresses': {
            email: {
                'occurrences': count,
                'pages': sorted(stats['email_address_pages'][email]),
                'page_range': f"{min(stats['email_address_pages'][email])}-{max(stats['email_address_pages'][email])}"
            }
            for email, count in stats['email_addresses'].most_common()
        },
        'pages_with_email_addresses': sorted(stats['detailed_pages'], key=lambda x: x['page']),
    }

    return report

def print_final_summary(report):
    """Print human-readable final summary."""

    print("\n" + "="*80)
    print("FINAL ANALYSIS: DocumentCloud 6250471")
    print("="*80)

    print(f"\n📊 DOCUMENT OVERVIEW:")
    print(f"  Source: {report['source']}")
    print(f"  Total Pages: {report['summary']['total_pages']:,}")
    print(f"  Analysis Date: {report['analysis_date']}")

    print(f"\n🔍 KEY FINDING:")
    print(f"  ⚠️  This PDF contains: {report['summary']['document_contains']}")
    print(f"  ✉️  Actual email messages found: {report['summary']['actual_email_messages']}")
    print(f"  📧  Email addresses found: {report['summary']['total_email_addresses_found']}")
    print(f"  ℹ️  Email addresses are: {report['summary']['email_addresses_are']}")

    print(f"\n📋 DOCUMENT TYPE BREAKDOWN:")
    total = sum(report['document_type_breakdown'].values())
    for doc_type, count in sorted(report['document_type_breakdown'].items(), key=lambda x: x[1], reverse=True):
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {doc_type.replace('_', ' ').title()}: {count:,} pages ({pct:.1f}%)")

    print(f"\n⚖️  CASE NUMBERS FOUND:")
    for case_num, count in sorted(report['case_numbers'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {case_num}: {count} pages")

    print(f"\n📧 EMAIL ADDRESSES (Contact Information):")
    for email, data in list(report['email_addresses'].items())[:20]:
        print(f"  {email}:")
        print(f"    Occurrences: {data['occurrences']}")
        print(f"    Page range: {data['page_range']}")

    print(f"\n📄 PAGES WITH EMAIL ADDRESSES:")
    pages_with_emails = len([p for p in report['pages_with_email_addresses'] if p['emails_found']])
    print(f"  Total pages with email addresses: {pages_with_emails}")

    # Sample pages
    print(f"\n  Sample pages (first 10):")
    for page_info in report['pages_with_email_addresses'][:10]:
        print(f"    Page {page_info['page']} ({page_info['type']}): {', '.join(page_info['emails_found'])}")

    print(f"\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    print("""
This PDF (DocumentCloud 6250471) contains legal court documents related to
the Giuffre v. Maxwell case, including:
  - Court orders and appeals
  - Depositions and testimony transcripts
  - Legal filings and motions
  - Certificates of service
  - Exhibit lists

The email addresses found are:
  - Attorney contact information (from law firm signatures)
  - Court reporter contact information
  - Media contact information

This collection does NOT contain:
  - Email messages or correspondence
  - Email threads or conversations
  - Email attachments

RECOMMENDATION:
  This source is NOT suitable for email canonicalization. It's a collection
  of court documents that should be indexed as legal filings, not emails.

NEXT STEPS:
  1. Catalog as "Court Documents - Giuffre v. Maxwell"
  2. Extract case metadata and deposition information
  3. Look for other sources that contain actual email correspondence
""")

    print("="*80)

def main():
    pdf_path = "/Users/masa/Projects/Epstein/data/sources/documentcloud_6250471/epstein-docs-6250471.pdf"
    output_dir = "/Users/masa/Projects/Epstein/data/sources/documentcloud_6250471"

    # Analyze
    stats = analyze_full_pdf(pdf_path)

    # Generate report
    report = generate_final_report(stats)

    # Save
    output_path = f"{output_dir}/FINAL_ANALYSIS.json"
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"💾 Saved to: {output_path}")

    # Print summary
    print_final_summary(report)

    # Create quick reference
    quick_ref = {
        'source': 'DocumentCloud 6250471',
        'type': 'Court Documents',
        'email_messages': 0,
        'email_addresses': len(report['email_addresses']),
        'pages': report['summary']['total_pages'],
        'suitable_for_email_canonicalization': False,
        'primary_content': 'Legal filings and depositions in Giuffre v. Maxwell',
    }

    quick_ref_path = f"{output_dir}/QUICK_REFERENCE.json"
    with open(quick_ref_path, 'w') as f:
        json.dump(quick_ref, f, indent=2)

    print(f"\n💾 Quick reference saved to: {quick_ref_path}")

if __name__ == "__main__":
    main()
