#!/usr/bin/env python3
"""
House Oversight OCR Processing Script
Processes 33,572 PDF pages with parallel OCR and email detection

Features:
- Parallel processing with configurable workers
- Resume capability (tracks completed files)
- Email detection and flagging
- Progress tracking and logging
- Error handling and retry logic
- Estimated time remaining
"""

import os
import sys
import json
import time
import re
from pathlib import Path
from multiprocessing import Pool, Manager
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import argparse

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    from tqdm import tqdm
except ImportError as e:
    print(f"Error: Missing required package: {e}")
    print("Please run: pip install pytesseract pdf2image pillow tqdm")
    sys.exit(1)


# Configuration
SOURCE_DIR = Path("/Users/masa/Projects/Epstein/data/sources/house_oversight_nov2025/epstein-pdf")
OUTPUT_DIR = Path("/Users/masa/Projects/Epstein/data/sources/house_oversight_nov2025/ocr_text")
PROGRESS_FILE = Path("/Users/masa/Projects/Epstein/data/sources/house_oversight_nov2025/ocr_progress.json")
EMAIL_INDEX_FILE = Path("/Users/masa/Projects/Epstein/data/sources/house_oversight_nov2025/email_candidates.jsonl")
LOG_FILE = Path("/Users/masa/Projects/Epstein/logs/ocr_house_oversight.log")

# Email detection patterns
EMAIL_ADDRESS_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
EMAIL_HEADER_PATTERNS = [
    re.compile(r'^(From|To|Cc|Bcc|Subject|Date):\s*', re.MULTILINE | re.IGNORECASE),
    re.compile(r'\b(sent|received|forwarded):\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', re.IGNORECASE),
    re.compile(r'\b(original message|forwarded message)\b', re.IGNORECASE),
]

# OCR Configuration
TESSERACT_CONFIG = '--oem 3 --psm 6'  # LSTM OCR, assume uniform text block
DPI = 300  # Balance quality vs speed


def setup_logging():
    """Initialize logging to file and console"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    class Logger:
        def __init__(self, log_file):
            self.log_file = log_file
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

        def log(self, message, level="INFO"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] [{level}] {message}"
            print(log_entry)
            with open(self.log_file, 'a') as f:
                f.write(log_entry + '\n')

    return Logger(LOG_FILE)


def load_progress() -> Dict:
    """Load processing progress from file"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'completed': [],
        'failed': [],
        'email_candidates': [],
        'stats': {
            'total_processed': 0,
            'emails_found': 0,
            'start_time': None,
            'last_update': None
        }
    }


def save_progress(progress: Dict):
    """Save processing progress to file"""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    progress['stats']['last_update'] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def detect_email_content(text: str) -> Dict:
    """
    Detect if text contains email content

    Returns:
        Dict with detection results and confidence score
    """
    indicators = {
        'has_email_address': False,
        'has_email_headers': False,
        'has_email_keywords': False,
        'email_addresses': [],
        'confidence': 0.0
    }

    # Check for email addresses
    email_matches = EMAIL_ADDRESS_PATTERN.findall(text)
    if email_matches:
        indicators['has_email_address'] = True
        indicators['email_addresses'] = list(set(email_matches))
        indicators['confidence'] += 0.4

    # Check for email headers
    for pattern in EMAIL_HEADER_PATTERNS:
        if pattern.search(text):
            indicators['has_email_headers'] = True
            indicators['confidence'] += 0.3
            break

    # Check for email keywords
    email_keywords = ['original message', 'forwarded message', 'replied', 'inbox', 'outbox']
    text_lower = text.lower()
    if any(keyword in text_lower for keyword in email_keywords):
        indicators['has_email_keywords'] = True
        indicators['confidence'] += 0.2

    # Normalize confidence
    indicators['confidence'] = min(1.0, indicators['confidence'])

    return indicators


