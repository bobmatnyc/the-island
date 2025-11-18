#!/usr/bin/env python3
"""
ChromaDB Vector Store Builder
Epstein Document Archive - RAG System

Embeds all 33,562 OCR documents into ChromaDB for semantic search.
Uses sentence-transformers (all-MiniLM-L6-v2) for efficient embeddings.

Performance:
- ~5-10 documents/second
- ~5-6 hours for complete dataset
- ~2GB storage for embeddings

Usage:
    python3 scripts/rag/build_vector_store.py
    python3 scripts/rag/build_vector_store.py --batch-size 50
    python3 scripts/rag/build_vector_store.py --resume
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import argparse

# Project paths
PROJECT_ROOT = Path("/Users/masa/Projects/Epstein")
OCR_TEXT_DIR = PROJECT_ROOT / "data/sources/house_oversight_nov2025/ocr_text"
VECTOR_STORE_DIR = PROJECT_ROOT / "data/vector_store/chroma"
ENTITY_INDEX_PATH = PROJECT_ROOT / "data/md/entities/ENTITIES_INDEX.json"
PROGRESS_FILE = PROJECT_ROOT / "data/vector_store/embedding_progress.json"

# Collection name
COLLECTION_NAME = "epstein_documents"


class VectorStoreBuilder:
    def __init__(self, batch_size: int = 100, resume: bool = True):
        """Initialize the vector store builder."""
        self.batch_size = batch_size
        self.resume = resume

        # Create vector store directory
        VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB
        print("Initializing ChromaDB...")
        self.client = chromadb.PersistentClient(
            path=str(VECTOR_STORE_DIR),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=COLLECTION_NAME)
            print(f"✅ Found existing collection: {COLLECTION_NAME}")
            print(f"   Current documents: {self.collection.count()}")
        except:
            self.collection = self.client.create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "Epstein Document Archive - OCR Text Embeddings"}
            )
            print(f"✅ Created new collection: {COLLECTION_NAME}")

        # Initialize embedding model
        print("\nLoading sentence-transformers model...")
        print("Model: all-MiniLM-L6-v2 (384 dimensions)")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Model loaded successfully")

        # Load entity index for entity detection
        self.entity_index = self._load_entity_index()

        # Load progress
        self.processed_files = self._load_progress()

    def _load_entity_index(self) -> Dict:
        """Load entity index for entity mention detection."""
        if ENTITY_INDEX_PATH.exists():
            with open(ENTITY_INDEX_PATH, 'r') as f:
                data = json.load(f)
                print(f"✅ Loaded entity index: {len(data.get('entities', []))} entities")
                return data
        return {"entities": []}

    def _load_progress(self) -> set:
        """Load previously processed files for resume capability."""
        if self.resume and PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, 'r') as f:
                progress = json.load(f)
                processed = set(progress.get('processed_files', []))
                print(f"✅ Resume enabled: {len(processed)} files already processed")
                return processed
        return set()

    def _save_progress(self, processed_files: set):
        """Save progress for resume capability."""
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROGRESS_FILE, 'w') as f:
            json.dump({
                'processed_files': list(processed_files),
                'last_updated': datetime.now().isoformat(),
                'total_processed': len(processed_files)
            }, f, indent=2)

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from document text (basic pattern matching)."""
        # Common date patterns
        patterns = [
            r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b',  # MM/DD/YYYY
            r'\b(\d{4}-\d{2}-\d{2})\b',  # YYYY-MM-DD
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _detect_entity_mentions(self, text: str) -> List[str]:
        """Detect entity mentions in document text."""
        mentioned_entities = []
        text_lower = text.lower()

        for entity in self.entity_index.get('entities', []):
            name = entity.get('name', '')
            if not name:
                continue

            # Check for entity name (case-insensitive)
            if name.lower() in text_lower:
                mentioned_entities.append(name)
                continue

            # Check variations (last name only for "LastName, FirstName" format)
            if ',' in name:
                last_name = name.split(',')[0].strip()
                if len(last_name) > 3 and last_name.lower() in text_lower:
                    mentioned_entities.append(name)

        return list(set(mentioned_entities))  # Remove duplicates

    def _get_document_files(self) -> List[Path]:
        """Get all .txt files from OCR directory."""
        txt_files = sorted(OCR_TEXT_DIR.glob("*.txt"))
        print(f"\n📄 Found {len(txt_files)} text files")
        return txt_files

    def _read_document(self, file_path: Path) -> Optional[Dict]:
        """Read document and extract metadata."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            # Skip empty documents
            if len(text.strip()) < 50:
                return None

            # Extract metadata
            doc_id = file_path.stem  # DOJ-OGR-00000001

            # Extract date
            date = self._extract_date(text[:2000])  # Check first 2000 chars

            # Detect entity mentions (convert to comma-separated string for ChromaDB)
            entities = self._detect_entity_mentions(text)

            metadata = {
                'filename': file_path.name,
                'doc_id': doc_id,
                'source': 'house_oversight_nov2025',
                'file_size': len(text),
                'date_extracted': date if date else '',
                'entity_mentions': ', '.join(entities) if entities else ''
            }

            return {
                'id': doc_id,
                'text': text,
                'metadata': metadata
            }

        except Exception as e:
            print(f"⚠️  Error reading {file_path.name}: {e}")
            return None

    def build_vector_store(self):
        """Build the complete vector store."""
        print("\n" + "="*70)
        print("CHROMADB VECTOR STORE BUILDER")
        print("="*70)

        # Get all document files
        all_files = self._get_document_files()

        # Filter out already processed files
        files_to_process = [
            f for f in all_files
            if f.stem not in self.processed_files
        ]

        if not files_to_process:
            print("\n✅ All documents already processed!")
            print(f"Total documents in collection: {self.collection.count()}")
            return

        print(f"📊 Files to process: {len(files_to_process)}")
        print(f"   Already processed: {len(self.processed_files)}")
        print(f"   Batch size: {self.batch_size}")

        # Process in batches
        batch_docs = []
        batch_ids = []
        batch_metadatas = []

        start_time = datetime.now()

        with tqdm(total=len(files_to_process), desc="Embedding documents") as pbar:
            for file_path in files_to_process:
                # Read document
                doc = self._read_document(file_path)
                if not doc:
                    self.processed_files.add(file_path.stem)
                    pbar.update(1)
                    continue

                # Add to batch
                batch_docs.append(doc['text'])
                batch_ids.append(doc['id'])
                batch_metadatas.append(doc['metadata'])

                # Process batch when full
                if len(batch_docs) >= self.batch_size:
                    self._process_batch(batch_docs, batch_ids, batch_metadatas)

                    # Mark as processed
                    for doc_id in batch_ids:
                        self.processed_files.add(doc_id)

                    # Save progress
                    self._save_progress(self.processed_files)

                    # Clear batch
                    batch_docs = []
                    batch_ids = []
                    batch_metadatas = []

                    pbar.update(self.batch_size)

        # Process remaining documents
        if batch_docs:
            self._process_batch(batch_docs, batch_ids, batch_metadatas)
            for doc_id in batch_ids:
                self.processed_files.add(doc_id)
            self._save_progress(self.processed_files)

        # Final statistics
        elapsed = datetime.now() - start_time
        total_docs = self.collection.count()

        print("\n" + "="*70)
        print("✅ VECTOR STORE BUILD COMPLETE")
        print("="*70)
        print(f"Total documents embedded: {total_docs}")
        print(f"Time elapsed: {elapsed}")
        print(f"Average speed: {len(files_to_process) / elapsed.total_seconds():.2f} docs/second")
        print(f"Storage location: {VECTOR_STORE_DIR}")
        print("="*70)

    def _process_batch(self, documents: List[str], ids: List[str], metadatas: List[Dict]):
        """Process a batch of documents and add to ChromaDB."""
        try:
            # Generate embeddings
            embeddings = self.model.encode(
                documents,
                show_progress_bar=False,
                convert_to_numpy=True
            )

            # Add to collection
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )

        except Exception as e:
            print(f"\n⚠️  Error processing batch: {e}")
            # Try processing one by one
            for doc, doc_id, metadata in zip(documents, ids, metadatas):
                try:
                    embedding = self.model.encode([doc], show_progress_bar=False)
                    self.collection.add(
                        embeddings=embedding.tolist(),
                        documents=[doc],
                        ids=[doc_id],
                        metadatas=[metadata]
                    )
                except Exception as e2:
                    print(f"⚠️  Failed to process {doc_id}: {e2}")


def main():
    parser = argparse.ArgumentParser(description="Build ChromaDB vector store for Epstein documents")
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for processing')
    parser.add_argument('--no-resume', action='store_true', help='Start from scratch (ignore progress)')

    args = parser.parse_args()

    builder = VectorStoreBuilder(
        batch_size=args.batch_size,
        resume=not args.no_resume
    )

    builder.build_vector_store()


if __name__ == "__main__":
    main()
