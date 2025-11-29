#!/usr/bin/env python3
"""
Entity Biography Embeddings for ChromaDB

This script embeds entity biographies into the ChromaDB vector store to enable:
- Semantic similarity search for entity classification
- Entity clustering by biography similarity
- Discovery of related entities based on description overlap

The script uses the same embedding model as documents (all-MiniLM-L6-v2)
and stores entities with doc_type='entity_biography' for easy filtering.

Usage:
    python3 scripts/rag/embed_entity_biographies.py [--resume] [--batch-size N]

Options:
    --resume        Resume from checkpoint if available
    --batch-size N  Number of entities to process per batch (default: 100)
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("Error: chromadb not installed. Run: pip3 install chromadb")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Error: sentence-transformers not installed. Run: pip3 install sentence-transformers")
    sys.exit(1)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
VECTOR_STORE_DIR = PROJECT_ROOT / "data" / "vector_store" / "chroma"
ENTITY_BIOGRAPHIES_FILE = PROJECT_ROOT / "data" / "metadata" / "entity_biographies.json"
PROGRESS_FILE = PROJECT_ROOT / "data" / "metadata" / "entity_embedding_progress.json"

# ChromaDB configuration
COLLECTION_NAME = "epstein_documents"


class EntityBiographyEmbedder:
    """Embeds entity biographies into ChromaDB vector store."""

    def __init__(self, batch_size: int = 100):
        """Initialize the embedder.

        Args:
            batch_size: Number of entities to process per batch
        """
        self.batch_size = batch_size
        self.progress = self._load_progress()

        # Initialize ChromaDB
        print(f"Connecting to ChromaDB at {VECTOR_STORE_DIR}")
        self.client = chromadb.PersistentClient(
            path=str(VECTOR_STORE_DIR),
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )

        # Get existing collection
        try:
            self.collection = self.client.get_collection(name=COLLECTION_NAME)
            print(f"✓ Connected to collection '{COLLECTION_NAME}'")
        except Exception as e:
            print(f"Error: Could not get collection '{COLLECTION_NAME}': {e}")
            print("Run build_vector_store.py first to create the collection")
            sys.exit(1)

        # Initialize embedding model
        print("Loading sentence transformer model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✓ Model loaded")

    def _load_progress(self) -> Dict:
        """Load progress from checkpoint file."""
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
        return {
            "entities_processed": 0,
            "last_entity": None,
            "started_at": None,
            "updated_at": None,
        }

    def _save_progress(self):
        """Save progress to checkpoint file."""
        self.progress["updated_at"] = datetime.now().isoformat()
        with open(PROGRESS_FILE, "w") as f:
            json.dump(self.progress, f, indent=2)

    def _load_entities(self) -> Dict[str, Dict]:
        """Load entity biographies from JSON file."""
        print(f"Loading entity biographies from {ENTITY_BIOGRAPHIES_FILE}")

        if not ENTITY_BIOGRAPHIES_FILE.exists():
            print(f"Error: Entity biographies file not found at {ENTITY_BIOGRAPHIES_FILE}")
            sys.exit(1)

        with open(ENTITY_BIOGRAPHIES_FILE, "r") as f:
            data = json.load(f)

        entities = data.get("entities", {})
        print(f"✓ Loaded {len(entities)} entities")

        return entities

    def _create_embedding_text(self, entity: Dict) -> str:
        """Create text for embedding from entity data.

        Combines entity name and biography summary for embedding.

        Args:
            entity: Entity record dictionary

        Returns:
            Combined text for embedding
        """
        display_name = entity.get("display_name", entity.get("name", "Unknown"))
        summary = entity.get("summary", "")

        # Combine name and biography
        combined = f"{display_name}\n\n{summary}"

        # Truncate if too long (model has 512 token limit)
        # ~2000 characters ≈ 500 tokens
        if len(combined) > 2000:
            combined = combined[:2000] + "..."

        return combined

    def _create_metadata(self, entity_name: str, entity: Dict) -> Dict:
        """Create metadata for ChromaDB storage.

        Args:
            entity_name: Entity identifier (key in entities dict)
            entity: Entity record dictionary

        Returns:
            Metadata dictionary
        """
        # Extract relationship categories
        categories = entity.get("relationship_categories", [])
        category_types = [cat.get("type", "") for cat in categories if cat.get("type")]

        metadata = {
            "doc_type": "entity_biography",
            "entity_name": entity_name,
            "display_name": entity.get("display_name", entity_name),
            "word_count": entity.get("word_count", 0),
            "quality_score": entity.get("quality_score", 0.0),
            "generated_by": entity.get("generated_by", "unknown"),
            "category_count": len(category_types),
        }

        # Add primary category (highest priority/confidence)
        if category_types:
            metadata["primary_category"] = category_types[0]

        # Add all categories as comma-separated string
        if category_types:
            metadata["all_categories"] = ",".join(category_types)

        return metadata

    def embed_entities(self, resume: bool = False):
        """Embed all entity biographies into ChromaDB.

        Args:
            resume: If True, resume from last checkpoint
        """
        # Load entities
        entities = self._load_entities()
        total_entities = len(entities)

        # Determine starting point
        start_index = 0
        if resume and self.progress.get("last_entity"):
            # Find index of last processed entity
            entity_names = list(entities.keys())
            try:
                start_index = entity_names.index(self.progress["last_entity"]) + 1
                print(f"Resuming from entity #{start_index} ({self.progress['last_entity']})")
            except ValueError:
                print("Could not find last entity in current data, starting from beginning")

        # Initialize progress tracking
        if not self.progress.get("started_at"):
            self.progress["started_at"] = datetime.now().isoformat()

        # Process entities in batches
        entity_items = list(entities.items())[start_index:]
        total_to_process = len(entity_items)

        print(f"\nEmbedding {total_to_process} entities (total: {total_entities})")
        print(f"Batch size: {self.batch_size}")
        print("=" * 60)

        for i in range(0, len(entity_items), self.batch_size):
            batch = entity_items[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(entity_items) + self.batch_size - 1) // self.batch_size

            print(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} entities)")

            # Prepare batch data
            ids = []
            embeddings = []
            metadatas = []
            documents = []

            for entity_name, entity in batch:
                # Create embedding text
                text = self._create_embedding_text(entity)

                # Generate embedding
                embedding = self.model.encode(text).tolist()

                # Create metadata
                metadata = self._create_metadata(entity_name, entity)

                # Use entity_name as ID (with entity_bio_ prefix to avoid collisions)
                doc_id = f"entity_bio_{entity_name}"

                ids.append(doc_id)
                embeddings.append(embedding)
                metadatas.append(metadata)
                documents.append(text)

            # Add batch to ChromaDB
            try:
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=documents,
                )
                print(f"✓ Added {len(batch)} entities to vector store")
            except Exception as e:
                print(f"Error adding batch: {e}")
                raise

            # Update progress
            self.progress["entities_processed"] += len(batch)
            self.progress["last_entity"] = batch[-1][0]  # Last entity name in batch
            self._save_progress()

            # Progress update
            processed = start_index + i + len(batch)
            percent = (processed / total_entities) * 100
            print(f"Progress: {processed}/{total_entities} entities ({percent:.1f}%)")

        print("\n" + "=" * 60)
        print(f"✓ Completed embedding {total_to_process} entities")
        print(f"Total entities in collection: {self.collection.count()}")

        # Final statistics
        self._print_statistics()

    def _print_statistics(self):
        """Print collection statistics."""
        print("\nCollection Statistics:")
        print("=" * 60)

        # Total count
        total_count = self.collection.count()
        print(f"Total documents in collection: {total_count:,}")

        # Count by doc_type
        try:
            # Query for entity biographies
            entity_results = self.collection.get(
                where={"doc_type": "entity_biography"},
                limit=1
            )

            # Get all doc_types by sampling
            sample = self.collection.get(limit=1000)
            doc_types = {}
            for metadata in sample.get("metadatas", []):
                doc_type = metadata.get("doc_type", "unknown")
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

            print("\nBy document type:")
            for doc_type, count in sorted(doc_types.items()):
                print(f"  {doc_type}: {count:,}")

        except Exception as e:
            print(f"Could not get detailed statistics: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Embed entity biographies into ChromaDB vector store"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint if available",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of entities to process per batch (default: 100)",
    )

    args = parser.parse_args()

    # Create embedder
    embedder = EntityBiographyEmbedder(batch_size=args.batch_size)

    # Run embedding
    try:
        embedder.embed_entities(resume=args.resume)
        print("\n✓ Entity biography embedding completed successfully")
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Progress saved.")
        print("Resume with: python3 scripts/rag/embed_entity_biographies.py --resume")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