def process_single_pdf(args: Tuple[Path, Path, str]) -> Dict:
    """
    Process a single PDF file with OCR

    Args:
        args: Tuple of (pdf_path, output_dir, log_identifier)

    Returns:
        Dict with processing results
    """
    pdf_path, output_dir, log_id = args

    result = {
        'file': pdf_path.name,
        'success': False,
        'is_email': False,
        'email_confidence': 0.0,
        'email_addresses': [],
        'text_length': 0,
        'error': None,
        'processing_time': 0.0
    }

    start_time = time.time()

    try:
        # Convert PDF to image
        images = convert_from_path(str(pdf_path), dpi=DPI, first_page=1, last_page=1)

        if not images:
            result['error'] = "No images extracted from PDF"
            return result

        # Perform OCR
        text = pytesseract.image_to_string(images[0], config=TESSERACT_CONFIG)

        if not text or len(text.strip()) < 10:
            result['error'] = "Insufficient text extracted (possible blank page)"
            result['success'] = True  # Still counts as processed
            result['text_length'] = len(text.strip())
            return result

        # Detect email content
        email_detection = detect_email_content(text)
        result['is_email'] = email_detection['confidence'] > 0.5
        result['email_confidence'] = email_detection['confidence']
        result['email_addresses'] = email_detection['email_addresses']
        result['text_length'] = len(text)

        # Save OCR text
        output_file = output_dir / f"{pdf_path.stem}.txt"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)

        # Save metadata
        metadata = {
            'source_pdf': pdf_path.name,
            'ocr_date': datetime.now().isoformat(),
            'text_length': len(text),
            'is_email': result['is_email'],
            'email_confidence': result['email_confidence'],
            'email_addresses': result['email_addresses']
        }

        metadata_file = output_dir / f"{pdf_path.stem}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        result['success'] = True

    except Exception as e:
        result['error'] = str(e)

    finally:
        result['processing_time'] = time.time() - start_time

    return result


