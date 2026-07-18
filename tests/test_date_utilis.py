"""Unit tests for trending_repos.date_utils.

These tests require no network access and no mocking — date_utils is
pure and self-contained.
"""

from datetime import datetime, timedelta, timezone

import pytest

from trending_repos.date_utils import _days_for_duration, duration_to_date


# --- _days_for_duration ---------------------------------------------------

def test_days_for_duration_day():
    assert _days_for_duration("day") == 1


def test_days_for_duration_week():
    assert _days_for_duration("week") == 7


def test_days_for_duration_month():
    assert _days_for_duration("month") == 30


def test_days_for_duration_year():
    assert _days_for_duration("year") == 365


def test_days_for_duration_invalid_raises_value_error():
    with pytest.raises(ValueError):
        _days_for_duration("fortnight")


# --- duration_to_date ------------------------------------------------------

def test_duration_to_date_returns_iso_format():
    result = duration_to_date("week")
    # Will raise ValueError if the format doesn't match YYYY-MM-DD
    datetime.strptime(result, "%Y-%m-%d")


def test_duration_to_date_week_is_seven_days_before_today():
    expected = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    assert duration_to_date("week") == expected


def test_duration_to_date_day_is_one_day_before_today():
    expected = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    assert duration_to_date("day") == expected


def test_duration_to_date_invalid_duration_raises_value_error():
    with pytest.raises(ValueError):
        duration_to_date("decade")


def test_duration_to_date_uses_utc_not_local_time():
    # Regression guard for the "system clock/timezone irregularities"
    # edge case called out in the PRD (Section 8).
    result = duration_to_date("day")
    utc_expected = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    assert result == utc_expected