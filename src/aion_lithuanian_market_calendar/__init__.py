"""Lithuanian market, bank and public holiday calendar.

Answers the question every scheduler, payroll run and settlement job needs:
is today a working day in Lithuania, and if not, why not.

    from aion_lithuanian_market_calendar import is_business_day, next_business_day

    is_business_day()                      # today
    is_business_day("2026-12-25")          # False, Christmas Day
    next_business_day("2026-12-24")        # 2026-12-29

Holidays are computed, not tabulated. Every Lithuanian statutory non-working
day is derivable: twelve fixed dates, two from the Gregorian Easter computus,
and two from a first-Sunday-of-month rule. The package is therefore correct for
any year, offline, with no update and no network call.

Names are returned in English and Lithuanian.

Scope: the sixteen statutory non-working days (šventės) of article 123 of the
Labour Code. Lithuania's commemorative and flag days (atmintinos dienos), and
traditional celebrations such as Užgavėnės, are not days off. They never affect
business-day arithmetic; Užgavėnės is exposed separately by `observances()`.

MIT licensed. AION Analytics (India).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Iterable

from . import store
from .holidays import Holiday, Observance, easter_sunday, holiday_on, holidays, observances
from .sessions import (
    is_daylight_saving,
    is_open,
    is_trading_day,
    next_trading_day,
    session_bounds,
    session_bounds_utc,
    to_venue_time,
)
from .venues import VENUES, Venue, resolve, venues
from . import microstructure
from .microstructure import (
    CLOSED,
    CONTINUOUS,
    TargetClosingDay,
    get_market_phase,
    is_settlement_day,
    next_settlement_day,
    phase_name,
    target_closing_days,
)

__all__ = [
    # Settlement (TARGET) and intraday phase. New in 1.1.0.
    "microstructure",
    "CLOSED",
    "CONTINUOUS",
    "TargetClosingDay",
    "get_market_phase",
    "is_settlement_day",
    "next_settlement_day",
    "phase_name",
    "target_closing_days",
    "Holiday",
    "Observance",
    "easter_sunday",
    "holidays",
    "holiday_on",
    "observances",
    "is_public_holiday",
    "is_business_day",
    "is_weekend",
    "next_business_day",
    "previous_business_day",
    "business_days_between",
    "is_market_open",
    "holidays_between",
    # Sessions, timezone-correct. New in 1.0.0.
    "is_open",
    "is_trading_day",
    "next_trading_day",
    "is_daylight_saving",
    "session_bounds",
    "session_bounds_utc",
    "to_venue_time",
    # European venues, rules only.
    "Venue",
    "VENUES",
    "venues",
    "resolve",
    # Holiday data, its manifest and its refresh.
    "store",
    "data_status",
    "refresh_data",
    "__version__",
]

__version__ = "1.2.1"

#: Nasdaq Vilnius continuous trading, local time. Kept deliberately simple:
#: session times are the one part of an exchange calendar that does change by
#: announcement, so callers who need intraday precision should confirm against
#: the venue rather than trust a bundled constant.
_MARKET_OPEN = (10, 0)
_MARKET_CLOSE = (15, 55)


def _as_date(value: date | datetime | str | None) -> date:
    if value is None:
        return date.today()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).strip()[:10])


def is_weekend(when: date | datetime | str | None = None) -> bool:
    """Saturday or Sunday."""
    return _as_date(when).weekday() >= 5


def is_public_holiday(when: date | datetime | str | None = None) -> bool:
    """True if the date is a Lithuanian statutory non-working day."""
    return holiday_on(_as_date(when)) is not None


def is_business_day(when: date | datetime | str | None = None) -> bool:
    """True if banks and offices work that day.

    Lithuania does not move a holiday that falls on a weekend to the following
    Monday, so there is no substitute-day rule to apply.
    """
    day = _as_date(when)
    return not is_weekend(day) and holiday_on(day) is None


def next_business_day(after: date | datetime | str | None = None) -> date:
    """The next working day strictly after the given date."""
    day = _as_date(after) + timedelta(days=1)
    while not is_business_day(day):
        day += timedelta(days=1)
    return day


def previous_business_day(before: date | datetime | str | None = None) -> date:
    """The last working day strictly before the given date."""
    day = _as_date(before) - timedelta(days=1)
    while not is_business_day(day):
        day -= timedelta(days=1)
    return day


def business_days_between(start: date | datetime | str, end: date | datetime | str) -> int:
    """Count working days in the half-open interval [start, end)."""
    a, b = _as_date(start), _as_date(end)
    if a > b:
        a, b = b, a
    total, day = 0, a
    while day < b:
        if is_business_day(day):
            total += 1
        day += timedelta(days=1)
    return total


def is_market_open(at: date | datetime | str | None = None, *, market: str = "XVIL") -> bool:
    """True during continuous trading at the venue.

    .. deprecated:: 1.0.0
       Use :func:`is_open`, which takes the venue as ``venue=`` and requires a
       timezone-aware datetime.

    **This function was wrong before 1.0.0** and the fix changes its answers. It
    used to compare the caller's wall clock against 10:00-15:55 without
    converting anything, so the same instant returned different results depending
    on which timezone it was expressed in — correct in Lithuania, wrong
    everywhere else. It now converts to the venue's own zone first.

    A naive datetime is still accepted here, and interpreted as venue-local,
    purely so that code written against 0.x does not break on import. That
    interpretation is a guess. :func:`is_open` refuses it instead, which is why
    new code should use that.
    """
    venue = resolve(market)
    if isinstance(at, datetime):
        if at.tzinfo is None:
            at = at.replace(tzinfo=ZoneInfo(venue.timezone))
        return is_open(at, venue=venue.mic)
    return is_trading_day(_as_date(at), venue=venue.mic)


def data_status() -> dict:
    """Where the holiday data came from and how fresh it is.

    Check ``rule_only`` before trusting an exchange-holiday answer: True means no
    verified data loaded, so weekends and computed public holidays still apply
    but exchange closures are unknown.
    """
    return store.status()


def refresh_data(force: bool = False) -> str:
    """Fetch newer holiday data now rather than waiting for the daily check."""
    return store.refresh(force=force)


def holidays_between(start: date | datetime | str, end: date | datetime | str) -> Iterable[Holiday]:
    """Every statutory holiday in the half-open interval [start, end)."""
    a, b = _as_date(start), _as_date(end)
    for year in range(a.year, b.year + 1):
        for h in holidays(year):
            if a <= h.date < b:
                yield h
