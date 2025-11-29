#!/usr/bin/env python3
"""
Entity Classification System - Integration Tests

Tests for the entity classification system to ensure:
- Schema validation
- Complete entity coverage
- Valid category assignments
- Confidence score ranges
- Database integration

Author: Classification System Tests
Created: 2025-11-25
"""

import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List

import pytest


# Test data paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CLASSIFICATIONS_FILE = PROJECT_ROOT / "data/metadata/entity_classifications.json"
STATS_FILE = PROJECT_ROOT / "data/metadata/entity_statistics.json"
DB_FILE = PROJECT_ROOT / "data/metadata/entities.db"


# ==============================================================================
# SCHEMA VALIDATION TESTS
# ==============================================================================

def test_classification_file_exists():
    """Test that classification output file exists"""
    assert CLASSIFICATIONS_FILE.exists(), "Classification file not found"


def test_json_structure():
    """Test that output file has valid JSON structure"""
    with open(CLASSIFICATIONS_FILE) as f:
        data = json.load(f)

    assert "metadata" in data, "Missing metadata section"
    assert "classifications" in data, "Missing classifications section"


def test_metadata_schema():
    """Test that metadata section has required fields"""
    with open(CLASSIFICATIONS_FILE) as f:
        data = json.load(f)

    metadata = data["metadata"]

    required_fields = [
        "generated",
        "classifier",
        "total_entities",
        "successful"
    ]

    for field in required_fields:
        assert field in metadata, f"Missing metadata field: {field}"


def test_classification_schema():
    """Test that individual classifications have required fields"""
    with open(CLASSIFICATIONS_FILE) as f:
        data = json.load(f)

    # Test first classification
    if data["classifications"]:
        entity_id = next(iter(data["classifications"]))
        classification = data["classifications"][entity_id]

        # Required fields depend on schema type
        # Check for either old schema or new schema
        is_old_schema = "primary_role" in classification
        is_new_schema = "primary_category" in classification

        assert is_old_schema or is_new_schema, \
            "Classification must have either primary_role or primary_category"

        if is_old_schema:
            required_fields = [
                "primary_role",
                "connection_strength",
                "professional_category",
                "significance_score",
                "justification"
            ]
        else:
            required_fields = [
                "primary_category",
                "confidence_score",
                "reasoning",
                "tier"
            ]

        for field in required_fields:
            assert field in classification, \
                f"Missing classification field: {field}"


# ==============================================================================
# COVERAGE TESTS
# ==============================================================================

def test_all_entities_classified():
    """Test that all entities from statistics file are classified"""
    with open(STATS_FILE) as f:
        stats = json.load(f)

    with open(CLASSIFICATIONS_FILE) as f:
        classifications = json.load(f)

    total_entities = stats["total_entities"]
    classified_count = len(classifications["classifications"])

    # Allow for some failures, but should be >95% coverage
    coverage_pct = (classified_count / total_entities) * 100

    assert coverage_pct >= 95, \
        f"Insufficient coverage: {coverage_pct:.1f}% (expected >=95%)"


def test_no_duplicate_classifications():
    """Test that no entity is classified more than once"""
    with open(CLASSIFICATIONS_FILE) as f:
        data = json.load(f)

    entity_ids = list(data["classifications"].keys())
    unique_ids = set(entity_ids)

    assert len(entity_ids) == len(unique_ids), \
        "Duplicate classifications found"


# ==============================================================================
# CATEGORY VALIDATION TESTS
# ==============================================================================

