"""
tests/test_url_validation.py — Tests for GitHub URL validation

Run with: pytest tests/test_url_validation.py -v
"""

import pytest
from pydantic import ValidationError
from models.schemas import AnalyzeRequest


def test_valid_github_urls():
    """Valid GitHub URLs should be accepted."""
    valid_urls = [
        "https://github.com/tiangolo/fastapi",
        "https://github.com/facebook/react",
        "https://github.com/owner/my-cool-repo",
        "https://github.com/owner/repo/",  # trailing slash is normalized
    ]
    for url in valid_urls:
        request = AnalyzeRequest(url=url)
        assert "github.com" in request.url


def test_invalid_github_urls():
    """Invalid URLs should raise validation errors."""
    invalid_urls = [
        "https://gitlab.com/owner/repo",    # not GitHub
        "not-a-url",                        # not a URL at all
        "https://github.com/just-owner",    # missing repo
        "https://github.com/",              # missing owner/repo
        "http://notgithub.com/a/b",         # wrong domain
    ]
    for url in invalid_urls:
        with pytest.raises(ValidationError):
            AnalyzeRequest(url=url)


def test_url_normalization():
    """Trailing slash should be removed."""
    request = AnalyzeRequest(url="https://github.com/owner/repo/")
    assert not request.url.endswith("/")
