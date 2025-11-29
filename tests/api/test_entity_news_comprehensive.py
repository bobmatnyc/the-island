#!/usr/bin/env python3
"""
Comprehensive Entity News API Diagnostic
Tests the full flow from entity ID to news articles
"""

import sys
import json
import requests
from pathlib import Path

# Add server to path
sys.path.insert(0, '/Users/masa/Projects/epstein/server')

from services.news_service import NewsService
from services.entity_service import EntityService

def test_backend_directly():
    """Test NewsService and EntityService directly"""
    print("=" * 80)
    print("TEST 1: Direct Service Layer Test")
    print("=" * 80)

    news_service = NewsService(Path('data/metadata/news_articles_index.json'))
    entity_service = EntityService(Path('data'))

    entity_id = "jeffrey_epstein"

    # Test entity resolution
    entity_obj = entity_service.get_entity_by_id(entity_id)
    if entity_obj:
        canonical_name = entity_obj.get("name") if isinstance(entity_obj, dict) else entity_obj.name
        print(f"✅ Entity found: '{canonical_name}'")

        # Convert format if needed
        if ", " in canonical_name:
            parts = canonical_name.split(", ", 1)
            query_name = f"{parts[1]} {parts[0]}"
        else:
            query_name = canonical_name

        print(f"   Query name: '{query_name}'")
    else:
        query_name = entity_id
        print(f"❌ Entity not found, using ID as-is: '{query_name}'")

    # Test news search
    articles, total = news_service.search_articles(entity=query_name, limit=100)
    print(f"✅ News search: {total} articles found")

    if articles:
        print(f"   Sample: {articles[0].title[:80]}")

    return total

def test_api_endpoint():
    """Test the actual API endpoint"""
    print("\n" + "=" * 80)
    print("TEST 2: API Endpoint Test (http://localhost:8081)")
    print("=" * 80)

    try:
        # Test with entity ID
        response = requests.get(
            'http://localhost:8081/api/news/articles',
            params={'entity': 'jeffrey_epstein', 'limit': 100},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response: HTTP {response.status_code}")
            print(f"   Total articles: {data.get('total', 0)}")
            print(f"   Returned: {len(data.get('articles', []))}")
            print(f"   Limit: {data.get('limit')}")
            print(f"   Offset: {data.get('offset')}")

            if data.get('articles'):
                sample = data['articles'][0]
                print(f"   Sample: {sample.get('title', '')[:80]}")

            return data.get('total', 0)
        else:
            print(f"❌ API Error: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return 0

    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Backend not running on port 8081")
        return 0
    except requests.exceptions.Timeout:
        print("❌ Timeout: Request took longer than 10 seconds")
        return 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 0

def test_name_variations():
    """Test different name format variations"""
    print("\n" + "=" * 80)
    print("TEST 3: Name Format Variations")
    print("=" * 80)

    news_service = NewsService(Path('data/metadata/news_articles_index.json'))

    test_names = [
        "jeffrey_epstein",
        "Jeffrey Epstein",
        "Epstein, Jeffrey",
        "JEFFREY EPSTEIN",  # Test case sensitivity
    ]

    for name in test_names:
        articles, total = news_service.search_articles(entity=name, limit=5)
        status = "✅" if total > 0 else "❌"
        print(f"{status} '{name}': {total} articles")

def test_api_variations():
    """Test API with different name formats"""
    print("\n" + "=" * 80)
    print("TEST 4: API Name Format Variations")
    print("=" * 80)

    test_names = [
        "jeffrey_epstein",
        "Jeffrey Epstein",
        "Epstein, Jeffrey",
    ]

    for name in test_names:
        try:
            response = requests.get(
                'http://localhost:8081/api/news/articles',
                params={'entity': name, 'limit': 5},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                total = data.get('total', 0)
                status = "✅" if total > 0 else "❌"
                print(f"{status} '{name}': {total} articles")
            else:
                print(f"❌ '{name}': HTTP {response.status_code}")

        except Exception as e:
            print(f"❌ '{name}': {type(e).__name__}")

def main():
    """Run all diagnostic tests"""
    print("\n🔍 Entity News API Comprehensive Diagnostic\n")

    # Test direct services
    service_total = test_backend_directly()

    # Test API endpoint
    api_total = test_api_endpoint()

    # Test name variations
    test_name_variations()
    test_api_variations()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Direct Service: {service_total} articles")
    print(f"API Endpoint:   {api_total} articles")

    if service_total > 0 and api_total > 0:
        print("\n✅ All tests passed - backend is working correctly")
        print("\nIf frontend shows '0 articles', check:")
        print("1. Frontend API_BASE_URL environment variable")
        print("2. Browser console for CORS or network errors")
        print("3. Browser network tab to see actual API responses")
    elif service_total > 0 and api_total == 0:
        print("\n⚠️  Service works but API fails")
        print("   - Check if FastAPI server is running on port 8081")
        print("   - Check for CORS configuration issues")
    else:
        print("\n❌ Backend issue detected")
        print("   - Check NewsService.search_articles() implementation")
        print("   - Check entity name normalization logic")

if __name__ == '__main__':
    main()
