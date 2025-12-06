"""
Backend API Verification Tests for Entity Fixes
Tests the complete entity management API fixes in production.

Verifies:
1. Entity type filtering (person, organization, location)
2. Correct entity counts
3. Ghislaine Maxwell classification as person
4. NPA removal from locations
5. Required fields (entity_type, connection_count)
"""

import pytest
import requests

BASE_URL = "http://localhost:8081"
NGROK_URL = "https://the-island.ngrok.app"


class TestEntityAPIVerification:
    """Comprehensive API verification tests for entity fixes."""

    @pytest.fixture
    def api_base_url(self):
        """Get API base URL."""
        return f"{BASE_URL}/api"

    def test_person_filter_returns_correct_count(self, api_base_url):
        """Test person filter API returns 1,634 entities."""
        response = requests.get(f"{api_base_url}/entities?entity_type=person&limit=1")
        assert response.status_code == 200, f"API returned {response.status_code}"

        data = response.json()
        assert "total" in data, "Response missing 'total' field"
        assert data["total"] == 1634, f"Expected 1,634 persons, got {data['total']}"

        print(f"✅ Person filter: {data['total']} entities (expected 1,634)")

    def test_organization_filter_returns_correct_count(self, api_base_url):
        """Test organization filter API returns 902 entities."""
        response = requests.get(f"{api_base_url}/entities?entity_type=organization&limit=1")
        assert response.status_code == 200, f"API returned {response.status_code}"

        data = response.json()
        assert "total" in data, "Response missing 'total' field"
        assert data["total"] == 902, f"Expected 902 organizations, got {data['total']}"

        print(f"✅ Organization filter: {data['total']} entities (expected 902)")

    def test_location_filter_returns_correct_count(self, api_base_url):
        """Test location filter API returns 457 entities."""
        response = requests.get(f"{api_base_url}/entities?entity_type=location&limit=1")
        assert response.status_code == 200, f"API returned {response.status_code}"

        data = response.json()
        assert "total" in data, "Response missing 'total' field"
        assert data["total"] == 457, f"Expected 457 locations, got {data['total']}"

        print(f"✅ Location filter: {data['total']} entities (expected 457)")

    def test_ghislaine_maxwell_in_persons(self, api_base_url):
        """Test Ghislaine Maxwell is classified as person."""
        response = requests.get(f"{api_base_url}/entities?entity_type=person&limit=2000")
        assert response.status_code == 200, f"API returned {response.status_code}"

        data = response.json()
        entities = data.get("entities", [])

        # Find Ghislaine Maxwell
        ghislaine = next(
            (e for e in entities if "Maxwell" in e.get("name", "") and "Ghislaine" in e.get("name", "")),
            None
        )

        assert ghislaine is not None, "Ghislaine Maxwell not found in persons"
        assert ghislaine["entity_type"] == "person", \
            f"Expected person, got {ghislaine.get('entity_type')}"

        print(f"✅ Ghislaine Maxwell: classified as person (was: organization)")
        print(f"   - Name: {ghislaine.get('name')}")
        print(f"   - Connections: {ghislaine.get('connection_count', 0)}")

    def test_ghislaine_maxwell_not_in_organizations(self, api_base_url):
        """Test Ghislaine Maxwell is NOT in organizations."""
        response = requests.get(f"{api_base_url}/entities?entity_type=organization&limit=1000")
        assert response.status_code == 200, f"API returned {response.status_code}"

        data = response.json()
        entities = data.get("entities", [])

        # Verify Ghislaine Maxwell NOT in organizations
        ghislaine = next(
            (e for e in entities if "Maxwell" in e.get("name", "") and "Ghislaine" in e.get("name", "")),
            None
        )

        assert ghislaine is None, "Ghislaine Maxwell should NOT be in organizations"
        print(f"✅ Ghislaine Maxwell: NOT in organizations (correctly removed)")

    def test_npa_not_in_locations(self, api_base_url):
        """Test NPA is not in locations."""
        response = requests.get(f"{api_base_url}/entities?entity_type=location&limit=1000")
        assert response.status_code == 200, f"API returned {response.status_code}"

        data = response.json()
        entities = data.get("entities", [])

        # Verify NPA not found
        npa = next((e for e in entities if e.get("name") == "NPA"), None)

        assert npa is None, "NPA should not be in locations"
        print(f"✅ NPA: NOT in locations (correctly removed)")

    def test_entities_have_required_fields(self, api_base_url):
        """Test all entities have entity_type and connection_count fields."""
        response = requests.get(f"{api_base_url}/entities?limit=20")
        assert response.status_code == 200, f"API returned {response.status_code}"

        data = response.json()
        entities = data.get("entities", [])

        assert len(entities) > 0, "No entities returned"

        missing_type = []
        missing_count = []

        for entity in entities:
            if "entity_type" not in entity:
                missing_type.append(entity.get("name", "unknown"))
            if "connection_count" not in entity:
                missing_count.append(entity.get("name", "unknown"))

        assert len(missing_type) == 0, f"Missing entity_type: {missing_type}"
        assert len(missing_count) == 0, f"Missing connection_count: {missing_count}"

        print(f"✅ All {len(entities)} entities have required fields (entity_type, connection_count)")

    def test_entity_type_values_are_valid(self, api_base_url):
        """Test entity_type values are one of: person, organization, location."""
        valid_types = {"person", "organization", "location"}

        for entity_type in valid_types:
            response = requests.get(f"{api_base_url}/entities?entity_type={entity_type}&limit=10")
            assert response.status_code == 200, f"API returned {response.status_code} for {entity_type}"

            data = response.json()
            entities = data.get("entities", [])

            for entity in entities:
                actual_type = entity.get("entity_type")
                assert actual_type == entity_type, \
                    f"Entity {entity.get('name')} has type {actual_type}, expected {entity_type}"

        print(f"✅ All entity_type values are valid (person, organization, location)")

    def test_connection_count_is_numeric(self, api_base_url):
        """Test connection_count is a numeric value."""
        response = requests.get(f"{api_base_url}/entities?limit=20")
        assert response.status_code == 200, f"API returned {response.status_code}"

        data = response.json()
        entities = data.get("entities", [])

        for entity in entities:
            conn_count = entity.get("connection_count")
            assert isinstance(conn_count, (int, float)), \
                f"Entity {entity.get('name')} has non-numeric connection_count: {conn_count}"
            assert conn_count >= 0, \
                f"Entity {entity.get('name')} has negative connection_count: {conn_count}"

        print(f"✅ All connection_count values are non-negative numbers")

    def test_news_api_returns_articles(self, api_base_url):
        """Test news API returns articles."""
        response = requests.get(f"{api_base_url}/news/articles?limit=5")
        assert response.status_code == 200, f"News API returned {response.status_code}"

        data = response.json()
        assert "total" in data, "Response missing 'total' field"
        assert "articles" in data, "Response missing 'articles' field"

        total_articles = data["total"]
        articles = data["articles"]

        assert total_articles > 0, "No news articles found"
        assert len(articles) > 0, "No articles in response"

        print(f"✅ News API: {total_articles} total articles")

        # Check first article structure
        first_article = articles[0]
        required_fields = ["id", "title", "published_date", "publication"]
        for field in required_fields:
            assert field in first_article, f"Article missing field: {field}"

        print(f"   - Latest article: {first_article.get('title')[:60]}...")
        print(f"   - Published: {first_article.get('published_date')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
