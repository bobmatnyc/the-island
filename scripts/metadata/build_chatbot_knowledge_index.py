#!/usr/bin/env python3
"""Build comprehensive knowledge index for chatbot.

This script creates a master JSON index containing:
- All project files (scripts, data, sources)
- Data summaries (entities, documents, network)
- Ongoing work (downloads, classifications, processing)
- Quick statistics for chatbot responses

Used by chatbot to answer questions about project state.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def get_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of file."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return ""


def scan_scripts(base_path: Path) -> List[Dict[str, str]]:
    """Scan all Python scripts and categorize them."""
    scripts_dir = base_path / "scripts"
    scripts = []

    categories = {
        "extraction": "Data extraction and OCR processing",
        "download": "Downloading source documents",
        "classification": "Document classification and categorization",
        "analysis": "Entity analysis, network building, and relationships",
        "search": "Entity search and querying",
        "canonicalization": "Deduplication and canonical document creation",
        "utilities": "Utility scripts and helpers",
        "core": "Core libraries (hasher, deduplicator, database)",
    }

    for category, description in categories.items():
        category_dir = scripts_dir / category
        if category_dir.exists():
            for script_file in sorted(category_dir.glob("*.py")):
                if script_file.name.startswith("__"):
                    continue
                scripts.append({
                    "name": script_file.name,
                    "category": category,
                    "category_description": description,
                    "path": str(script_file),
                    "relative_path": str(script_file.relative_to(base_path))
                })

    return scripts


def scan_data_files(base_path: Path) -> Dict[str, Any]:
    """Scan all data files and categorize."""
    data_dir = base_path / "data"

    files = {
        "metadata": [],
        "entities": [],
        "canonical_emails": [],
        "source_pdfs": {},
        "markdown_extractions": {}
    }

    # Metadata files
    metadata_dir = data_dir / "metadata"
    if metadata_dir.exists():
        for file in sorted(metadata_dir.glob("*.json")):
            files["metadata"].append({
                "name": file.name,
                "path": str(file),
                "size_bytes": file.stat().st_size,
                "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            })

    # Entity files
    entities_dir = data_dir / "md" / "entities"
    if entities_dir.exists():
        for file in sorted(entities_dir.glob("*")):
            if file.is_file():
                files["entities"].append({
                    "name": file.name,
                    "path": str(file),
                    "size_bytes": file.stat().st_size
                })

    # Canonical emails
    canonical_emails_dir = data_dir / "canonical" / "emails"
    if canonical_emails_dir.exists():
        email_files = list(canonical_emails_dir.glob("*.md"))
        files["canonical_emails"] = [{
            "name": f.name,
            "path": str(f)
        } for f in sorted(email_files)]

    # Source PDFs
    sources_dir = data_dir / "sources"
    if sources_dir.exists():
        for source in sources_dir.iterdir():
            if source.is_dir():
                pdf_count = len(list(source.glob("**/*.pdf")))
                files["source_pdfs"][source.name] = {
                    "path": str(source),
                    "pdf_count": pdf_count
                }

    return files


def read_master_index(base_path: Path) -> Dict[str, Any]:
    """Read master document index."""
    index_path = base_path / "data" / "metadata" / "master_document_index.json"
    if index_path.exists():
        with open(index_path) as f:
            return json.load(f)
    return {}


def read_entity_index(base_path: Path) -> Dict[str, Any]:
    """Read entity index."""
    entity_path = base_path / "data" / "md" / "entities" / "ENTITIES_INDEX.json"
    if entity_path.exists():
        with open(entity_path) as f:
            return json.load(f)
    return {}


def read_entity_network(base_path: Path) -> Dict[str, Any]:
    """Read entity network graph."""
    network_path = base_path / "data" / "metadata" / "entity_network.json"
    if network_path.exists():
        with open(network_path) as f:
            return json.load(f)
    return {}


def read_email_statistics(base_path: Path) -> Dict[str, Any]:
    """Read email statistics."""
    email_stats_path = base_path / "data" / "canonical" / "emails" / "email_statistics.json"
    if email_stats_path.exists():
        with open(email_stats_path) as f:
            return json.load(f)
    return {}


def read_download_log(base_path: Path) -> List[Dict[str, Any]]:
    """Read download log."""
    download_log_path = base_path / "data" / "metadata" / "download_log.json"
    if download_log_path.exists():
        with open(download_log_path) as f:
            return json.load(f)
    return []


def check_ongoing_work(base_path: Path) -> Dict[str, Any]:
    """Check for ongoing background processes and pending work."""
    ongoing = {
        "downloads_in_progress": [],
        "pending_classifications": 0,
        "background_processes": []
    }

    # Check for download log recent entries
    download_log = read_download_log(base_path)
    if download_log:
        recent = download_log[-5:]  # Last 5 downloads
        ongoing["recent_downloads"] = [{
            "source": d["source"],
            "filename": d["filename"],
            "downloaded_at": d["downloaded_at"]
        } for d in recent]

    # Check master index for unclassified documents
    master_index = read_master_index(base_path)
    classifications_path = base_path / "data" / "metadata" / "document_classifications.json"
    if classifications_path.exists():
        with open(classifications_path) as f:
            classifications = json.load(f)
        total_docs = master_index.get("unique_documents", 0)
        classified_count = len(classifications)
        ongoing["pending_classifications"] = total_docs - classified_count

    return ongoing


def build_knowledge_index(base_path: Path) -> Dict[str, Any]:
    """Build comprehensive knowledge index."""

    print("Building chatbot knowledge index...")

    # Read all data sources
    master_index = read_master_index(base_path)
    entity_index = read_entity_index(base_path)
    network = read_entity_network(base_path)
    email_stats = read_email_statistics(base_path)

    # Scan files
    scripts = scan_scripts(base_path)
    data_files = scan_data_files(base_path)
    ongoing = check_ongoing_work(base_path)

    # Count emails from different sources
    canonical_email_count = len(data_files["canonical_emails"])

    # Get top entities from network
    top_connections = []
    if "edges" in network:
        # Count connections per entity
        entity_connections = {}
        for edge in network["edges"]:
            source = edge.get("source", "")
            target = edge.get("target", "")
            entity_connections[source] = entity_connections.get(source, 0) + 1
            entity_connections[target] = entity_connections.get(target, 0) + 1

        # Sort by connection count
        sorted_entities = sorted(
            entity_connections.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        top_connections = [
            {"name": name, "connection_count": count}
            for name, count in sorted_entities
        ]

    # Build index
    index = {
        "generated_at": datetime.now().isoformat(),
        "project_root": str(base_path),

        "files": {
            "scripts": scripts,
            "data_files": data_files
        },

        "data_summary": {
            "entities": {
                "total": entity_index.get("total_entities", 0),
                "billionaires": entity_index.get("statistics", {}).get("billionaires", 0),
                "in_black_book": entity_index.get("statistics", {}).get("in_black_book", 0),
                "in_flight_logs": entity_index.get("statistics", {}).get("in_flight_logs", 0),
                "source_file": str(base_path / "data" / "md" / "entities" / "ENTITIES_INDEX.json"),
                "top_frequent_flyers": entity_index.get("top_frequent_flyers", [])[:5]
            },

            "documents": {
                "total_files": master_index.get("total_files", 0),
                "unique_documents": master_index.get("unique_documents", 0),
                "duplicates": master_index.get("total_duplicates", 0),
                "deduplication_rate": f"{(master_index.get('total_duplicates', 0) / master_index.get('total_files', 1) * 100):.1f}%",
                "sources": master_index.get("sources", {}),
                "index_file": str(base_path / "data" / "metadata" / "master_document_index.json")
            },

            "emails": {
                "canonical_count": canonical_email_count,
                "date_range": email_stats.get("date_range", {}),
                "unique_participants": email_stats.get("unique_participants", 0),
                "participant_list": email_stats.get("participant_list", []),
                "statistics_file": str(base_path / "data" / "canonical" / "emails" / "email_statistics.json")
            },

            "network": {
                "total_nodes": len(network.get("nodes", [])),
                "total_edges": len(network.get("edges", [])),
                "top_connections": top_connections,
                "network_file": str(base_path / "data" / "metadata" / "entity_network.json")
            }
        },

        "ongoing_work": ongoing,

        "quick_stats": {
            "total_pdfs": sum([src.get("document_count", 0) for src in master_index.get("sources", {}).values()]),
            "total_emails": canonical_email_count,
            "unique_documents": master_index.get("unique_documents", 0),
            "deduplication_rate": f"{(master_index.get('total_duplicates', 0) / master_index.get('total_files', 1) * 100):.1f}%",
            "unique_entities": entity_index.get("total_entities", 0),
            "network_nodes": len(network.get("nodes", [])),
            "network_edges": len(network.get("edges", []))
        },

        "search_capabilities": {
            "entity_search": {
                "script": "scripts/search/entity_search.py",
                "capabilities": [
                    "Search by entity name",
                    "Find entity connections",
                    "Multi-entity search",
                    "Search by document type"
                ]
            },
            "classification_types": [
                "email", "court_filing", "financial", "flight_log",
                "contact_book", "investigative", "legal_agreement",
                "personal", "media", "administrative", "unknown"
            ]
        },

        "key_reports": {
            "entity_network_stats": str(base_path / "data" / "metadata" / "entity_network_stats.txt"),
            "classification_report": str(base_path / "data" / "metadata" / "classification_report.txt"),
            "entity_statistics": str(base_path / "data" / "metadata" / "entity_statistics_summary.txt"),
            "relationship_system": str(base_path / "data" / "metadata" / "RELATIONSHIP_SYSTEM_SUMMARY.md")
        }
    }

    return index


def main():
    """Main execution."""
    base_path = Path(__file__).resolve().parents[2]

    # Build index
    index = build_knowledge_index(base_path)

    # Write to file
    output_path = base_path / "data" / "metadata" / "chatbot_knowledge_index.json"
    with open(output_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"✓ Chatbot knowledge index created: {output_path}")
    print(f"  - {len(index['files']['scripts'])} scripts indexed")
    print(f"  - {index['data_summary']['entities']['total']} entities")
    print(f"  - {index['data_summary']['documents']['unique_documents']} unique documents")
    print(f"  - {index['data_summary']['network']['total_nodes']} network nodes")
    print(f"  - {index['data_summary']['network']['total_edges']} network edges")
    print(f"  - {index['data_summary']['emails']['canonical_count']} canonical emails")


if __name__ == "__main__":
    main()