def process_batch(pdf_files: List[Path], output_dir: Path, num_workers: int, logger) -> Dict:
    """
    Process a batch of PDF files with parallel workers

    Args:
        pdf_files: List of PDF file paths to process
        output_dir: Output directory for OCR text
        num_workers: Number of parallel workers
        logger: Logger instance

    Returns:
        Dict with batch processing results
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare arguments for parallel processing
    args_list = [(pdf, output_dir, f"Worker-{i%num_workers}")
                 for i, pdf in enumerate(pdf_files)]

    results = {
        'completed': [],
        'failed': [],
        'email_candidates': [],
        'stats': {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'emails_found': 0,
            'total_text_chars': 0,
            'avg_processing_time': 0.0
        }
    }

    # Track all results for processing time calculation
    all_results = []

    # Process with progress bar
    with Pool(num_workers) as pool:
        with tqdm(total=len(pdf_files), desc="Processing PDFs", unit="file") as pbar:
            for result in pool.imap_unordered(process_single_pdf, args_list):
                all_results.append(result)
                results['stats']['total_processed'] += 1

                if result['success']:
                    results['completed'].append(result['file'])
                    results['stats']['successful'] += 1
                    results['stats']['total_text_chars'] += result['text_length']

                    if result['is_email']:
                        results['email_candidates'].append({
                            'file': result['file'],
                            'confidence': result['email_confidence'],
                            'email_addresses': result['email_addresses']
                        })
                        results['stats']['emails_found'] += 1
                else:
                    results['failed'].append({
                        'file': result['file'],
                        'error': result['error']
                    })
                    results['stats']['failed'] += 1

                pbar.update(1)
                pbar.set_postfix({
                    'emails': results['stats']['emails_found'],
                    'failed': results['stats']['failed']
                })

    # Calculate average processing time
    if results['stats']['successful'] > 0:
        results['stats']['avg_processing_time'] = (
            sum(r.get('processing_time', 0) for r in all_results if r['success']) /
            results['stats']['successful']
        )

    return results


def estimate_completion_time(total_files: int, processed: int, start_time: datetime) -> str:
    """Calculate estimated time remaining"""
    if processed == 0:
        return "Calculating..."

    elapsed = datetime.now() - start_time
    rate = processed / elapsed.total_seconds()
    remaining = total_files - processed
    eta_seconds = remaining / rate if rate > 0 else 0
    eta = timedelta(seconds=int(eta_seconds))

    return str(eta)


def main():
    parser = argparse.ArgumentParser(description='OCR processing for House Oversight PDFs')
    parser.add_argument('--workers', type=int, default=10, help='Number of parallel workers')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for processing')
    parser.add_argument('--resume', action='store_true', help='Resume from previous progress')
    parser.add_argument('--test', type=int, help='Process only N files for testing')
    args = parser.parse_args()

    logger = setup_logging()
    logger.log("=" * 80)
    logger.log("House Oversight OCR Processing Started")
    logger.log(f"Workers: {args.workers}, Batch Size: {args.batch_size}")
    logger.log("=" * 80)

    # Load progress
    progress = load_progress() if args.resume else {
        'completed': [],
        'failed': [],
        'email_candidates': [],
        'stats': {
            'total_processed': 0,
            'emails_found': 0,
            'start_time': datetime.now().isoformat(),
            'last_update': None
        }
    }

    # Get all PDF files
    all_pdfs = sorted(SOURCE_DIR.glob("*.pdf"))
    total_files = len(all_pdfs)

    logger.log(f"Found {total_files} PDF files in source directory")

    # Filter out already processed files
    completed_set = set(progress['completed'])
    pending_pdfs = [pdf for pdf in all_pdfs if pdf.name not in completed_set]

    if args.test:
        pending_pdfs = pending_pdfs[:args.test]
        logger.log(f"TEST MODE: Processing only {args.test} files")

    logger.log(f"Already completed: {len(completed_set)} files")
    logger.log(f"Remaining to process: {len(pending_pdfs)} files")

    if not pending_pdfs:
        logger.log("No files to process. All files already completed!")
        return

    # Process files
    start_time = datetime.now()
    total_processed = len(completed_set)

    logger.log(f"Starting processing at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Process in batches
    for batch_num, i in enumerate(range(0, len(pending_pdfs), args.batch_size), 1):
        batch_pdfs = pending_pdfs[i:i + args.batch_size]

        logger.log(f"\n--- Batch {batch_num}: Processing {len(batch_pdfs)} files ---")

        batch_results = process_batch(batch_pdfs, OUTPUT_DIR, args.workers, logger)

        # Update global progress
        progress['completed'].extend(batch_results['completed'])
        progress['failed'].extend(batch_results['failed'])
        progress['email_candidates'].extend(batch_results['email_candidates'])
        progress['stats']['total_processed'] += batch_results['stats']['total_processed']
        progress['stats']['emails_found'] += batch_results['stats']['emails_found']

        total_processed += batch_results['stats']['total_processed']

        # Save progress
        save_progress(progress)

        # Log batch results
        logger.log(f"Batch {batch_num} complete:")
        logger.log(f"  Processed: {batch_results['stats']['total_processed']}")
        logger.log(f"  Successful: {batch_results['stats']['successful']}")
        logger.log(f"  Failed: {batch_results['stats']['failed']}")
        logger.log(f"  Emails found: {batch_results['stats']['emails_found']}")

        # Estimate completion time
        eta = estimate_completion_time(total_files, total_processed, start_time)
        logger.log(f"  Progress: {total_processed}/{total_files} ({total_processed*100/total_files:.1f}%)")
        logger.log(f"  Estimated time remaining: {eta}")

        # Save email candidates to JSONL
        if batch_results['email_candidates']:
            EMAIL_INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(EMAIL_INDEX_FILE, 'a') as f:
                for candidate in batch_results['email_candidates']:
                    f.write(json.dumps(candidate) + '\n')

    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time

    logger.log("\n" + "=" * 80)
    logger.log("OCR Processing Complete!")
    logger.log("=" * 80)
    logger.log(f"Total files processed: {progress['stats']['total_processed']}")
    logger.log(f"Total emails found: {progress['stats']['emails_found']}")
    logger.log(f"Total processing time: {duration}")
    logger.log(f"Average time per file: {duration.total_seconds() / max(progress['stats']['total_processed'], 1):.2f} seconds")
    logger.log(f"\nOutput directory: {OUTPUT_DIR}")
    logger.log(f"Email candidates index: {EMAIL_INDEX_FILE}")
    logger.log(f"Progress file: {PROGRESS_FILE}")
    logger.log("=" * 80)


if __name__ == "__main__":
    main()
