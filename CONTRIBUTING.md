# Contributing

Corrections to holiday data are the most valuable contribution this project can
receive, and they do not require writing any code.

## Reporting a wrong date

Open an issue with the year, the date, and what it should be. If you can point
at the Labour Code or another primary source, include it. Holiday rules are the
one thing in this package that must be right, and a native speaker noticing a
wrong name or a missing day is worth more than a refactor.

### Three questions that are now answered

Earlier releases asked for help with three facts. A Lithuanian native speaker
confirmed all three in September 2026, and they are now settled:

1. **The list of sixteen is complete.** It matches article 123 of the Labour
   Code.
2. **Father's Day is the first Sunday of June** — 7 June 2026. One published
   source claimed 1 June 2026, which is a Monday.
3. **A holiday falling on a weekend is absorbed.** No replacement weekday is
   given. This is what the package already did, and it is correct.

The same review surfaced one thing worth repeating, because it is the most
common way to get a Lithuanian calendar wrong: **Užgavėnės is not a day off.**
Several commercial "nedarbo dienos" websites list seventeen days for 2026 by
including it. It is absent from article 123 and is an ordinary working day, so
it lives in `observances()`, never in `holidays()`.

## Code changes

1. Fork and branch from `main`.
2. Add a test. Holiday logic without a test will not be merged.
3. Run the suite: `python -m pytest tests -q`
4. Keep to PEP 8, four spaces, type hints where they help.

Holidays are computed rather than stored in a table, deliberately: it is what
makes the package correct for any future year without maintenance. Please do not
replace the computation with a data file.

## Licence

By contributing you agree your work is licensed under the MIT Licence.

## Links

- Package: https://pypi.org/project/aion-lithuanian-market-calendar/
- Website: https://dashboard.aiondashboard.site

## Reporting or fixing a holiday

A wrong date here makes someone's settlement job run on a day the market was
shut. It is the most valuable bug report this project can get.

**By issue** — the easiest route. Give the date, the venue, and the announcement
it comes from. The announcement matters: a date with no source cannot be checked
by the next person and cannot be defended when a user asks where it came from.

**By pull request** — use the CLI rather than editing JSON by hand, because it
keeps the two data directories in step and records why:

```bash
python -m ingest add-holiday --date 2026-11-17 --type exchange \
    --reason "Day of national mourning (Seimas resolution XIV-1234)"

python -m ingest add-half-day --date 2026-12-31 --close 12:30 \
    --reason "Nasdaq Baltic early close"

python ingest/build_manifest.py src/aion_lithuanian_market_calendar/data
python ingest/build_manifest.py data

python -m ingest verify          # manifests match, and the data is self-consistent
pytest -q
```

`verify` checks three things a hash cannot: that a per-venue list is not missing
a date the global list has (the per-venue list wins, so the date would silently
do nothing), that no day is both a full closure and a half-day, and that every
date belongs to the year its file claims. Each of those has actually been got
wrong here, and each was found by a failing test rather than by a user.

**Never edit `manifest.json` by hand.** It exists to prove the data files are the
ones the maintainer intended; a hash typed by a person proves nothing.

## Venue hours

`src/aion_lithuanian_market_calendar/venues.py` carries session rules only, and
each entry has a `verified_on` date. If you confirm one against the venue's own
published schedule, update that date in the same PR — an entry nobody has checked
in two years should be treated as a guess.

## Timezones

No UTC offset may appear in source. `zoneinfo` or nothing; an offset written down
is wrong twice a year, and CI fails the build if one appears.
