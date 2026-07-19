"""Presentation layer for the GitHub Trending Repositories CLI.

Pure functions only: takes normalized repository data in, returns
display-ready strings out. No I/O, no printing — cli.py owns actually
writing these strings to stdout.
"""

HEADER_SEPARATOR_WIDTH = 52
DESCRIPTION_MAX_LENGTH = 100
NO_DESCRIPTION_PLACEHOLDER = "No description provided"
UNKNOWN_LANGUAGE_PLACEHOLDER = "Unknown"
NO_RESULTS_MESSAGE = "No trending repositories found for this period."


def _truncate_description(text: str, max_length: int = DESCRIPTION_MAX_LENGTH) -> str:
    """Shorten an overly long description with a trailing ellipsis.

    Args:
        text: The raw description text.
        max_length: Maximum number of characters before truncating.

    Returns:
        The original text if it fits within max_length, otherwise a
        truncated version ending in "...".
    """
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


def format_single_repository(repo: dict, rank: int) -> str:
    """Format one repository entry as a display-ready text block.

    Args:
        repo: A normalized repository dict (name, description, stars,
            language, url).
        rank: The repository's 1-based position in the results.

    Returns:
        A multi-line string: title line, description line, URL line.
    """
    description = repo.get("description") or NO_DESCRIPTION_PLACEHOLDER
    language = repo.get("language") or UNKNOWN_LANGUAGE_PLACEHOLDER
    stars = repo.get("stars", 0)
    stars_formatted = f"{stars:,}"
    truncated_description = _truncate_description(description)

    title_line = f"{rank}. {repo.get('name', 'unknown/unknown')} \u2605 {stars_formatted} [{language}]"
    description_line = f"   {truncated_description}"
    url_line = f"   {repo.get('url', '')}"

    return "\n".join([title_line, description_line, url_line])


def format_repository_list(repos: list, duration: str) -> str:
    """Produce the full block of text to print for a list of repositories.

    Args:
        repos: A list of normalized repository dicts, already sorted and
            limited by the caller.
        duration: The duration keyword used for the query (e.g. "week"),
            used to build a self-describing header.

    Returns:
        The complete multi-line string ready to print to stdout. If repos
        is empty, returns a header plus a single clear "no results"
        sentence rather than an empty block.
    """
    header = f"Trending Repositories (last {duration})"
    separator = "-" * HEADER_SEPARATOR_WIDTH

    if not repos:
        return "\n".join([header, separator, NO_RESULTS_MESSAGE])

    entries = [
        format_single_repository(repo, rank)
        for rank, repo in enumerate(repos, start=1)
    ]

    return "\n".join([header, separator, "\n\n".join(entries)])