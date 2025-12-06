#!/usr/bin/env python3
"""
Relationship Gap Analysis Script
Audits document-entity, entity-entity, and news-entity relationships
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# Paths
DATA_DIR = Path("/Users/masa/Projects/epstein/data/metadata")
DOCS_ENTITIES = DATA_DIR / "document_entities_full.json"
ENTITY_DOCS = DATA_DIR / "entity_document_index.json"
ENTITY_NETWORK = DATA_DIR / "entity_network.json"
ENTITY_RELATIONSHIPS = DATA_DIR / "entity_relationships_enhanced.json"
NEWS_INDEX = DATA_DIR / "news_articles_index.json"
ENTITY_BIOGRAPHIES = DATA_DIR / "entity_biographies.json"


def load_json(filepath: Path) -> dict:
    """Load JSON file"""
    try:
        with open(filepath) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return {}


def analyze_doc_entity_bidirectionality():
    """Check if document-entity relationships are bidirectional"""
    print("\n=== ANALYZING DOCUMENT-ENTITY BIDIRECTIONALITY ===")

    doc_entities = load_json(DOCS_ENTITIES)
    entity_docs = load_json(ENTITY_DOCS)

    # Extract actual data
    entities_data = doc_entities.get("entities", {})
    entity_to_docs = entity_docs.get("entity_to_documents", {})

    print(f"Total entities in document_entities_full.json: {len(entities_data)}")
    print(f"Total entities in entity_document_index.json: {len(entity_to_docs)}")

    # Check for entities in docs but not in index
    entities_in_docs = set(entities_data.keys())
    entities_in_index = set(entity_to_docs.keys())

    missing_from_index = entities_in_docs - entities_in_index
    missing_from_docs = entities_in_index - entities_in_docs

    print(f"\nEntities in docs but NOT in index: {len(missing_from_index)}")
    if missing_from_index and len(missing_from_index) < 20:
        print(f"Missing from index: {sorted(list(missing_from_index))[:10]}")

    print(f"Entities in index but NOT in docs: {len(missing_from_docs)}")
    if missing_from_docs and len(missing_from_docs) < 20:
        print(f"Missing from docs: {sorted(list(missing_from_docs))[:10]}")

    # Analyze document sources vs entity index
    doc_mismatches = []
    for entity_name, entity_data in list(entities_data.items())[:100]:  # Sample
        if not entity_name or entity_name in ["-1", "-2", ""]:
            continue

        doc_sources = set(entity_data.get("document_sources", []))

        if entity_name in entity_to_docs:
            indexed_docs = set([d["doc_id"] for d in entity_to_docs[entity_name].get("documents", [])])

            if doc_sources != indexed_docs:
                missing_in_index = doc_sources - indexed_docs
                extra_in_index = indexed_docs - doc_sources
                if missing_in_index or extra_in_index:
                    doc_mismatches.append({
                        "entity": entity_name,
                        "missing_in_index": len(missing_in_index),
                        "extra_in_index": len(extra_in_index)
                    })

    print(f"\nDocument mismatches in sample of 100: {len(doc_mismatches)}")
    if doc_mismatches:
        print(f"Example mismatches: {doc_mismatches[:3]}")

    return {
        "total_entities_in_docs": len(entities_in_docs),
        "total_entities_in_index": len(entities_in_index),
        "missing_from_index": len(missing_from_index),
        "missing_from_docs": len(missing_from_docs),
        "doc_mismatches_in_sample": len(doc_mismatches)
    }


def analyze_entity_connections():
    """Analyze entity-entity connection completeness"""
    print("\n=== ANALYZING ENTITY-ENTITY CONNECTIONS ===")

    entity_network = load_json(ENTITY_NETWORK)
    entity_relationships = load_json(ENTITY_RELATIONSHIPS)

    nodes = entity_network.get("nodes", [])
    edges = entity_network.get("edges", [])
    relationships = entity_relationships.get("relationships", [])

    print(f"Entity network nodes: {len(nodes)}")
    print(f"Entity network edges: {len(edges)}")
    print(f"Enhanced relationships: {len(relationships)}")

    # Check bidirectionality of edges
    edge_pairs = defaultdict(list)
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        weight = edge.get("weight", 0)
        contexts = edge.get("contexts", [])

        edge_pairs[(source, target)].append({"weight": weight, "contexts": contexts})

    # Check for asymmetric connections
    asymmetric = []
    for (src, tgt), data in edge_pairs.items():
        reverse = (tgt, src)
        if reverse not in edge_pairs:
            asymmetric.append((src, tgt, data[0]["weight"]))

    print(f"\nAsymmetric connections (A→B but not B→A): {len(asymmetric)}")
    if asymmetric:
        print(f"Example asymmetric: {asymmetric[:5]}")

    # Analyze connection sources
    connection_sources = defaultdict(int)
    for edge in edges:
        for context in edge.get("contexts", []):
            connection_sources[context] += 1

    print(f"\nConnection sources:")
    for source, count in sorted(connection_sources.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count}")

    # Check relationship metadata
    relationships_with_metadata = [r for r in relationships if r.get("metadata")]
    print(f"\nRelationships with metadata: {len(relationships_with_metadata)}/{len(relationships)}")

    # Sample relationship structure
    if relationships:
        print(f"\nSample relationship structure:")
        sample = relationships[0]
        print(f"  Keys: {sample.keys()}")
        if "metadata" in sample:
            print(f"  Metadata keys: {sample['metadata'].keys() if sample['metadata'] else 'None'}")

    return {
        "network_nodes": len(nodes),
        "network_edges": len(edges),
        "enhanced_relationships": len(relationships),
        "asymmetric_connections": len(asymmetric),
        "connection_sources": dict(connection_sources),
        "relationships_with_metadata": len(relationships_with_metadata)
    }


def analyze_news_entity_links():
    """Analyze news article to entity relationships"""
    print("\n=== ANALYZING NEWS-ENTITY RELATIONSHIPS ===")

    news_index = load_json(NEWS_INDEX)
    entity_docs = load_json(ENTITY_DOCS)

    articles = news_index.get("articles", [])
    entity_to_docs = entity_docs.get("entity_to_documents", {})

    print(f"Total news articles: {len(articles)}")

    # Check entity mentions in news
    articles_with_entities = [a for a in articles if a.get("entities_mentioned")]
    articles_with_counts = [a for a in articles if a.get("entity_mention_counts")]

    print(f"Articles with entities_mentioned: {len(articles_with_entities)}")
    print(f"Articles with entity_mention_counts: {len(articles_with_counts)}")

    # Check if news articles are tracked in entity_document_index
    news_in_entity_index = 0
    for entity_name, entity_data in entity_to_docs.items():
        docs = entity_data.get("documents", [])
        for doc in docs:
            if "news" in doc.get("filename", "").lower() or "article" in doc.get("filename", "").lower():
                news_in_entity_index += 1
                break

    print(f"Entities with news documents in index: {news_in_entity_index}")

    # Analyze entity mention distribution
    entity_mentions = defaultdict(int)
    for article in articles_with_entities:
        for entity in article.get("entities_mentioned", []):
            entity_mentions[entity] += 1

    print(f"\nUnique entities mentioned in news: {len(entity_mentions)}")
    print(f"Top 10 mentioned entities:")
    for entity, count in sorted(entity_mentions.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {entity}: {count} articles")

    # Check for orphan news (no entity links)
    orphan_news = [a for a in articles if not a.get("entities_mentioned")]
    print(f"\nOrphan news articles (no entities): {len(orphan_news)}")

    return {
        "total_news_articles": len(articles),
        "articles_with_entities": len(articles_with_entities),
        "unique_entities_in_news": len(entity_mentions),
        "orphan_news_articles": len(orphan_news)
    }


def analyze_orphan_documents():
    """Find documents with no entity links"""
    print("\n=== ANALYZING ORPHAN DOCUMENTS ===")

    doc_entities = load_json(DOCS_ENTITIES)
    entities_data = doc_entities.get("entities", {})

    # Collect all document IDs that have entities
    docs_with_entities = set()
    for entity_data in entities_data.values():
        doc_sources = entity_data.get("document_sources", [])
        docs_with_entities.update(doc_sources)

    print(f"Total documents with entity links: {len(docs_with_entities)}")

    # Note: We'd need to check against master_document_index.json for total docs
    # For now, report what we have

    return {
        "documents_with_entities": len(docs_with_entities)
    }


def analyze_orphan_entities():
    """Find entities with no document links"""
    print("\n=== ANALYZING ORPHAN ENTITIES ===")

    entity_docs = load_json(ENTITY_DOCS)
    entity_biographies = load_json(ENTITY_BIOGRAPHIES)

    entity_to_docs = entity_docs.get("entity_to_documents", {})

    # Check for entities with no documents
    orphan_entities = []
    for entity_name, entity_data in entity_to_docs.items():
        docs = entity_data.get("documents", [])
        if not docs or len(docs) == 0:
            orphan_entities.append(entity_name)

    print(f"Entities with no document links: {len(orphan_entities)}")
    if orphan_entities:
        print(f"Sample orphan entities: {orphan_entities[:10]}")

    # Check entities in biographies but not in entity_document_index
    bio_entities = set(entity_biographies.keys()) if entity_biographies else set()
    index_entities = set(entity_to_docs.keys())

    in_bio_not_index = bio_entities - index_entities
    print(f"\nEntities in biographies but not in document index: {len(in_bio_not_index)}")
    if in_bio_not_index:
        print(f"Sample: {sorted(list(in_bio_not_index))[:10]}")

    return {
        "orphan_entities": len(orphan_entities),
        "in_bio_not_index": len(in_bio_not_index)
    }


def generate_report():
    """Generate comprehensive relationship gap analysis report"""
    print("Starting Relationship Gap Analysis...")
    print("=" * 70)

    results = {}

    # Run all analyses
    results["doc_entity_bidirectionality"] = analyze_doc_entity_bidirectionality()
    results["entity_connections"] = analyze_entity_connections()
    results["news_entity_links"] = analyze_news_entity_links()
    results["orphan_documents"] = analyze_orphan_documents()
    results["orphan_entities"] = analyze_orphan_entities()

    # Generate markdown report
    report_path = Path("/Users/masa/Projects/epstein/docs/audit/relationship-gap-analysis.md")

    with open(report_path, "w") as f:
        f.write("# Relationship Gap Analysis Report\n\n")
        f.write(f"**Generated:** {__import__('datetime').datetime.now().isoformat()}\n\n")

        f.write("## Executive Summary\n\n")
        f.write("This audit examines relationship completeness across documents, entities, and news articles.\n\n")

        f.write("## 1. Document-Entity Bidirectionality\n\n")
        f.write(f"- **Total entities in document_entities_full.json:** {results['doc_entity_bidirectionality']['total_entities_in_docs']:,}\n")
        f.write(f"- **Total entities in entity_document_index.json:** {results['doc_entity_bidirectionality']['total_entities_in_index']:,}\n")
        f.write(f"- **Entities missing from index:** {results['doc_entity_bidirectionality']['missing_from_index']:,}\n")
        f.write(f"- **Entities missing from docs:** {results['doc_entity_bidirectionality']['missing_from_docs']:,}\n\n")

        f.write("### Status\n")
        if results['doc_entity_bidirectionality']['missing_from_index'] > 0 or results['doc_entity_bidirectionality']['missing_from_docs'] > 0:
            f.write("⚠️ **PARTIAL** - Asymmetric relationships detected\n\n")
        else:
            f.write("✅ **COMPLETE** - Bidirectional relationships maintained\n\n")

        f.write("## 2. Entity-Entity Connections\n\n")
        f.write(f"- **Network nodes:** {results['entity_connections']['network_nodes']:,}\n")
        f.write(f"- **Network edges:** {results['entity_connections']['network_edges']:,}\n")
        f.write(f"- **Enhanced relationships:** {results['entity_connections']['enhanced_relationships']:,}\n")
        f.write(f"- **Asymmetric connections:** {results['entity_connections']['asymmetric_connections']:,}\n")
        f.write(f"- **Relationships with metadata:** {results['entity_connections']['relationships_with_metadata']:,}\n\n")

        f.write("### Connection Sources\n")
        for source, count in results['entity_connections']['connection_sources'].items():
            f.write(f"- **{source}:** {count:,} connections\n")
        f.write("\n")

        f.write("### Status\n")
        if results['entity_connections']['asymmetric_connections'] > 0:
            f.write("⚠️ **ASYMMETRIC** - Some connections are unidirectional\n\n")
        else:
            f.write("✅ **SYMMETRIC** - All connections are bidirectional\n\n")

        f.write("## 3. News-Entity Relationships\n\n")
        f.write(f"- **Total news articles:** {results['news_entity_links']['total_news_articles']:,}\n")
        f.write(f"- **Articles with entity links:** {results['news_entity_links']['articles_with_entities']:,}\n")
        f.write(f"- **Unique entities in news:** {results['news_entity_links']['unique_entities_in_news']:,}\n")
        f.write(f"- **Orphan news articles:** {results['news_entity_links']['orphan_news_articles']:,}\n\n")

        f.write("### Status\n")
        if results['news_entity_links']['orphan_news_articles'] > 0:
            f.write(f"⚠️ **INCOMPLETE** - {results['news_entity_links']['orphan_news_articles']} news articles lack entity links\n\n")
        else:
            f.write("✅ **COMPLETE** - All news articles have entity links\n\n")

        f.write("## 4. Orphan Entities\n\n")
        f.write(f"- **Entities with no documents:** {results['orphan_entities']['orphan_entities']:,}\n")
        f.write(f"- **In biographies but not index:** {results['orphan_entities']['in_bio_not_index']:,}\n\n")

        f.write("### Status\n")
        if results['orphan_entities']['orphan_entities'] > 0:
            f.write(f"⚠️ **GAP DETECTED** - {results['orphan_entities']['orphan_entities']} orphan entities found\n\n")
        else:
            f.write("✅ **COMPLETE** - All entities have document links\n\n")

        f.write("## 5. Identified Gaps\n\n")

        gaps = []
        if results['doc_entity_bidirectionality']['missing_from_index'] > 0:
            gaps.append(f"- **Missing reverse index:** {results['doc_entity_bidirectionality']['missing_from_index']} entities in docs not in index")
        if results['doc_entity_bidirectionality']['missing_from_docs'] > 0:
            gaps.append(f"- **Stale index entries:** {results['doc_entity_bidirectionality']['missing_from_docs']} entities in index not in docs")
        if results['entity_connections']['asymmetric_connections'] > 0:
            gaps.append(f"- **Asymmetric connections:** {results['entity_connections']['asymmetric_connections']} unidirectional entity links")
        if results['news_entity_links']['orphan_news_articles'] > 0:
            gaps.append(f"- **Orphan news:** {results['news_entity_links']['orphan_news_articles']} news articles without entity links")
        if results['orphan_entities']['orphan_entities'] > 0:
            gaps.append(f"- **Orphan entities:** {results['orphan_entities']['orphan_entities']} entities without documents")

        if gaps:
            f.write("\n".join(gaps))
            f.write("\n\n")
        else:
            f.write("✅ **No critical gaps detected**\n\n")

        f.write("## 6. Recommendations\n\n")
        f.write("### High Priority\n")
        if results['doc_entity_bidirectionality']['missing_from_index'] > 0:
            f.write("1. **Rebuild entity_document_index.json** to include all entities from document_entities_full.json\n")
        if results['entity_connections']['asymmetric_connections'] > 50:
            f.write("2. **Review asymmetric connections** - Most should be bidirectional for network analysis\n")
        if results['news_entity_links']['orphan_news_articles'] > 0:
            f.write("3. **Add entity extraction for news articles** - Currently missing entity links\n")

        f.write("\n### Medium Priority\n")
        f.write("1. **Add connection metadata** - Track when, where, and why entities are connected\n")
        f.write("2. **Implement connection weights** - Distinguish strong vs weak relationships\n")
        f.write("3. **Track connection sources** - Document vs flight log vs news article\n\n")

        f.write("### Low Priority\n")
        f.write("1. **Clean up orphan entities** - Remove or merge entities with no documents\n")
        f.write("2. **Validate entity name normalization** - Ensure consistent entity naming\n\n")

        f.write("## 7. Target Relationship Model\n\n")
        f.write("```\n")
        f.write("Document ↔ Entities (BIDIRECTIONAL)\n")
        f.write("  - document_entities_full.json: entities.{entity}.document_sources[]\n")
        f.write("  - entity_document_index.json: entity_to_documents.{entity}.documents[]\n")
        f.write("\n")
        f.write("Entity ↔ Entity (BIDIRECTIONAL)\n")
        f.write("  - entity_network.json: edges[] with source/target\n")
        f.write("  - Should have both A→B and B→A edges\n")
        f.write("  - Include connection metadata: source, weight, contexts\n")
        f.write("\n")
        f.write("News ↔ Entities (BIDIRECTIONAL)\n")
        f.write("  - news_articles_index.json: articles[].entities_mentioned[]\n")
        f.write("  - entity_document_index.json: Should track news as documents\n")
        f.write("```\n\n")

        f.write("---\n")
        f.write("*End of Report*\n")

    print(f"\n{'=' * 70}")
    print(f"Report saved to: {report_path}")
    print(f"{'=' * 70}\n")

    return results


if __name__ == "__main__":
    generate_report()
