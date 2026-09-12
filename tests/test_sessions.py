"""Session correctness, and the regressions that would have caught the 0.x bug.

Before 1.0.0 ``is_market_open`` compared the caller's wall clock against
10:00-15:55 without converting anything, so the same instant answered differently
depending on which timezone it was expressed in. Every user outside Lithuania got
wrong answers. ``test_same_instant_is_the_same_answer_everywhere`` is the test
that was missing.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from aion_lithuanian_market_calendar import store
from aion_lithuanian_market_calendar.sessions import (
    is_open,
    is_trading_day,
    next_trading_day,
    session_bounds,
    to_venue_time,
)
from aion_lithuanian_market_calendar.venues import VENUES, resolve

VILNIUS = ZoneInfo("Europe/Vilnius")
#: Thursday, an ordinary trading day, midday.
TRADING_NOON = datetime(2026, 9, 10, 12, 0, tzinfo=VILNIUS)


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    """No test touches the network. A suite that depends on a remote host is a
    suite that fails on a plane."""
    monkeypatch.setenv("AION_LT_CALENDAR_OFFLINE", "1")


# --------------------------------------------------------------------------
# The bug
# --------------------------------------------------------------------------
@pytest.mark.parametrize("zone", [
    "Europe/Vilnius", "UTC", "Asia/Kolkata", "America/New_York",
    "Australia/Sydney", "Pacific/Kiritimati",
])
def test_same_instant_is_the_same_answer_everywhere(zone):
    """One moment in time has one answer, however it is written down."""
    assert is_open(TRADING_NOON.astimezone(ZoneInfo(zone))) is True


@pytest.mark.parametrize("zone", ["UTC", "Asia/Kolkata", "America/New_York"])
def test_a_closed_instant_is_closed_everywhere(zone):
    before_open = TRADING_NOON.replace(hour=8)
    assert is_open(before_open.astimezone(ZoneInfo(zone))) is False


def test_naive_datetimes_raise():
    """A naive datetime has no answer; guessing one hides the caller's mistake."""
    with pytest.raises(ValueError, match="naive"):
        is_open(datetime(2026, 9, 10, 12, 0))


def test_the_error_says_what_to_pass_instead():
    with pytest.raises(ValueError) as excinfo:
        to_venue_time(datetime(2026, 9, 10), resolve("XVIL"))
    assert "Europe/Vilnius" in str(excinfo.value)


# --------------------------------------------------------------------------
# Daylight saving
# --------------------------------------------------------------------------
def test_dst_shifts_the_session_in_utc_but_not_locally():
    """10:00 local is 08:00 UTC in winter and 07:00 UTC in summer. Both open."""
    winter = datetime(2026, 1, 15, 10, 0, tzinfo=VILNIUS)
    summer = datetime(2026, 7, 15, 10, 0, tzinfo=VILNIUS)
    assert winter.astimezone(timezone.utc).hour == 8
    assert summer.astimezone(timezone.utc).hour == 7
    assert is_open(winter) is True
    assert is_open(summer) is True


@pytest.mark.parametrize("day", [date(2026, 3, 29), date(2026, 10, 25)])
def test_dst_transition_days_do_not_break(day):
    """The last Sundays of March and October. Both are Sundays, so closed -- but
    the conversion must not raise on a day with a missing or repeated hour."""
    moment = datetime(day.year, day.month, day.day, 12, 0, tzinfo=VILNIUS)
    assert is_open(moment) is False


def test_no_utc_offset_is_hardcoded_anywhere():
    """A written-down offset is wrong twice a year."""
    import pathlib
    src = pathlib.Path(__file__).resolve().parents[1] / "src"
    for path in src.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for bad in ("timedelta(hours=2)", "timedelta(hours=3)", "+02:00", "+03:00"):
            assert bad not in text, f"{path.name} hardcodes an offset: {bad}"


# --------------------------------------------------------------------------
# Boundaries
# --------------------------------------------------------------------------
@pytest.mark.parametrize("hour,minute,expected", [
    (9, 59, False), (10, 0, True), (13, 0, True), (15, 55, True), (15, 56, False),
])
def test_session_boundaries_are_inclusive_at_both_ends(hour, minute, expected):
    assert is_open(TRADING_NOON.replace(hour=hour, minute=minute)) is expected