def test_valid_categories():
    """Test that all categories are from valid set"""
    # Define valid categories for both schemas
    OLD_SCHEMA_ROLES = [
        "Close Associate", "Business Partner", "Political Figure",
        "Victim", "Law Enforcement", "Legal Team", "Social Contact",
        "Family Member", "Documented Individual", "Unknown"
    ]

    NEW_SCHEMA_CATEGORIES = [
        "CORE_NETWORK", "BUSINESS_FINANCIAL", "POLITICAL_GOVERNMENT",
        "CELEBRITY_ENTERTAINMENT", "ACADEMIC_SCIENTIFIC",
        "PHILANTHROPIC_NONPROFIT", "SOCIAL_ELITE", "STAFF_EMPLOYEES",
        "LEGAL_INVESTIGATIVE", "VICTIMS_SURVIVORS", "UNKNOWN_PERIPHERAL"
    ]

    with open(CLASSIFICATIONS_FILE) as f:
        data = json.load(f)

    # Detect schema type from first classification
    if data["classifications"]:
        first_classification = next(iter(data["classifications"].values()))
        is_old_schema = "primary_role" in first_classification

        if is_old_schema:
            valid_categories = OLD_SCHEMA_ROLES
            category_field = "primary_role"
        else:
            valid_categories = NEW_SCHEMA_CATEGORIES
            category_field = "primary_category"

        # Validate all classifications
        invalid_classifications = []
        for entity_id, classification in data["classifications"].items():
            category = classification.get(category_field)
            if category not in valid_categories:
                invalid_classifications.append(
                    f"{entity_id}: {category}"
                )

        assert len(invalid_classifications) == 0, \
            f"Invalid categories found: {invalid_classifications[:5]}"


def test_connection_strength_valid():
    """Test that connection strength values are valid (old schema only)"""
    VALID_STRENGTHS = [
        "Core Circle", "Frequent Associate",
        "Occasional Contact", "Documented Only"
    ]

    with open(CLASSIFICATIONS_FILE) as f:
        data = json.load(f)

    # Only test if using old schema
    if data["classifications"]:
        first_classification = next(iter(data["classifications"].values()))
        if "connection_strength" not in first_classification:
            pytest.skip("New schema does not use connection_strength")

        invalid = []
        for entity_id, classification in data["classifications"].items():
            strength = classification.get("connection_strength")
            if strength not in VALID_STRENGTHS:
                invalid.append(f"{entity_id}: {strength}")

        assert len(invalid) == 0, \
            f"Invalid connection strengths: {invalid[:5]}"


# ==============================================================================
# SCORE VALIDATION TESTS
# ==============================================================================

def test_confidence_scores_in_range():
    """Test that all confidence scores are between 0.0 and 1.0"""
    with open(CLASSIFICATIONS_FILE) as f:
        data = json.load(f)

    # Detect score field
    if data["classifications"]:
        first_classification = next(iter(data["classifications"].values()))
        score_field = "confidence_score" if "confidence_score" in first_classification else "significance_score"

        if score_field == "confidence_score":
            min_val, max_val = 0.0, 1.0
        else:
            min_val, max_val = 1, 10

        invalid = []
        for entity_id, classification in data["classifications"].items():
            score = classification.get(score_field, 0)
            if not (min_val <= score <= max_val):
                invalid.append(f"{entity_id}: {score}")

        assert len(invalid) == 0, \
            f"Invalid scores (expected {min_val}-{max_val}): {invalid[:5]}"


def test_reasonable_average_scores():
    """Test that average scores are reasonable"""
    with open(CLASSIFICATIONS_FILE) as f:
        data = json.load(f)

    # Detect score field
    if data["classifications"]:
        first_classification = next(iter(data["classifications"].values()))
        score_field = "confidence_score" if "confidence_score" in first_classification else "significance_score"

        scores = [
            c.get(score_field, 0)
            for c in data["classifications"].values()
        ]

        if scores:
            avg_score = sum(scores) / len(scores)

            if score_field == "confidence_score":
                # Confidence: average should be >0.5
                assert avg_score >= 0.5, \
                    f"Low average confidence: {avg_score:.2f}"
            else:
                # Significance: average should be 3-8
                assert 3 <= avg_score <= 8, \
                    f"Unreasonable average significance: {avg_score:.1f}"


def test_high_confidence_distribution():
    """Test that majority of classifications have reasonable confidence"""
    with open(CLASSIFICATIONS_FILE) as f:
        data = json.load(f)

    # Detect score field
    if data["classifications"]:
        first_classification = next(iter(data["classifications"].values()))
        score_field = "confidence_score" if "confidence_score" in first_classification else "significance_score"

        if score_field == "confidence_score":
            # Count classifications with confidence >= 0.60
            high_conf = sum(
                1 for c in data["classifications"].values()
                if c.get(score_field, 0) >= 0.60
            )
        else:
            # Count classifications with significance >= 5
            high_conf = sum(
                1 for c in data["classifications"].values()
                if c.get(score_field, 0) >= 5
            )

        total = len(data["classifications"])
        high_conf_pct = (high_conf / total) * 100 if total > 0 else 0

        assert high_conf_pct >= 50, \
            f"Too many low-confidence classifications: {high_conf_pct:.1f}%"


