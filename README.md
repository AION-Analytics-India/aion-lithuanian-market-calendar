# aion-lithuanian-market-calendar

**Lithuanian public holiday, bank and market calendar. Never needs updating.**

[![PyPI](https://img.shields.io/pypi/v/aion-lithuanian-market-calendar)](https://pypi.org/project/aion-lithuanian-market-calendar/)
[![Python](https://img.shields.io/pypi/pyversions/aion-lithuanian-market-calendar)](https://pypi.org/project/aion-lithuanian-market-calendar/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

*Lietuviškai: [README.lt.md](README.lt.md)*

```bash
pip install aion-lithuanian-market-calendar
```

```python
from aion_lithuanian_market_calendar import is_business_day, next_business_day, holiday_on

is_business_day()                       # is today a working day in Lithuania
is_business_day("2026-12-25")           # False
next_business_day("2026-12-24")         # date(2026, 12, 28)

holiday_on("2026-06-24")
# Holiday(date=2026-06-24, name_en="St John's Day, Midsummer", name_lt="Rasos ir Joninės")
```

## Why this never needs updating

Every Lithuanian statutory non-working day is **computable**. Twelve are fixed
dates. Two derive from Easter. Two are the first Sunday of a named month.

So this package calculates them rather than shipping a table of dates that goes
stale every December. Install it once and it is correct for 2027, 2040, and any
year after that, **offline, with no network call and no maintenance**.

That is a deliberate difference from calendars for markets whose holidays are
announced annually and genuinely cannot be derived.

**Easter uses the Gregorian (Western) computus.** Lithuania is predominantly
Catholic and observes Western Easter, not the Orthodox date. Getting this wrong
misplaces two holidays every year.

## The sixteen statutory holidays

| Date | English | Lietuviškai |
|---|---|---|
| 1 January | New Year's Day | Naujieji metai |
| 16 February | Day of Restoration of the State | Lietuvos valstybės atkūrimo diena |
| 11 March | Day of Restoration of Independence | Lietuvos nepriklausomybės atkūrimo diena |
| *moveable* | Easter Sunday | Šv. Velykos |
| *moveable* | Easter Monday | Antroji šv. Velykų diena |
| 1 May | International Labour Day | Tarptautinė darbo diena |
| *first Sunday of May* | Mother's Day | Motinos diena |
| *first Sunday of June* | Father's Day | Tėvo diena |
| 24 June | St John's Day, Midsummer | Rasos ir Joninės |
| 6 July | Statehood Day | Valstybės diena |
| 15 August | Assumption Day | Žolinė |
| 1 November | All Saints' Day | Visų šventųjų diena |
| 2 November | All Souls' Day | Mirusiųjų atminimo diena, Vėlinės |
| 24 December | Christmas Eve | Šv. Kūčios |
| 25 December | Christmas Day | Šv. Kalėdos |
| 26 December | Second Day of Christmas | Antroji šv. Kalėdų diena |

**No substitute days.** Lithuania does not move a holiday that falls on a
weekend to the following Monday. Assumption Day on Saturday 15 August 2026 is
simply absorbed.

## API

```python
is_business_day(when=None)          # working day for banks and offices
is_public_holiday(when=None)        # statutory non-working day
is_weekend(when=None)

next_business_day(after=None)
previous_business_day(before=None)
business_days_between(start, end)   # half-open interval

holidays(year)                      # all sixteen, ordered
holiday_on(day)                     # Holiday or None
easter_sunday(year)

is_market_open(at=None, market="XVIL")   # Nasdaq Vilnius
```

Dates accept `date`, `datetime`, an ISO string, or `None` for today.

## Scope

Covers the sixteen statutory **non-working** days (*šventės*).

Lithuania also has commemorative and flag days (*atmintinos dienos*), which are
official but remain **working days**, so they do not change business-day
arithmetic and are out of scope here.

Exchange session times are the one part of a market calendar that changes by
announcement rather than by rule. `is_market_open` uses standard Nasdaq Vilnius
continuous trading hours; confirm against the venue if you need intraday
precision.

## Verification

Easter is unit-tested against known dates for 2024, 2025, 2026, 2027, 2030 and
2035. Mother's Day and Father's Day are asserted to fall on a Sunday for every
year from 2024 to 2040. The full 2026 date list is pinned in the test suite.

Holiday dates should be confirmed against the Lithuanian Labour Code for any
use with legal or financial consequence. Corrections are welcome as issues.

## Related

- [aion-indian-market-calendar](https://pypi.org/project/aion-indian-market-calendar/) — the Indian sibling
- [aion-indian-market-intelligence](https://pypi.org/project/aion-indian-market-intelligence/)

MIT licensed. Built by **AION Analytics (India)**, an independent India-based
firm, not affiliated with Aion Analytics LLC (United States) or AION Labs
(Israel).
