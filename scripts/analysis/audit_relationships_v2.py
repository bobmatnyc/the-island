#!/usr/bin/env python3
"""
Relationship Gap Analysis Script v2
Audits document-entity, entity-entity, and news-entity relationships
Accounts for different entity naming formats
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
ALL_DOCUMENTS = DATA_DIR / "all_documents_index.json"


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

    # NOTE: Different formats - document_entities_full uses normalized lowercase names
    # entity_document_index uses "Last, First" format
    # This is NOT a bidirectionality issue but a naming format difference

    # Collect document coverage
    docs_from_entities_file = set()
    for entity_data in entities_data.values():
        doc_sources = entity_data.get("document_sources", [])
        docs_from_entities_file.update(doc_sources)

    docs_from_index_file = set()
    for entity_data in entity_to_docs.values():
        docs = entity_data.get("documents", [])
        for doc in docs:
            docs_from_index_file.add(doc.get("doc_id"))

    print(f"\nDocument coverage:")
    print(f"  Documents referenced in document_entities_full.json: {len(docs_from_entities_file)}")
    print(f"  Documents referenced in entity_document_index.json: {len(docs_from_index_file)}")

    common_docs = docs_from_entities_file & docs_from_index_file
    only_in_entities = docs_from_entities_file - docs_from_index_file
    only_in_index = docs_from_index_file - docs_from_entities_file

    print(f"  Common documents: {len(common_docs)}")
    print(f"  Only in document_entities_full: {len(only_in_entities)}")
    print(f"  Only in entity_document_index: {len(only_in_index)}")

    # Sample entity formats
    print(f"\nEntity naming formats:")
    print(f"  document_entities_full sample: {list(entities_data.keys())[1000:1003]}")
    print(f"  entity_document_index sample: {list(entity_to_docs.keys())[0:3]}")

    return {
        "entities_in_full": len(entities_data),
        "entities_in_index": len(entity_to_docs),
        "docs_in_full": len(docs_from_entities_file),
        "docs_in_index": len(docs_from_index_file),
        "common_docs": len(common_docs),
        "only_in_full": len(only_in_entities),
        "only_in_index": len(only_in_index),
        "format_issue": True  # Different entity name formats
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

    # Analyze edge directionality
    edge_map = {}
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        weight = edge.get("weight", 0)
        contexts = edge.get("contexts", [])

        key = f"{source}→{target}"
        edge_map[key] = {"weight": weight, "contexts": contexts}

    # Check for asymmetric connections
    asymmetric = []
    symmetric = []

    checked = set()
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")

        pair = tuple(sorted([source, target]))
        if pair in checked:
            continue
        checked.add(pair)

        forward = f"{source}→{target}"
        reverse = f"{target}→{source}"

        has_forward = forward in edge_map
        has_reverse = reverse in edge_map

        if has_forward and has_reverse:
            symmetric.append((source, target, edge_map[forward]["weight"], edge_map[reverse]["weight"]))
        elif has_forward:
            asymmetric.append((source, target, edge_map[forward]["weight"], "forward only"))
        elif has_reverse:
            asymmetric.append((target, source, edge_map[reverse]["weight"], "reverse only"))

    print(f"\nConnection symmetry:")
    print(f"  Symmetric (bidirectional): {len(symmetric)}")
    print(f"  Asymmetric (unidirectional): {len(asymmetric)}")

    if asymmetric:
        print(f"  Sample asymmetric: {asymmetric[:5]}")

    # Analyze connection sources
    connection_sources = defaultdict(int)
    for edge in edges:
        for context in edge.get("contexts", []):
            connection_sources[context] += 1

    print(f"\nConnection sources:")
    for source, count in sorted(connection_sources.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count} edges")

    # Check relationship metadata
    relationships_with_metadata = 0
    for rel in relationships:
        if rel.get("sources") or rel.get("confidence") or rel.get("notes"):
            relationships_with_metadata += 1

    print(f"\nRelationships with metadata: {relationships_with_metadata}/{len(relationships)}")

    # Sample relationship structure
    if relationships:
        print(f"\nSample relationship structure:")
        sample = relationships[0]
        print(f"  {sample}")

    return {
        "network_nodes": len(nodes),
        "network_edges": len(edges),
        "enhanced_relationships": len(relationships),
        "symmetric_connections": len(symmetric),
        "asymmetric_connections": len(asymmetric),
        "connection_sources": dict(connection_sources),
        "relationships_with_metadata": relationships_with_metadata
    }


def analyze_news_entity_links():
    """Analyze news article to entity relationships"""
    print("\n=== ANALYZING NEWS-ENTITY RELATIONSHIPS ===")

    news_index = load_json(NEWS_INDEX)
    articles = news_index.get("articles", [])

    print(f"Total news articles: {len(articles)}")

    # Check entity mentions in news
    articles_with_entities = [a for a in articles if a.get("entities_mentioned")]
    articles_with_counts = [a for a in articles if a.get("entity_mention_counts")]

    print(f"Articles with entities_mentioned: {len(articles_with_entities)}")
    print(f"Articles with entity_mention_counts: {len(articles_with_counts)}")

    # Analyze entity mention distribution
    entity_mentions = defaultdict(int)
    total_mentions = 0
    for article in articles_with_entities:
        for entity in article.get("entities_mentioned", []):
            entity_mentions[entity] += 1
            total_mentions += 1

    print(f"\nEntity coverage in news:")
    print(f"  Unique entities mentioned: {len(entity_mentions)}")
    print(f"  Total entity mentions: {total_mentions}")
    print(f"  Average entities per article: {total_mentions / len(articles) if articles else 0:.1f}")

    print(f"\nTop 10 mentioned entities:")
    for entity, count in sorted(entity_mentions.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {entity}: {count} articles")

    # Check for orphan news (no entity links)
    orphan_news = [a for a in articles if not a.get("entities_mentioned")]
    print(f"\nOrphan news articles (no entities): {len(orphan_news)}")

    # Check if news articles have IDs that could be tracked
    news_with_ids = [a for a in articles if a.get("id")]
    print(f"News articles with IDs: {len(news_with_ids)}")

    return {
        "total_news_articles": len(articles),
        "articles_with_entities": len(articles_with_entities),
        "unique_entities_in_news": len(entity_mentions),
        "total_entity_mentions": total_mentions,
        "orphan_news_articles": len(orphan_news),
        "news_with_ids": len(news_with_ids)
    }


def analyze_document_coverage():
    """Analyze total document coverage"""
    print("\n=== ANALYZING DOCUMENT COVERAGE ===")

    all_docs = load_json(ALL_DOCUMENTS)
    doc_entities = load_json(DOCS_ENTITIES)

    total_docs = len(all_docs.get("documents", []))
    print(f"Total documents in all_documents_index.json: {total_docs}")

    # Count documents with entities
    entities_data = doc_entities.get("entities", {})
    docs_with_entities = set()
    for entity_data in entities_data.values():
        doc_sources = entity_data.get("document_sources", [])
        docs_with_entities.update(doc_sources)

    print(f"Documents with entity links: {len(docs_with_entities)}")
    print(f"Documents without entities: {total_docs - len(docs_with_entities)}")
    print(f"Coverage: {len(docs_with_entities) / total_docs * 100:.1f}%")

    return {
        "total_documents": total_docs,
        "documents_with_entities": len(docs_with_entities),
        "orphan_documents": total_docs - len(docs_with_entities),
        "coverage_percent": len(docs_with_entities) / total_docs * 100 if total_docs else 0
    }


def generate_report():
    """Generate comprehensive relationship gap analysis report"""
    print("Starting Relationship Gap Analysis v2...")
    print("=" * 70)

    results = {}

    # Run all analyses
    results["doc_entity"] = analyze_doc_entity_bidirectionality()
    results["entity_connections"] = analyze_entity_connections()
    results["news_entity"] = analyze_news_entity_links()
    results["document_coverage"] = analyze_document_coverage()

    # Generate markdown report
    report_path = Path("/Users/masa/Projects/epstein/docs/audit/relationship-gap-analysis.md")

    with open(report_path, "w") as f:
        f.write("# Relationship Gap Analysis Report\n\n")
        f.write(f"**Generated:** {__import__('datetime').datetime.now().isoformat()}\n\n")

        f.write("## Executive Summary\n\n")
        f.write("This audit examines relationship completeness across documents, entities, and news articles.\n\n")

        # Key findings
        f.write("### Key Findings\n\n")

        gaps = []
        if results["doc_entity"]["format_issue"]:
            gaps.append("⚠️ **Entity naming format inconsistency** between files")
        if results["entity_connections"]["asymmetric_connections"] > 0:
            gaps.append(f"⚠️ **{results['entity_connections']['asymmetric_connections']} asymmetric connections** (unidirectional)")
        if results["document_coverage"]["orphan_documents"] > 0:
            gaps.append(f"⚠️ **{results['document_coverage']['orphan_documents']:,} orphan documents** ({100 - results['document_coverage']['coverage_percent']:.1f}% of total)")
        if results["news_entity"]["orphan_news_articles"] > 0:
            gaps.append(f"⚠️ **{results['news_entity']['orphan_news_articles']} orphan news articles**")

        if gaps:
            for gap in gaps:
                f.write(f"{gap}\n")
        else:
            f.write("✅ No critical relationship gaps detected\n")
        f.write("\n")

        # Detailed sections
        f.write("## 1. Document-Entity Relationships\n\n")
        f.write("### Overview\n")
        f.write(f"- **Entities in document_entities_full.json:** {results['doc_entity']['entities_in_full']:,}\n")
        f.write(f"- **Entities in entity_document_index.json:** {results['doc_entity']['entities_in_index']:,}\n")
        f.write(f"- **Documents in document_entities_full.json:** {results['doc_entity']['docs_in_full']:,}\n")
        f.write(f"- **Documents in entity_document_index.json:** {results['doc_entity']['docs_in_index']:,}\n\n")

        f.write("### Document Coverage Overlap\n")
        f.write(f"- **Common documents:** {results['doc_entity']['common_docs']:,}\n")
        f.write(f"- **Only in document_entities_full:** {results['doc_entity']['only_in_full']:,}\n")
        f.write(f"- **Only in entity_document_index:** {results['doc_entity']['only_in_index']:,}\n\n")

        f.write("### Critical Issue: Entity Naming Format Mismatch\n")
        f.write("⚠️ **WARNING:** The two files use different entity naming formats:\n\n")
        f.write("- `document_entities_full.json`: Uses lowercase normalized names (e.g., `colorado`, `nicole simmons`)\n")
        f.write("- `entity_document_index.json`: Uses \"Last, First\" format (e.g., `Maxwell, Ghislaine`)\n\n")
        f.write("**Impact:** Cannot directly compare entity lists due to format differences. Need entity name mapping.\n\n")

        f.write("## 2. Entity-Entity Connections\n\n")
        f.write(f"- **Network nodes:** {results['entity_connections']['network_nodes']:,}\n")
        f.write(f"- **Network edges:** {results['entity_connections']['network_edges']:,}\n")
        f.write(f"- **Symmetric connections:** {results['entity_connections']['symmetric_connections']:,}\n")
        f.write(f"- **Asymmetric connections:** {results['entity_connections']['asymmetric_connections']:,}\n")
        f.write(f"- **Enhanced relationships:** {results['entity_connections']['enhanced_relationships']:,}\n")
        f.write(f"- **Relationships with metadata:** {results['entity_connections']['relationships_with_metadata']:,}\n\n")

        f.write("### Connection Sources\n")
        for source, count in results['entity_connections']['connection_sources'].items():
            f.write(f"- **{source}:** {count:,} edges\n")
        f.write("\n")

        asymmetric_pct = (results['entity_connections']['asymmetric_connections'] / results['entity_connections']['network_edges'] * 100) if results['entity_connections']['network_edges'] else 0
        f.write(f"### Asymmetric Connections Analysis\n")
        f.write(f"**{asymmetric_pct:.1f}%** of connections are unidirectional (asymmetric).\n\n")
        f.write("**Expected behavior:** For co-occurrence networks (e.g., appearing together in flight logs), ")
        f.write("connections should typically be symmetric (if A appears with B, then B appears with A).\n\n")
        f.write("**Recommendation:** Review if asymmetric connections are intentional or indicate data issues.\n\n")

        f.write("## 3. News-Entity Relationships\n\n")
        f.write(f"- **Total news articles:** {results['news_entity']['total_news_articles']:,}\n")
        f.write(f"- **Articles with entity links:** {results['news_entity']['articles_with_entities']:,}\n")
        f.write(f"- **Coverage:** {results['news_entity']['articles_with_entities'] / results['news_entity']['total_news_articles'] * 100:.1f}%\n")
        f.write(f"- **Unique entities mentioned:** {results['news_entity']['unique_entities_in_news']:,}\n")
        f.write(f"- **Total entity mentions:** {results['news_entity']['total_entity_mentions']:,}\n")
        f.write(f"- **Orphan news articles:** {results['news_entity']['orphan_news_articles']:,}\n\n")

        if results['news_entity']['orphan_news_articles'] == 0:
            f.write("✅ **COMPLETE:** All news articles have entity links\n\n")
        else:
            f.write(f"⚠️ **GAP:** {results['news_entity']['orphan_news_articles']} news articles lack entity links\n\n")

        f.write("## 4. Document Coverage\n\n")
        f.write(f"- **Total documents:** {results['document_coverage']['total_documents']:,}\n")
        f.write(f"- **Documents with entities:** {results['document_coverage']['documents_with_entities']:,}\n")
        f.write(f"- **Orphan documents:** {results['document_coverage']['orphan_documents']:,}\n")
        f.write(f"- **Coverage:** {results['document_coverage']['coverage_percent']:.1f}%\n\n")

        if results['document_coverage']['orphan_documents'] > 0:
            f.write(f"⚠️ **GAP:** {results['document_coverage']['orphan_documents']:,} documents have no entity extractions\n\n")
        else:
            f.write("✅ **COMPLETE:** All documents have entity links\n\n")

        # Recommendations
        f.write("## 5. Identified Gaps Summary\n\n")

        all_gaps = []
        if results["doc_entity"]["format_issue"]:
            all_gaps.append({
                "priority": "P0 - Critical",
                "issue": "Entity naming format mismatch",
                "impact": "Cannot reconcile entity references across files",
                "recommendation": "Create entity_name_mappings.json to map between formats"
            })

        if results['document_coverage']['orphan_documents'] > 0:
            all_gaps.append({
                "priority": "P1 - High",
                "issue": f"{results['document_coverage']['orphan_documents']:,} orphan documents",
                "impact": f"{100 - results['document_coverage']['coverage_percent']:.1f}% of documents lack entity extraction",
                "recommendation": "Run entity extraction on missing documents"
            })

        if results['entity_connections']['asymmetric_connections'] > 100:
            all_gaps.append({
                "priority": "P2 - Medium",
                "issue": f"{results['entity_connections']['asymmetric_connections']:,} asymmetric connections",
                "impact": "Network analysis may be incomplete or biased",
                "recommendation": "Review and symmetrize co-occurrence connections"
            })

        if results['entity_connections']['relationships_with_metadata'] == 0:
            all_gaps.append({
                "priority": "P2 - Medium",
                "issue": "No relationship metadata",
                "impact": "Cannot determine when/where/why entities connected",
                "recommendation": "Add metadata: source documents, dates, connection types"
            })

        for gap in all_gaps:
            f.write(f"### {gap['priority']}: {gap['issue']}\n")
            f.write(f"- **Impact:** {gap['impact']}\n")
            f.write(f"- **Recommendation:** {gap['recommendation']}\n\n")

        # Target model
        f.write("## 6. Target Relationship Model\n\n")
        f.write("```\n")
        f.write("DOCUMENT ↔ ENTITIES (Bidirectional)\n")
        f.write("├─ Forward: document_entities_full.json\n")
        f.write("│  └─ entities.{entity}.document_sources[]\n")
        f.write("└─ Reverse: entity_document_index.json\n")
        f.write("   └─ entity_to_documents.{entity}.documents[]\n")
        f.write("\n")
        f.write("ENTITY ↔ ENTITY (Bidirectional)\n")
        f.write("├─ Network: entity_network.json\n")
        f.write("│  ├─ nodes[]: {id, name, connection_count}\n")
        f.write("│  └─ edges[]: {source, target, weight, contexts[]}\n")
        f.write("└─ Enhanced: entity_relationships_enhanced.json\n")
        f.write("   └─ relationships[]: {entity_a, entity_b, type, metadata}\n")
        f.write("\n")
        f.write("NEWS ↔ ENTITIES (Bidirectional)\n")
        f.write("├─ Forward: news_articles_index.json\n")
        f.write("│  └─ articles[].entities_mentioned[]\n")
        f.write("└─ Reverse: (MISSING - should track in entity_document_index)\n")
        f.write("\n")
        f.write("CONNECTION METADATA (Target)\n")
        f.write("├─ source: document_id or \"flight_log\" or \"news:{article_id}\"\n")
        f.write("├─ weight: co-occurrence count\n")
        f.write("├─ contexts: [\"flight_log\", \"legal_doc\", \"news\"]\n")
        f.write("├─ dates: when connection observed\n")
        f.write("└─ type: relationship type (business, personal, legal, etc.)\n")
        f.write("```\n\n")

        f.write("## 7. Action Items\n\n")
        f.write("### Immediate (P0)\n")
        f.write("1. **Create entity name mapping file** (`entity_name_mappings.json`)\n")
        f.write("   - Map between normalized names and \"Last, First\" format\n")
        f.write("   - Enable cross-file entity reconciliation\n\n")

        f.write("### High Priority (P1)\n")
        f.write("1. **Process orphan documents** - Extract entities from remaining documents\n")
        f.write("2. **Add news articles to entity_document_index** - Track news as document sources\n\n")

        f.write("### Medium Priority (P2)\n")
        f.write("1. **Review asymmetric connections** - Determine if intentional or error\n")
        f.write("2. **Add connection metadata** - Track source, dates, relationship types\n")
        f.write("3. **Enhance relationship tracking** - Add bidirectional flags and confidence scores\n\n")

        f.write("### Low Priority (P3)\n")
        f.write("1. **Standardize entity naming** - Choose single format across all files\n")
        f.write("2. **Add connection strength metrics** - Beyond simple co-occurrence counts\n")
        f.write("3. **Implement relationship ontology** - Classify connection types\n\n")

        f.write("---\n")
        f.write("*End of Report*\n")

    print(f"\n{'=' * 70}")
    print(f"Report saved to: {report_path}")
    print(f"{'=' * 70}\n")

    # Print summary
    print("\nSUMMARY OF GAPS:")
    print(f"  ⚠️ Entity naming format mismatch (cannot reconcile)")
    print(f"  ⚠️ {results['document_coverage']['orphan_documents']:,} orphan documents")
    print(f"  ⚠️ {results['entity_connections']['asymmetric_connections']:,} asymmetric connections")
    if results['entity_connections']['relationships_with_metadata'] == 0:
        print(f"  ⚠️ No relationship metadata")

    return results


if __name__ == "__main__":
    generate_report()
