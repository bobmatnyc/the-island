#!/usr/bin/env python3
"""
RAG System Test Suite
Epstein Document Archive - Comprehensive Testing

Tests all components of the RAG system:
- Vector store embedding and retrieval
- Entity-document linking
- Semantic search accuracy
- Knowledge graph integration
- API endpoint functionality
- Performance benchmarks

Usage:
    python3 scripts/rag/test_rag_system.py
    python3 scripts/rag/test_rag_system.py --quick
    python3 scripts/rag/test_rag_system.py --benchmark
"""

import argparse
import json
import sys
import time
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


# Project paths
PROJECT_ROOT = Path("/Users/masa/Projects/Epstein")
VECTOR_STORE_DIR = PROJECT_ROOT / "data/vector_store/chroma"
ENTITY_DOC_INDEX_PATH = PROJECT_ROOT / "data/metadata/entity_document_index.json"
ENTITY_NETWORK_PATH = PROJECT_ROOT / "data/metadata/entity_network.json"
OCR_TEXT_DIR = PROJECT_ROOT / "data/sources/house_oversight_nov2025/ocr_text"

COLLECTION_NAME = "epstein_documents"


class RAGSystemTester:
    def __init__(self):
        """Initialize the test suite."""
        self.results = {
            "passed": 0,
            "failed": 0,
            "warnings": 0,
            "tests": []
        }

        # Load components
        try:
            self.client = chromadb.PersistentClient(
                path=str(VECTOR_STORE_DIR),
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_collection(name=COLLECTION_NAME)
            self.model = SentenceTransformer("all-MiniLM-L6-v2")

            with open(ENTITY_DOC_INDEX_PATH) as f:
                self.entity_doc_index = json.load(f)

            with open(ENTITY_NETWORK_PATH) as f:
                self.entity_network = json.load(f)

            print("✅ All components loaded successfully\n")

        except Exception as e:
            print(f"❌ Failed to load components: {e}")
            sys.exit(1)

    def test_vector_store_existence(self):
        """Test 1: Verify vector store exists and has documents."""
        test_name = "Vector Store Existence"
        try:
            count = self.collection.count()
            assert count > 0, "Vector store is empty"
            assert count >= 1000, f"Expected at least 1000 documents, got {count}"

            self._pass_test(test_name, f"Vector store has {count:,} documents")

        except Exception as e:
            self._fail_test(test_name, str(e))

    def test_embedding_generation(self):
        """Test 2: Verify embedding generation works."""
        test_name = "Embedding Generation"
        try:
            test_text = "This is a test document about Jeffrey Epstein."
            embedding = self.model.encode([test_text])[0]

            assert len(embedding) == 384, f"Expected 384 dimensions, got {len(embedding)}"
            assert embedding.dtype.name.startswith("float"), "Embeddings should be floats"

            self._pass_test(test_name, f"Generated {len(embedding)}-dimensional embedding")

        except Exception as e:
            self._fail_test(test_name, str(e))

    def test_semantic_search_basic(self):
        """Test 3: Basic semantic search functionality."""
        test_name = "Semantic Search - Basic"
        try:
            query = "Epstein financial records"
            query_embedding = self.model.encode([query])[0]

            start_time = time.time()
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=10
            )
            query_time = (time.time() - start_time) * 1000

            assert len(results["ids"][0]) > 0, "No results returned"
            assert query_time < 500, f"Query too slow: {query_time:.2f}ms"

            self._pass_test(
                test_name,
                f"Found {len(results['ids'][0])} results in {query_time:.2f}ms"
            )

        except Exception as e:
            self._fail_test(test_name, str(e))

    def test_semantic_search_relevance(self):
        """Test 4: Verify semantic search returns relevant results."""
        test_name = "Semantic Search - Relevance"
        try:
            # Test known entity query
            query = "Ghislaine Maxwell"
            query_embedding = self.model.encode([query])[0]

            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=5
            )

            # Check if results mention the entity
            relevant_count = 0
            for _i, doc in enumerate(results["documents"][0]):
                if "maxwell" in doc.lower() or "ghislaine" in doc.lower():
                    relevant_count += 1

            relevance_rate = relevant_count / len(results["documents"][0])
            assert relevance_rate >= 0.6, f"Low relevance: {relevance_rate:.2%}"

            self._pass_test(
                test_name,
                f"Relevance rate: {relevance_rate:.2%} ({relevant_count}/5 relevant)"
            )

        except Exception as e:
            self._fail_test(test_name, str(e))

    def test_entity_document_index(self):
        """Test 5: Verify entity-document index is functional."""
        test_name = "Entity-Document Index"
        try:
            entity_to_docs = self.entity_doc_index.get("entity_to_documents", {})

            # Check known entities
            test_entities = ["Jeffrey Epstein", "Maxwell, Ghislaine", "Clinton, Bill"]
            found_entities = 0

            for entity in test_entities:
                if entity in entity_to_docs:
                    found_entities += 1
                    entity_data = entity_to_docs[entity]
                    assert "documents" in entity_data, f"Missing documents for {entity}"
                    assert "mention_count" in entity_data, f"Missing mention_count for {entity}"

            assert found_entities >= 1, "No test entities found in index"

            self._pass_test(
                test_name,
                f"Found {found_entities}/{len(test_entities)} test entities, "
                f"total entities: {len(entity_to_docs)}"
            )

        except Exception as e:
            self._fail_test(test_name, str(e))

    def test_entity_search(self):
        """Test 6: Entity-based document retrieval."""
        test_name = "Entity Search"
        try:
            entity_to_docs = self.entity_doc_index.get("entity_to_documents", {})

            # Pick first entity with documents
            entity = None
            for e, data in entity_to_docs.items():
                if data["document_count"] > 0:
                    entity = e
                    break

            assert entity is not None, "No entities with documents found"

            entity_data = entity_to_docs[entity]
            docs = entity_data["documents"][:5]

            assert len(docs) > 0, f"No documents for entity: {entity}"

            # Verify document structure
            for doc in docs:
                assert "doc_id" in doc, "Missing doc_id"
                assert "filename" in doc, "Missing filename"
                assert "mentions" in doc, "Missing mentions count"

            self._pass_test(
                test_name,
                f"Retrieved {len(docs)} documents for '{entity}'"
            )

        except Exception as e:
            self._fail_test(test_name, str(e))

    def test_entity_network(self):
        """Test 7: Verify entity network structure."""
        test_name = "Entity Network"
        try:
            nodes = self.entity_network.get("nodes", [])
            edges = self.entity_network.get("edges", [])

            assert len(nodes) > 0, "No nodes in entity network"
            assert len(edges) > 0, "No edges in entity network"

            # Verify node structure
            sample_node = nodes[0]
            assert "id" in sample_node, "Node missing 'id'"
            assert "name" in sample_node, "Node missing 'name'"

            # Verify edge structure
            sample_edge = edges[0]
            assert "source" in sample_edge, "Edge missing 'source'"
            assert "target" in sample_edge, "Edge missing 'target'"
            assert "weight" in sample_edge, "Edge missing 'weight'"

            self._pass_test(
                test_name,
                f"Network has {len(nodes)} nodes, {len(edges)} edges"
            )

        except Exception as e:
            self._fail_test(test_name, str(e))

    def test_multi_entity_search(self):
        """Test 8: Search for documents mentioning multiple entities."""
        test_name = "Multi-Entity Search"
        try:
            entity_to_docs = self.entity_doc_index.get("entity_to_documents", {})

            # Find two entities with overlapping documents
            test_entities = []
            for entity, data in entity_to_docs.items():
                if data["document_count"] >= 5:
                    test_entities.append(entity)
                    if len(test_entities) >= 2:
                        break

            assert len(test_entities) >= 2, "Not enough entities with documents"

            # Find intersection
            doc_sets = [
                {doc["doc_id"] for doc in entity_to_docs[entity]["documents"]}
                for entity in test_entities
            ]
            common_docs = set.intersection(*doc_sets)

            self._pass_test(
                test_name,
                f"Found {len(common_docs)} documents mentioning both {test_entities[0]} and {test_entities[1]}"
            )

        except Exception as e:
            self._fail_test(test_name, str(e))

    def test_metadata_extraction(self):
        """Test 9: Verify metadata is extracted correctly."""
        test_name = "Metadata Extraction"
        try:
            # Get a sample document
            results = self.collection.get(limit=10)

            assert len(results["metadatas"]) > 0, "No metadata found"

            metadata_fields = ["filename", "doc_id", "source", "file_size"]
            found_fields = 0

            for metadata in results["metadatas"]:
                for field in metadata_fields:
                    if field in metadata:
                        found_fields += 1
                        break

            coverage = found_fields / len(results["metadatas"])
            assert coverage >= 0.8, f"Low metadata coverage: {coverage:.2%}"

            self._pass_test(
                test_name,
                f"Metadata coverage: {coverage:.2%}"
            )

        except Exception as e:
            self._fail_test(test_name, str(e))

    def test_performance_benchmark(self):
        """Test 10: Performance benchmarks."""
        test_name = "Performance Benchmark"
        try:
            # Test query performance
            test_queries = [
                "Epstein financial transactions",
                "Ghislaine Maxwell",
                "Little St. James Island",
                "flight logs",
                "Virginia Giuffre"
            ]

            query_times = []
            for query in test_queries:
                query_embedding = self.model.encode([query])[0]
                start_time = time.time()
                self.collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=10
                )
                query_time = (time.time() - start_time) * 1000
                query_times.append(query_time)

            avg_query_time = sum(query_times) / len(query_times)
            max_query_time = max(query_times)

            # Performance targets
            assert avg_query_time < 500, f"Average query time too high: {avg_query_time:.2f}ms"
            assert max_query_time < 1000, f"Max query time too high: {max_query_time:.2f}ms"

            self._pass_test(
                test_name,
                f"Avg: {avg_query_time:.2f}ms, Max: {max_query_time:.2f}ms"
            )

        except Exception as e:
            self._fail_test(test_name, str(e))

    def _pass_test(self, test_name: str, details: str):
        """Record a passed test."""
        self.results["passed"] += 1
        self.results["tests"].append({
            "name": test_name,
            "status": "PASS",
            "details": details
        })
        print(f"✅ PASS: {test_name}")
        print(f"   {details}\n")

    def _fail_test(self, test_name: str, error: str):
        """Record a failed test."""
        self.results["failed"] += 1
        self.results["tests"].append({
            "name": test_name,
            "status": "FAIL",
            "error": error
        })
        print(f"❌ FAIL: {test_name}")
        print(f"   Error: {error}\n")

    def run_all_tests(self, quick: bool = False):
        """Run all tests."""
        print("="*70)
        print("RAG SYSTEM TEST SUITE")
        print("="*70)
        print()

        # Core tests (always run)
        self.test_vector_store_existence()
        self.test_embedding_generation()
        self.test_semantic_search_basic()
        self.test_entity_document_index()
        self.test_entity_network()

        # Extended tests (skip if quick mode)
        if not quick:
            self.test_semantic_search_relevance()
            self.test_entity_search()
            self.test_multi_entity_search()
            self.test_metadata_extraction()
            self.test_performance_benchmark()

        # Print summary
        print("="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")

        if self.results["failed"] > 0:
            print("\nFailed tests:")
            for test in self.results["tests"]:
                if test["status"] == "FAIL":
                    print(f"  - {test['name']}: {test['error']}")

        total = self.results["passed"] + self.results["failed"]
        success_rate = self.results["passed"] / total if total > 0 else 0

        print(f"\nSuccess rate: {success_rate:.1%}")
        print("="*70)

        return self.results


def main():
    parser = argparse.ArgumentParser(description="Test RAG system")
    parser.add_argument("--quick", action="store_true", help="Run only core tests")
    parser.add_argument("--benchmark", action="store_true", help="Run performance benchmarks only")

    args = parser.parse_args()

    tester = RAGSystemTester()

    if args.benchmark:
        print("Running performance benchmarks...\n")
        tester.test_performance_benchmark()
    else:
        results = tester.run_all_tests(quick=args.quick)

        # Exit with error code if tests failed
        if results["failed"] > 0:
            sys.exit(1)


if __name__ == "__main__":
    main()
