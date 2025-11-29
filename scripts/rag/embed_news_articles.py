#!/usr/bin/env python3
"""
News Article Embedder
Epstein Document Archive - RAG System

Embeds news articles into ChromaDB for semantic search alongside court documents.
Uses same embedding model (all-MiniLM-L6-v2) as existing document embeddings.

Design Decision: Unified Collection Strategy
Rationale: News articles stored in same ChromaDB collection as court documents
using doc_type='news_article' for filtering. Enables cross-document semantic
search while maintaining ability to filter by document type.

Performance:
- ~50-100 articles/second (text is shorter than court docs)
- 100 articles = ~1-2 seconds
- 1000 articles = ~10-20 seconds

Usage:
    python3 scripts/rag/embed_news_articles.py
    python3 scripts/rag/embed_news_articles.py --batch-size 100
    python3 scripts/rag/embed_news_articles.py --force-reindex
    python3 scripts/rag/embed_news_articles.py --limit 20  # Testing
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
NEWS_INDEX_PATH = PROJECT_ROOT / "data/metadata/news_articles_index.json"
VECTOR_STORE_DIR = PROJECT_ROOT / "data/vector_store/chroma"
PROGRESS_FILE = PROJECT_ROOT / "data/vector_store/news_embedding_progress.json"

COLLECTION_NAME = "epstein_documents"


class NewsArticleEmbedder:
    """
    Embed news articles into ChromaDB for semantic search.

    Handles loading articles, generating embeddings, and storing in same
    collection as court documents with appropriate metadata.
    """

    def __init__(
        self, batch_size: int = 50, force_reindex: bool = False, limit: Optional[int] = None
    ):
        """
        Initialize news article embedder.

        Args:
            batch_size: Number of articles to process at once
            force_reindex: Delete existing news embeddings and reindex
            limit: Only embed first N articles (for testing)
        """
        self.batch_size = batch_size
        self.force_reindex = force_reindex
        self.limit = limit

        # Create directories
        VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB
        print("Initializing ChromaDB...")
        self.client = chromadb.PersistentClient(
            path=str(VECTOR_STORE_DIR),
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )

        # Get existing collection
        try:
            self.collection = self.client.get_collection(name=COLLECTION_NAME)
            print(f"✅ Connected to collection: {COLLECTION_NAME}")
            print(f"   Total documents: {self.collection.count()}")
        except Exception as e:
            raise RuntimeError(
                f"Collection '{COLLECTION_NAME}' not found. "
                f"Run build_vector_store.py first. Error: {e}"
            )

        # Initialize embedding model (same as court docs)
        print("\nLoading embedding model...")
        print("Model: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Model loaded successfully")

        # Load progress
        self.processed_ids = self._load_progress()

    def _load_progress(self) -> set:
        """Load previously processed article IDs for resume capability."""
        if not self.force_reindex and PROGRESS_FILE.exists():
            with open(PROGRESS_FILE) as f:
                progress = json.load(f)
                processed = set(progress.get("processed_article_ids", []))
                print(f"✅ Resume enabled: {len(processed)} articles already processed")
                return processed
        return set()

    def _save_progress(self, processed_ids: set):
        """Save progress for resume capability."""
        with open(PROGRESS_FILE, "w") as f:
            json.dump(
                {
                    "processed_article_ids": list(processed_ids),
                    "last_updated": datetime.now().isoformat(),
                    "total_processed": len(processed_ids),
                },
                f,
                indent=2,
            )

    def _load_news_articles(self) -> list[dict]:
        """
        Load news articles from index.

        Returns:
            List of article dictionaries

        Error Handling: Raises FileNotFoundError if index missing
        """
        if not NEWS_INDEX_PATH.exists():
            raise FileNotFoundError(
                f"News articles index not found: {NEWS_INDEX_PATH}\n"
                "Create articles first using the news articles API."
            )

        with open(NEWS_INDEX_PATH, encoding="utf-8") as f:
            data = json.load(f)

        articles = data.get("articles", [])
        print(f"\n📰 Found {len(articles)} articles in index")

        return articles

    def _remove_existing_news_embeddings(self):
        """
        Remove all existing news article embeddings.

        Used when --force-reindex is specified.
        """
        print("\n🗑️  Removing existing news article embeddings...")

        # Get all IDs with doc_type='news_article'
        try:
            results = self.collection.get(where={"doc_type": "news_article"})

            if results["ids"]:
                print(f"   Found {len(results['ids'])} existing news embeddings")
                self.collection.delete(ids=results["ids"])
                print("✅ Existing news embeddings removed")
            else:
                print("   No existing news embeddings found")

        except Exception as e:
            print(f"⚠️  Error removing embeddings: {e}")

    def _create_embedding_text(self, article: dict) -> str:
        """
        Create text for embedding from article data.

        Combines title + content_excerpt with smart truncation.

        Args:
            article: Article dictionary

        Returns:
            Text string for embedding (max ~500 tokens ≈ 2000 chars)

        Design Decision: Title + Content Strategy
        Rationale: Title provides topical context, excerpt provides content.
        Combined embeddings capture both "what is this about" and "what does it say".
        Max 2000 chars prevents token overflow (384-dim model handles ~512 tokens).
        """
        title = article.get("title", "")
        excerpt = article.get("content_excerpt", "")

        # Combine with clear separator
        combined = f"{title}\n\n{excerpt}"

        # Truncate to ~2000 characters (safe for 512 token limit)
        if len(combined) > 2000:
            combined = combined[:2000] + "..."

        return combined

    def _create_metadata(self, article: dict) -> dict:
        """
        Create ChromaDB metadata from article.

        Metadata Structure: Consistent with existing court document metadata
        but includes article-specific fields (publication, credibility, etc.)

        Args:
            article: Article dictionary

        Returns:
            Metadata dictionary for ChromaDB storage
        """
        # Extract entity mentions (convert list to comma-separated string)
        entities = article.get("entities_mentioned", [])
        entity_str = ", ".join(entities) if entities else ""

        # Extract tags
        tags = article.get("tags", [])
        tags_str = ", ".join(tags) if tags else ""

        # Credibility factors
        cred_factors = article.get("credibility_factors", {})

        metadata = {
            # Document type identifier (for filtering)
            "doc_type": "news_article",
            # Core identifiers
            "doc_id": f"news:{article['id']}",
            "article_id": article["id"],
            # Article metadata
            "title": article.get("title", ""),
            "publication": article.get("publication", ""),
            "author": article.get("author", ""),
            "published_date": article.get("published_date", ""),
            "url": str(article.get("url", "")),
            # Content metadata
            "word_count": article.get("word_count", 0),
            "content_length": len(article.get("content_excerpt", "")),
            # Entity and tag information
            "entity_mentions": entity_str,
            "tags": tags_str,
            # Credibility scoring
            "credibility_score": article.get("credibility_score", 0.75),
            "source_tier": cred_factors.get("source_reputation", "tier_3"),
            # Archive status (ChromaDB doesn't accept None values)
            "archive_url": str(article.get("archive_url") or ""),
            "archive_status": article.get("archive_status", "not_archived"),
            # Processing metadata
            "scraped_at": article.get("scraped_at", ""),
            "embedded_at": datetime.now().isoformat(),
        }

        return metadata

    def embed_articles(self):
        """
        Main embedding process.

        Workflow:
        1. Load articles from index
        2. Remove existing embeddings if force_reindex
        3. Filter to unprocessed articles
        4. Batch embed and store in ChromaDB
        5. Save progress after each batch
        """
        print("\n" + "=" * 70)
        print("NEWS ARTICLE EMBEDDER")
        print("=" * 70)

        # Load articles
        articles = self._load_news_articles()

        # Apply limit for testing
        if self.limit:
            articles = articles[: self.limit]
            print(f"⚠️  Limit applied: Processing first {self.limit} articles")

        # Remove existing if force reindex
        if self.force_reindex:
            self._remove_existing_news_embeddings()
            self.processed_ids = set()

        # Filter to unprocessed
        articles_to_process = [a for a in articles if a["id"] not in self.processed_ids]

        if not articles_to_process:
            print("\n✅ All articles already embedded!")
            print(f"Total embedded: {len(self.processed_ids)}")
            return

        print("\n📊 Processing Status:")
        print(f"   Total articles: {len(articles)}")
        print(f"   Already processed: {len(self.processed_ids)}")
        print(f"   To process: {len(articles_to_process)}")
        print(f"   Batch size: {self.batch_size}")

        # Process in batches
        batch_texts = []
        batch_ids = []
        batch_metadatas = []

        start_time = datetime.now()

        with tqdm(total=len(articles_to_process), desc="Embedding articles") as pbar:
            for article in articles_to_process:
                # Create embedding text
                embed_text = self._create_embedding_text(article)

                # Create metadata
                metadata = self._create_metadata(article)

                # Add to batch
                batch_texts.append(embed_text)
                batch_ids.append(f"news:{article['id']}")
                batch_metadatas.append(metadata)

                # Process batch when full
                if len(batch_texts) >= self.batch_size:
                    self._process_batch(batch_texts, batch_ids, batch_metadatas)

                    # Mark as processed
                    for article in articles_to_process[
                        len(self.processed_ids) : len(self.processed_ids) + len(batch_ids)
                    ]:
                        self.processed_ids.add(article["id"])

                    # Save progress
                    self._save_progress(self.processed_ids)

                    # Clear batch
                    batch_texts = []
                    batch_ids = []
                    batch_metadatas = []

                    pbar.update(self.batch_size)

        # Process remaining
        if batch_texts:
            self._process_batch(batch_texts, batch_ids, batch_metadatas)
            for batch_id in batch_ids:
                # Extract article_id from news:uuid
                article_id = batch_id.split(":", 1)[1]
                self.processed_ids.add(article_id)
            self._save_progress(self.processed_ids)
            pbar.update(len(batch_texts))

        # Final statistics
        elapsed = datetime.now() - start_time
        total_in_collection = self.collection.count()

        print("\n" + "=" * 70)
        print("✅ EMBEDDING COMPLETE")
        print("=" * 70)
        print(f"Articles embedded: {len(articles_to_process)}")
        print(f"Total documents in collection: {total_in_collection}")
        print(f"Time elapsed: {elapsed}")
        print(
            f"Average speed: {len(articles_to_process) / elapsed.total_seconds():.2f} articles/second"
        )
        print(f"Storage location: {VECTOR_STORE_DIR}")
        print("=" * 70)

    def _process_batch(self, texts: list[str], ids: list[str], metadatas: list[dict]):
        """
        Process batch of articles and add to ChromaDB.

        Error Handling: Falls back to one-by-one processing if batch fails.
        Individual failures are logged but don't stop the process.
        """
        try:
            # Generate embeddings
            embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)

            # Add to collection
            self.collection.add(
                embeddings=embeddings.tolist(), documents=texts, ids=ids, metadatas=metadatas
            )

        except Exception as e:
            print(f"\n⚠️  Batch processing failed: {e}")
            print("   Falling back to one-by-one processing...")

            # Try one by one
            for text, doc_id, metadata in zip(texts, ids, metadatas):
                try:
                    embedding = self.model.encode([text], show_progress_bar=False)
                    self.collection.add(
                        embeddings=embedding.tolist(),
                        documents=[text],
                        ids=[doc_id],
                        metadatas=[metadata],
                    )
                except Exception as e2:
                    print(f"⚠️  Failed to embed {doc_id}: {e2}")


def main():
    parser = argparse.ArgumentParser(description="Embed news articles into ChromaDB vector store")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of articles to process at once (default: 50)",
    )
    parser.add_argument(
        "--force-reindex", action="store_true", help="Delete existing news embeddings and reindex"
    )
    parser.add_argument("--limit", type=int, help="Only embed first N articles (for testing)")

    args = parser.parse_args()

    embedder = NewsArticleEmbedder(
        batch_size=args.batch_size, force_reindex=args.force_reindex, limit=args.limit
    )

    embedder.embed_articles()


if __name__ == "__main__":
    main()
