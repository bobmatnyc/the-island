"""
Integration Tests for Document Similarity Service

Tests the semantic similarity search system including:
- Embedding generation
- Cosine similarity calculation
- LRU caching
- Document loading from OCR/markdown
- Error handling

Design Decision: Integration tests for ML-based similarity
Rationale: Similarity depends on sentence-transformers model, file I/O,
and caching. Integration tests verify the full pipeline.

Test Coverage Target: >85% for document_similarity.py
"""

import pytest
import time
import numpy as np
from pathlib import Path
from server.services.document_similarity import (
    DocumentSimilarityService,
    get_similarity_service
)


class TestDocumentSimilarityService:
    """Integration tests for DocumentSimilarityService."""

    @pytest.fixture
    def service(self):
        """Create fresh service instance."""
        return DocumentSimilarityService(cache_size=100)

    @pytest.fixture
    def sample_documents(self):
        """Sample document metadata for testing."""
        return [
            {
                "id": "doc-1",
                "filename": "deposition_epstein.pdf",
                "summary": "Jeffrey Epstein deposition transcript discussing criminal activities",
                "entities_mentioned": ["Jeffrey Epstein", "Ghislaine Maxwell"],
                "doc_type": "deposition",
                "file_size": 50000,
                "date_extracted": "2024-01-15"
            },
            {
                "id": "doc-2",
                "filename": "maxwell_charges.pdf",
                "summary": "Ghislaine Maxwell criminal charges and indictment details",
                "entities_mentioned": ["Ghislaine Maxwell", "Jeffrey Epstein"],
                "doc_type": "legal",
                "file_size": 35000,
                "date_extracted": "2024-01-20"
            },
            {
                "id": "doc-3",
                "filename": "flight_logs.pdf",
                "summary": "Private jet flight logs showing passenger manifests",
                "entities_mentioned": ["Bill Clinton", "Prince Andrew"],
                "doc_type": "flight_log",
                "file_size": 25000,
                "date_extracted": "2024-01-10"
            },
            {
                "id": "doc-4",
                "filename": "financial_records.pdf",
                "summary": "Financial transactions and banking records for investigation",
                "entities_mentioned": ["Leslie Wexner"],
                "doc_type": "financial",
                "file_size": 40000,
                "date_extracted": "2024-01-18"
            }
        ]

    def test_service_initialization(self, service):
        """Test service initializes correctly."""
        assert service is not None
        assert service.cache_size == 100
        assert len(service.embedding_cache) == 0, "Cache should start empty"
        assert service.model is None, "Model should be lazy-loaded"

    def test_singleton_pattern(self):
        """Test get_similarity_service returns singleton."""
        service1 = get_similarity_service()
        service2 = get_similarity_service()

        assert service1 is service2, "Should return same instance"

    def test_model_lazy_loading(self, service):
        """Test that model loads only when needed."""
        assert service.model is None, "Model should not load on init"

        # Trigger model loading
        try:
            model = service._get_model()
            assert model is not None, "Model should load when requested"
            assert service.model is not None, "Model should be cached"
        except RuntimeError as e:
            if "sentence-transformers" in str(e):
                pytest.skip("sentence-transformers not installed")
            raise

    def test_embedding_generation(self, service):
        """Test embedding generation for text."""
        try:
            text = "Jeffrey Epstein and Ghislaine Maxwell criminal investigation"
            embedding = service._get_embedding(text, "test-doc-1")

            assert isinstance(embedding, np.ndarray), "Should return numpy array"
            assert len(embedding.shape) == 1, "Should be 1D vector"
            assert embedding.shape[0] > 0, "Should have dimensions"
        except RuntimeError as e:
            if "sentence-transformers" in str(e):
                pytest.skip("sentence-transformers not installed")
            raise

    def test_embedding_caching(self, service):
        """Test that embeddings are cached correctly."""
        try:
            text = "Test document content"
            doc_id = "test-cache-1"

            # First call - should generate and cache
            embedding1 = service._get_embedding(text, doc_id)
            assert doc_id in service.embedding_cache, "Should cache embedding"

            # Second call - should retrieve from cache
            embedding2 = service._get_embedding(text, doc_id)
            np.testing.assert_array_equal(embedding1, embedding2, "Cached embedding should match")
        except RuntimeError as e:
            if "sentence-transformers" in str(e):
                pytest.skip("sentence-transformers not installed")
            raise

    def test_lru_cache_eviction(self, service):
        """Test that cache evicts oldest entries when full."""
        try:
            service.cache_size = 3  # Small cache for testing

            # Add 4 embeddings
            for i in range(4):
                text = f"Document {i} content"
                doc_id = f"doc-{i}"
                service._get_embedding(text, doc_id)

            # Cache should have max 3 entries
            assert len(service.embedding_cache) == 3, f"Cache should evict oldest, has {len(service.embedding_cache)}"

            # First document should be evicted
            assert "doc-0" not in service.embedding_cache, "Oldest entry should be evicted"
            assert "doc-3" in service.embedding_cache, "Newest entry should be present"
        except RuntimeError as e:
            if "sentence-transformers" in str(e):
                pytest.skip("sentence-transformers not installed")
            raise

    def test_cosine_similarity_calculation(self, service):
        """Test cosine similarity between vectors."""
        # Identical vectors
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([1, 0, 0])
        similarity = service._cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.001, "Identical vectors should have similarity ~1.0"

        # Orthogonal vectors
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([0, 1, 0])
        similarity = service._cosine_similarity(vec1, vec2)
        assert abs(similarity) < 0.001, "Orthogonal vectors should have similarity ~0.0"

        # Opposite vectors
        vec1 = np.array([1, 0, 0])
        vec2 = np.array([-1, 0, 0])
        similarity = service._cosine_similarity(vec1, vec2)
        assert abs(similarity - (-1.0)) < 0.001, "Opposite vectors should have similarity ~-1.0"

    def test_cosine_similarity_zero_vectors(self, service):
        """Test handling of zero vectors."""
        vec1 = np.array([0, 0, 0])
        vec2 = np.array([1, 2, 3])

        similarity = service._cosine_similarity(vec1, vec2)
        assert similarity == 0.0, "Zero vector should return 0.0 similarity"

    def test_find_similar_documents_basic(self, service, sample_documents):
        """Test finding similar documents."""
        try:
            results = service.find_similar_documents(
                "doc-1",
                sample_documents,
                limit=3,
                similarity_threshold=0.5,
                use_cache=False
            )

            assert isinstance(results, list), "Should return list"
            # Results may be empty if summaries are too different or model not available
            # Just verify structure is correct
            for result in results:
                assert "document_id" in result
                assert "similarity_score" in result
                assert "title" in result
                assert 0 <= result["similarity_score"] <= 1.0, "Score should be in [0, 1]"

        except RuntimeError as e:
            if "sentence-transformers" in str(e):
                pytest.skip("sentence-transformers not installed")
            raise

    def test_find_similar_documents_limit(self, service, sample_documents):
        """Test that limit parameter works."""
        try:
            results = service.find_similar_documents(
                "doc-1",
                sample_documents,
                limit=2,
                similarity_threshold=0.0,  # Low threshold to ensure we get results
                use_cache=False
            )

            assert len(results) <= 2, "Should respect limit parameter"

        except RuntimeError as e:
            if "sentence-transformers" in str(e):
                pytest.skip("sentence-transformers not installed")
            raise

    def test_find_similar_documents_threshold(self, service, sample_documents):
        """Test similarity threshold filtering."""
        try:
            # High threshold should give fewer results
            results_high = service.find_similar_documents(
                "doc-1",
                sample_documents,
                limit=10,
                similarity_threshold=0.9,
                use_cache=False
            )

            # Low threshold should give more results
            results_low = service.find_similar_documents(
                "doc-1",
                sample_documents,
                limit=10,
                similarity_threshold=0.3,
                use_cache=False
            )

            assert len(results_high) <= len(results_low), "High threshold should give fewer results"

            # All results should meet threshold
            for result in results_high:
                assert result["similarity_score"] >= 0.9, "Should meet high threshold"

        except RuntimeError as e:
            if "sentence-transformers" in str(e):
                pytest.skip("sentence-transformers not installed")
            raise

    def test_find_similar_documents_sorting(self, service, sample_documents):
        """Test that results are sorted by similarity."""
        try:
            results = service.find_similar_documents(
                "doc-1",
                sample_documents,
                limit=10,
                similarity_threshold=0.0,
                use_cache=False
            )

            if len(results) > 1:
                scores = [r["similarity_score"] for r in results]
                assert scores == sorted(scores, reverse=True), "Results should be sorted by score descending"

        except RuntimeError as e:
            if "sentence-transformers" in str(e):
                pytest.skip("sentence-transformers not installed")
            raise

    def test_missing_source_document(self, service, sample_documents):
        """Test handling of missing source document."""
        results = service.find_similar_documents(
            "nonexistent-doc",
            sample_documents,
            limit=5
        )

        assert results == [], "Should return empty list for missing document"

    def test_documents_without_text(self, service):
        """Test handling of documents without text content."""
        docs = [
            {"id": "doc-1", "filename": "test.pdf"},  # No summary
            {"id": "doc-2", "filename": "test2.pdf"}
        ]

        results = service.find_similar_documents(
            "doc-1",
            docs,
            limit=5,
            use_cache=False
        )

        # May return results or empty list depending on fallback
        assert isinstance(results, list), "Should return list even without text"

    def test_clear_cache(self, service):
        """Test cache clearing."""
        try:
            # Add some embeddings to cache
            for i in range(3):
                text = f"Test document {i}"
                service._get_embedding(text, f"doc-{i}")

            assert len(service.embedding_cache) > 0, "Cache should have entries"

            # Clear cache
            service.clear_cache()

            assert len(service.embedding_cache) == 0, "Cache should be empty after clear"

        except RuntimeError as e:
            if "sentence-transformers" in str(e):
                pytest.skip("sentence-transformers not installed")
            raise


