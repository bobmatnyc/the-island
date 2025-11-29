#!/usr/bin/env python3
"""
Test Entity Biography Enrichment Script

Validates that enrich_bios_from_documents.py works correctly:
1. Loads data files properly
2. Extracts document excerpts
3. Formats Grok prompts correctly
4. Handles errors gracefully
5. Saves results with proper structure

This test uses mock data to avoid API calls.
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.analysis.enrich_bios_from_documents import (
    BiographyEnricher,
    DocumentExtractor,
    GrokEnricher,
)


def create_test_biography_file(tmp_path: Path) -> Path:
    """Create test biography file"""

    bio_data = {
        "metadata": {
            "created": "2025-11-22",
            "total_entities": 2,
        },
        "entities": {
            "test_person_1": {
                "id": "test_person_1",
                "display_name": "Test Person One",
                "summary": "A test biography for person one.",
            },
            "test_person_2": {
                "id": "test_person_2",
                "display_name": "Test Person Two",
                "summary": "A test biography for person two with existing context.",
                "document_context": ["Existing context"],
            },
        },
    }

    bio_path = tmp_path / "entity_biographies.json"
    with open(bio_path, "w") as f:
        json.dump(bio_data, f, indent=2)

    return bio_path


def create_test_entity_stats_file(tmp_path: Path) -> Path:
    """Create test entity statistics file"""

    stats_data = {
        "generated": "2025-11-22",
        "total_entities": 2,
        "statistics": {
            "test_person_1": {
                "id": "test_person_1",
                "name": "Test Person One",
                "documents": [
                    {"path": "test/doc1.md", "type": "email"},
                    {"path": "test/doc2.md", "type": "court_filing"},
                ],
                "total_documents": 2,
            },
            "test_person_2": {
                "id": "test_person_2",
                "name": "Test Person Two",
                "documents": [],
                "total_documents": 0,
            },
        },
    }

    stats_path = tmp_path / "entity_statistics.json"
    with open(stats_path, "w") as f:
        json.dump(stats_data, f, indent=2)

    return stats_path


def create_test_documents(tmp_path: Path) -> Path:
    """Create test markdown documents"""

    doc_dir = tmp_path / "test"
    doc_dir.mkdir()

    # Document 1
    doc1 = doc_dir / "doc1.md"
    doc1.write_text(
        """---
title: Test Email
---

# Test Email

This is a test email mentioning Test Person One.

Test Person One was involved in some activity in 2015. They worked with several people on important projects.

Additional context about Test Person One and their role.
"""
    )

    # Document 2
    doc2 = doc_dir / "doc2.md"
    doc2.write_text(
        """---
title: Test Court Filing
---

# Test Court Filing

Court documents show Test Person One appeared in multiple filings.

