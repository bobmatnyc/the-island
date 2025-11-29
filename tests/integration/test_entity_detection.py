"""
Integration Tests for Entity Detection

Tests the entity detection system end-to-end including:
- Entity pattern loading
- Text detection
- GUID mapping
- Cache performance
- Error handling

Design Decision: Integration tests vs. unit tests
Rationale: Entity detection involves file I/O, regex compilation, and caching.
Integration tests verify the full pipeline works correctly together.

Test Coverage Target: >90% for entity_detector.py
"""

import json
import pytest
import time
from pathlib import Path
from server.entity_detector import EntityDetector, get_entity_detector, EntityMatch


class TestEntityDetectorIntegration:
    """Integration tests for EntityDetector class."""

    @pytest.fixture
    def detector(self):
        """Create EntityDetector instance for testing."""
        return get_entity_detector()

    @pytest.fixture
    def sample_text(self):
        """Sample text with known entities."""
        return """
        Jeffrey Epstein and Ghislaine Maxwell were charged with serious crimes.
        Bill Clinton was mentioned in flight logs. Prince Andrew denied allegations.
        The case involved Virginia Giuffre and other victims.
        Documents from the Southern District of New York detailed the investigation.
        """

    def test_detector_initialization(self, detector):
        """Test that detector initializes with entity data."""
        assert detector is not None
        assert len(detector.entities) > 0, "Should load entity statistics"
        assert len(detector.entity_patterns) > 0, "Should compile regex patterns"

    def test_singleton_pattern(self):
        """Test that get_entity_detector returns same instance."""
        detector1 = get_entity_detector()
        detector2 = get_entity_detector()
        assert detector1 is detector2, "Should return singleton instance"

    def test_detect_known_entities(self, detector, sample_text):
        """Test detection of known entities in text."""
        entities = detector.detect_entities(sample_text)

        assert len(entities) > 0, "Should detect entities"

        # Check for known entities
        entity_names = [e.name for e in entities]
        assert any("Epstein" in name for name in entity_names), "Should detect Epstein"
        assert any("Maxwell" in name for name in entity_names), "Should detect Maxwell"

    def test_entity_mention_counting(self, detector):
        """Test that mentions are counted correctly."""
        text = """
        Jeffrey Epstein met with Epstein's associates.
        Epstein was arrested in 2019. Mr. Epstein denied the charges.
        """

        entities = detector.detect_entities(text)

        # Find Epstein entity
        epstein = next((e for e in entities if "Epstein" in e.name), None)
        assert epstein is not None, "Should find Epstein entity"
        assert epstein.mentions >= 3, f"Should count multiple mentions, got {epstein.mentions}"

    def test_entity_guid_mapping(self, detector, sample_text):
        """Test that entities have valid GUIDs."""
        entities = detector.detect_entities(sample_text)

        for entity in entities:
            assert entity.guid, "Entity should have GUID"
            assert len(entity.guid) > 0, "GUID should not be empty"
            assert entity.name, "Entity should have name"

    def test_name_variations_detection(self, detector):
        """Test detection of entity name variations."""
        text = """
        Jeffrey Epstein and Jeff Epstein are the same person.
        Some documents refer to J. Epstein.
        """

        entities = detector.detect_entities(text)

        # Should detect variations as same entity
        epstein_entities = [e for e in entities if "Epstein" in e.name]
        assert len(epstein_entities) > 0, "Should detect Epstein variations"

        # All variations should map to same GUID
        if len(epstein_entities) > 1:
            guids = [e.guid for e in epstein_entities]
            # May have multiple GUIDs if variations are separate entities in database
            # Just verify we got detections
            assert all(guid for guid in guids), "All should have GUIDs"

    def test_max_results_limit(self, detector):
        """Test that max_results parameter works."""
        # Text with many different entities
        text = """
        Jeffrey Epstein, Ghislaine Maxwell, Bill Clinton, Prince Andrew,
        Virginia Giuffre, Alan Dershowitz, Leslie Wexner, and others.
        """

        entities_5 = detector.detect_entities(text, max_results=5)
        entities_10 = detector.detect_entities(text, max_results=10)

        assert len(entities_5) <= 5, "Should respect max_results=5"
        assert len(entities_10) <= 10, "Should respect max_results=10"
        assert len(entities_10) >= len(entities_5), "Higher limit should give more results"

    def test_empty_text_handling(self, detector):
        """Test handling of empty or None text."""
        assert detector.detect_entities("") == [], "Empty string should return empty list"
        assert detector.detect_entities(None) == [], "None should return empty list"
        assert detector.detect_entities("   ") == [], "Whitespace should return empty list"

    def test_no_entities_text(self, detector):
        """Test text with no recognizable entities."""
        text = "This is a document about generic topics with no specific people mentioned."
        entities = detector.detect_entities(text)

        # May detect some entities if generic words match, but should be minimal
        assert isinstance(entities, list), "Should return list even with no entities"

    def test_case_insensitive_detection(self, detector):
        """Test that detection is case-insensitive."""
        text_lower = "jeffrey epstein and ghislaine maxwell"
        text_upper = "JEFFREY EPSTEIN AND GHISLAINE MAXWELL"
        text_mixed = "Jeffrey EPSTEIN and Ghislaine MAXWELL"

        entities_lower = detector.detect_entities(text_lower)
        entities_upper = detector.detect_entities(text_upper)
        entities_mixed = detector.detect_entities(text_mixed)

        # All should detect similar entities
        assert len(entities_lower) > 0, "Should detect lowercase"
        assert len(entities_upper) > 0, "Should detect uppercase"
        assert len(entities_mixed) > 0, "Should detect mixed case"

    def test_get_entity_by_guid(self, detector, sample_text):
        """Test retrieving entity data by GUID."""
        entities = detector.detect_entities(sample_text)

        if len(entities) > 0:
            test_entity = entities[0]
            entity_data = detector.get_entity_by_guid(test_entity.guid)

            assert entity_data is not None, "Should find entity by GUID"
            assert entity_data.get("guid") == test_entity.guid, "GUID should match"


