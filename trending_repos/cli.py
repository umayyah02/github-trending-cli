"""CLI orchestration layer for the GitHub Trending Repositories CLI.

This is the only module that reads sys.argv or writes to stdout. It owns
argument parsing, validation, pipeline orchestration (date_utils ->
github_client -> formatter), and top-level error handling.
"""

import argparse
import sys

from trending_repos.date_utils import duration_to_date
from trending_repos.formatter import format_repository_list
from trending_repos.github_client import (
    TrendingRepoError,
    ValidationError,
    fetch_trending_repositories,
)

VALID_DURATIONS = ("day", "week", "month", "year")
DEFAULT_DURATION = "week"
DEFAULT_LIMIT = 10


def parse_arguments(argv=None) -> argparse.Namespace:
    """Define and parse --duration and --limit via argparse.

    Args:
        argv: Optional list of argument strings. When None, argparse
            reads from sys.argv itself.

    Returns:
        An argparse.Namespace with `duration` and `limit` attributes.
    """
    parser = argparse.ArgumentParser(
        prog="trending-repos",
        description="Discover trending GitHub repositories from your terminal.",
    )
    parser.add_argument(
        "--duration",
        default=DEFAULT_DURATION,
        help=(
            f"Time window to search: one of {list(VALID_DURATIONS)}. "
            f"Default: {DEFAULT_DURATION}."
        ),
    )
    parser.add_argument(
        "--limit",
        default=DEFAULT_LIMIT,
        help=f"Number of repositories to display. Default: {DEFAULT_LIMIT}.",
    )
    return parser.parse_args(argv)


def validate_arguments(args: argparse.Namespace) -> None:
    """Confirm duration is supported and limit is a valid positive integer.

    Runs before any network call, per the TDD's "fail fast" principle.
    Normalizes args.duration to lowercase and args.limit to int in place.

    Args:
        args: The parsed argparse.Namespace.

    Raises:
        ValidationError: If duration is not one of the supported
            keywords, or limit does not parse as a positive integer.
    """
    duration = str(args.duration).lower()
    if duration not in VALID_DURATIONS:
        raise ValidationError(
            f"Invalid --duration '{args.duration}'. "
            f"Expected one of {list(VALID_DURATIONS)}."
        )
    args.duration = duration

    try:
        limit = int(args.limit)
    except (TypeError, ValueError):
        raise ValidationError(
            f"Invalid --limit '{args.limit}'. Expected a positive integer."
        )

    if limit < 1:
        raise ValidationError(
            f"Invalid --limit '{args.limit}'. Must be a positive integer (>= 1)."
        )

    args.limit = limit
    # NOTE: behavior when --limit exceeds a recommended maximum (clamp vs.
    # reject) is an open design decision per the PRD appendix — deferred
    # to Milestone 6, not yet implemented here.


def main() -> int:
    """Top-level orchestration: parse -> validate -> fetch -> format -> print.

    The only broad exception handler in the application lives here, per
    the TDD's error-handling strategy: every other module raises typed
    exceptions rather than swallowing them.

    Returns:
        Process exit code: 0 on success (including zero results),
        1 on any handled TrendingRepoError.
    """
    args = parse_arguments()

    try:
        validate_arguments(args)
        date_cutoff = duration_to_date(args.duration)
        repos = fetch_trending_repositories(date_cutoff, args.limit)
        output = format_repository_list(repos, args.duration)
    except TrendingRepoError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())