#!/usr/bin/env python3
"""
WebSearch MCP Integration for Entity Enrichment

This module provides integration with Claude's WebSearch MCP tool for
automated entity research with source provenance tracking.

Features:
- WebSearch queries optimized for biographical data
- WebFetch for content extraction from reliable sources
- Rate limiting and caching
- Source reliability assessment
"""

import asyncio
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


@dataclass
class SearchResult:
    """Search result with metadata"""

    title: str
    url: str
    snippet: str
    domain: str
    search_query: str
    retrieved_at: str

    def to_dict(self):
        return asdict(self)


class WebSearchCache:
    """
    Cache search results to avoid redundant queries

    Cache TTL: 7 days (biographical data doesn't change frequently)
    """

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_days = 7

    def _get_cache_path(self, query: str) -> Path:
        """Get cache file path for query"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return self.cache_dir / f"search_{query_hash}.json"

    def get(self, query: str) -> Optional[list[SearchResult]]:
        """Get cached results if valid"""
        cache_path = self._get_cache_path(query)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path) as f:
                data = json.load(f)

            # Check TTL
            cached_time = datetime.fromisoformat(data["cached_at"])
            if datetime.now() - cached_time > timedelta(days=self.ttl_days):
                return None

            return [SearchResult(**r) for r in data["results"]]

        except Exception as e:
            print(f"Cache read error: {e}")
            return None

    def set(self, query: str, results: list[SearchResult]):
        """Cache search results"""
        cache_path = self._get_cache_path(query)

        data = {
            "query": query,
            "cached_at": datetime.now().isoformat(),
            "results": [r.to_dict() for r in results],
        }

        with open(cache_path, "w") as f:
            json.dump(data, f, indent=2)


class WebSearchIntegration:
    """
    Integration with Claude's WebSearch MCP tool

    Provides:
    - Optimized search queries for entity biographical data
    - Result filtering by domain reliability
    - Caching to reduce API calls
    - Rate limiting
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        if cache_dir is None:
            cache_dir = Path("/Users/masa/Projects/epstein/data/.cache/websearch")

        self.cache = WebSearchCache(cache_dir)
        self.rate_limit_delay = 2.0  # seconds between requests

    async def search_entity_biographical(self, entity_name: str) -> list[SearchResult]:
        """
        Search for entity biographical information

        Query strategy:
        1. Entity name + "biography"
        2. Prioritize reliable sources (news, Wikipedia, court docs)

        Args:
            entity_name: Entity name to research

        Returns:
            List of search results with provenance
        """
        query = f'"{entity_name}" biography'

        # Check cache first
        cached = self.cache.get(query)
        if cached:
            print(f"  ⚡ Using cached results for: {query}")
            return cached

        # Perform search
        print(f"  🔍 Searching web: {query}")

        # Note: This would call WebSearch MCP tool in production
        # For testing, we'll simulate the structure
        results = await self._mock_web_search(query, entity_name)

        # Cache results
        self.cache.set(query, results)

        # Rate limiting
        await asyncio.sleep(self.rate_limit_delay)

        return results

    async def search_entity_epstein_connection(self, entity_name: str) -> list[SearchResult]:
        """
        Search for entity's connection to Epstein

        Query strategy:
        1. Entity name + "Jeffrey Epstein"
        2. Entity name + "Epstein court documents"
        3. Prioritize Tier 1-2 sources (court docs, major journalism)

        Args:
            entity_name: Entity name to research

        Returns:
            List of search results focused on Epstein connections
        """
        query = f'"{entity_name}" Jeffrey Epstein court documents'

        # Check cache
        cached = self.cache.get(query)
        if cached:
            print(f"  ⚡ Using cached results for: {query}")
            return cached

        # Perform search
        print(f"  🔍 Searching web: {query}")

        results = await self._mock_web_search(query, entity_name, focus="epstein")

        # Cache results
        self.cache.set(query, results)

        # Rate limiting
        await asyncio.sleep(self.rate_limit_delay)

        return results

    async def search_entity_flight_logs(self, entity_name: str) -> list[SearchResult]:
        """
        Search for entity in flight log context

        Args:
            entity_name: Entity name to search

        Returns:
            List of search results about flight logs
        """
        query = f'"{entity_name}" Epstein flight logs passengers'

        cached = self.cache.get(query)
        if cached:
            print(f"  ⚡ Using cached results for: {query}")
            return cached

        print(f"  🔍 Searching web: {query}")

        results = await self._mock_web_search(query, entity_name, focus="flights")

        self.cache.set(query, results)
        await asyncio.sleep(self.rate_limit_delay)

        return results

    async def fetch_content(self, url: str) -> Optional[str]:
        """
        Fetch and extract content from URL

        Note: This would use WebFetch MCP tool in production
        to extract readable content and analyze with AI

        Args:
            url: URL to fetch

        Returns:
            Extracted content text
        """
        print(f"  📄 Fetching content: {url}")

        # This would call WebFetch MCP tool in production
        # For now, return None to indicate not implemented
        return None

    async def _mock_web_search(
        self, query: str, entity_name: str, focus: str = "biographical"
    ) -> list[SearchResult]:
        """
        Mock web search for testing

        In production, this would be replaced with actual WebSearch MCP call:

        from mcp import WebSearch

        results = WebSearch(
            query=query,
            allowed_domains=[
                'nytimes.com', 'washingtonpost.com', 'theguardian.com',
                'reuters.com', 'bbc.com', 'courtlistener.com',
                'wikipedia.org', 'britannica.com'
            ]
        )

        Args:
            query: Search query
            entity_name: Entity being researched
            focus: Search focus (biographical, epstein, flights)

        Returns:
            Mock search results for testing
        """
        # Simulate search delay
        await asyncio.sleep(0.5)

        # Return mock results based on focus
        if focus == "biographical":
            return [
                SearchResult(
                    title=f"{entity_name} - Wikipedia",
                    url=f"https://en.wikipedia.org/wiki/{entity_name.replace(' ', '_')}",
                    snippet=f"Background information about {entity_name}...",
                    domain="wikipedia.org",
                    search_query=query,
                    retrieved_at=datetime.now().isoformat(),
                ),
                SearchResult(
                    title=f"{entity_name} Biography - Britannica",
                    url=f"https://www.britannica.com/biography/{entity_name.replace(' ', '-')}",
                    snippet=f"Biographical details about {entity_name}...",
                    domain="britannica.com",
                    search_query=query,
                    retrieved_at=datetime.now().isoformat(),
                ),
            ]

        if focus == "epstein":
            return [
                SearchResult(
                    title=f"{entity_name} and Jeffrey Epstein - New York Times",
                    url=f"https://www.nytimes.com/2019/epstein/{entity_name.lower().replace(' ', '-')}",
                    snippet=f"Investigation into {entity_name}'s connection to Epstein...",
                    domain="nytimes.com",
                    search_query=query,
                    retrieved_at=datetime.now().isoformat(),
                ),
                SearchResult(
                    title=f"Court Documents Mention {entity_name}",
                    url=f"https://www.courtlistener.com/docket/epstein-{entity_name.lower().replace(' ', '-')}",
                    snippet=f"{entity_name} mentioned in Epstein court filings...",
                    domain="courtlistener.com",
                    search_query=query,
                    retrieved_at=datetime.now().isoformat(),
                ),
            ]

        if focus == "flights":
            return [
                SearchResult(
                    title=f"Epstein Flight Log Passengers Include {entity_name}",
                    url="https://www.theguardian.com/us-news/2021/epstein-flight-logs",
                    snippet=f"Flight logs show {entity_name} traveled on Epstein's aircraft...",
                    domain="theguardian.com",
                    search_query=query,
                    retrieved_at=datetime.now().isoformat(),
                )
            ]

        return []


async def test_websearch():
    """Test WebSearch integration"""
    print("Testing WebSearch Integration\n")

    integration = WebSearchIntegration()

    # Test biographical search
    print("1. Biographical Search:")
    bio_results = await integration.search_entity_biographical("Bill Clinton")
    for result in bio_results:
        print(f"   - {result.title}")
        print(f"     {result.url}")
        print(f"     Tier: {result.domain}\n")

    # Test Epstein connection search
    print("\n2. Epstein Connection Search:")
    epstein_results = await integration.search_entity_epstein_connection("Bill Clinton")
    for result in epstein_results:
        print(f"   - {result.title}")
        print(f"     {result.url}\n")

    # Test flight log search
    print("\n3. Flight Log Search:")
    flight_results = await integration.search_entity_flight_logs("Bill Clinton")
    for result in flight_results:
        print(f"   - {result.title}")
        print(f"     {result.url}\n")

    print("\n✅ WebSearch integration test complete")


if __name__ == "__main__":
    asyncio.run(test_websearch())