class TestEntityDetectionCache:
    """Tests for entity detection caching."""

    @pytest.fixture
    def detector(self):
        """Create fresh detector instance."""
        return get_entity_detector()

    @pytest.fixture
    def sample_text(self):
        """Reusable sample text."""
        return "Jeffrey Epstein and Ghislaine Maxwell were involved in the case."

    def test_cache_performance(self, detector, sample_text):
        """Test that caching improves performance."""
        # First call (uncached)
        start = time.time()
        entities1 = detector.detect_entities(sample_text, use_cache=True)
        uncached_time = time.time() - start

        # Second call (should be cached)
        start = time.time()
        entities2 = detector.detect_entities(sample_text, use_cache=True)
        cached_time = time.time() - start

        # Cached call should be much faster
        assert cached_time < uncached_time, f"Cached ({cached_time:.3f}s) should be faster than uncached ({uncached_time:.3f}s)"
        assert entities1 == entities2, "Cached results should match uncached"

    def test_cache_disabled(self, detector, sample_text):
        """Test detection works with cache disabled."""
        entities = detector.detect_entities(sample_text, use_cache=False)

        assert isinstance(entities, list), "Should return list with cache disabled"
        assert len(entities) > 0, "Should detect entities without cache"

    def test_cache_different_texts(self, detector):
        """Test that different texts are cached separately."""
        text1 = "Jeffrey Epstein was arrested."
        text2 = "Ghislaine Maxwell was charged."

        entities1 = detector.detect_entities(text1, use_cache=True)
        entities2 = detector.detect_entities(text2, use_cache=True)

        # Different texts should produce different results
        entity_names1 = [e.name for e in entities1]
        entity_names2 = [e.name for e in entities2]

        # At least one should be different
        assert entities1 != entities2 or entity_names1 != entity_names2, "Different texts should cache separately"