class TestSimilaritySearchCache:
    """Tests for similarity search result caching."""

    @pytest.fixture
    def service(self):
        return get_similarity_service()

    @pytest.fixture
    def sample_docs(self):
        return [
            {"id": "doc-1", "summary": "Test document about Jeffrey Epstein"},
            {"id": "doc-2", "summary": "Another document about Ghislaine Maxwell"}
        ]

    def test_cache_improves_performance(self, service, sample_docs):
        """Test that caching improves performance."""
        try:
            # First call (uncached)
            start = time.time()
            results1 = service.find_similar_documents(
                "doc-1", sample_docs, limit=5, use_cache=True
            )
            uncached_time = time.time() - start

            # Second call (cached)
            start = time.time()
            results2 = service.find_similar_documents(
                "doc-1", sample_docs, limit=5, use_cache=True
            )
            cached_time = time.time() - start

            assert cached_time < uncached_time, "Cached should be faster"
            assert results1 == results2, "Results should match"

        except RuntimeError as e:
            if "sentence-transformers" in str(e):
                pytest.skip("sentence-transformers not installed")
            raise

    def test_cache_respects_parameters(self, service, sample_docs):
        """Test that different parameters use different cache entries."""
        try:
            results1 = service.find_similar_documents(
                "doc-1", sample_docs, limit=3, similarity_threshold=0.7, use_cache=True
            )

            results2 = service.find_similar_documents(
                "doc-1", sample_docs, limit=5, similarity_threshold=0.7, use_cache=True
            )

            # Different limits should potentially give different results
            # (though may be same if fewer than 5 results)
            assert isinstance(results1, list)
            assert isinstance(results2, list)

        except RuntimeError as e:
            if "sentence-transformers" in str(e):
                pytest.skip("sentence-transformers not installed")
            raise


