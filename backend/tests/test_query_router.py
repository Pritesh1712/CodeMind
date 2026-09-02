"""
tests/test_query_router.py — Tests for query type classification

Run with: pytest tests/test_query_router.py -v
"""

import pytest
from routing.query_router import classify_query, QueryType


class TestExactReferenceClassification:
    """Queries that should be classified as EXACT_REFERENCE."""

    def test_where_is_used(self):
        result = classify_query("Where is authenticate() used?")
        assert result.query_type == QueryType.EXACT_REFERENCE

    def test_find_all_references(self):
        result = classify_query("Find all references to UserService")
        assert result.query_type == QueryType.EXACT_REFERENCE

    def test_which_files(self):
        result = classify_query("Which files import axios?")
        assert result.query_type == QueryType.EXACT_REFERENCE

    def test_where_is_defined(self):
        result = classify_query("Where is the Database class defined?")
        assert result.query_type == QueryType.EXACT_REFERENCE

    def test_usages_of(self):
        result = classify_query("Show me usages of the login function")
        assert result.query_type == QueryType.EXACT_REFERENCE

    def test_called_from(self):
        result = classify_query("Where is processPayment called from?")
        assert result.query_type == QueryType.EXACT_REFERENCE

    def test_list_all(self):
        result = classify_query("List all functions that call the API")
        assert result.query_type == QueryType.EXACT_REFERENCE


class TestConceptualClassification:
    """Queries that should be classified as CONCEPTUAL."""

    def test_how_does_auth_work(self):
        result = classify_query("How does authentication work?")
        assert result.query_type == QueryType.CONCEPTUAL

    def test_explain_architecture(self):
        result = classify_query("Explain the database architecture")
        assert result.query_type == QueryType.CONCEPTUAL

    def test_what_is(self):
        result = classify_query("What is the main entry point of this app?")
        assert result.query_type == QueryType.CONCEPTUAL

    def test_how_are_errors_handled(self):
        result = classify_query("How are errors handled?")
        assert result.query_type == QueryType.CONCEPTUAL

    def test_describe_pattern(self):
        result = classify_query("Describe the middleware pattern used here")
        assert result.query_type == QueryType.CONCEPTUAL


class TestConfidenceScores:
    def test_confidence_is_valid_range(self):
        result = classify_query("Where is X used?")
        assert 0.0 <= result.confidence <= 1.0

    def test_reasoning_is_non_empty(self):
        result = classify_query("How does this work?")
        assert result.reasoning != ""
