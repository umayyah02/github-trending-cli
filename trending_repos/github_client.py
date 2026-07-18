"""GitHub API data access layer for the GitHub Trending Repositories CLI.

This is the only module that performs network I/O. It builds the search
request, sends it, interprets the HTTP response, parses the JSON body,
and normalizes raw GitHub data into the internal repository shape. All
failure modes (network, HTTP status, JSON) are converted into typed
exceptions rooted at TrendingRepoError so the CLI layer never has to
handle raw requests/JSON exceptions directly.
"""

from urllib.parse import urlencode

import requests

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
REQUEST_TIMEOUT_SECONDS = 10
USER_AGENT = "trending-repos-cli"
API_VERSION = "2022-11-28"


# --- Exception hierarchy ----------------------------------------------------
# Rooted at a single base so cli.py can catch TrendingRepoError as a safety
# net while still allowing specific except blocks for tailored messaging.

class TrendingRepoError(Exception):
    """Base exception for all application-specific errors."""


class ValidationError(TrendingRepoError):
    """Raised when user-supplied CLI arguments fail validation.

    Raised by cli.py, before any network call is made. Defined here
    alongside the rest of the hierarchy so every module that needs the
    exception tree imports it from one place.
    """


class NetworkError(TrendingRepoError):
    """Raised when a connection, DNS, or timeout failure prevents the
    request from completing."""


class RateLimitError(TrendingRepoError):
    """Raised when the GitHub API rejects the request due to rate
    limiting (HTTP 403)."""


class ApiRequestError(TrendingRepoError):
    """Raised for non-2xx GitHub API responses other than rate limiting
    (e.g. 422, 5xx)."""


class ResponseParsingError(TrendingRepoError):
    """Raised when the response body is not valid JSON or does not match
    the expected shape."""


# --- Request construction ---------------------------------------------------

def build_search_url(date_cutoff: str, limit: int) -> str:
    """Construct the full GitHub Search API URL for trending repositories.

    Args:
        date_cutoff: ISO 8601 date string; only repos created after this
            date are included.
        limit: Desired number of results. Used to set per_page, capped at
            the GitHub API's maximum of 100 per page.

    Returns:
        The full request URL, including query parameters.
    """
    per_page = min(limit, 100)
    params = {
        "q": f"created:>{date_cutoff}",
        "sort": "stars",
        "order": "desc",
        "per_page": per_page,
    }
    return f"{GITHUB_SEARCH_URL}?{urlencode(params)}"


# --- Response handling -------------------------------------------------------

def _normalize_repo(raw_item: dict) -> dict:
    """Convert a raw GitHub API repository item into the internal shape.

    Every field is read defensively with an explicit default, since the
    GitHub API may return null for description/language.

    Args:
        raw_item: A single item from the response's "items" list.

    Returns:
        A dict with keys: name, description, stars, language, url.
    """
    return {
        "name": raw_item.get("full_name", "unknown/unknown"),
        "description": raw_item.get("description"),
        "stars": raw_item.get("stargazers_count", 0),
        "language": raw_item.get("language"),
        "url": raw_item.get("html_url", ""),
    }


def _handle_response_errors(response: "requests.Response") -> None:
    """Inspect an HTTP response and raise a typed exception on failure.

    Args:
        response: The requests.Response object returned by the API call.

    Raises:
        RateLimitError: If the response is a 403 caused by rate limiting.
        ApiRequestError: For any other non-2xx status code.
    """
    if response.status_code == 200:
        return

    if response.status_code == 403:
        reset_header = response.headers.get("X-RateLimit-Reset")
        message = "GitHub API rate limit exceeded."
        if reset_header:
            message += f" Limit resets at Unix timestamp {reset_header}."
        raise RateLimitError(message)

    if response.status_code == 422:
        raise ApiRequestError(
            "GitHub API rejected the search query as invalid (HTTP 422). "
            "This indicates a bug in query construction, not bad user input."
        )

    if 500 <= response.status_code < 600:
        raise ApiRequestError(
            f"GitHub API server error (HTTP {response.status_code}). "
            "Please try again later."
        )

    raise ApiRequestError(
        f"GitHub API request failed with unexpected status "
        f"{response.status_code}."
    )


# --- Public entry point -------------------------------------------------------

def fetch_trending_repositories(date_cutoff: str, limit: int) -> list:
    """Fetch trending repositories from the GitHub Search API.

    Sends the HTTP request, handles the response status, parses the JSON
    body, and returns normalized repository records.

    Args:
        date_cutoff: ISO 8601 date string used as the creation-date filter.
        limit: Desired number of results.

    Returns:
        A list of normalized repository dicts (see _normalize_repo).

    Raises:
        NetworkError: If the request fails due to connection or timeout
            issues.
        RateLimitError: If GitHub responds with a rate-limit error.
        ApiRequestError: If GitHub responds with any other error status.
        ResponseParsingError: If the response body isn't valid JSON or is
            missing the expected "items" key.
    """
    url = build_search_url(date_cutoff, limit)
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": API_VERSION,
    }

    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.exceptions.RequestException as exc:
        raise NetworkError(
            f"Network error while contacting GitHub API: {exc}"
        ) from exc

    _handle_response_errors(response)

    try:
        payload = response.json()
        items = payload["items"]
    except (ValueError, KeyError, TypeError) as exc:
        raise ResponseParsingError(
            f"Unexpected response format from GitHub API: {exc}"
        ) from exc

    return [_normalize_repo(item) for item in items[:limit]]