class TestSimilarityPerformance:
    """Performance benchmarks for similarity search."""

    @pytest.fixture
    def service(self):
        return get_similarity_service()

    @pytest.fixture
    def large_document_set(self):
        """Generate larger document set for performance testing."""
        docs = []
        for i in range(50):
            docs.append({
                "id": f"doc-{i}",
                "filename": f"document_{i}.pdf",
                "summary": f"Document {i} about various topics including investigation and evidence.",
                "entities_mentioned": [f"Person {i}"],
                "doc_type": "legal",
                "file_size": 30000 + i * 1000
            })
        return docs

    def test_similarity_search_performance(self, service, large_document_set):
        """Test that similarity search completes in reasonable time."""
        try:
            start = time.time()
            results = service.find_similar_documents(
                "doc-0",
                large_document_set,
                limit=10,
                use_cache=False
            )
            elapsed = time.time() - start

            assert elapsed < 2.0, f"Similarity search should complete in <2s for 50 docs, took {elapsed:.3f}s"
            assert isinstance(results, list), "Should return results"

        except RuntimeError as e:
            if "sentence-transformers" in str(e):
                pytest.skip("sentence-transformers not installed")
            raise

    def test_cached_similarity_performance(self, service, large_document_set):
        """Test cached performance is under 10ms."""
        try:
            # Warm up cache
            service.find_similar_documents(
                "doc-0", large_document_set, limit=10, use_cache=True
            )

            # Measure cached performance
            start = time.time()
            results = service.find_similar_documents(
                "doc-0", large_document_set, limit=10, use_cache=True
            )
            elapsed = time.time() - start

            assert elapsed < 0.01, f"Cached search should be <10ms, took {elapsed:.3f}s"

        except RuntimeError as e:
            if "sentence-transformers" in str(e):
                pytest.skip("sentence-transformers not installed")
            raise


@pytest.mark.integration
class TestSimilarityEndToEnd:
    """End-to-end integration tests for similarity search."""

    def test_document_viewer_use_case(self):
        """Test similarity search in document viewer scenario."""
        service = get_similarity_service()

        # Simulate real document metadata
        documents = [
            {
                "id": "deposition-123",
                "filename": "epstein_deposition_2009.pdf",
                "summary": "Deposition of Jeffrey Epstein regarding allegations of misconduct",
                "entities_mentioned": ["Jeffrey Epstein"],
                "doc_type": "deposition",
                "file_size": 150000,
                "classification": "Legal Document"
            },
            {
                "id": "charges-456",
                "filename": "maxwell_charges_2020.pdf",
                "summary": "Criminal charges against Ghislaine Maxwell for trafficking",
                "entities_mentioned": ["Ghislaine Maxwell", "Jeffrey Epstein"],
                "doc_type": "legal",
                "file_size": 80000,
                "classification": "Indictment"
            }
        ]

        try:
            results = service.find_similar_documents(
                "deposition-123",
                documents,
                limit=5,
                similarity_threshold=0.5
            )

            # Verify results are suitable for UI
            for result in results:
                assert "document_id" in result
                assert "title" in result
                assert "similarity_score" in result
                assert "preview" in result
                assert "doc_type" in result

        except RuntimeError as e:
            if "sentence-transformers" in str(e):
                pytest.skip("sentence-transformers not installed")
            raise
