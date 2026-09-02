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
from typing import Iterable

from .holidays import Holiday, Observance, easter_sunday, holiday_on, holidays, observances

__all__ = [
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
    "__version__",
]

__version__ = "0.1.1"

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
    """True during Nasdaq Vilnius continuous trading on a working day.

    `market` accepts the MIC code XVIL. Passing a date rather than a datetime
    tests the trading day only, ignoring the time of day.
    """
    if market.upper() not in {"XVIL", "VILNIUS", "NASDAQ_VILNIUS"}:
        raise ValueError(f"unknown market {market!r}; this package covers XVIL")
    if isinstance(at, datetime):
        if not is_business_day(at.date()):
            return False
        opens = at.replace(hour=_MARKET_OPEN[0], minute=_MARKET_OPEN[1], second=0, microsecond=0)
        closes = at.replace(hour=_MARKET_CLOSE[0], minute=_MARKET_CLOSE[1], second=0, microsecond=0)
        return opens <= at <= closes
    return is_business_day(at)


def holidays_between(start: date | datetime | str, end: date | datetime | str) -> Iterable[Holiday]:
    """Every statutory holiday in the half-open interval [start, end)."""
    a, b = _as_date(start), _as_date(end)
    for year in range(a.year, b.year + 1):
        for h in holidays(year):
            if a <= h.date < b:
                yield h
