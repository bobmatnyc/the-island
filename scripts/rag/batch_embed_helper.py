#!/usr/bin/env python3
"""
Batch Embedding Helper Utilities
Epstein Document Archive - RAG System

Utility functions for managing news article embeddings:
- Check embedding status
- Batch embed articles efficiently
- Remove embeddings for reindexing
- Monitor progress

Design Decision: Shared Utility Functions
Rationale: These functions are used by both the main embedding script and
API endpoints that trigger background embedding. Extracted to avoid duplication.

Usage:
    from scripts.rag.batch_embed_helper import (
        check_embedding_status,
        remove_news_embeddings,
        batch_embed_articles
    )
"""

import json
from datetime import datetime
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
NEWS_INDEX_PATH = PROJECT_ROOT / "data/metadata/news_articles_index.json"
VECTOR_STORE_DIR = PROJECT_ROOT / "data/vector_store/chroma"
PROGRESS_FILE = PROJECT_ROOT / "data/vector_store/news_embedding_progress.json"

COLLECTION_NAME = "epstein_documents"


def get_chroma_collection():
    """
    Get ChromaDB collection.

    Returns:
        ChromaDB collection object

    Error Handling: Raises RuntimeError if collection not found
    """
    client = chromadb.PersistentClient(
        path=str(VECTOR_STORE_DIR), settings=Settings(anonymized_telemetry=False)
    )

    try:
        collection = client.get_collection(name=COLLECTION_NAME)
        return collection
    except Exception as e:
        raise RuntimeError(
            f"Collection '{COLLECTION_NAME}' not found. "
            f"Run build_vector_store.py first. Error: {e}"
        )


def get_embedding_model():
    """
    Get sentence-transformers embedding model.

    Returns:
        SentenceTransformer model (all-MiniLM-L6-v2)

    Performance: Model cached after first load (~500ms initial load)
    """
    return SentenceTransformer("all-MiniLM-L6-v2")


def check_embedding_status() -> dict:
    """
    Check how many news articles are embedded vs total available.

    Returns:
        Dictionary with embedding status:
        - total_articles: Articles in news_articles_index.json
        - embedded_articles: Articles with embeddings in ChromaDB
        - not_embedded: Articles without embeddings
        - embedding_rate: Percentage embedded
        - last_updated: When embeddings were last updated

    Usage:
        >>> status = check_embedding_status()
        >>> print(f"Embedded: {status['embedded_articles']}/{status['total_articles']}")

    Performance: O(n) where n = number of embedded news articles
    """
    # Load news index
    if not NEWS_INDEX_PATH.exists():
        return {
            "total_articles": 0,
            "embedded_articles": 0,
            "not_embedded": 0,
            "embedding_rate": 0.0,
            "last_updated": None,
            "error": "News articles index not found",
        }

    with open(NEWS_INDEX_PATH) as f:
        news_data = json.load(f)

    total_articles = len(news_data.get("articles", []))

    # Check embeddings
    try:
        collection = get_chroma_collection()

        # Query for news articles
        results = collection.get(where={"doc_type": "news_article"})

        embedded_count = len(results["ids"]) if results["ids"] else 0

        # Get last update time from progress file
        last_updated = None
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE) as f:
                progress = json.load(f)
                last_updated = progress.get("last_updated")

        return {
            "total_articles": total_articles,
            "embedded_articles": embedded_count,
            "not_embedded": total_articles - embedded_count,
            "embedding_rate": (
                (embedded_count / total_articles * 100) if total_articles > 0 else 0.0
            ),
            "last_updated": last_updated,
        }

    except Exception as e:
        return {
            "total_articles": total_articles,
            "embedded_articles": 0,
            "not_embedded": total_articles,
            "embedding_rate": 0.0,
            "last_updated": None,
            "error": str(e),
        }


def remove_news_embeddings() -> dict:
    """
    Remove all news article embeddings from ChromaDB.

    Used for reindexing or cleanup operations.

    Returns:
        Dictionary with removal status:
        - removed_count: Number of embeddings removed
        - success: True if operation succeeded
        - error: Error message if failed

    Usage:
        >>> result = remove_news_embeddings()
        >>> print(f"Removed {result['removed_count']} embeddings")

    Error Handling: Returns error dict if operation fails, doesn't raise
    """
    try:
        collection = get_chroma_collection()

        # Get all news article IDs
        results = collection.get(where={"doc_type": "news_article"})

        if not results["ids"]:
            return {"removed_count": 0, "success": True, "message": "No news embeddings found"}

        # Delete all news embeddings
        collection.delete(ids=results["ids"])

        # Clear progress file
        if PROGRESS_FILE.exists():
            PROGRESS_FILE.unlink()

        return {
            "removed_count": len(results["ids"]),
            "success": True,
            "message": f"Removed {len(results['ids'])} news article embeddings",
        }

    except Exception as e:
        return {"removed_count": 0, "success": False, "error": str(e)}


