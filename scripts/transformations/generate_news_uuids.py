#!/usr/bin/env python3
"""
Generate deterministic UUIDs for news articles and transform to canonical schema.

This script:
1. Generates UUID5 from source_url (deterministic)
2. Maps entity names to entity UUIDs
3. Transforms news articles to canonical schema
4. Creates mapping file for cross-reference

Design Decision:
- News items are NOT documents (they're supplementary, non-authoritative)
- UUID5 based on source_url ensures same article always gets same UUID
- Entity linking uses entity UUIDs from Issue #18

Usage:
    python scripts/transformations/generate_news_uuids.py
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

# UUID namespace for news articles (DNS namespace)
NEWS_NAMESPACE = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
METADATA_DIR = DATA_DIR / "metadata"
TRANSFORMED_DIR = DATA_DIR / "transformed"

SOURCE_FILE = METADATA_DIR / "news_articles_index.json"
ENTITY_MAPPINGS_FILE = TRANSFORMED_DIR / "entity_uuid_mappings.json"
OUTPUT_FILE = TRANSFORMED_DIR / "news_articles.json"
MAPPINGS_FILE = TRANSFORMED_DIR / "news_uuid_mappings.json"


def generate_news_uuid(source_url: str) -> str:
    """
    Generate deterministic UUID5 from source URL.

    Args:
        source_url: Original article URL

    Returns:
        UUID string in canonical form

    Design Decision: UUID5 with DNS namespace ensures:
    - Deterministic: Same URL always generates same UUID
    - Collision-resistant: Different URLs generate different UUIDs
    - Standard: Uses official UUID5 specification (RFC 4122)
    """
    # Normalize URL (lowercase, strip trailing slash)
    normalized_url = source_url.lower().rstrip('/')

    # Generate UUID5 from normalized URL
    return str(uuid.uuid5(NEWS_NAMESPACE, normalized_url))


def normalize_entity_name(name: str) -> str:
    """
    Normalize entity name for matching against entity_uuid_mappings.

    Same normalization as entity UUID generation to ensure matches.
    """
    import re

    # Lowercase
    normalized = name.lower()

    # Remove possessives
    normalized = re.sub(r"'s\b", "", normalized)

    # Remove commas and most punctuation, keep hyphens
    normalized = re.sub(r"[,\.;:!?\"']", "", normalized)

    # Collapse multiple spaces
    normalized = re.sub(r"\s+", " ", normalized)

    # Strip whitespace
    normalized = normalized.strip()

    return normalized


def build_entity_lookup(mappings_data: Dict) -> Dict[str, str]:
    """
    Build lookup map from normalized entity name to UUID.

    Returns:
        Dict mapping normalized_name -> entity_uuid
    """
    lookup = {}

    for entity_uuid, entity_data in mappings_data['mappings'].items():
        # Map canonical name
        canonical = entity_data['canonical_name']
        normalized = normalize_entity_name(canonical)
        lookup[normalized] = entity_uuid

        # Map aliases
        for alias in entity_data.get('aliases', []):
            normalized_alias = normalize_entity_name(alias)
            if normalized_alias not in lookup:
                lookup[normalized_alias] = entity_uuid

    return lookup


def map_entity_to_uuid(entity_name: str, entity_lookup: Dict[str, str]) -> str | None:
    """
    Map entity name to UUID using lookup table.

    Args:
        entity_name: Entity name from news article
        entity_lookup: Normalized name -> UUID mapping

    Returns:
        Entity UUID or None if not found
    """
    normalized = normalize_entity_name(entity_name)
    return entity_lookup.get(normalized)


def classify_article_type(article: Dict[str, Any]) -> str:
    """
    Classify article type based on tags and content.

    Returns:
        article_type from canonical enum
    """
    tags = article.get('tags', [])
    tags_str = ' '.join(tags).lower()

    # Classification logic based on tags
    if 'court' in tags_str or 'legal' in tags_str or 'trial' in tags_str:
        return 'court_coverage'
    elif 'investigation' in tags_str:
        return 'investigation'
    elif 'timeline' in tags_str:
        return 'timeline'
    elif 'analysis' in tags_str:
        return 'analysis'
    elif 'breaking' in tags_str:
        return 'breaking_news'
    elif 'profile' in tags_str or 'biography' in tags_str:
        return 'profile'
    elif 'opinion' in tags_str or 'editorial' in tags_str:
        return 'opinion'
    else:
        return 'other'


def assess_credibility(article: Dict[str, Any]) -> str:
    """
    Assess publication credibility based on tier.

    Maps credibility_score and tier to canonical indicator.
    """
    credibility_score = article.get('credibility_score', 0.0)
    tier = article.get('credibility_factors', {}).get('tier', 'unknown')

    # Map tier to credibility indicator
    tier_mapping = {
        'tier_1': 'high',     # Major newspapers, AP, Reuters
        'tier_2': 'medium',   # Regional papers, specialty outlets
        'tier_3': 'low'       # Questionable sources
    }

    credibility = tier_mapping.get(tier, 'unknown')

    # Adjust based on score if available
    if credibility_score >= 0.8:
        return 'high'
    elif credibility_score >= 0.6:
        return 'medium' if credibility != 'high' else 'high'
    elif credibility_score >= 0.4:
        return 'medium'
    elif credibility_score > 0:
        return 'low'

    return credibility


def transform_news_article(
    article: Dict[str, Any],
    entity_lookup: Dict[str, str]
) -> Dict[str, Any]:
    """
    Transform news article to canonical schema.

    Args:
        article: Legacy news article
        entity_lookup: Entity name -> UUID mapping

    Returns:
        Transformed article matching canonical schema
    """
    # Generate UUID from source URL
    source_url = article['url']
    news_id = generate_news_uuid(source_url)

    # Map entities to UUIDs
    entity_names = article.get('entities_mentioned', [])
    extracted_entities = []
    entity_mention_counts = {}
    unmatched_entities = []

    for entity_name in entity_names:
        entity_uuid = map_entity_to_uuid(entity_name, entity_lookup)

        if entity_uuid:
            # Get mention count from original data (default to 1 if missing or 0)
            count = article.get('entity_mention_counts', {}).get(entity_name, 1)

            # Skip entities with 0 mentions (data quality issue in source)
            if count == 0:
                continue

            extracted_entities.append(entity_uuid)
            entity_mention_counts[entity_uuid] = count
        else:
            unmatched_entities.append(entity_name)

    # Build canonical article
    canonical = {
        'news_id': news_id,
        'source_url': source_url,
        'publication': article['publication'],
        'published_date': article['published_date'],
        'title': article['title'],
        'author': article.get('author'),
        'content_excerpt': article.get('content_excerpt', ''),
        'word_count': article.get('word_count', 0),
        'extracted_entities': extracted_entities,
        'entity_mention_counts': entity_mention_counts,
        'credibility_indicator': assess_credibility(article),
        'article_type': classify_article_type(article),
        'tags': article.get('tags', []),
        'archive_url': article.get('archive_url'),
        'archive_status': article.get('archive_status', 'not_archived')
    }

    # Add legacy IDs
    canonical['legacy_ids'] = {
        'original_id': article['id']
    }

    # Add metadata
    canonical['metadata'] = {
        'scraped_at': article.get('scraped_at'),
        'last_verified': article.get('last_verified'),
        'language': article.get('language', 'en'),
        'access_type': article.get('access_type', 'public')
    }

    # Track unmatched entities for reporting
    if unmatched_entities:
        canonical['metadata']['unmatched_entities'] = unmatched_entities

    return canonical


def create_mapping_entry(article: Dict[str, Any], canonical: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create mapping entry for old ID to new UUID.

    Args:
        article: Legacy news article
        canonical: Transformed article

    Returns:
        Mapping dictionary
    """
    return {
        'news_id': canonical['news_id'],
        'legacy_id': article['id'],
        'source_url': canonical['source_url'],
        'publication': canonical['publication'],
        'published_date': canonical['published_date'],
        'title': canonical['title']
    }


