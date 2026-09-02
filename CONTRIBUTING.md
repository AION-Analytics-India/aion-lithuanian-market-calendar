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
