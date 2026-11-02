"""Daylight saving state and UTC session bounds for the European venues."""
from datetime import date, datetime, timezone

import pytest

from aion_lithuanian_market_calendar import is_daylight_saving, is_open, session_bounds_utc, venues


@pytest.mark.parametrize(
    "day,expected",
    [
        (date(2026, 3, 27), False),  # Friday before the last Sunday of March
        (date(2026, 3, 30), True),   # Monday after it
        (date(2026, 10, 23), True),  # Friday before the last Sunday of October
        (date(2026, 10, 26), False), # Monday after it
    ],
)
@pytest.mark.parametrize("venue", [v.mic for v in venues()])
def test_state_changes_on_the_eu_dates_for_every_venue(venue, day, expected):
    assert is_daylight_saving(day, venue) is expected


def test_utc_bounds_shift_while_local_bounds_do_not():
    assert session_bounds_utc(date(2026, 3, 27), "XVIL") == (
        datetime(2026, 3, 27, 8, 0, tzinfo=timezone.utc),
        datetime(2026, 3, 27, 13, 55, tzinfo=timezone.utc),
    )
    assert session_bounds_utc(date(2026, 3, 30), "XVIL") == (
        datetime(2026, 3, 30, 7, 0, tzinfo=timezone.utc),
        datetime(2026, 3, 30, 12, 55, tzinfo=timezone.utc),
    )


def test_utc_bounds_agree_with_is_open_on_both_sides_of_the_change():
    for day in (date(2026, 10, 23), date(2026, 10, 26)):
        opens, closes = session_bounds_utc(day, "XETR")
        assert is_open(opens, "XETR") and is_open(closes, "XETR")


def test_closed_day_has_no_bounds():
    assert session_bounds_utc(date(2026, 3, 28), "XVIL") is None


def test_unknown_venue_raises():
    with pytest.raises(ValueError):
        is_daylight_saving(date(2026, 7, 1), "NOPE")
