"""
tests/test_confidence_scorer.py — Tests for confidence scoring

Run with: pytest tests/test_confidence_scorer.py -v
"""

import pytest
from confidence.scorer import calculate_confidence


def make_chunk(score: float) -> dict:
    """Helper to create a fake chunk with a given similarity score."""
    return {
        "file_path": "src/test.py",
        "start_line": 1,
        "end_line": 10,
        "code": "def test(): pass",
        "similarity_score": score,
    }


class TestNoChunks:
    def test_empty_chunks_gives_zero_confidence(self):
        result = calculate_confidence([])
        assert result.score == 0.0
        assert not result.is_sufficient


class TestLowConfidence:
    def test_very_low_similarity_is_insufficient(self):
        chunks = [make_chunk(0.1), make_chunk(0.05)]
        result = calculate_confidence(chunks)
        assert not result.is_sufficient

    def test_single_low_match(self):
        result = calculate_confidence([make_chunk(0.15)])
        assert not result.is_sufficient


class TestHighConfidence:
    def test_exact_match_gives_high_confidence(self):
        chunks = [make_chunk(1.0), make_chunk(0.9), make_chunk(0.85)]
        result = calculate_confidence(chunks)
        assert result.is_sufficient
        assert result.score > 0.5

    def test_multiple_good_matches_are_sufficient(self):
        chunks = [make_chunk(0.7), make_chunk(0.65), make_chunk(0.6),
                  make_chunk(0.55), make_chunk(0.5)]
        result = calculate_confidence(chunks)
        assert result.is_sufficient


class TestScoreFields:
    def test_all_fields_present(self):
        chunks = [make_chunk(0.8)]
        result = calculate_confidence(chunks)
        assert hasattr(result, 'score')
        assert hasattr(result, 'is_sufficient')
        assert hasattr(result, 'top_similarity')
        assert hasattr(result, 'relevant_count')
        assert hasattr(result, 'reasoning')

    def test_score_in_valid_range(self):
        for score in [0.0, 0.3, 0.5, 0.8, 1.0]:
            result = calculate_confidence([make_chunk(score)])
            assert 0.0 <= result.score <= 1.0