def main():
    """Main execution function."""
    print("=" * 80)
    print("News Article UUID Generation and Transformation")
    print("=" * 80)
    print()

    # Load entity mappings
    print(f"Loading entity mappings: {ENTITY_MAPPINGS_FILE}")
    with open(ENTITY_MAPPINGS_FILE, 'r') as f:
        entity_mappings = json.load(f)

    print(f"  Total entities: {len(entity_mappings['mappings']):,}")

    # Build entity lookup
    print("Building entity lookup table...")
    entity_lookup = build_entity_lookup(entity_mappings)
    print(f"  Lookup entries: {len(entity_lookup):,}")
    print()

    # Load news articles
    print(f"Loading news articles: {SOURCE_FILE}")
    with open(SOURCE_FILE, 'r') as f:
        news_data = json.load(f)

    articles = news_data['articles']
    metadata = news_data['metadata']

    print(f"  Total articles: {metadata['total_articles']:,}")
    print(f"  Date range: {metadata['date_range']['earliest']} to {metadata['date_range']['latest']}")
    print(f"  Sources: {len(metadata['sources'])}")
    print()

    # Transform articles
    print("Transforming articles...")
    transformed_articles = []
    uuid_mappings = []

    # Statistics
    stats = {
        'total': 0,
        'with_entities': 0,
        'total_entity_mentions': 0,
        'unmatched_entities': 0,
        'by_publication': defaultdict(int),
        'by_type': defaultdict(int),
        'by_credibility': defaultdict(int)
    }

    unmatched_entity_names = set()

    for i, article in enumerate(articles):
        if i % 50 == 0 and i > 0:
            print(f"  Processed {i:,} articles...")

        canonical = transform_news_article(article, entity_lookup)
        transformed_articles.append(canonical)

        mapping = create_mapping_entry(article, canonical)
        uuid_mappings.append(mapping)

        # Update statistics
        stats['total'] += 1
        if canonical['extracted_entities']:
            stats['with_entities'] += 1
        stats['total_entity_mentions'] += len(canonical['extracted_entities'])
        stats['by_publication'][canonical['publication']] += 1
        stats['by_type'][canonical['article_type']] += 1
        stats['by_credibility'][canonical['credibility_indicator']] += 1

        # Track unmatched entities
        unmatched = canonical['metadata'].get('unmatched_entities', [])
        if unmatched:
            stats['unmatched_entities'] += len(unmatched)
            unmatched_entity_names.update(unmatched)

    print(f"✓ Transformed {len(transformed_articles):,} articles")
    print()

    # Generate statistics
    print("Article Statistics:")
    print(f"  Total articles: {stats['total']:,}")
    print(f"  Articles with entities: {stats['with_entities']:,} ({stats['with_entities']/stats['total']*100:.1f}%)")
    print(f"  Total entity mentions: {stats['total_entity_mentions']:,}")
    print(f"  Avg mentions per article: {stats['total_entity_mentions']/stats['total']:.1f}")
    print()

    print("Article Type Distribution:")
    for article_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
        pct = (count / stats['total']) * 100
        print(f"  {article_type:20s}: {count:4,} ({pct:5.1f}%)")
    print()

    print("Credibility Distribution:")
    for cred, count in sorted(stats['by_credibility'].items(), key=lambda x: x[1], reverse=True):
        pct = (count / stats['total']) * 100
        print(f"  {cred:10s}: {count:4,} ({pct:5.1f}%)")
    print()

    print("Top 10 Publications:")
    for pub, count in sorted(stats['by_publication'].items(), key=lambda x: x[1], reverse=True)[:10]:
        pct = (count / stats['total']) * 100
        print(f"  {pub:30s}: {count:3,} ({pct:5.1f}%)")
    print()

    # Entity matching report
    if stats['unmatched_entities'] > 0:
        print(f"⚠️  Unmatched Entities: {stats['unmatched_entities']:,} mentions of {len(unmatched_entity_names)} unique entities")
        print("  Top unmatched entities:")
        for entity_name in sorted(unmatched_entity_names)[:10]:
            print(f"    - {entity_name}")
        print()

    # Save outputs
    TRANSFORMED_DIR.mkdir(exist_ok=True)

    # Save transformed articles
    print(f"Saving transformed articles: {OUTPUT_FILE}")
    output_data = {
        'metadata': {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'schema_version': '1.0',
            'total_articles': len(transformed_articles),
            'namespace': str(NEWS_NAMESPACE),
            'date_range': metadata['date_range'],
            'statistics': {
                'with_entities': stats['with_entities'],
                'total_entity_mentions': stats['total_entity_mentions'],
                'unmatched_entities': stats['unmatched_entities'],
                'unique_unmatched': len(unmatched_entity_names)
            }
        },
        'articles': transformed_articles
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output_data, f, indent=2)

    file_size_mb = OUTPUT_FILE.stat().st_size / 1024 / 1024
    print(f"  Size: {file_size_mb:.2f} MB")
    print()

    # Save UUID mappings
    print(f"Saving UUID mappings: {MAPPINGS_FILE}")
    mappings_output = {
        'metadata': {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_mappings': len(uuid_mappings)
        },
        'mappings': uuid_mappings
    }

    with open(MAPPINGS_FILE, 'w') as f:
        json.dump(mappings_output, f, indent=2)

    print()
    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)
    print()
    print(f"Transformed articles: {OUTPUT_FILE}")
    print(f"UUID mappings: {MAPPINGS_FILE}")
    print()
    print("Next steps:")
    print("1. Validate schema compliance: scripts/validation/validate_news.py")
    print("2. Review unmatched entities for missing entity records")
    print("3. Update API endpoints to use news UUIDs")
    print()


if __name__ == '__main__':
    main()