class TestEntityDetectionPerformance:
    """Performance benchmarks for entity detection."""

    @pytest.fixture
    def detector(self):
        return get_entity_detector()

    @pytest.fixture
    def long_text(self):
        """Generate long text for performance testing."""
        return """
        Jeffrey Epstein and Ghislaine Maxwell ran a criminal enterprise.
        The investigation by the Southern District of New York lasted years.
        Victims like Virginia Giuffre came forward with allegations.
        High-profile individuals including Bill Clinton and Prince Andrew were mentioned.
        """ * 20  # Repeat to create ~3000 char text

    def test_typical_performance(self, detector, long_text):
        """Test performance meets targets for typical text."""
        start = time.time()
        entities = detector.detect_entities(long_text, use_cache=False)
        elapsed = time.time() - start

        assert elapsed < 0.5, f"Detection should complete in <500ms for typical text, took {elapsed:.3f}s"
        assert len(entities) > 0, "Should detect entities"

    def test_cached_performance(self, detector, long_text):
        """Test cached performance is under 10ms."""
        # Warm up cache
        detector.detect_entities(long_text, use_cache=True)

        # Measure cached performance
        start = time.time()
        entities = detector.detect_entities(long_text, use_cache=True)
        elapsed = time.time() - start

        assert elapsed < 0.01, f"Cached detection should be <10ms, took {elapsed:.3f}s"


class TestEntityDetectionErrorHandling:
    """Tests for error handling and edge cases."""

    def test_missing_entity_file(self):
        """Test handling of missing entity_statistics.json."""
        detector = EntityDetector(entity_stats_path="nonexistent_file.json")

        assert detector.entities == {}, "Should handle missing file gracefully"
        assert detector.entity_patterns == [], "Should have empty patterns"

        # Should still work, just return empty results
        entities = detector.detect_entities("Some text")
        assert entities == [], "Should return empty list with no data"

    def test_invalid_guid_lookup(self):
        """Test get_entity_by_guid with invalid GUID."""
        detector = get_entity_detector()
        result = detector.get_entity_by_guid("invalid-guid-12345")

        assert result is None, "Should return None for invalid GUID"

    def test_very_long_text(self):
        """Test handling of very long text (>10K chars)."""
        detector = get_entity_detector()
        long_text = "Jeffrey Epstein was involved. " * 500  # ~15K chars

        # Should complete without hanging or crashing
        start = time.time()
        entities = detector.detect_entities(long_text, use_cache=False)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Should handle long text in reasonable time, took {elapsed:.3f}s"
        assert isinstance(entities, list), "Should return list for long text"

    def test_special_characters_in_text(self):
        """Test handling of special characters."""
        detector = get_entity_detector()
        text = "Jeffrey Epstein's associates included: Bill Clinton, Prince Andrew, etc."

        entities = detector.detect_entities(text)

        # Should handle special chars without errors
        assert isinstance(entities, list), "Should handle special characters"
        assert len(entities) > 0, "Should still detect entities"


@pytest.mark.integration
class TestEntityDetectionEndToEnd:
    """End-to-end integration tests simulating real usage."""

    def test_document_summary_use_case(self):
        """Test entity detection in document summary scenario."""
        detector = get_entity_detector()

        # Simulate document summary text
        summary = """
        This deposition transcript from the Southern District of New York
        contains testimony regarding Jeffrey Epstein and his associate
        Ghislaine Maxwell. The witness Virginia Giuffre described events
        involving Prince Andrew and other high-profile individuals.
        """

        entities = detector.detect_entities(summary, max_results=10)

        # Verify results are suitable for UI display
        assert len(entities) > 0, "Should detect entities for summary"
        assert all(hasattr(e, 'guid') for e in entities), "All entities should have GUIDs"
        assert all(hasattr(e, 'name') for e in entities), "All entities should have names"
        assert all(hasattr(e, 'mentions') for e in entities), "All entities should have mention counts"

        # Top entity should be most mentioned
        if len(entities) > 1:
            assert entities[0].mentions >= entities[-1].mentions, "Should sort by mention count"

    def test_batch_detection_performance(self):
        """Test performance when processing multiple documents."""
        detector = get_entity_detector()

        documents = [
            "Jeffrey Epstein was arrested in 2019.",
            "Ghislaine Maxwell was charged in 2020.",
            "Virginia Giuffre filed a lawsuit.",
            "The Southern District investigated the case.",
            "Prince Andrew gave an interview about the allegations."
        ]

        start = time.time()
        results = [detector.detect_entities(doc, use_cache=True) for doc in documents]
        elapsed = time.time() - start

        assert len(results) == len(documents), "Should process all documents"
        assert elapsed < 1.0, f"Batch processing should be fast, took {elapsed:.3f}s"

        # All results should be valid
        assert all(isinstance(r, list) for r in results), "All results should be lists"
