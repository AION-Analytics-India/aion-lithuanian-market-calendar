"""Lithuanian statutory holidays, derived rather than tabulated.

Every one of Lithuania's sixteen statutory non-working days (šventės) is
computable for any year: twelve are fixed calendar dates, two derive from
Easter, and two are the first Sunday of a named month.

That matters for the design. The Indian sibling package ships a per-year data
file because Indian exchange holidays are announced annually and cannot be
derived. Lithuania's cannot drift in the same way, so this package computes
them instead. Once installed it is correct for 2027, 2040 and beyond with no
update, no network call and no maintenance.

Easter uses the Gregorian (Western) computus. Lithuania is predominantly
Catholic and observes Western Easter, not the Orthodox date. Using the wrong
computus would misplace two holidays every year.

**Source.** The list and the Lithuanian names follow article 123 of the Labour
Code (Darbo kodeksas, 123 straipsnis "Švenčių dienos") verbatim, in nominative
form. Article 123 enumerates fourteen items; two of them ("Kalėdų dienomis",
and the Easter Sunday-and-Monday pair) cover two calendar days each, which is
why sixteen dates fall out of fourteen provisions.

**Traditional celebrations are not holidays.** Užgavėnės, Joninių išvakarės and
similar folk days are widely printed on Lithuanian wall calendars and on several
commercial "nedarbo dienos" websites, but they are absent from article 123 and
are ordinary working days. They are exposed separately by :func:`observances`
and deliberately excluded from every business-day calculation. See the README.

Genuinely unpredictable events, such as a one-off national day of mourning
declared by the Seimas, cannot be derived by definition and are out of scope.
If one is ever needed it belongs in an optional override layer, not here: this
module stays purely computational so it can never go stale.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache

__all__ = ["Holiday", "Observance", "easter_sunday", "holidays", "holiday_on", "observances"]


@dataclass(frozen=True)
class Holiday:
    """One statutory non-working day."""

    date: date
    name_en: str
    name_lt: str
    #: True when the date moves year to year (Easter, Mother's Day, Father's Day).
    moveable: bool = False

    def __str__(self) -> str:  # pragma: no cover - display helper
        return f"{self.date.isoformat()}  {self.name_en} ({self.name_lt})"


@dataclass(frozen=True)
class Observance:
    """A traditional celebration that is **not** a day off.

    Kept apart from :class:`Holiday` so it can never leak into business-day
    arithmetic by accident.
    """

    date: date
    name_en: str
    name_lt: str
    moveable: bool = True

    def __str__(self) -> str:  # pragma: no cover - display helper
        return f"{self.date.isoformat()}  {self.name_en} ({self.name_lt}) [working day]"


def easter_sunday(year: int) -> date:
    """Gregorian (Western) Easter Sunday.

    Anonymous Gregorian algorithm, also called Meeus/Jones/Butcher. Valid for
    any year in the Gregorian calendar.
    """
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    lu = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * lu) // 451
    month, day = divmod(h + lu - 7 * m + 114, 31)
    return date(year, month, day + 1)


def _first_sunday(year: int, month: int) -> date:
    """First Sunday of a month. Monday is weekday() == 0, Sunday is 6."""
    d = date(year, month, 1)
    return d + timedelta(days=(6 - d.weekday()) % 7)


@lru_cache(maxsize=64)
def holidays(year: int) -> tuple[Holiday, ...]:
    """Every statutory non-working day in `year`, ordered by date.

    Lithuania does not shift a holiday that falls on a weekend to the following
    Monday, so no substitute-day logic applies. A holiday landing on a Saturday
    is simply absorbed.
    """
    easter = easter_sunday(year)
    items = [
        Holiday(date(year, 1, 1), "New Year's Day", "Naujieji metai"),
        Holiday(date(year, 2, 16), "Day of Restoration of the State of Lithuania",
                "Lietuvos valstybės atkūrimo diena"),
        Holiday(date(year, 3, 11), "Day of Restoration of Independence of Lithuania",
                "Lietuvos nepriklausomybės atkūrimo diena"),
        Holiday(easter, "Easter Sunday", "Šv. Velykos", moveable=True),
        Holiday(easter + timedelta(days=1), "Easter Monday", "Velykų antroji diena", moveable=True),
        Holiday(date(year, 5, 1), "International Labour Day", "Tarptautinė darbo diena"),
        Holiday(_first_sunday(year, 5), "Mother's Day", "Motinos diena", moveable=True),
        Holiday(_first_sunday(year, 6), "Father's Day", "Tėvo diena", moveable=True),
        Holiday(date(year, 6, 24), "Day of Dew and St John (Midsummer)", "Rasos ir Joninių diena"),
        Holiday(date(year, 7, 6), "Statehood Day and Day of the National Anthem",
                "Valstybės (Lietuvos karaliaus Mindaugo karūnavimo) ir Tautiškos giesmės diena"),
        Holiday(date(year, 8, 15), "Assumption Day",
                "Žolinė (Švč. Mergelės Marijos ėmimo į dangų diena)"),
        Holiday(date(year, 11, 1), "All Saints' Day", "Visų Šventųjų diena"),
        Holiday(date(year, 11, 2), "Day of Remembrance of the Dead (All Souls' Day)",
                "Mirusiųjų atminimo (Vėlinių) diena"),
        Holiday(date(year, 12, 24), "Christmas Eve", "Šv. Kūčios"),
        Holiday(date(year, 12, 25), "Christmas Day", "Šv. Kalėdos"),
        Holiday(date(year, 12, 26), "Second Day of Christmas", "Šv. Kalėdų antroji diena"),
    ]
    return tuple(sorted(items, key=lambda h: h.date))


@lru_cache(maxsize=64)
def observances(year: int) -> tuple[Observance, ...]:
    """Traditional celebrations that are **working days**, ordered by date.

    These are not in article 123 and are not days off. They are provided because
    Lithuanian wall calendars and several commercial holiday websites print them
    alongside the statutory list, so a caller comparing this package against such
    a calendar would otherwise think a day were missing.

    Nothing here affects :func:`~aion_lithuanian_market_calendar.is_business_day`,
    :func:`~aion_lithuanian_market_calendar.is_market_open` or any other
    business-day calculation.
    """
    # Shrove Tuesday: the day before Ash Wednesday, so Easter minus 47 days.
    return (
        Observance(easter_sunday(year) - timedelta(days=47),
                   "Shrove Tuesday (Carnival)", "Užgavėnės"),
    )


def holiday_on(day: date | datetime | str) -> Holiday | None:
    """The statutory holiday falling on `day`, or None.

    Accepts a date, a datetime, or an ISO string, matching every other
    date-taking function in this package.
    """
    if isinstance(day, datetime):
        day = day.date()
    elif not isinstance(day, date):
        day = date.fromisoformat(str(day).strip()[:10])
    for h in holidays(day.year):
        if h.date == day:
            return h
    return None
