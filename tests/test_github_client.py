"""Unit tests for trending_repos.github_client.

No real network calls are made. requests.get is mocked via a small
FakeResponse stand-in so behavior can be tested for every branch in
_handle_response_errors and fetch_trending_repositories.
"""

from unittest.mock import patch

import pytest
import requests

from trending_repos.github_client import (
    ApiRequestError,
    NetworkError,
    RateLimitError,
    ResponseParsingError,
    TrendingRepoError,
    _handle_response_errors,
    _normalize_repo,
    build_search_url,
    fetch_trending_repositories,
)


class FakeResponse:
    """Minimal stand-in for requests.Response used in tests."""

    def __init__(self, status_code, json_data=None, headers=None, json_error=False):
        self.status_code = status_code
        self._json_data = json_data
        self.headers = headers or {}
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise ValueError("No JSON could be decoded")
        return self._json_data


# --- build_search_url --------------------------------------------------------

def test_build_search_url_contains_expected_params():
    url = build_search_url("2026-07-11", 20)
    assert url.startswith("https://api.github.com/search/repositories?")
    assert "q=created%3A%3E2026-07-11" in url
    assert "sort=stars" in url
    assert "order=desc" in url
    assert "per_page=20" in url


def test_build_search_url_caps_per_page_at_100():
    url = build_search_url("2026-07-11", 500)
    assert "per_page=100" in url


# --- _normalize_repo ----------------------------------------------------------

def test_normalize_repo_full_data():
    raw = {
        "full_name": "torvalds/linux",
        "description": "Linux kernel source tree",
        "stargazers_count": 1204,
        "language": "C",
        "html_url": "https://github.com/torvalds/linux",
    }
    result = _normalize_repo(raw)
    assert result == {
        "name": "torvalds/linux",
        "description": "Linux kernel source tree",
        "stars": 1204,
        "language": "C",
        "url": "https://github.com/torvalds/linux",
    }


def test_normalize_repo_missing_description_and_language():
    raw = {
        "full_name": "someuser/somerepo",
        "description": None,
        "stargazers_count": 5,
        "language": None,
        "html_url": "https://github.com/someuser/somerepo",
    }
    result = _normalize_repo(raw)
    assert result["description"] is None
    assert result["language"] is None


def test_normalize_repo_missing_keys_entirely_uses_defaults():
    result = _normalize_repo({})
    assert result["name"] == "unknown/unknown"
    assert result["stars"] == 0
    assert result["url"] == ""


# --- _handle_response_errors ---------------------------------------------------

def test_handle_response_errors_200_returns_none():
    assert _handle_response_errors(FakeResponse(200)) is None


def test_handle_response_errors_403_raises_rate_limit_error():
    with pytest.raises(RateLimitError):
        _handle_response_errors(FakeResponse(403))


def test_handle_response_errors_403_includes_reset_time_in_message():
    response = FakeResponse(403, headers={"X-RateLimit-Reset": "1234567890"})
    with pytest.raises(RateLimitError, match="1234567890"):
        _handle_response_errors(response)


def test_handle_response_errors_422_raises_api_request_error():
    with pytest.raises(ApiRequestError):
        _handle_response_errors(FakeResponse(422))


def test_handle_response_errors_500_raises_api_request_error():
    with pytest.raises(ApiRequestError):
        _handle_response_errors(FakeResponse(503))


def test_handle_response_errors_unexpected_status_raises_api_request_error():
    with pytest.raises(ApiRequestError):
        _handle_response_errors(FakeResponse(418))


# --- fetch_trending_repositories -----------------------------------------------

@patch("trending_repos.github_client.requests.get")
def test_fetch_trending_repositories_success(mock_get):
    mock_get.return_value = FakeResponse(
        200,
        json_data={
            "items": [
                {
                    "full_name": "torvalds/linux",
                    "description": "Linux kernel source tree",
                    "stargazers_count": 1204,
                    "language": "C",
                    "html_url": "https://github.com/torvalds/linux",
                }
            ]
        },
    )
    result = fetch_trending_repositories("2026-07-11", 10)
    assert len(result) == 1
    assert result[0]["name"] == "torvalds/linux"


@patch("trending_repos.github_client.requests.get")
def test_fetch_trending_repositories_respects_limit_slicing(mock_get):
    items = [
        {"full_name": f"user/repo{i}", "stargazers_count": i}
        for i in range(5)
    ]
    mock_get.return_value = FakeResponse(200, json_data={"items": items})
    result = fetch_trending_repositories("2026-07-11", 3)
    assert len(result) == 3


@patch("trending_repos.github_client.requests.get")
def test_fetch_trending_repositories_network_error_raises_network_error(mock_get):
    mock_get.side_effect = requests.exceptions.ConnectionError("DNS failure")
    with pytest.raises(NetworkError):
        fetch_trending_repositories("2026-07-11", 10)


@patch("trending_repos.github_client.requests.get")
def test_fetch_trending_repositories_timeout_raises_network_error(mock_get):
    mock_get.side_effect = requests.exceptions.Timeout("timed out")
    with pytest.raises(NetworkError):
        fetch_trending_repositories("2026-07-11", 10)


@patch("trending_repos.github_client.requests.get")
def test_fetch_trending_repositories_rate_limit_propagates(mock_get):
    mock_get.return_value = FakeResponse(403)
    with pytest.raises(RateLimitError):
        fetch_trending_repositories("2026-07-11", 10)


@patch("trending_repos.github_client.requests.get")
def test_fetch_trending_repositories_malformed_json_raises_parsing_error(mock_get):
    mock_get.return_value = FakeResponse(200, json_error=True)
    with pytest.raises(ResponseParsingError):
        fetch_trending_repositories("2026-07-11", 10)


@patch("trending_repos.github_client.requests.get")
def test_fetch_trending_repositories_missing_items_key_raises_parsing_error(mock_get):
    mock_get.return_value = FakeResponse(200, json_data={"unexpected": "shape"})
    with pytest.raises(ResponseParsingError):
        fetch_trending_repositories("2026-07-11", 10)


def test_all_exceptions_inherit_from_trending_repo_error():
    for exc_cls in (NetworkError, RateLimitError, ApiRequestError, ResponseParsingError):
        assert issubclass(exc_cls, TrendingRepoError)