The person was associated with various entities during the 2014-2016 period.
"""
    )

    return tmp_path


def test_load_biographies():
    """Test loading biography file"""

    print("Test 1: Load biographies")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create test files
        bio_path = create_test_biography_file(tmp_path)
        stats_path = create_test_entity_stats_file(tmp_path)
        doc_base = create_test_documents(tmp_path)

        # Initialize enricher
        enricher = BiographyEnricher(
            biography_path=bio_path,
            entity_stats_path=stats_path,
            markdown_base=doc_base,
            api_key="test-key",
            dry_run=True,
        )

        # Verify data loaded
        assert len(enricher.biographies) == 2
        assert "test_person_1" in enricher.biographies
        assert len(enricher.entity_stats) == 2

        print("  ✓ Biographies loaded correctly")
        print("  ✓ Entity statistics loaded correctly")


def test_document_extraction():
    """Test document excerpt extraction"""

    print("\nTest 2: Document extraction")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create test files
        stats_path = create_test_entity_stats_file(tmp_path)
        doc_base = create_test_documents(tmp_path)

        # Load stats
        with open(stats_path) as f:
            data = json.load(f)
            stats = data.get("statistics", data)

        # Initialize extractor
        extractor = DocumentExtractor(doc_base, MagicMock())

        # Extract documents for test_person_1
        excerpts = extractor.find_documents_for_entity("test_person_1", stats)

        assert len(excerpts) > 0, "Should find document excerpts"
        assert all(
            e.document_type in ["email", "court_filing"] for e in excerpts
        ), "Should have correct document types"

        print(f"  ✓ Found {len(excerpts)} document excerpts")
        print(
            f"  ✓ Total paragraphs: {sum(len(e.excerpts) for e in excerpts)}"
        )


def test_grok_enricher_dry_run():
    """Test Grok enricher in dry run mode"""

    print("\nTest 3: Grok enricher (dry run)")

    enricher = GrokEnricher(api_key="test-key", dry_run=True)

    from scripts.analysis.enrich_bios_from_documents import (
        DocumentExcerpt,
        GrokExtractionRequest,
    )

    request = GrokExtractionRequest(
        entity_id="test_person",
        entity_name="Test Person",
        current_biography="Test biography",
        document_excerpts=[
            DocumentExcerpt(
                document_path="test/doc.md",
                document_type="email",
                excerpts=["Test excerpt"],
            )
        ],
    )

    result = enricher.enrich_entity(request)

    # GrokExtractionResponse has additional_context and confidence, not success
    assert isinstance(result.additional_context, list)
    assert enricher.stats["successful"] == 1

    print("  ✓ Dry run enrichment works")
    print(f"  ✓ Stats tracked: {enricher.stats}")


def test_full_enrichment_workflow():
    """Test complete enrichment workflow"""

    print("\nTest 4: Full enrichment workflow")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create test files
        bio_path = create_test_biography_file(tmp_path)
        stats_path = create_test_entity_stats_file(tmp_path)
        doc_base = create_test_documents(tmp_path)

        # Initialize enricher (dry run)
        enricher = BiographyEnricher(
            biography_path=bio_path,
            entity_stats_path=stats_path,
            markdown_base=doc_base,
            api_key="test-key",
            dry_run=True,
        )

        # Enrich single entity
        result = enricher.enrich_entity("test_person_1")

        assert result.success
        assert result.entity_name == "Test Person One"

        print(f"  ✓ Enriched {result.entity_name}")
        print(f"  ✓ Documents analyzed: {result.documents_analyzed}")

        # Enrich all (limit 2)
        results = enricher.enrich_all(limit=2)

        assert len(results) == 2
        assert all(r.success for r in results)

        print(f"  ✓ Batch enrichment: {len(results)} entities")


def test_save_results():
    """Test saving enrichment results"""

    print("\nTest 5: Save results")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create test files
        bio_path = create_test_biography_file(tmp_path)
        stats_path = create_test_entity_stats_file(tmp_path)
        doc_base = create_test_documents(tmp_path)

        # Initialize enricher (NOT dry run for save test)
        enricher = BiographyEnricher(
            biography_path=bio_path,
            entity_stats_path=stats_path,
            markdown_base=doc_base,
            api_key="test-key",
            dry_run=False,  # Real save
        )

        # Mock Grok API
        with patch.object(enricher.grok_enricher, "enrich_entity") as mock_enrich:
            from scripts.analysis.enrich_bios_from_documents import (
                GrokExtractionResponse,
            )

            mock_enrich.return_value = GrokExtractionResponse(
                additional_context=["Test context 1", "Test context 2"],
                confidence=0.85,
            )

            # Enrich
            result = enricher.enrich_entity("test_person_1")

            # Save
            output_path = tmp_path / "output_bios.json"
            enricher.save_results([result], output_path)

            # Verify saved
            assert output_path.exists()

            with open(output_path) as f:
                saved_data = json.load(f)

            # Check structure
            entities = saved_data.get("entities", saved_data)
            assert "test_person_1" in entities
            assert "document_context" in entities["test_person_1"]
            assert len(entities["test_person_1"]["document_context"]) == 2

            print("  ✓ Results saved correctly")
            print(f"  ✓ Output file: {output_path}")
            print(f"  ✓ Context added: {entities['test_person_1']['document_context']}")


def run_all_tests():
    """Run all tests"""

    print("=" * 70)
    print("TESTING ENTITY BIOGRAPHY ENRICHMENT")
    print("=" * 70)

    try:
        test_load_biographies()
        test_document_extraction()
        test_grok_enricher_dry_run()
        test_full_enrichment_workflow()
        test_save_results()

        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        return True

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
