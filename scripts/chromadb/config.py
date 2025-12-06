"""
ChromaDB Configuration for Epstein Document Archive

Centralized configuration for ChromaDB settings, paths, and embedding models.
"""

from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHROMADB_DIR = DATA_DIR / "chromadb"

# Data source paths
DOCUMENT_CLASSIFICATIONS_PATH = DATA_DIR / "transformed" / "document_classifications.json"
DOCUMENT_ENTITIES_PATH = DATA_DIR / "transformed" / "document_to_entities.json"
ALL_DOCUMENTS_INDEX_PATH = DATA_DIR / "metadata" / "all_documents_index.json"

# ChromaDB settings
COLLECTION_NAME = "epstein_documents"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast, efficient, 384-dim embeddings

# Performance settings
BATCH_SIZE = 100  # Documents per batch for embedding
MAX_DOCUMENTS = None  # Set to integer to limit (for testing), None for all

# Embedding strategy
# Since most documents lack extracted text, we use a fallback strategy:
# 1. Use summary from all_documents_index if available
# 2. Use filename + classification + source as pseudo-content
# 3. Mark in metadata whether real content or pseudo-content
USE_FILENAME_FALLBACK = True

# Metadata schema for filtering
# These fields will be stored in ChromaDB metadata for each document
METADATA_FIELDS = [
    "filename",
    "source",
    "classification",  # new_classification from document_classifications
    "confidence",
    "doc_type",
    "file_size",
    "entity_count",
    "has_real_content",  # True if using summary, False if using filename fallback
    "path",
]

# Progress reporting
PROGRESS_INTERVAL = 500  # Report progress every N documents
VERBOSE = True
