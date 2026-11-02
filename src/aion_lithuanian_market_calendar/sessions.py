"""Is this venue trading at this instant?

The bug this replaces
---------------------
Until 1.0.0 the answer was computed by taking the caller's datetime and calling
``.replace(hour=10)`` on it to build the open time. That does not convert
anything. It asks "is the wall clock between 10:00 and 15:55" in whatever
timezone the caller happened to pass — so the same instant gave different answers
depending on how it was expressed:

    12:00 Europe/Vilnius     -> True    correct
    the same instant in UTC  -> False   wrong
    the same instant in IST  -> True    right by luck, 14:30 is inside 10:00-15:55

Anyone outside Lithuania got wrong answers, which is most users of a package
published from India. Version 1.0.0 fixes it by converting to the venue's own
zone before comparing, and by refusing naive datetimes outright.

Why naive datetimes raise
-------------------------
A naive datetime has no answer. Treating it as venue-local would be a guess that
is right in one country, and treating it as UTC would be a guess that is right in
none. Both hide the caller's real mistake. So it raises, with a message that says
what to pass instead — the failure is cheap now and expensive in production.

Daylight saving is handled by ``zoneinfo``. No UTC offset is written down
anywhere in this package, because a written-down offset is wrong twice a year.
"""
from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from . import store
from .venues import Venue, resolve


def _zone(venue: Venue) -> ZoneInfo:
    return ZoneInfo(venue.timezone)


def to_venue_time(at: datetime, venue: Venue) -> datetime:
    """Convert an aware datetime into the venue's local time."""
    if at.tzinfo is None or at.tzinfo.utcoffset(at) is None:
        raise ValueError(
            "naive datetime has no answer here: pass a timezone-aware one, e.g. "
            "datetime.now(timezone.utc) or "
            f"datetime(2026, 9, 10, 12, 0, tzinfo=ZoneInfo({venue.timezone!r}))"
        )
    return at.astimezone(_zone(venue))


def session_bounds(day: date, venue: Venue) -> tuple[time, time] | None:
    """Opening and closing local times for a given day, or None if closed.

    Closed means: not a trading weekday, or an exchange holiday. A half-day
    returns the same open with the early close.
    """
    if not venue.trades_on_weekday(day.weekday()):
        return None
    if store.is_exchange_holiday(day, venue.mic):
        return None
    early = store.half_day_close(day, venue.mic)
    return (venue.opens, early or venue.closes)


def is_daylight_saving(day: date | None = None, venue: str = "XVIL") -> bool:
    """True if the venue's own zone is on daylight saving on this day (at local noon).

    The state comes from the IANA zone database through ``zoneinfo``, so no change
    date is written in this package and later years need no upkeep.

    Compares UTC offsets instead of reading ``tzinfo.dst()``. Some builds of the zone
    database record Europe/Dublin with its summer time as standard and a negative
    saving in winter, so ``dst()`` is inverted there. The higher offset of the year is
    summer in every build.
    """
    market = resolve(venue)
    day = day or date.today()
    zone = _zone(market)
    noon = datetime(day.year, day.month, day.day, 12, tzinfo=zone)
    year_offsets = [datetime(day.year, month, 1, 12, tzinfo=zone).utcoffset() for month in (1, 7)]
    return noon.utcoffset() > min(year_offsets)


def session_bounds_utc(day: date, venue: str = "XVIL") -> tuple[datetime, datetime] | None:
    """Open and close of this day's session as UTC datetimes, or None if closed.

    Venue hours stay fixed in local time, so these move by an hour when the venue's
    zone changes. Same holiday and half-day handling as ``session_bounds``.
    """
    market = resolve(venue)
    bounds = session_bounds(day, market)
    if bounds is None:
        return None
    zone, utc = _zone(market), ZoneInfo("UTC")
    return tuple(datetime.combine(day, clock, tzinfo=zone).astimezone(utc) for clock in bounds)


def is_open(at: datetime | None = None, venue: str = "XVIL") -> bool:
    """True if the venue is in continuous trading at this instant.

    ``at`` must be timezone-aware. Defaults to now, in UTC.

    Continuous trading only: opening and closing auctions, pre-open and
    post-close are not modelled, so a caller who needs those should treat this
    as "the main session" rather than "the venue is reachable".
    """
    market = resolve(venue)
    moment = to_venue_time(at if at is not None else datetime.now(ZoneInfo("UTC")), market)
    bounds = session_bounds(moment.date(), market)
    if bounds is None:
        return False
    opens, closes = bounds
    local = moment.time()
    if market.break_start and market.break_end and market.break_start <= local < market.break_end:
        return False
    return opens <= local <= closes


def is_trading_day(day: date | None = None, venue: str = "XVIL") -> bool:
    """Does the venue trade at all on this calendar day?"""
    market = resolve(venue)
    return session_bounds(day or date.today(), market) is not None


def next_trading_day(day: date | None = None, venue: str = "XVIL") -> date:
    """The next day the venue trades, strictly after ``day``."""
    from datetime import timedelta
    market = resolve(venue)
    cursor = (day or date.today()) + timedelta(days=1)
    # A venue closed for more than a fortnight is a data error, not a holiday.
    for _ in range(30):
        if session_bounds(cursor, market) is not None:
            return cursor
        cursor += timedelta(days=1)
    raise RuntimeError(f"{market.mic} appears closed for 30 days; the holiday data is wrong")
