#!/usr/bin/env python3
"""
Validate news articles against canonical schema.

This script validates:
1. Schema compliance (JSON Schema validation)
2. UUID format and uniqueness
3. Entity UUID references exist
4. Required fields present
5. Data integrity (dates, URLs, etc.)

Usage:
    python scripts/validation/validate_news.py
    python scripts/validation/validate_news.py --verbose
"""

import json
import uuid
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
from collections import defaultdict

try:
    import jsonschema
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    print("⚠️  jsonschema not installed. Install with: pip install jsonschema")

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
SCHEMAS_DIR = DATA_DIR / "schemas"
TRANSFORMED_DIR = DATA_DIR / "transformed"

NEWS_FILE = TRANSFORMED_DIR / "news_articles.json"
SCHEMA_FILE = SCHEMAS_DIR / "news_schema.json"
ENTITY_MAPPINGS_FILE = TRANSFORMED_DIR / "entity_uuid_mappings.json"


def validate_uuid_format(uuid_str: str) -> bool:
    """Validate UUID format."""
    try:
        uuid.UUID(uuid_str)
        return True
    except (ValueError, AttributeError):
        return False


def validate_url_format(url: str) -> bool:
    """Validate URL format (basic check)."""
    if not url:
        return False
    pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(pattern.match(url))


def validate_date_format(date_str: str) -> bool:
    """Validate ISO date format (YYYY-MM-DD)."""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except (ValueError, TypeError):
        return False


def validate_schema_compliance(article: Dict[str, Any], schema: Dict) -> Tuple[bool, List[str]]:
    """
    Validate article against JSON schema.

    Returns:
        (is_valid, error_messages)
    """
    if not JSONSCHEMA_AVAILABLE:
        return True, ["JSON Schema validation skipped (jsonschema not installed)"]

    errors = []
    try:
        validate(instance=article, schema=schema)
        return True, []
    except ValidationError as e:
        errors.append(f"Schema validation error: {e.message}")
        return False, errors


def validate_article(
    article: Dict[str, Any],
    schema: Dict,
    entity_uuids: set,
    news_ids_seen: set,
    verbose: bool = False
) -> Tuple[bool, List[str]]:
    """
    Validate single news article.

    Returns:
        (is_valid, errors)
    """
    errors = []

    # Check schema compliance
    schema_valid, schema_errors = validate_schema_compliance(article, schema)
    if not schema_valid:
        errors.extend(schema_errors)

    # Validate news_id
    news_id = article.get('news_id')
    if not news_id:
        errors.append("Missing news_id")
    elif not validate_uuid_format(news_id):
        errors.append(f"Invalid news_id UUID format: {news_id}")
    elif news_id in news_ids_seen:
        errors.append(f"Duplicate news_id: {news_id}")
    else:
        news_ids_seen.add(news_id)

    # Validate required fields
    required_fields = ['source_url', 'title', 'published_date', 'publication']
    for field in required_fields:
        if field not in article or not article[field]:
            errors.append(f"Missing required field: {field}")

    # Validate source_url format
    source_url = article.get('source_url')
    if source_url and not validate_url_format(source_url):
        errors.append(f"Invalid source_url format: {source_url}")

    # Validate published_date format
    published_date = article.get('published_date')
    if published_date and not validate_date_format(published_date):
        errors.append(f"Invalid published_date format: {published_date}")

    # Validate entity UUIDs
    extracted_entities = article.get('extracted_entities', [])
    for entity_uuid in extracted_entities:
        if not validate_uuid_format(entity_uuid):
            errors.append(f"Invalid entity UUID format: {entity_uuid}")
        elif entity_uuid not in entity_uuids:
            errors.append(f"Entity UUID not found in mappings: {entity_uuid}")

    # Validate entity_mention_counts
    entity_mention_counts = article.get('entity_mention_counts', {})
    for entity_uuid, count in entity_mention_counts.items():
        if not validate_uuid_format(entity_uuid):
            errors.append(f"Invalid entity UUID in mention_counts: {entity_uuid}")
        if not isinstance(count, int) or count < 1:
            errors.append(f"Invalid mention count for {entity_uuid}: {count}")

    # Check consistency between extracted_entities and mention_counts
    extracted_set = set(extracted_entities)
    mentioned_set = set(entity_mention_counts.keys())
    if extracted_set != mentioned_set:
        missing_in_counts = extracted_set - mentioned_set
        extra_in_counts = mentioned_set - extracted_set
        if missing_in_counts:
            errors.append(f"Entities in extracted_entities but not in mention_counts: {missing_in_counts}")
        if extra_in_counts:
            errors.append(f"Entities in mention_counts but not in extracted_entities: {extra_in_counts}")

    # Validate enums
    credibility = article.get('credibility_indicator')
    if credibility and credibility not in ['high', 'medium', 'low', 'unknown']:
        errors.append(f"Invalid credibility_indicator: {credibility}")

    article_type = article.get('article_type')
    valid_types = ['breaking_news', 'investigation', 'opinion', 'court_coverage',
                   'profile', 'timeline', 'analysis', 'other']
    if article_type and article_type not in valid_types:
        errors.append(f"Invalid article_type: {article_type}")

    archive_status = article.get('archive_status')
    if archive_status and archive_status not in ['archived', 'not_archived', 'pending']:
        errors.append(f"Invalid archive_status: {archive_status}")

    # Validate archive_url if present
    archive_url = article.get('archive_url')
    if archive_url and not validate_url_format(archive_url):
        errors.append(f"Invalid archive_url format: {archive_url}")

    is_valid = len(errors) == 0
    return is_valid, errors