# ==============================================================================
# DATABASE INTEGRATION TESTS
# ==============================================================================

def test_database_table_exists():
    """Test that database classification table exists"""
    if not DB_FILE.exists():
        pytest.skip("Database file does not exist")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='entity_classifications'
    """)

    result = cursor.fetchone()
    conn.close()

    assert result is not None, "entity_classifications table not found"


def test_database_classifications_count():
    """Test that database has reasonable number of classifications"""
    if not DB_FILE.exists():
        pytest.skip("Database file does not exist")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM entity_classifications")
        db_count = cursor.fetchone()[0]

        # Should have at least some classifications
        assert db_count > 0, "No classifications in database"

        # Load JSON to compare
        with open(CLASSIFICATIONS_FILE) as f:
            data = json.load(f)
        json_count = len(data["classifications"])

        # Database should have similar count to JSON (allow 10% variance)
        variance = abs(db_count - json_count) / json_count if json_count > 0 else 0
        assert variance < 0.1, \
            f"Database/JSON count mismatch: DB={db_count}, JSON={json_count}"

    finally:
        conn.close()


# ==============================================================================
# QUALITY TESTS
# ==============================================================================

def test_justification_not_empty():
    """Test that justification/reasoning fields are not empty"""
    with open(CLASSIFICATIONS_FILE) as f:
        data = json.load(f)

    # Detect reasoning field
    if data["classifications"]:
        first_classification = next(iter(data["classifications"].values()))
        reasoning_field = "reasoning" if "reasoning" in first_classification else "justification"

        empty = []
        for entity_id, classification in data["classifications"].items():
            reasoning = classification.get(reasoning_field, "").strip()
            if not reasoning or reasoning == "[DRY RUN]":
                empty.append(entity_id)

        # Allow up to 5% empty (for failed classifications)
        empty_pct = (len(empty) / len(data["classifications"])) * 100 if data["classifications"] else 0
        assert empty_pct < 5, \
            f"Too many empty reasonings: {empty_pct:.1f}%"


def test_classification_timestamps():
    """Test that classifications have valid timestamps"""
    with open(CLASSIFICATIONS_FILE) as f:
        data = json.load(f)

    # Check metadata timestamp
    assert "generated" in data["metadata"], "Missing generation timestamp"

    # Try parsing timestamp
    from datetime import datetime
    try:
        datetime.fromisoformat(data["metadata"]["generated"].replace("Z", "+00:00"))
    except ValueError:
        pytest.fail("Invalid metadata timestamp format")


# ==============================================================================
# STATISTICAL VALIDATION
# ==============================================================================

def test_category_distribution():
    """Test that category distribution is reasonable"""
    with open(CLASSIFICATIONS_FILE) as f:
        data = json.load(f)

    # Count categories
    category_counts = {}
    for classification in data["classifications"].values():
        # Detect category field
        category = classification.get("primary_category") or classification.get("primary_role")
        category_counts[category] = category_counts.get(category, 0) + 1

    # No single category should dominate (>70%)
    total = len(data["classifications"])
    for category, count in category_counts.items():
        pct = (count / total) * 100 if total > 0 else 0
        assert pct < 70, \
            f"Category '{category}' dominates: {pct:.1f}%"


def test_tier_breakdown():
    """Test that tier breakdown is present in new schema"""
    with open(CLASSIFICATIONS_FILE) as f:
        data = json.load(f)

    # Only test if using new schema with tiers
    if data["classifications"]:
        first_classification = next(iter(data["classifications"].values()))
        if "tier" not in first_classification:
            pytest.skip("Old schema does not use tiers")

        # Count tiers
        tier_counts = {1: 0, 2: 0, 3: 0}
        for classification in data["classifications"].values():
            tier = classification.get("tier", 3)
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

        # Each tier should have some classifications
        assert tier_counts[1] > 0 or tier_counts[2] > 0 or tier_counts[3] > 0, \
            "No classifications in any tier"


# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================

if __name__ == "__main__":
    # Run pytest
    sys.exit(pytest.main([__file__, "-v", "-s"]))
