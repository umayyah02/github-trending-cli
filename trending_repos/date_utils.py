"""Pure date/duration logic for the GitHub Trending Repositories CLI.

No I/O, no printing, no argument parsing — fully unit-testable in isolation.
"""

from datetime import datetime, timedelta, timezone

_DAYS_BY_DURATION = {
    "day": 1,
    "week": 7,
    "month": 30,
    "year": 365,
}


def _days_for_duration(duration: str) -> int:
    """Map a duration keyword to a numeric day offset.

    Args:
        duration: One of "day", "week", "month", "year".

    Returns:
        The number of days corresponding to the duration keyword.

    Raises:
        ValueError: If duration is not one of the supported keywords.
    """
    if duration not in _DAYS_BY_DURATION:
        raise ValueError(
            f"Unsupported duration: {duration!r}. "
            f"Expected one of {sorted(_DAYS_BY_DURATION)}."
        )
    return _DAYS_BY_DURATION[duration]


def duration_to_date(duration: str) -> str:
    """Convert a duration keyword into an ISO 8601 date cutoff string.

    The cutoff is computed as "now" in UTC minus the number of days for
    the given duration, so date math is consistent regardless of the
    local system timezone.

    Args:
        duration: One of "day", "week", "month", "year".

    Returns:
        An ISO 8601 date string, e.g. "2026-07-11".

    Raises:
        ValueError: If duration is not one of the supported keywords.
    """
    days = _days_for_duration(duration)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return cutoff.strftime("%Y-%m-%d")