def main():
    """Main validation function."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate news articles against schema')
    parser.add_argument('--verbose', action='store_true', help='Show validation details for each article')
    args = parser.parse_args()

    print("=" * 80)
    print("News Article Validation")
    print("=" * 80)
    print()

    # Load schema
    print(f"Loading schema: {SCHEMA_FILE}")
    with open(SCHEMA_FILE, 'r') as f:
        schema = json.load(f)
    print("  ✓ Schema loaded")
    print()

    # Load entity mappings
    print(f"Loading entity mappings: {ENTITY_MAPPINGS_FILE}")
    with open(ENTITY_MAPPINGS_FILE, 'r') as f:
        entity_mappings = json.load(f)

    entity_uuids = set(entity_mappings['mappings'].keys())
    print(f"  ✓ Loaded {len(entity_uuids):,} entity UUIDs")
    print()

    # Load news articles
    print(f"Loading news articles: {NEWS_FILE}")
    with open(NEWS_FILE, 'r') as f:
        news_data = json.load(f)

    articles = news_data['articles']
    metadata = news_data['metadata']

    print(f"  Total articles: {metadata['total_articles']:,}")
    print()

    # Validate articles
    print("Validating articles...")
    print()

    news_ids_seen = set()
    valid_count = 0
    invalid_count = 0
    all_errors = []

    stats = {
        'by_error_type': defaultdict(int),
        'invalid_articles': []
    }

    for i, article in enumerate(articles):
        if (i + 1) % 50 == 0:
            print(f"  Validated {i + 1:,} articles...")

        is_valid, errors = validate_article(
            article,
            schema,
            entity_uuids,
            news_ids_seen,
            verbose=args.verbose
        )

        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
            all_errors.extend(errors)

            # Track invalid article
            stats['invalid_articles'].append({
                'news_id': article.get('news_id', 'UNKNOWN'),
                'title': article.get('title', 'UNKNOWN'),
                'errors': errors
            })

            # Categorize errors
            for error in errors:
                # Extract error type (first part before colon)
                error_type = error.split(':')[0] if ':' in error else error
                stats['by_error_type'][error_type] += 1

            if args.verbose:
                print(f"\n❌ Invalid article: {article.get('title', 'UNKNOWN')[:60]}")
                print(f"   news_id: {article.get('news_id', 'UNKNOWN')}")
                for error in errors:
                    print(f"   - {error}")

    print()
    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print()

    # Overall results
    total = valid_count + invalid_count
    success_rate = (valid_count / total * 100) if total > 0 else 0

    print(f"Total articles validated: {total:,}")
    print(f"  ✓ Valid: {valid_count:,} ({success_rate:.1f}%)")
    if invalid_count > 0:
        print(f"  ✗ Invalid: {invalid_count:,} ({100 - success_rate:.1f}%)")
    print()

    # UUID validation
    print(f"UUID Validation:")
    print(f"  Unique news_ids: {len(news_ids_seen):,}")
    print(f"  Expected: {total:,}")
    if len(news_ids_seen) == total:
        print(f"  ✓ All news_ids are unique")
    else:
        duplicates = total - len(news_ids_seen)
        print(f"  ✗ {duplicates} duplicate news_ids found")
    print()

    # Error breakdown
    if invalid_count > 0:
        print("Error Breakdown:")
        for error_type, count in sorted(stats['by_error_type'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_type:40s}: {count:4,}")
        print()

        # Show sample invalid articles
        print("Sample Invalid Articles (first 5):")
        for article in stats['invalid_articles'][:5]:
            print(f"  {article['title'][:60]}")
            print(f"    news_id: {article['news_id']}")
            for error in article['errors'][:3]:  # Show first 3 errors
                print(f"      - {error}")
            if len(article['errors']) > 3:
                print(f"      ... and {len(article['errors']) - 3} more errors")
            print()

    # Final verdict
    print("=" * 80)
    if invalid_count == 0:
        print("✅ ALL ARTICLES VALID")
        print("=" * 80)
        return 0
    else:
        print("❌ VALIDATION FAILED")
        print("=" * 80)
        print()
        print("Action required:")
        print("1. Review errors above")
        print("2. Fix data issues in source or transformation script")
        print("3. Re-run transformation: scripts/transformations/generate_news_uuids.py")
        print("4. Re-validate: scripts/validation/validate_news.py")
        return 1


if __name__ == '__main__':
    exit(main())
