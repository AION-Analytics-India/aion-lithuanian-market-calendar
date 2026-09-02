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
# Holiday(date=2026-06-24, name_en='Day of Dew and St John (Midsummer)',
#         name_lt='Rasos ir Joninių diena')
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

Names follow **article 123 of the Labour Code** (*Darbo kodeksas, 123 straipsnis
„Švenčių dienos"*) in nominative form. Article 123 lists fourteen provisions;
two of them cover two calendar days each — Easter Sunday together with Easter
Monday, and 25 with 26 December — which is why sixteen dates fall out of
fourteen provisions.

| Date | English | Lietuviškai |
|---|---|---|
| 1 January | New Year's Day | Naujieji metai |
| 16 February | Day of Restoration of the State of Lithuania | Lietuvos valstybės atkūrimo diena |
| 11 March | Day of Restoration of Independence of Lithuania | Lietuvos nepriklausomybės atkūrimo diena |
| *moveable* | Easter Sunday | Šv. Velykos |
| *moveable* | Easter Monday | Velykų antroji diena |
| 1 May | International Labour Day | Tarptautinė darbo diena |
| *first Sunday of May* | Mother's Day | Motinos diena |
| *first Sunday of June* | Father's Day | Tėvo diena |
| 24 June | Day of Dew and St John (Midsummer) | Rasos ir Joninių diena |
| 6 July | Statehood Day and Day of the National Anthem | Valstybės (Lietuvos karaliaus Mindaugo karūnavimo) ir Tautiškos giesmės diena |
| 15 August | Assumption Day | Žolinė (Švč. Mergelės Marijos ėmimo į dangų diena) |
| 1 November | All Saints' Day | Visų Šventųjų diena |
| 2 November | Day of Remembrance of the Dead (All Souls' Day) | Mirusiųjų atminimo (Vėlinių) diena |
| 24 December | Christmas Eve | Šv. Kūčios |
| 25 December | Christmas Day | Šv. Kalėdos |
| 26 December | Second Day of Christmas | Šv. Kalėdų antroji diena |

**No substitute days.** Lithuania does not move a holiday that falls on a
weekend to the following Monday. Assumption Day on Saturday 15 August 2026 is
simply absorbed, and the Monday after is an ordinary working day.

## Užgavėnės is not a day off

Several Lithuanian calendar and accounting websites publish a *„nedarbo dienos"*
list of **seventeen** days for 2026, the extra entry being **Užgavėnės** (Shrove
Tuesday, 17 February 2026).

Užgavėnės does not appear in article 123. It is a traditional pre-Lent
celebration and an **ordinary working day**. Treating it as a day off would
shift every downstream settlement and payroll date that crosses it.

Because a caller comparing this package against a printed wall calendar would
otherwise think a day were missing, it is exposed explicitly — and separately:

```python
from aion_lithuanian_market_calendar import observances, is_business_day

observances(2026)
# (Observance(date=2026-02-17, name_en='Shrove Tuesday (Carnival)',
#             name_lt='Užgavėnės'),)

is_business_day("2026-02-17")   # True — it is a working day
```

`observances()` never affects `is_business_day`, `is_market_open`, or any other
business-day arithmetic. The test suite asserts that separation for every year
from 2024 to 2040.

## API

```python
is_business_day(when=None)          # working day for banks and offices
is_public_holiday(when=None)        # statutory non-working day
is_weekend(when=None)

next_business_day(after=None)
previous_business_day(before=None)
business_days_between(start, end)   # half-open interval

holidays(year)                      # all sixteen, ordered
holidays_between(start, end)        # half-open interval
holiday_on(day)                     # Holiday or None
observances(year)                   # traditional days that are NOT days off
easter_sunday(year)

is_market_open(at=None, market="XVIL")   # Nasdaq Vilnius
```

Dates accept `date`, `datetime`, an ISO string, or `None` for today.

## Scope

Covers the sixteen statutory **non-working** days (*šventės*) of article 123.

Lithuania also has commemorative and flag days (*atmintinos dienos*), which are
official but remain **working days**, so they do not change business-day
arithmetic and are out of scope here. Traditional celebrations are likewise not
days off; the one most often mistaken for one, Užgavėnės, is covered above.

Exchange session times are the one part of a market calendar that changes by
announcement rather than by rule. `is_market_open` uses standard Nasdaq Vilnius
continuous trading hours; confirm against the venue if you need intraday
precision.

## Verification

Easter is unit-tested against known dates for 2024, 2025, 2026, 2027, 2030 and
2035. Mother's Day and Father's Day are asserted to fall on a Sunday for every
year from 2024 to 2040. The full 2026 date list and every Lithuanian holiday
name are pinned in the test suite.

The holiday list and its Lithuanian spellings were checked against the text of
article 123 of the Labour Code, and independently reviewed by a Lithuanian
native speaker in September 2026. That review confirmed three things this
package had implemented but could not previously source:

- the list of sixteen is **complete**;
- Father's Day is the **first Sunday of June** (7 June 2026), not 1 June as one
  published source claimed — 1 June 2026 is a Monday;
- a holiday falling on a weekend gets **no replacement weekday**.

Version 0.1.1 corrected six Lithuanian names against the statutory wording,
most consequentially `Visų šventųjų` → **`Visų Šventųjų`** and the restoration
of `ir Tautiškos giesmės diena` to the 6 July name. No date changed.

Confirm against the Labour Code for any use with legal or financial
consequence. Corrections are welcome as issues.

## Related

- [aion-indian-market-calendar](https://pypi.org/project/aion-indian-market-calendar/) — the Indian sibling
- [aion-indian-market-intelligence](https://pypi.org/project/aion-indian-market-intelligence/)

MIT licensed. Built by **AION Analytics (India)**, an independent India-based
firm, not affiliated with Aion Analytics LLC (United States) or AION Labs
(Israel).
