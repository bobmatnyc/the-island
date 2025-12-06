#!/usr/bin/env python3
"""
ChromaDB Completeness Verification Suite
Epstein Document Archive - M5 Verification & Launch

Validates ChromaDB indexing completeness, integrity, and search functionality.

Expected Collections:
- epstein_documents: 38,482 items (documents, metadata, embeddings)
- epstein_entities: 2,939 items (entities with biographical info)
- epstein_relationships: 32,316 items (entity relationships)

Verification Tests:
1. Collection Existence: All 3 collections present
2. Count Accuracy: Collection counts match expected
3. Metadata Integrity: Required fields present and valid
4. Embedding Consistency: Embeddings are 384-dimensional (all-MiniLM-L6-v2)
5. Sample Queries: Search functionality works
6. Cross-Collection: Hybrid search across all collections

Usage:
    python3 scripts/verification/verify_chromadb.py
    python3 scripts/verification/verify_chromadb.py --verbose
    python3 scripts/verification/verify_chromadb.py --test-queries-only
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CHROMADB_DIR = PROJECT_ROOT / "data/chromadb"
REPORT_DIR = PROJECT_ROOT / "docs/qa-reports"

# Expected collection specifications
EXPECTED_COLLECTIONS = {
    "epstein_documents": {
        "expected_count": 38482,
        "tolerance": 0.01,  # 1% tolerance
        "required_metadata": ["source", "filename", "doc_type"],
        "embedding_dimension": 384,
    },
    "epstein_entities": {
        "expected_count": 2939,
        "tolerance": 0.01,
        "required_metadata": ["canonical_name", "entity_type", "normalized_name"],
        "embedding_dimension": 384,
    },
    "epstein_relationships": {
        "expected_count": 32316,
        "tolerance": 0.01,
        "required_metadata": ["source_name", "target_name", "source_id", "target_id"],
        "embedding_dimension": 384,
    },
}

# Test queries for functional validation
TEST_QUERIES = [
    {
        "query": "Jeffrey Epstein",
        "expected_collections": ["epstein_documents", "epstein_entities", "epstein_relationships"],
        "min_results": 10,
    },
    {
        "query": "flight logs private jet",
        "expected_collections": ["epstein_documents", "epstein_relationships"],
        "min_results": 5,
    },
    {
        "query": "Little St. James private island",
        "expected_collections": ["epstein_documents", "epstein_entities"],
        "min_results": 3,
    },
]


class ChromaDBVerifier:
    """Comprehensive ChromaDB verification suite."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "chromadb_path": str(CHROMADB_DIR),
            "tests": [],
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0,
            },
        }
        self.client = None
        self.model = None

    def log(self, message: str, level: str = "INFO"):
        """Log message with level."""
        if self.verbose or level in ["ERROR", "WARNING"]:
            prefix = {
                "INFO": "✓",
                "WARNING": "⚠",
                "ERROR": "✗",
                "DETAIL": "  →",
            }.get(level, "•")
            print(f"{prefix} {message}")

    def add_test_result(
        self, test_name: str, passed: bool, details: dict[str, Any], warnings: list[str] = None
    ):
        """Record test result."""
        self.results["tests"].append(
            {
                "name": test_name,
                "passed": passed,
                "details": details,
                "warnings": warnings or [],
            }
        )
        self.results["summary"]["total_tests"] += 1
        if passed:
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
        if warnings:
            self.results["summary"]["warnings"] += len(warnings)

    def connect_chromadb(self) -> bool:
        """Connect to ChromaDB and verify directory exists."""
        test_name = "ChromaDB Connection"
        self.log(f"Testing: {test_name}")

        try:
            if not CHROMADB_DIR.exists():
                self.add_test_result(
                    test_name,
                    False,
                    {"error": f"ChromaDB directory not found: {CHROMADB_DIR}"},
                )
                self.log(f"ChromaDB directory not found: {CHROMADB_DIR}", "ERROR")
                return False

            self.client = chromadb.PersistentClient(
                path=str(CHROMADB_DIR), settings=Settings(anonymized_telemetry=False)
            )

            self.add_test_result(
                test_name, True, {"chromadb_path": str(CHROMADB_DIR), "connection": "successful"}
            )
            self.log("ChromaDB connection established", "INFO")
            return True

        except Exception as e:
            self.add_test_result(test_name, False, {"error": str(e)})
            self.log(f"Failed to connect to ChromaDB: {e}", "ERROR")
            return False

    def verify_collections_exist(self) -> bool:
        """Verify all expected collections exist."""
        test_name = "Collection Existence"
        self.log(f"\nTesting: {test_name}")

        try:
            collections = self.client.list_collections()
            collection_names = {coll.name for coll in collections}

            missing = []
            found = []

            for expected_name in EXPECTED_COLLECTIONS.keys():
                if expected_name in collection_names:
                    found.append(expected_name)
                    self.log(f"Found collection: {expected_name}", "DETAIL")
                else:
                    missing.append(expected_name)
                    self.log(f"Missing collection: {expected_name}", "ERROR")

            passed = len(missing) == 0
            details = {"found": found, "missing": missing, "total_collections": len(collections)}

            self.add_test_result(test_name, passed, details)
            return passed

        except Exception as e:
            self.add_test_result(test_name, False, {"error": str(e)})
            self.log(f"Error checking collections: {e}", "ERROR")
            return False

    def verify_collection_counts(self) -> bool:
        """Verify each collection has expected number of items."""
        test_name = "Collection Counts"
        self.log(f"\nTesting: {test_name}")

        all_passed = True
        collection_details = {}

        for coll_name, spec in EXPECTED_COLLECTIONS.items():
            try:
                collection = self.client.get_collection(name=coll_name)
                actual_count = collection.count()
                expected_count = spec["expected_count"]
                tolerance = spec["tolerance"]

                # Calculate acceptable range
                min_count = int(expected_count * (1 - tolerance))
                max_count = int(expected_count * (1 + tolerance))

                passed = min_count <= actual_count <= max_count
                variance = ((actual_count - expected_count) / expected_count) * 100

                collection_details[coll_name] = {
                    "actual_count": actual_count,
                    "expected_count": expected_count,
                    "variance_percent": round(variance, 2),
                    "passed": passed,
                }

                if passed:
                    self.log(
                        f"{coll_name}: {actual_count:,} items (expected {expected_count:,})", "DETAIL"
                    )
                else:
                    self.log(
                        f"{coll_name}: {actual_count:,} items - OUT OF RANGE (expected {expected_count:,} ±{tolerance*100}%)",
                        "ERROR",
                    )
                    all_passed = False

            except Exception as e:
                collection_details[coll_name] = {"error": str(e), "passed": False}
                self.log(f"Error checking {coll_name}: {e}", "ERROR")
                all_passed = False

        self.add_test_result(test_name, all_passed, collection_details)
        return all_passed

    def verify_metadata_integrity(self) -> bool:
        """Verify metadata fields are present and valid."""
        test_name = "Metadata Integrity"
        self.log(f"\nTesting: {test_name}")

        all_passed = True
        metadata_details = {}

        for coll_name, spec in EXPECTED_COLLECTIONS.items():
            try:
                collection = self.client.get_collection(name=coll_name)

                # Sample 100 items for metadata verification
                sample_size = min(100, collection.count())
                results = collection.get(limit=sample_size, include=["metadatas"])

                if not results["metadatas"]:
                    metadata_details[coll_name] = {
                        "error": "No metadata found",
                        "passed": False,
                    }
                    self.log(f"{coll_name}: No metadata found", "ERROR")
                    all_passed = False
                    continue

                # Check required fields
                required_fields = spec["required_metadata"]
                missing_fields = []
                field_coverage = {}

                for field in required_fields:
                    present_count = sum(1 for m in results["metadatas"] if field in m)
                    coverage = (present_count / sample_size) * 100
                    field_coverage[field] = round(coverage, 1)

                    if coverage < 95:  # At least 95% coverage
                        missing_fields.append(f"{field} ({coverage:.1f}% coverage)")

                passed = len(missing_fields) == 0
                metadata_details[coll_name] = {
                    "sample_size": sample_size,
                    "field_coverage": field_coverage,
                    "missing_fields": missing_fields,
                    "passed": passed,
                }

                if passed:
                    self.log(
                        f"{coll_name}: All required fields present ({sample_size} samples)", "DETAIL"
                    )
                else:
                    self.log(
                        f"{coll_name}: Missing or incomplete fields: {', '.join(missing_fields)}",
                        "ERROR",
                    )
                    all_passed = False

            except Exception as e:
                metadata_details[coll_name] = {"error": str(e), "passed": False}
                self.log(f"Error checking {coll_name} metadata: {e}", "ERROR")
                all_passed = False

        self.add_test_result(test_name, all_passed, metadata_details)
        return all_passed

    def verify_embedding_consistency(self) -> bool:
        """Verify embeddings are 384-dimensional (all-MiniLM-L6-v2)."""
        test_name = "Embedding Consistency"
        self.log(f"\nTesting: {test_name}")

        all_passed = True
        embedding_details = {}

        for coll_name, spec in EXPECTED_COLLECTIONS.items():
            try:
                collection = self.client.get_collection(name=coll_name)

                # Sample 50 items for embedding verification
                sample_size = min(50, collection.count())
                results = collection.get(limit=sample_size, include=["embeddings"])

                # Check if embeddings exist (handle numpy array)
                embeddings_exist = (
                    results["embeddings"] is not None
                    and len(results["embeddings"]) > 0
                )

                if not embeddings_exist:
                    embedding_details[coll_name] = {
                        "error": "No embeddings found",
                        "passed": False,
                    }
                    self.log(f"{coll_name}: No embeddings found", "ERROR")
                    all_passed = False
                    continue

                # Check embedding dimensions
                expected_dim = spec["embedding_dimension"]
                dimensions = []
                for emb in results["embeddings"]:
                    # Handle both list and numpy array types
                    try:
                        if hasattr(emb, '__len__') and not isinstance(emb, str):
                            dimensions.append(len(emb))
                    except:
                        pass

                if not dimensions:
                    embedding_details[coll_name] = {
                        "error": "Could not extract embedding dimensions",
                        "passed": False,
                    }
                    self.log(f"{coll_name}: Could not extract dimensions", "ERROR")
                    all_passed = False
                    continue

                # Check all dimensions match expected
                incorrect_dims = [d for d in dimensions if d != expected_dim]
                passed = len(incorrect_dims) == 0

                embedding_details[coll_name] = {
                    "sample_size": len(dimensions),
                    "expected_dimension": expected_dim,
                    "actual_dimensions": list(set(dimensions)),
                    "incorrect_count": len(incorrect_dims),
                    "passed": passed,
                }

                if passed:
                    self.log(
                        f"{coll_name}: All embeddings {expected_dim}D ({len(dimensions)} samples)",
                        "DETAIL",
                    )
                else:
                    self.log(
                        f"{coll_name}: {len(incorrect_dims)} embeddings have incorrect dimensions",
                        "ERROR",
                    )
                    all_passed = False

            except Exception as e:
                embedding_details[coll_name] = {"error": str(e), "passed": False}
                self.log(f"Error checking {coll_name} embeddings: {e}", "ERROR")
                all_passed = False

        self.add_test_result(test_name, all_passed, embedding_details)
        return all_passed

    def load_embedding_model(self) -> bool:
        """Load sentence-transformers model for query testing."""
        try:
            self.log("\nLoading embedding model (all-MiniLM-L6-v2)...", "INFO")
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            self.log("Model loaded successfully", "INFO")
            return True
        except Exception as e:
            self.log(f"Failed to load embedding model: {e}", "ERROR")
            return False

    def verify_sample_queries(self) -> bool:
        """Test sample queries to verify search functionality."""
        test_name = "Sample Query Tests"
        self.log(f"\nTesting: {test_name}")

        if not self.load_embedding_model():
            self.add_test_result(
                test_name, False, {"error": "Could not load embedding model"}
            )
            return False

        all_passed = True
        query_results = []

        for test_query in TEST_QUERIES:
            query = test_query["query"]
            self.log(f"Query: '{query}'", "DETAIL")

            query_result = {
                "query": query,
                "collections_tested": {},
                "passed": True,
            }

            # Generate query embedding
            query_embedding = self.model.encode([query])[0]

            # Test each expected collection
            for coll_name in test_query["expected_collections"]:
                try:
                    collection = self.client.get_collection(name=coll_name)

                    # Perform search
                    results = collection.query(
                        query_embeddings=[query_embedding.tolist()],
                        n_results=test_query["min_results"],
                    )

                    result_count = len(results["ids"][0]) if results["ids"] else 0
                    passed = result_count >= test_query["min_results"]

                    query_result["collections_tested"][coll_name] = {
                        "result_count": result_count,
                        "min_expected": test_query["min_results"],
                        "passed": passed,
                    }

                    if passed:
                        self.log(f"  {coll_name}: {result_count} results", "DETAIL")
                    else:
                        self.log(
                            f"  {coll_name}: Only {result_count} results (expected {test_query['min_results']}+)",
                            "WARNING",
                        )
                        query_result["passed"] = False
                        all_passed = False

                except Exception as e:
                    query_result["collections_tested"][coll_name] = {
                        "error": str(e),
                        "passed": False,
                    }
                    self.log(f"  {coll_name}: Error - {e}", "ERROR")
                    query_result["passed"] = False
                    all_passed = False

            query_results.append(query_result)

        self.add_test_result(test_name, all_passed, {"queries": query_results})
        return all_passed

    def verify_cross_collection_search(self) -> bool:
        """Test hybrid search across multiple collections."""
        test_name = "Cross-Collection Search"
        self.log(f"\nTesting: {test_name}")

        if not self.model:
            if not self.load_embedding_model():
                self.add_test_result(
                    test_name, False, {"error": "Could not load embedding model"}
                )
                return False

        try:
            # Test query that should return results from all collections
            query = "Jeffrey Epstein connections"
            self.log(f"Hybrid query: '{query}'", "DETAIL")

            query_embedding = self.model.encode([query])[0]

            search_results = {}
            for coll_name in EXPECTED_COLLECTIONS.keys():
                collection = self.client.get_collection(name=coll_name)
                results = collection.query(
                    query_embeddings=[query_embedding.tolist()], n_results=5
                )

                result_count = len(results["ids"][0]) if results["ids"] else 0
                search_results[coll_name] = result_count
                self.log(f"  {coll_name}: {result_count} results", "DETAIL")

            # Check that we got results from all collections
            passed = all(count > 0 for count in search_results.values())

            self.add_test_result(
                test_name,
                passed,
                {
                    "query": query,
                    "results_per_collection": search_results,
                    "all_collections_returned_results": passed,
                },
            )

            if not passed:
                self.log("Some collections returned no results", "WARNING")

            return passed

        except Exception as e:
            self.add_test_result(test_name, False, {"error": str(e)})
            self.log(f"Error in cross-collection search: {e}", "ERROR")
            return False

    def run_all_tests(self, test_queries_only: bool = False) -> bool:
        """Run all verification tests."""
        print("\n" + "=" * 70)
        print("CHROMADB COMPLETENESS VERIFICATION SUITE")
        print("Epstein Document Archive - M5 Verification & Launch")
        print("=" * 70)

        if test_queries_only:
            if not self.connect_chromadb():
                return False
            self.verify_sample_queries()
            self.verify_cross_collection_search()
        else:
            # Full test suite
            if not self.connect_chromadb():
                return False

            self.verify_collections_exist()
            self.verify_collection_counts()
            self.verify_metadata_integrity()
            self.verify_embedding_consistency()
            self.verify_sample_queries()
            self.verify_cross_collection_search()

        return self.results["summary"]["failed"] == 0

    def generate_report(self) -> str:
        """Generate markdown report."""
        passed = self.results["summary"]["passed"]
        failed = self.results["summary"]["failed"]
        total = self.results["summary"]["total_tests"]
        warnings = self.results["summary"]["warnings"]

        status_icon = "✅" if failed == 0 else "❌"
        overall_status = "PASS" if failed == 0 else "FAIL"

        report = f"""# ChromaDB Completeness Verification Report

**Status**: {status_icon} **{overall_status}**

**Generated**: {self.results['timestamp']}
**ChromaDB Path**: `{self.results['chromadb_path']}`

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | {total} |
| Passed | {passed} |
| Failed | {failed} |
| Warnings | {warnings} |
| Success Rate | {(passed/total*100 if total > 0 else 0):.1f}% |

## Test Results

"""

        for test in self.results["tests"]:
            icon = "✅" if test["passed"] else "❌"
            report += f"### {icon} {test['name']}\n\n"

            if test["passed"]:
                report += "**Status**: PASSED\n\n"
            else:
                report += "**Status**: FAILED\n\n"

            # Add details
            report += "**Details**:\n```json\n"
            report += json.dumps(test["details"], indent=2)
            report += "\n```\n\n"

            # Add warnings if any
            if test["warnings"]:
                report += "**Warnings**:\n"
                for warning in test["warnings"]:
                    report += f"- ⚠️ {warning}\n"
                report += "\n"

        # Add recommendations
        report += "## Recommendations\n\n"

        if failed == 0:
            report += "✅ All verification tests passed. ChromaDB is ready for production use.\n\n"
            report += "**Next Steps**:\n"
            report += "- Monitor query performance in production\n"
            report += "- Set up regular verification checks (weekly)\n"
            report += "- Document any schema changes\n"
        else:
            report += "⚠️ Some verification tests failed. Address the following issues:\n\n"
            for test in self.results["tests"]:
                if not test["passed"]:
                    report += f"- **{test['name']}**: "
                    if "error" in test["details"]:
                        report += test["details"]["error"]
                    else:
                        report += "See details above"
                    report += "\n"

        report += "\n---\n\n"
        report += "*Generated by ChromaDB Verification Suite v1.0*\n"

        return report

    def save_report(self, report: str):
        """Save report to file."""
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = REPORT_DIR / f"chromadb-verification-{timestamp}.md"

        with open(report_file, "w") as f:
            f.write(report)

        self.log(f"\nReport saved: {report_file}", "INFO")
        return report_file


def main():
    parser = argparse.ArgumentParser(description="ChromaDB Completeness Verification Suite")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--test-queries-only", action="store_true", help="Only test query functionality"
    )
    parser.add_argument("--save-report", action="store_true", help="Save report to file")

    args = parser.parse_args()

    verifier = ChromaDBVerifier(verbose=args.verbose)

    # Run tests
    success = verifier.run_all_tests(test_queries_only=args.test_queries_only)

    # Print summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    summary = verifier.results["summary"]
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Warnings: {summary['warnings']}")

    if success:
        print("\n✅ All verification tests passed!")
    else:
        print(f"\n❌ {summary['failed']} test(s) failed")

    # Generate and optionally save report
    report = verifier.generate_report()

    if args.save_report:
        report_file = verifier.save_report(report)
        print(f"\nReport saved to: {report_file}")
    else:
        print("\n" + "=" * 70)
        print("FULL REPORT")
        print("=" * 70)
        print(report)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