def test_weekends_are_closed():
    saturday = datetime(2026, 9, 12, 12, 0, tzinfo=VILNIUS)
    assert saturday.weekday() == 5
    assert is_open(saturday) is False
    assert is_open(saturday + timedelta(days=1)) is False


# --------------------------------------------------------------------------
# Exchange holidays are not public holidays
# --------------------------------------------------------------------------
def test_good_friday_closes_the_exchange_but_is_not_a_public_holiday():
    """The case that makes the two lists different, and the reason for the split."""
    good_friday = date(2026, 4, 3)
    assert store.is_exchange_holiday(good_friday) is True
    assert store.is_public_holiday_listed(good_friday) is False
    assert is_trading_day(good_friday) is False


def test_christmas_eve_is_a_full_closure_not_a_half_day():
    """Sv. Kucios is a Lithuanian statutory holiday. An early version of the data
    listed it as a half-day as well; the session logic honoured the closure and
    the half-day sat there looking authoritative."""
    eve = date(2026, 12, 24)
    assert store.is_exchange_holiday(eve) is True
    assert store.half_day_close(eve) is None


def test_new_years_eve_is_a_half_day():
    """A working day with an early close -- which is what a half-day actually is."""
    assert store.half_day_close(date(2026, 12, 31)) == time(12, 30)
    assert is_open(datetime(2026, 12, 31, 11, 0, tzinfo=VILNIUS)) is True
    assert is_open(datetime(2026, 12, 31, 13, 0, tzinfo=VILNIUS)) is False


def test_next_trading_day_steps_over_the_christmas_closure():
    assert next_trading_day(date(2026, 12, 24)) == date(2026, 12, 28)


# --------------------------------------------------------------------------
# Venues
# --------------------------------------------------------------------------
def test_every_venue_has_a_real_iana_zone():
    for venue in VENUES.values():
        ZoneInfo(venue.timezone)          # raises if the zone is not real


def test_every_venue_opens_before_it_closes():
    for venue in VENUES.values():
        assert venue.opens < venue.closes, venue.mic


def test_venues_resolve_by_mic_and_alias_case_insensitively():
    assert resolve("xetra").mic == "XETR"
    assert resolve("Frankfurt").mic == "XETR"
    assert resolve("XVIL").mic == "XVIL"
    assert resolve("nasdaq_vilnius").mic == "XVIL"


def test_an_unknown_venue_names_the_alternatives():
    with pytest.raises(ValueError, match="XVIL"):
        resolve("NOT_A_VENUE")


def test_european_venues_open_simultaneously_in_utc():
    """Europe's exchanges are synchronised in UTC, not in local time.

    Lisbon opens 08:00 WET, Frankfurt 09:00 CET, Vilnius 10:00 EET -- three
    different wall clocks, and every one of them is 07:00 UTC. The local
    difference exactly cancels the zone difference.

    This is the strongest single check on the venue table: mistype one timezone
    -- Europe/London for Lisbon, say -- and that venue falls out of the 07:00
    alignment immediately.
    """
    moment = datetime(2026, 9, 10, 7, 5, tzinfo=timezone.utc)
    for mic in VENUES:
        if mic == "ASEX":
            continue                       # opens 07:15 UTC; see the next test
        assert is_open(moment, venue=mic) is True, f"{mic} should be open at 07:05 UTC"


def test_athens_is_the_exception_that_proves_the_alignment():
    """Athens opens 10:15 EET, a quarter hour later than everyone else in UTC."""
    just_before = datetime(2026, 9, 10, 7, 5, tzinfo=timezone.utc)
    just_after = datetime(2026, 9, 10, 7, 20, tzinfo=timezone.utc)
    assert is_open(just_before, venue="ASEX") is False
    assert is_open(just_after, venue="ASEX") is True
    # while Frankfurt was already trading through both
    assert is_open(just_before, venue="XETR") is True


def test_venues_close_at_different_times_unlike_their_opens():
    """The opens align; the closes do not. Prague shuts at 16:20 CET and
    Frankfurt trades until 17:30, so there is an hour when one is open and the
    other is not -- which only comes out right if each is compared in its own
    zone."""
    moment = datetime(2026, 9, 10, 15, 0, tzinfo=timezone.utc)   # 17:00 CEST
    assert is_open(moment, venue="XETR") is True
    assert is_open(moment, venue="XPRA") is False