def batch_embed_articles(articles: list[dict], batch_size: int = 50) -> dict:
    """
    Embed a batch of articles efficiently.

    Used by API endpoints to embed newly created articles.

    Args:
        articles: List of article dictionaries to embed
        batch_size: Number of articles to process at once

    Returns:
        Dictionary with embedding results:
        - embedded_count: Number successfully embedded
        - failed_count: Number that failed
        - errors: List of error messages for failures
        - duration_seconds: Time taken

    Usage:
        >>> new_articles = [article1, article2, article3]
        >>> result = batch_embed_articles(new_articles)
        >>> print(f"Embedded {result['embedded_count']} articles")

    Performance:
    - ~50-100 articles/second for typical news articles
    - Batch processing more efficient than one-by-one

    Error Handling: Individual failures logged but don't stop batch processing
    """
    start_time = datetime.now()

    try:
        collection = get_chroma_collection()
        model = get_embedding_model()

        embedded_count = 0
        failed_count = 0
        errors = []

        # Process articles in batches
        for i in range(0, len(articles), batch_size):
            batch = articles[i : i + batch_size]

            batch_texts = []
            batch_ids = []
            batch_metadatas = []

            for article in batch:
                # Create embedding text (title + excerpt)
                title = article.get("title", "")
                excerpt = article.get("content_excerpt", "")
                embed_text = f"{title}\n\n{excerpt}"

                if len(embed_text) > 2000:
                    embed_text = embed_text[:2000] + "..."

                # Create metadata
                entities = article.get("entities_mentioned", [])
                tags = article.get("tags", [])
                cred_factors = article.get("credibility_factors", {})

                metadata = {
                    "doc_type": "news_article",
                    "doc_id": f"news:{article['id']}",
                    "article_id": article["id"],
                    "title": article.get("title", ""),
                    "publication": article.get("publication", ""),
                    "author": article.get("author", ""),
                    "published_date": article.get("published_date", ""),
                    "url": str(article.get("url", "")),
                    "word_count": article.get("word_count", 0),
                    "entity_mentions": ", ".join(entities) if entities else "",
                    "tags": ", ".join(tags) if tags else "",
                    "credibility_score": article.get("credibility_score", 0.75),
                    "source_tier": cred_factors.get("source_reputation", "tier_3"),
                    "embedded_at": datetime.now().isoformat(),
                }

                batch_texts.append(embed_text)
                batch_ids.append(f"news:{article['id']}")
                batch_metadatas.append(metadata)

            # Generate embeddings
            try:
                embeddings = model.encode(
                    batch_texts, show_progress_bar=False, convert_to_numpy=True
                )

                # Add to collection
                collection.add(
                    embeddings=embeddings.tolist(),
                    documents=batch_texts,
                    ids=batch_ids,
                    metadatas=batch_metadatas,
                )

                embedded_count += len(batch)

            except Exception:
                # Try one by one for this batch
                for text, doc_id, metadata in zip(batch_texts, batch_ids, batch_metadatas):
                    try:
                        embedding = model.encode([text], show_progress_bar=False)
                        collection.add(
                            embeddings=embedding.tolist(),
                            documents=[text],
                            ids=[doc_id],
                            metadatas=[metadata],
                        )
                        embedded_count += 1
                    except Exception as e2:
                        failed_count += 1
                        errors.append(f"Failed to embed {doc_id}: {e2!s}")

        elapsed = datetime.now() - start_time

        return {
            "embedded_count": embedded_count,
            "failed_count": failed_count,
            "errors": errors[:10],  # Limit to first 10 errors
            "duration_seconds": elapsed.total_seconds(),
            "success": True,
        }

    except Exception as e:
        return {
            "embedded_count": 0,
            "failed_count": len(articles),
            "errors": [str(e)],
            "duration_seconds": 0,
            "success": False,
        }


def get_progress_info() -> dict:
    """
    Get detailed progress information about embedding process.

    Returns:
        Dictionary with progress details:
        - total_processed: Articles processed so far
        - last_updated: When progress was last saved
        - processed_ids: List of processed article IDs

    Usage:
        >>> progress = get_progress_info()
        >>> print(f"Last updated: {progress['last_updated']}")
    """
    if not PROGRESS_FILE.exists():
        return {"total_processed": 0, "last_updated": None, "processed_ids": []}

    with open(PROGRESS_FILE) as f:
        return json.load(f)


# CLI interface for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python batch_embed_helper.py status    - Check embedding status")
        print("  python batch_embed_helper.py remove    - Remove all news embeddings")
        print("  python batch_embed_helper.py progress  - Show progress info")
        sys.exit(1)

    command = sys.argv[1]

    if command == "status":
        status = check_embedding_status()
        print("\n📊 Embedding Status:")
        print(f"   Total articles: {status['total_articles']}")
        print(f"   Embedded: {status['embedded_articles']}")
        print(f"   Not embedded: {status['not_embedded']}")
        print(f"   Embedding rate: {status['embedding_rate']:.1f}%")
        print(f"   Last updated: {status.get('last_updated', 'Never')}")

        if "error" in status:
            print(f"\n⚠️  Error: {status['error']}")

    elif command == "remove":
        result = remove_news_embeddings()
        if result["success"]:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ Error: {result['error']}")

    elif command == "progress":
        progress = get_progress_info()
        print("\n📈 Progress Info:")
        print(f"   Total processed: {progress['total_processed']}")
        print(f"   Last updated: {progress.get('last_updated', 'Never')}")
        print(f"   Processed IDs: {len(progress.get('processed_ids', []))}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
