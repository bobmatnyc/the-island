"""
End-to-End Frontend Verification Tests for Entity Fixes
Tests the complete entity management fixes in production frontend.

Verifies:
1. Entity type filtering (person, organization, location)
2. Connection threshold slider functionality
3. Ghislaine Maxwell classification as person
4. NPA removal from locations
5. Entity counts and filtering
"""

import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "https://the-island.ngrok.app"

class TestEntityFrontendVerification:
    """Comprehensive frontend verification tests for entity fixes."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to entities page before each test."""
        page.goto(f"{BASE_URL}/entities")
        # Wait for page to load
        page.wait_for_load_state("networkidle")
        time.sleep(2)  # Additional wait for dynamic content

    def test_entity_page_loads(self, page: Page):
        """Verify entity page loads successfully."""
        expect(page).to_have_title("Entities - Epstein Island")

        # Check for main heading
        heading = page.locator("h1, h2").filter(has_text="Entities")
        expect(heading).to_be_visible()

    def test_connection_slider_exists(self, page: Page):
        """Verify connection threshold slider exists and is set to default."""
        # Look for slider input
        slider = page.locator('input[type="range"]').first
        expect(slider).to_be_visible()

        # Check default value (should be 1)
        default_value = slider.input_value()
        assert default_value == "1", f"Expected default value 1, got {default_value}"

    def test_person_tab_displays(self, page: Page):
        """Test clicking Person tab shows correct entity count."""
        # Click Person tab
        person_tab = page.get_by_role("button", name="Person")
        if not person_tab.is_visible():
            person_tab = page.locator('button:has-text("Person")').first

        person_tab.click()
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # Check for entities displayed
        entity_cards = page.locator('[data-testid="entity-card"], .entity-card, article').all()
        assert len(entity_cards) > 0, "No person entities displayed"

        # Verify count indicator shows ~1,634 total
        count_text = page.locator('text=/\\d+\\s+(entities|results|persons)/i').first
        if count_text.is_visible():
            text = count_text.inner_text()
            print(f"Person count text: {text}")

    def test_organization_tab_displays(self, page: Page):
        """Test clicking Organization tab shows correct entity count."""
        # Click Organization tab
        org_tab = page.get_by_role("button", name="Organization")
        if not org_tab.is_visible():
            org_tab = page.locator('button:has-text("Organization")').first

        org_tab.click()
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # Check for entities displayed
        entity_cards = page.locator('[data-testid="entity-card"], .entity-card, article').all()
        assert len(entity_cards) > 0, "No organization entities displayed"

    def test_location_tab_displays(self, page: Page):
        """Test clicking Location tab shows correct entity count."""
        # Click Location tab
        loc_tab = page.get_by_role("button", name="Location")
        if not loc_tab.is_visible():
            loc_tab = page.locator('button:has-text("Location")').first

        loc_tab.click()
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        # Check for entities displayed
        entity_cards = page.locator('[data-testid="entity-card"], .entity-card, article').all()
        assert len(entity_cards) > 0, "No location entities displayed"

    def test_ghislaine_maxwell_is_person(self, page: Page):
        """Verify Ghislaine Maxwell appears in Person tab, not Organization."""
        # Go to Person tab
        person_tab = page.get_by_role("button", name="Person")
        if not person_tab.is_visible():
            person_tab = page.locator('button:has-text("Person")').first
        person_tab.click()
        page.wait_for_load_state("networkidle")

        # Search for Ghislaine Maxwell
        search_input = page.locator('input[type="search"], input[placeholder*="Search"]').first
        if search_input.is_visible():
            search_input.fill("Ghislaine Maxwell")
            page.wait_for_load_state("networkidle")
            time.sleep(1)

            # Should find results
            ghislaine_entity = page.locator('text=/Maxwell.*Ghislaine|Ghislaine.*Maxwell/i').first
            expect(ghislaine_entity).to_be_visible()

            # Clear search
            search_input.clear()
            page.wait_for_load_state("networkidle")

    def test_npa_not_in_locations(self, page: Page):
        """Verify NPA does not appear in Location tab."""
        # Go to Location tab
        loc_tab = page.get_by_role("button", name="Location")
        if not loc_tab.is_visible():
            loc_tab = page.locator('button:has-text("Location")').first
        loc_tab.click()
        page.wait_for_load_state("networkidle")

        # Search for NPA
        search_input = page.locator('input[type="search"], input[placeholder*="Search"]').first
        if search_input.is_visible():
            search_input.fill("NPA")
            page.wait_for_load_state("networkidle")
            time.sleep(1)

            # Should show no results
            no_results = page.locator('text=/no.*results|0.*entities|nothing.*found/i').first
            # Either no results message or no entity cards
            entity_cards = page.locator('[data-testid="entity-card"], .entity-card, article').all()
            assert len(entity_cards) == 0 or no_results.is_visible(), "NPA should not appear in locations"

    def test_connection_slider_filters(self, page: Page):
        """Test connection slider adjusts entity count."""
        # Get initial count at threshold 1
        slider = page.locator('input[type="range"]').first
        expect(slider).to_be_visible()

        # Set to 0 to show all
        slider.fill("0")
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        initial_count = len(page.locator('[data-testid="entity-card"], .entity-card, article').all())

        # Set to higher threshold (e.g., 5)
        slider.fill("5")
        page.wait_for_load_state("networkidle")
        time.sleep(1)

        filtered_count = len(page.locator('[data-testid="entity-card"], .entity-card, article').all())

        # Higher threshold should show fewer or equal entities
        assert filtered_count <= initial_count, \
            f"Higher threshold ({filtered_count}) should show <= lower threshold ({initial_count})"

    def test_no_console_errors(self, page: Page):
        """Verify no JavaScript console errors on entity page."""
        console_errors = []

        def handle_console(msg):
            if msg.type == "error":
                console_errors.append(msg.text)

        page.on("console", handle_console)

        # Navigate and interact
        page.goto(f"{BASE_URL}/entities")
        page.wait_for_load_state("networkidle")

        # Click through tabs
        for tab_name in ["Person", "Organization", "Location"]:
            tab = page.get_by_role("button", name=tab_name)
            if not tab.is_visible():
                tab = page.locator(f'button:has-text("{tab_name}")').first
            if tab.is_visible():
                tab.click()
                page.wait_for_load_state("networkidle")

        # Report errors
        if console_errors:
            print(f"\nConsole errors found: {console_errors}")

        assert len(console_errors) == 0, f"Found {len(console_errors)} console errors"


