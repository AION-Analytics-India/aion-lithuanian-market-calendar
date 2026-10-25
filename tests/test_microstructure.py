"""TARGET settlement days and intraday phases.

The TARGET dates for 2026 and 2027 are the ones the ECB publishes on its own
holiday page (closing days marked there): they are the expected values here so a
computus or rule mistake shows up as a wrong date, not a passing test.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

import aion_lithuanian_market_calendar as lt
from aion_lithuanian_market_calendar import store
from aion_lithuanian_market_calendar import microstructure as ms

VILNIUS = ZoneInfo("Europe/Vilnius")


@pytest.fixture(autouse=True)
def _isolated(monkeypatch, tmp_path):
    """Offline, with an empty cache, so only the bundled data answers."""
    monkeypatch.setenv("AION_LT_CALENDAR_OFFLINE", "1")
    monkeypatch.setattr(store, "CACHE_DIR", tmp_path / "cache")
    store._state.update({"loaded": False, "data": {}, "source": "none", "warned": set()})
    yield
    store._state.update({"loaded": False, "data": {}, "source": "none", "warned": set()})


def test_new_functions_are_exported_from_the_package_root():
    for name in ("is_settlement_day", "next_settlement_day", "target_closing_days",
                 "get_market_phase", "phase_name"):
        assert name in lt.__all__ and callable(getattr(lt, name))


# --- TARGET -----------------------------------------------------------------------

@pytest.mark.parametrize(
    "year, expected",
    [
        (2026, ["2026-01-01", "2026-04-03", "2026-04-06", "2026-05-01", "2026-12-25", "2026-12-26"]),
        (2027, ["2027-01-01", "2027-03-26", "2027-03-29", "2027-05-01", "2027-12-25", "2027-12-26"]),
    ],
)
def test_target_closing_days_match_the_ecb_calendar(year, expected):
    assert [d.date.isoformat() for d in ms.target_closing_days(year)] == expected


def test_closing_days_carry_both_languages():
    names = {d.name_en: d.name_lt for d in ms.target_closing_days(2026)}
    assert names["Good Friday"] == "Didysis penktadienis"
    assert names["Easter Monday"] == "Velykų antroji diena"
    assert all(d.name_en and d.name_lt for d in ms.target_closing_days(2026))


def test_good_friday_is_a_business_day_but_not_a_settlement_day():
    # Not a Lithuanian public holiday; TARGET is closed.
    assert lt.is_business_day("2026-04-03") is True
    assert ms.is_settlement_day("2026-04-03") is False


def test_lithuanian_holiday_still_settles():
    # 16 February: offices shut, TARGET open.
    assert lt.is_business_day("2026-02-16") is False
    assert ms.is_settlement_day("2026-02-16") is True


def test_weekend_does_not_settle():
    assert ms.is_settlement_day(date(2026, 10, 24)) is False
    assert ms.is_settlement_day(datetime(2026, 10, 25, 12, 0)) is False


def test_next_settlement_day_skips_the_easter_closure():
    assert ms.next_settlement_day("2026-04-02") == date(2026, 4, 7)


def test_rule_does_not_reach_before_2002():
    with pytest.raises(ValueError, match="from 2002"):
        ms.is_settlement_day("2001-06-01")


# --- phases -------------------------------------------------------------------------

@pytest.mark.parametrize(
    "clock, expected",
    [((9, 59), ms.CLOSED), ((10, 0), ms.CONTINUOUS), ((15, 54), ms.CONTINUOUS), ((15, 55), ms.CLOSED)],
)
def test_vilnius_phase_on_an_ordinary_day(clock, expected):
    at = datetime(2026, 10, 26, *clock, tzinfo=VILNIUS)
    assert ms.get_market_phase(at, "XVIL") == expected


def test_same_instant_same_phase_in_any_timezone():
    at = datetime(2026, 10, 26, 12, 0, tzinfo=VILNIUS)
    assert ms.get_market_phase(at.astimezone(timezone.utc)) == ms.get_market_phase(at) == ms.CONTINUOUS


def test_exchange_holiday_is_closed():
    assert ms.get_market_phase(datetime(2026, 12, 24, 12, 0, tzinfo=VILNIUS)) == ms.CLOSED


def test_17_november_2026_trades():
    # A test entry once published this as a Nasdaq Baltic closure. It is not one.
    for venue in ("XVIL", "XRIS", "XTAL"):
        at = datetime(2026, 11, 17, 12, 0, tzinfo=ZoneInfo(lt.resolve(venue).timezone))
        assert ms.get_market_phase(at, venue) == ms.CONTINUOUS


def test_naive_datetime_is_refused():
    with pytest.raises(ValueError, match="naive"):
        ms.get_market_phase(datetime(2026, 10, 26, 12, 0))


def test_phase_names_in_both_languages():
    assert ms.phase_name(ms.CONTINUOUS, "en") == "Continuous trading"
    assert ms.phase_name(ms.CONTINUOUS, "lt") == "Nepertraukiama prekyba"
    assert ms.phase_name(ms.CLOSED, "lt") == "Prekyba nevyksta"
    with pytest.raises(ValueError):
        ms.phase_name("PRE_OPEN", "en")
