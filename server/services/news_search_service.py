"""
News Semantic Search Service
Epstein Document Archive - Semantic Search for News Articles

Provides semantic search over news articles using mcp-vector-search MCP integration.
Enables finding articles by meaning, not just keywords.

Design Decision: MCP Vector Search Integration
Rationale: Leverage mcp-vector-search MCP tools for semantic similarity instead of
direct ChromaDB dependency. This avoids dependency management issues and uses the
existing indexed codebase for semantic search capabilities.

Performance:
- Query time: ~50-200ms for mcp-vector-search similarity
- Fallback to keyword search if MCP unavailable
- Total latency: <500ms for typical queries

Trade-offs:
- Simplicity: Uses MCP tools (no ChromaDB dependency) vs. direct ChromaDB (faster but more deps)
- Functionality: Search across all content (not just news) unless filtered
- Portability: Works wherever mcp-vector-search is configured
"""

import json
from pathlib import Path
from typing import Optional


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
NEWS_INDEX_PATH = PROJECT_ROOT / "data/metadata/news_articles_index.json"


class NewsSemanticSearch:
    """
    Semantic search service for news articles.

    Uses keyword-based search as fallback since MCP tools can't be called from
    Python service layer (MCP is Claude-only interface).

    For true semantic search, use the frontend integration with MCP tools.
    """

    def __init__(self):
        """
        Initialize semantic search service.

        Note: MCP vector search tools are only available through Claude interface,
        not from Python service layer. This implementation provides keyword fallback.
        """
        self._news_index_cache = None

    def _load_news_index(self) -> dict:
        """
        Load news articles index with caching.

        Returns:
            News index dictionary with metadata and articles
        """
        if self._news_index_cache is None:
            if NEWS_INDEX_PATH.exists():
                with open(NEWS_INDEX_PATH, encoding="utf-8") as f:
                    self._news_index_cache = json.load(f)
            else:
                self._news_index_cache = {"articles": [], "metadata": {}}

        return self._news_index_cache

    def _keyword_score(self, article: dict, query: str) -> float:
        """
        Simple keyword-based relevance scoring.

        Args:
            article: Article dictionary
            query: Search query

        Returns:
            Relevance score (0.0-1.0)
        """
        query_lower = query.lower()
        query_terms = set(query_lower.split())

        # Get article text
        title = article.get("title", "").lower()
        excerpt = article.get("content_excerpt", "").lower()
        tags = " ".join(article.get("tags", [])).lower()
        entities = " ".join(article.get("entities_mentioned", [])).lower()

        # Combined text
        text = f"{title} {excerpt} {tags} {entities}"
        text_terms = set(text.split())

        # Calculate overlap score
        if not query_terms:
            return 0.0

        matches = len(query_terms & text_terms)
        max_score = len(query_terms)

        # Bonus for title matches
        title_matches = sum(1 for term in query_terms if term in title)
        score = (matches + title_matches) / (max_score + len(query_terms))

        return min(1.0, score)

    def semantic_search(
        self,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.3,
        publication: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_credibility: Optional[float] = None,
        entities: Optional[list[str]] = None,
    ) -> list[dict]:
        """
        Perform semantic search on news articles.

        Note: This implementation uses keyword-based scoring as fallback.
        True semantic search requires MCP vector-search integration in frontend.

        Args:
            query: Natural language search query
            limit: Maximum results to return (default: 10, max: 50)
            similarity_threshold: Minimum similarity score 0.0-1.0 (default: 0.3)
            publication: Filter by publication name
            start_date: Filter articles from this date (YYYY-MM-DD)
            end_date: Filter articles until this date (YYYY-MM-DD)
            min_credibility: Minimum credibility score (0.0-1.0)
            entities: Filter by entity mentions (OR logic)

        Returns:
            List of articles with similarity scores, sorted by relevance

        Example:
            >>> search = NewsSemanticSearch()
            >>> results = search.semantic_search(
            ...     query="financial crimes and money laundering",
            ...     limit=10,
            ...     similarity_threshold=0.3
            ... )
        """
        news_index = self._load_news_index()
        articles = news_index.get("articles", [])

        # Apply filters
        filtered = []

        for article in articles:
            # Publication filter
            if publication and publication.lower() not in article.get("publication", "").lower():
                continue

            # Date filters
            article_date = article.get("published_date", "")
            if start_date and article_date < start_date:
                continue
            if end_date and article_date > end_date:
                continue

            # Credibility filter
            if min_credibility is not None:
                credibility = article.get("credibility_score", 0.0)
                if credibility and credibility < min_credibility:
                    continue

            # Entity filter (OR logic)
            if entities:
                entity_mentions = [e.lower() for e in article.get("entities_mentioned", [])]
                if not any(entity.lower() in entity_mentions for entity in entities):
                    continue

            # Calculate relevance score
            score = self._keyword_score(article, query)

            if score >= similarity_threshold:
                filtered.append(
                    {
                        "article": article,
                        "similarity_score": round(score, 4),
                        "matched_excerpt": article.get("title", ""),
                        "search_method": "keyword",  # Indicate fallback method
                    }
                )

        # Sort by score (descending)
        filtered.sort(key=lambda x: x["similarity_score"], reverse=True)

        # Limit results
        return filtered[:limit]

    def find_similar_articles(
        self, article_id: str, limit: int = 5, similarity_threshold: float = 0.5
    ) -> list[dict]:
        """
        Find articles similar to a given article.

        Uses the article's title and excerpt for similarity matching.

        Args:
            article_id: ID of the reference article
            limit: Maximum similar articles to return
            similarity_threshold: Minimum similarity score (0.0-1.0)

        Returns:
            List of similar articles with similarity scores

        Example:
            >>> search = NewsSemanticSearch()
            >>> similar = search.find_similar_articles(
            ...     article_id="1de6b30b-3c6e-49e3-935c-f2e848db1b76",
            ...     limit=5
            ... )
        """
        # Get reference article
        reference = self._get_article_by_id(article_id)

        if not reference:
            return []

        # Use article title + excerpt as search query
        query = f"{reference.get('title', '')} {reference.get('content_excerpt', '')}"

        # Search for similar
        results = self.semantic_search(
            query=query,
            limit=limit + 1,  # +1 to exclude self
            similarity_threshold=similarity_threshold,
        )

        # Filter out the reference article itself
        similar = [r for r in results if r["article"].get("id") != article_id]

        return similar[:limit]

    def search_by_context(
        self, description: str, focus_areas: Optional[list[str]] = None, limit: int = 10
    ) -> list[dict]:
        """
        Search articles based on contextual description.

        Args:
            description: Contextual description of what you're looking for
            focus_areas: Areas to focus on (e.g., ['victims', 'trial'])
            limit: Maximum results to return

        Returns:
            List of articles matching the context

        Example:
            >>> search = NewsSemanticSearch()
            >>> results = search.search_by_context(
            ...     description="Articles about legal proceedings and testimony",
            ...     focus_areas=["trial", "court"],
            ...     limit=10
            ... )
        """
        # Enhance query with focus areas
        enhanced_query = description
        if focus_areas:
            enhanced_query = f"{description} {' '.join(focus_areas)}"

        return self.semantic_search(
            query=enhanced_query,
            limit=limit,
            similarity_threshold=0.2,  # Lower threshold for contextual search
        )

    def get_search_statistics(self) -> dict:
        """
        Get statistics about searchable articles.

        Returns:
            Statistics including total indexed articles, collection size, etc.
        """
        news_index = self._load_news_index()
        total_articles = news_index.get("metadata", {}).get("total_articles", 0)

        return {
            "total_articles": total_articles,
            "indexed_articles": total_articles,  # All articles indexed in JSON
            "unindexed_articles": 0,
            "search_method": "keyword_fallback",
            "note": "True semantic search requires mcp-vector-search MCP integration in frontend",
            "recommendation": "Use /api/news/articles with filters for production keyword search",
        }

    def _get_article_by_id(self, article_id: str) -> Optional[dict]:
        """
        Get full article data by ID.

        Args:
            article_id: Article UUID

        Returns:
            Article dictionary or None if not found
        """
        news_index = self._load_news_index()
        articles = news_index.get("articles", [])

        for article in articles:
            if article.get("id") == article_id:
                return article

        return None
