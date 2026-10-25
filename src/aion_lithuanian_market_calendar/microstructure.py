"""Settlement days and intraday phases.

Settlement: TARGET, not the Lithuanian calendar
-----------------------------------------------
Euro payments and euro securities settlement run on TARGET (T2, and T2S for
securities), which closes on its own fixed days: New Year's Day, Good Friday,
Easter Monday, 1 May, 25 December and 26 December, in addition to weekends.
The ECB Governing Council set that list in December 2000 to apply from 2002
"until further notice", and it has not changed since.

That list is not the Lithuanian one, in both directions. 16 February, 11 March,
24 June, 6 July, 15 August, 1 and 2 November and 24 December are Lithuanian public
holidays on which TARGET settles. Good Friday is a TARGET closing day and not a
Lithuanian public holiday. So "is it a business day in Lithuania" and "does euro
settlement happen" are separate questions, answered by ``is_business_day`` and
:func:`is_settlement_day`.

Like the statutory holidays, the closing days are computed, not tabulated, so
this module needs no data and no network.

Phases: only what is sourced
----------------------------
:func:`get_market_phase` returns ``CONTINUOUS`` or ``CLOSED``. The venue rules
in ``venues`` hold each venue's continuous-trading window and nothing else.
Opening and closing auctions, pre-open and post-trading are not modelled,
because the published sources found so far disagree on them; returning a
pre-open phase on a guess would be worse than not returning one. The phase
strings match the Indian sibling package, so code can handle both.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

from .holidays import easter_sunday
from .sessions import session_bounds, to_venue_time
from .venues import resolve

__all__ = [
    "CONTINUOUS",
    "CLOSED",
    "PHASE_NAMES",
    "TARGET_RULE_EFFECTIVE_FROM",
    "TargetClosingDay",
    "get_market_phase",
    "is_settlement_day",
    "next_settlement_day",
    "phase_name",
    "target_closing_days",
]

CONTINUOUS = "CONTINUOUS"
CLOSED = "CLOSED"

#: Display names, English and Lithuanian.
PHASE_NAMES: dict[str, dict[str, str]] = {
    CONTINUOUS: {"en": "Continuous trading", "lt": "Nepertraukiama prekyba"},
    CLOSED: {"en": "Closed", "lt": "Prekyba nevyksta"},
}

#: The ECB decision of December 2000 applies from 1 January 2002.
TARGET_RULE_EFFECTIVE_FROM = date(2002, 1, 1)

_SOURCE = ("ECB, long-term calendar for TARGET closing days (press release of "
           "14 December 2000), applying from 2002 until further notice")


@dataclass(frozen=True)
class TargetClosingDay:
    """One day on which TARGET does not settle."""

    date: date
    name_en: str
    name_lt: str

    def __str__(self) -> str:  # pragma: no cover - display helper
        return f"{self.date.isoformat()}  {self.name_en} ({self.name_lt})"


def _as_date(value: date | datetime | str | None) -> date:
    if value is None:
        return date.today()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


@lru_cache(maxsize=64)
def target_closing_days(year: int) -> tuple[TargetClosingDay, ...]:
    """The six TARGET closing days of *year*, in date order.

    Some fall on a weekend in a given year; they are listed anyway, since the
    list is the rule, and a weekend is closed regardless.
    """
    if year < TARGET_RULE_EFFECTIVE_FROM.year:
        raise ValueError(f"the TARGET closing-day rule applies from 2002 ({_SOURCE})")
    easter = easter_sunday(year)
    return (
        TargetClosingDay(date(year, 1, 1), "New Year's Day", "Naujieji metai"),
        TargetClosingDay(easter - timedelta(days=2), "Good Friday", "Didysis penktadienis"),
        TargetClosingDay(easter + timedelta(days=1), "Easter Monday", "Velykų antroji diena"),
        TargetClosingDay(date(year, 5, 1), "Labour Day", "Tarptautinė darbo diena"),
        TargetClosingDay(date(year, 12, 25), "Christmas Day", "Šv. Kalėdos"),
        TargetClosingDay(date(year, 12, 26), "Second Day of Christmas", "Šv. Kalėdų antroji diena"),
    )


def is_settlement_day(when: date | datetime | str | None = None) -> bool:
    """True if TARGET settles euro payments and securities on this day.

    Weekends and the six TARGET closing days are not settlement days. Lithuanian
    public holidays other than those six are: 16 February, for example, is a
    settlement day although Lithuanian banks' offices are shut.
    """
    day = _as_date(when)
    if day.weekday() >= 5:
        return False
    return day not in {item.date for item in target_closing_days(day.year)}


def next_settlement_day(after: date | datetime | str | None = None) -> date:
    """The next TARGET settlement day strictly after *after*."""
    cursor = _as_date(after) + timedelta(days=1)
    while not is_settlement_day(cursor):
        cursor += timedelta(days=1)
    return cursor


def get_market_phase(at: datetime | None = None, venue: str = "XVIL") -> str:
    """``CONTINUOUS`` or ``CLOSED`` for *venue* at the instant *at*.

    *at* must be timezone-aware, as everywhere in this package; it defaults to
    now. The window is half-open: the closing minute is ``CLOSED``. Holidays,
    half-days and midday breaks come from the same rules and data as
    ``is_open``.
    """
    market = resolve(venue)
    moment = to_venue_time(at if at is not None else datetime.now(ZoneInfo("UTC")), market)
    bounds = session_bounds(moment.date(), market)
    if bounds is None:
        return CLOSED
    local = moment.time()
    if market.break_start and market.break_end and market.break_start <= local < market.break_end:
        return CLOSED
    opens, closes = bounds
    return CONTINUOUS if opens <= local < closes else CLOSED


def phase_name(phase: str, lang: str = "en") -> str:
    """The display name of *phase* in ``"en"`` or ``"lt"``."""
    try:
        return PHASE_NAMES[phase][lang]
    except KeyError:
        raise ValueError(f"unknown phase {phase!r} or language {lang!r}") from None