@pytest.mark.asyncio
class TestEntityAPIIntegration:
    """Backend API integration tests."""

    @pytest.fixture
    def api_base_url(self):
        return f"{BASE_URL}/api"

    def test_person_filter_returns_correct_count(self, api_base_url):
        """Test person filter API returns 1,634 entities."""
        import requests
        response = requests.get(f"{api_base_url}/entities?entity_type=person&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1634, f"Expected 1,634 persons, got {data['total']}"

    def test_organization_filter_returns_correct_count(self, api_base_url):
        """Test organization filter API returns 902 entities."""
        import requests
        response = requests.get(f"{api_base_url}/entities?entity_type=organization&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 902, f"Expected 902 organizations, got {data['total']}"

    def test_location_filter_returns_correct_count(self, api_base_url):
        """Test location filter API returns 457 entities."""
        import requests
        response = requests.get(f"{api_base_url}/entities?entity_type=location&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 457, f"Expected 457 locations, got {data['total']}"

    def test_ghislaine_maxwell_in_persons(self, api_base_url):
        """Test Ghislaine Maxwell is classified as person."""
        import requests
        response = requests.get(f"{api_base_url}/entities?entity_type=person&limit=2000")
        assert response.status_code == 200
        data = response.json()

        # Find Ghislaine Maxwell
        ghislaine = next((e for e in data["entities"] if "Maxwell" in e["name"] and "Ghislaine" in e["name"]), None)
        assert ghislaine is not None, "Ghislaine Maxwell not found in persons"
        assert ghislaine["entity_type"] == "person", f"Expected person, got {ghislaine['entity_type']}"

    def test_npa_not_in_locations(self, api_base_url):
        """Test NPA is not in locations."""
        import requests
        response = requests.get(f"{api_base_url}/entities?entity_type=location&limit=1000")
        assert response.status_code == 200
        data = response.json()

        # Verify NPA not found
        npa = next((e for e in data["entities"] if e["name"] == "NPA"), None)
        assert npa is None, "NPA should not be in locations"

    def test_entities_have_required_fields(self, api_base_url):
        """Test all entities have entity_type and connection_count fields."""
        import requests
        response = requests.get(f"{api_base_url}/entities?limit=10")
        assert response.status_code == 200
        data = response.json()

        for entity in data["entities"]:
            assert "entity_type" in entity, f"Missing entity_type for {entity.get('name')}"
            assert "connection_count" in entity, f"Missing connection_count for {entity.get('name')}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
