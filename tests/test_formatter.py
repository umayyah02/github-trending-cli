"""Unit tests for trending_repos.formatter.

Pure string-in/string-out logic — no mocking, no I/O required.
"""

from trending_repos.formatter import (
    NO_RESULTS_MESSAGE,
    _truncate_description,
    format_repository_list,
    format_single_repository,
)


# --- _truncate_description ---------------------------------------------------

def test_truncate_description_short_text_unchanged():
    text = "A short description."
    assert _truncate_description(text) == text


def test_truncate_description_long_text_gets_ellipsis():
    text = "x" * 150
    result = _truncate_description(text, max_length=100)
    assert result.endswith("...")
    assert len(result) == 103  # 100 chars + "..."


def test_truncate_description_exact_max_length_unchanged():
    text = "x" * 100
    assert _truncate_description(text, max_length=100) == text


# --- format_single_repository -------------------------------------------------

def test_format_single_repository_full_data():
    repo = {
        "name": "torvalds/linux",
        "description": "Linux kernel source tree",
        "stars": 1204,
        "language": "C",
        "url": "https://github.com/torvalds/linux",
    }
    result = format_single_repository(repo, rank=1)
    assert "1. torvalds/linux" in result
    assert "1,204" in result
    assert "[C]" in result
    assert "Linux kernel source tree" in result
    assert "https://github.com/torvalds/linux" in result


def test_format_single_repository_missing_description_uses_placeholder():
    repo = {
        "name": "someuser/somerepo",
        "description": None,
        "stars": 5,
        "language": "Python",
        "url": "https://github.com/someuser/somerepo",
    }
    result = format_single_repository(repo, rank=2)
    assert "No description provided" in result


def test_format_single_repository_missing_language_uses_placeholder():
    repo = {
        "name": "someuser/somerepo",
        "description": "Some description",
        "stars": 5,
        "language": None,
        "url": "https://github.com/someuser/somerepo",
    }
    result = format_single_repository(repo, rank=1)
    assert "[Unknown]" in result


def test_format_single_repository_large_star_count_has_thousands_separator():
    repo = {
        "name": "user/repo",
        "description": "desc",
        "stars": 123456,
        "language": "Go",
        "url": "https://github.com/user/repo",
    }
    result = format_single_repository(repo, rank=1)
    assert "123,456" in result


def test_format_single_repository_long_description_is_truncated():
    repo = {
        "name": "user/repo",
        "description": "x" * 150,
        "stars": 1,
        "language": "Go",
        "url": "https://github.com/user/repo",
    }
    result = format_single_repository(repo, rank=1)
    assert "..." in result
    assert "x" * 150 not in result


# --- format_repository_list -----------------------------------------------------

def test_format_repository_list_includes_header_with_duration():
    result = format_repository_list([], "month")
    assert "Trending Repositories (last month)" in result


def test_format_repository_list_empty_shows_no_results_message():
    result = format_repository_list([], "week")
    assert NO_RESULTS_MESSAGE in result


def test_format_repository_list_multiple_repos_are_ranked_in_order():
    repos = [
        {"name": "a/one", "description": "d", "stars": 10, "language": "Go", "url": "u1"},
        {"name": "b/two", "description": "d", "stars": 5, "language": "Go", "url": "u2"},
    ]
    result = format_repository_list(repos, "day")
    assert "1. a/one" in result
    assert "2. b/two" in result


def test_format_repository_list_returns_single_string():
    repos = [
        {"name": "a/one", "description": "d", "stars": 10, "language": "Go", "url": "u1"},
    ]
    result = format_repository_list(repos, "day")
    assert isinstance(result, str)