#!/usr/bin/env python3
"""
ChromaDB Document Indexing Script

Indexes all Epstein documents into ChromaDB for vector search and retrieval.

Usage:
    python scripts/chromadb/index_documents.py [--reset] [--limit N]

Options:
    --reset: Delete existing collection and start fresh
    --limit N: Index only first N documents (for testing)
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.chromadb.config import (
    ALL_DOCUMENTS_INDEX_PATH,
    BATCH_SIZE,
    CHROMADB_DIR,
    COLLECTION_NAME,
    DOCUMENT_CLASSIFICATIONS_PATH,
    DOCUMENT_ENTITIES_PATH,
    EMBEDDING_MODEL,
    MAX_DOCUMENTS,
    METADATA_FIELDS,
    PROGRESS_INTERVAL,
    USE_FILENAME_FALLBACK,
    VERBOSE,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO if VERBOSE else logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DocumentIndexer:
    """Index documents into ChromaDB with metadata for filtering."""

    def __init__(self, reset: bool = False):
        """Initialize ChromaDB client and collection.

        Args:
            reset: If True, delete existing collection and start fresh
        """
        self.reset = reset
        self.stats = {
            "total_documents": 0,
            "indexed": 0,
            "with_real_content": 0,
            "with_pseudo_content": 0,
            "errors": 0,
        }

        # Initialize ChromaDB
        logger.info(f"Initializing ChromaDB at {CHROMADB_DIR}")
        CHROMADB_DIR.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(CHROMADB_DIR),
            settings=Settings(anonymized_telemetry=False),
        )

        # Get or create collection
        if reset:
            try:
                self.client.delete_collection(name=COLLECTION_NAME)
                logger.info(f"Deleted existing collection: {COLLECTION_NAME}")
            except Exception as e:
                # Collection doesn't exist - this is fine
                logger.debug(f"Collection does not exist yet: {e}")

        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Epstein document archive with embeddings"},
        )

        logger.info(f"Collection '{COLLECTION_NAME}' ready")
        logger.info(f"Using embedding model: {EMBEDDING_MODEL}")

    def load_data(self) -> Dict:
        """Load all data sources into memory.

        Returns:
            Dictionary with loaded data: classifications, entities, all_docs
        """
        logger.info("Loading data files...")

        with open(DOCUMENT_CLASSIFICATIONS_PATH) as f:
            classifications_data = json.load(f)
            classifications = {
                doc["id"]: doc for doc in classifications_data["documents"]
            }

        with open(DOCUMENT_ENTITIES_PATH) as f:
            entities_data = json.load(f)
            doc_entities = entities_data["document_to_entities"]

        # Load all_documents_index for additional metadata
        with open(ALL_DOCUMENTS_INDEX_PATH) as f:
            all_docs_data = json.load(f)
            all_docs = {doc["id"]: doc for doc in all_docs_data["documents"]}

        logger.info(f"Loaded {len(classifications)} document classifications")
        logger.info(f"Loaded {len(doc_entities)} document-entity mappings")
        logger.info(f"Loaded {len(all_docs)} documents from all_documents_index")

        return {
            "classifications": classifications,
            "doc_entities": doc_entities,
            "all_docs": all_docs,
        }

    def prepare_document_text(self, doc_id: str, doc: Dict, all_docs: Dict) -> tuple[str, bool]:
        """Prepare text content for embedding.

        Args:
            doc_id: Document ID
            doc: Document classification data
            all_docs: All documents index data

        Returns:
            Tuple of (text_content, has_real_content)
        """
        # Strategy 1: Check if document has summary in all_docs
        if doc_id in all_docs and "summary" in all_docs[doc_id]:
            summary = all_docs[doc_id]["summary"]
            if summary and len(summary.strip()) > 10:
                return summary, True

        # Strategy 2: Use filename + classification + source as pseudo-content
        if USE_FILENAME_FALLBACK:
            filename = doc.get("filename", "unknown")
            classification = doc.get("new_classification", "unknown")
            source = doc.get("source", "unknown")
            keywords = ", ".join(doc.get("keywords_matched", []))

            pseudo_content = f"Document: {filename}. Classification: {classification}. Source: {source}."
            if keywords:
                pseudo_content += f" Keywords: {keywords}."

            return pseudo_content, False

        # Strategy 3: Minimal fallback
        return f"Document ID: {doc_id}", False

    def prepare_metadata(
        self, doc_id: str, doc: Dict, all_docs: Dict, doc_entities: Dict, has_real_content: bool
    ) -> Dict:
        """Prepare metadata for ChromaDB storage.

        Args:
            doc_id: Document ID
            doc: Document classification data
            all_docs: All documents index data
            doc_entities: Document-entity mappings
            has_real_content: Whether document has real content vs pseudo-content

        Returns:
            Metadata dictionary
        """
        # Get entity count
        entities = doc_entities.get(doc_id, [])
        entity_count = len(entities) if entities else 0

        # Get additional info from all_docs if available
        doc_info = all_docs.get(doc_id, {})

        metadata = {
            "filename": doc.get("filename", "unknown"),
            "source": doc.get("source", "unknown"),
            "classification": doc.get("new_classification", "unknown"),
            "confidence": float(doc.get("confidence", 0.0)),
            "doc_type": doc_info.get("doc_type", doc_info.get("type", "unknown")),
            "file_size": int(doc_info.get("file_size", 0)),
            "entity_count": entity_count,
            "has_real_content": has_real_content,
            "path": doc.get("path", ""),
        }

        # ChromaDB requires all metadata values to be str, int, float, or bool
        # Convert any None to empty string
        for key, value in metadata.items():
            if value is None:
                metadata[key] = ""

        return metadata

    def index_documents(self, limit: Optional[int] = None):
        """Index documents in batches.

        Args:
            limit: Maximum number of documents to index (for testing)
        """
        data = self.load_data()
        classifications = data["classifications"]
        doc_entities = data["doc_entities"]
        all_docs = data["all_docs"]

        # Determine documents to index
        doc_ids = list(classifications.keys())
        if limit:
            doc_ids = doc_ids[:limit]
            logger.info(f"Limiting to first {limit} documents")

        self.stats["total_documents"] = len(doc_ids)
        logger.info(f"Starting indexing of {len(doc_ids)} documents...")

        # Process in batches
        for i in tqdm(range(0, len(doc_ids), BATCH_SIZE), desc="Indexing batches"):
            batch_ids = doc_ids[i : i + BATCH_SIZE]
            batch_documents = []
            batch_metadatas = []
            batch_ids_clean = []

            for doc_id in batch_ids:
                try:
                    doc = classifications[doc_id]

                    # Prepare text content
                    text_content, has_real_content = self.prepare_document_text(
                        doc_id, doc, all_docs
                    )

                    # Prepare metadata
                    metadata = self.prepare_metadata(
                        doc_id, doc, all_docs, doc_entities, has_real_content
                    )

                    batch_documents.append(text_content)
                    batch_metadatas.append(metadata)
                    batch_ids_clean.append(doc_id)

                    # Update stats
                    if has_real_content:
                        self.stats["with_real_content"] += 1
                    else:
                        self.stats["with_pseudo_content"] += 1

                except Exception as e:
                    logger.error(f"Error preparing document {doc_id}: {e}")
                    self.stats["errors"] += 1

            # Add batch to collection
            if batch_documents:
                try:
                    self.collection.add(
                        documents=batch_documents,
                        metadatas=batch_metadatas,
                        ids=batch_ids_clean,
                    )
                    self.stats["indexed"] += len(batch_documents)

                    if (i // BATCH_SIZE) % (PROGRESS_INTERVAL // BATCH_SIZE) == 0:
                        logger.info(
                            f"Progress: {self.stats['indexed']}/{self.stats['total_documents']} "
                            f"({self.stats['indexed']/self.stats['total_documents']*100:.1f}%)"
                        )

                except Exception as e:
                    logger.error(f"Error adding batch {i}: {e}")
                    self.stats["errors"] += len(batch_documents)

        logger.info("Indexing complete!")

    def print_statistics(self):
        """Print indexing statistics."""
        print("\n" + "=" * 60)
        print("INDEXING STATISTICS")
        print("=" * 60)
        print(f"Total documents processed: {self.stats['total_documents']}")
        print(f"Successfully indexed: {self.stats['indexed']}")
        print(f"  - With real content: {self.stats['with_real_content']}")
        print(f"  - With pseudo-content: {self.stats['with_pseudo_content']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"\nCollection size: {self.collection.count()} documents")
        print(f"ChromaDB location: {CHROMADB_DIR}")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Index Epstein documents into ChromaDB"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing collection and start fresh",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=MAX_DOCUMENTS,
        help="Maximum number of documents to index (for testing)",
    )

    args = parser.parse_args()

    try:
        indexer = DocumentIndexer(reset=args.reset)
        indexer.index_documents(limit=args.limit)
        indexer.print_statistics()

        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
